"""RAG ration generation: retrieve eligible meals, ask an LLM to arrange IDs."""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, OpenAIError
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import AIGeneration, Meal, Profile, Ration, RationMeal, User

logger = logging.getLogger(__name__)

DIET_COMPATIBILITY = {
    "omnivore": ["omnivore", "vegetarian", "vegan", "pescatarian"],
    "vegetarian": ["vegetarian", "vegan"],
    "vegan": ["vegan"],
    "pescatarian": ["pescatarian", "vegetarian", "vegan"],
}
MEAL_SLOTS = {
    3: [("Завтрак", "breakfast", "breakfast"), ("Обед", "lunch", "lunch"), ("Ужин", "dinner", "dinner")],
    4: [("Завтрак", "breakfast", "breakfast"), ("Обед", "lunch", "lunch"),
        ("Перекус", "snack", "snack"), ("Ужин", "dinner", "dinner")],
    5: [("Завтрак", "breakfast", "breakfast"), ("2-й завтрак", "breakfast", "second_breakfast"),
        ("Обед", "lunch", "lunch"), ("Полдник", "snack", "snack"), ("Ужин", "dinner", "dinner")],
}
EXCLUSION_ROOTS = {
    "мяс": ["мяс", "курин", "индейк", "говядин", "свин", "баран"],
    "рыб": ["рыб", "лосос", "тунец", "треск", "форел"],
    "молок": ["молок", "молоч", "творог", "йогурт", "сыр", "сливк"],
    "молоч": ["молок", "молоч", "творог", "йогурт", "сыр", "сливк"],
    "орех": ["орех", "миндал", "фундук", "кешью", "грецк"],
    "арахис": ["арахис"], "яйц": ["яйц"],
    "глютен": ["глютен", "хлеб", "макарон", "пшениц"],
    "пшениц": ["глютен", "хлеб", "макарон", "пшениц"],
    "соя": ["соя", "соев"],
    "лактоз": ["молок", "молоч", "творог", "йогурт", "сыр", "сливк"],
}
GOAL_ALIASES = {
    "maintain": "maintain", "поддерживать форму": "maintain", "поддержать форму": "maintain",
    "сохранить форму": "maintain", "lose_weight": "lose_weight", "сбросить вес": "lose_weight",
    "похудеть": "lose_weight", "gain_weight": "gain_weight", "набрать массу": "gain_weight",
    "набрать вес": "gain_weight",
}


@lru_cache(maxsize=1)
def _embedding_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Для RAG-генерации установите зависимости backend/requirements.txt") from exc
    return SentenceTransformer(settings.embedding_model, device="cpu")


def _encode(text_value: str) -> list[float]:
    vector = _embedding_model().encode(text_value, normalize_embeddings=True)
    return [float(value) for value in vector]


def _normalize_goal(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().casefold()
    return GOAL_ALIASES.get(normalized, normalized)


def _restriction_patterns(restrictions: str | None) -> list[str]:
    if not restrictions:
        return []
    fragments = re.split(r"[,;\n]+|\s+и\s+", restrictions.casefold())
    roots: set[str] = set()
    for fragment in fragments:
        fragment = re.sub(r"^\s*(без|исключить|исключи|не употреблять|не есть|аллергия на|аллергия)\s+", "", fragment).strip()
        if not fragment:
            continue
        matched = False
        for key, variants in EXCLUSION_ROOTS.items():
            if key in fragment:
                roots.update(variants)
                matched = True
        if not matched:
            roots.add(fragment)
    return [f"%{root}%" for root in sorted(roots)]


async def _profile(db: AsyncSession, user: User) -> Profile:
    value = (await db.execute(text("SELECT * FROM profiles WHERE user_id = :user_id"), {"user_id": user.id})).mappings().first()
    if value is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.flush()
        return profile
    # Keep the database mapping as a light object; no ORM schema changes are needed.
    return Profile(**dict(value))


async def _retrieve_candidates(db: AsyncSession, profile: Profile, meal_type: str,
                               query: str, limit: int = 5) -> list[dict[str, Any]]:
    vector = await asyncio.to_thread(_encode, query)
    vector_literal = "[" + ",".join(f"{number:.8f}" for number in vector) + "]"
    goal = _normalize_goal(profile.goal)
    diets = DIET_COMPATIBILITY.get(profile.diet_type, [profile.diet_type])
    exclusions = _restriction_patterns(profile.restrictions)
    filters = [
        "m.status = 'published'",
        "m.embedding IS NOT NULL",
        "m.meal_type = :meal_type",
        "m.diet_type = ANY(CAST(:diet_types AS varchar[]))",
    ]
    params: dict[str, Any] = {"meal_type": meal_type, "diet_types": diets,
                              "embedding": vector_literal, "limit": limit}
    if goal:
        filters.append("m.goal = :goal")
        params["goal"] = goal
    if profile.max_cooking_time is not None:
        filters.append("m.cooking_time <= :max_cooking_time")
        params["max_cooking_time"] = profile.max_cooking_time
    if exclusions:
        filters.extend([
            """NOT EXISTS (SELECT 1 FROM unnest(COALESCE(m.allergens, ARRAY[]::text[])) AS a(value)
               WHERE lower(a.value) LIKE ANY(CAST(:exclusions AS text[])))""",
            """NOT EXISTS (SELECT 1 FROM meal_products mp JOIN products p ON p.id = mp.product_id
               WHERE mp.meal_id = m.id AND (lower(p.name) LIKE ANY(CAST(:exclusions AS text[]))
               OR lower(p.category) LIKE ANY(CAST(:exclusions AS text[]))))""",
        ])
        params["exclusions"] = exclusions
    statement = text(f"""
        SELECT m.id, m.name, m.meal_type, m.calories, m.protein, m.fat, m.carbs,
               m.cost, m.cooking_time, m.servings,
               1 - (m.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM meals m
        WHERE {' AND '.join(filters)}
        ORDER BY m.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)
    rows = (await db.execute(statement, params)).mappings().all()
    return [dict(row) for row in rows]


def _parse_model_output(output: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", output, flags=re.IGNORECASE).strip()
    start = cleaned.find("{")
    if start < 0:
        raise ValueError("В ответе модели не найден JSON")
    try:
        value, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    except json.JSONDecodeError as exc:
        raise ValueError("Модель вернула некорректный JSON") from exc
    if not isinstance(value, dict) or not isinstance(value.get("days"), list):
        raise ValueError("В JSON модели отсутствует массив days")
    return value


def _build_prompt(profile: Profile, days: int, extra_request: str,
                  groups: list[dict[str, Any]]) -> str:
    slots = MEAL_SLOTS[profile.meals_per_day]
    budget = f"до {profile.budget} рублей в день" if profile.budget is not None else "без заданного лимита"
    preferences = profile.preferences or "не указаны"
    lines = [
        "Составь рацион питания на русском языке.",
        f"Дней: {days}. Количество приёмов пищи в день: {len(slots)}.",
        f"Порядок приёмов пищи: {', '.join(label for label, _, _ in slots)}.",
        f"Цель: {profile.goal or 'maintain'}. Тип питания: {profile.diet_type}.",
        f"Бюджет: {budget}. Предпочтения профиля: {preferences}.",
        f"Пожелания к этому рациону: {extra_request.strip() or 'не указаны'}.",
        "Используй исключительно candidate_id из разрешённого списка каждого слота. Не выдумывай блюда или ID.",
        "Ответь только JSON без Markdown в форме: {\"days\":[{\"day\":1,\"meals\":[\"M001\"]}],\"notes\":[]}.",
        "В каждом дне укажи от 1 до указанного максимума ID. Количество блюд может отличаться между днями.",
        "Не более одного блюда в каждом слоте в день; ID внутри meals могут идти в любом порядке.",
        "Старайся приблизиться к числу приёмов пищи профиля, если подходят кандидаты.",
        "Кандидаты:",
    ]
    for group in groups:
        lines.append(f"Слот {group['slot']} ({group['meal_type']}):")
        for candidate in group["candidates"]:
            lines.append(
                f"  [{candidate['candidate_id']}] {candidate['name']} — {candidate['calories']} ккал; "
                f"Б {candidate['protein']} г, Ж {candidate['fat']} г, У {candidate['carbs']} г; "
                f"цена {candidate['cost']} ₽, готовка {candidate['cooking_time']} мин"
            )
    lines += [f"В days должны быть ровно {days} дней с номерами от 1 до {days}.",
              f"На день разрешено не более {len(slots)} ID, не более одного ID на слот."]
    return "\n".join(lines)


async def _ask_model(prompt: str, model: str) -> tuple[str, dict[str, Any]]:
    api_key = (settings.openrouter_api_key or "").strip()
    if not api_key:
        raise HTTPException(503, "Не задан OPENROUTER_API_KEY для генерации рациона")
    try:
        def request_completion():
            with OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=settings.openrouter_timeout_seconds,
            ) as client:
                return client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )

        completion = await asyncio.to_thread(request_completion)
    except AuthenticationError as exc:
        logger.exception("OpenRouter authentication failed for model %s", model)
        raise HTTPException(
            502,
            "OpenRouter отклонил OPENROUTER_API_KEY. Проверьте ключ в backend/.env "
            "(без префикса Bearer) и перезапустите API.",
        ) from exc
    except APITimeoutError as exc:
        raise HTTPException(504, "Модель не ответила за отведённое время") from exc
    except APIConnectionError as exc:
        raise HTTPException(502, "Не удалось подключиться к OpenRouter") from exc
    except APIStatusError as exc:
        logger.exception("OpenRouter returned HTTP %s for model %s", exc.status_code, model)
        raise HTTPException(502, f"OpenRouter вернул HTTP {exc.status_code} для модели {model}") from exc
    except OpenAIError as exc:
        logger.exception("OpenAI SDK request failed for model %s", model)
        raise HTTPException(502, f"Ошибка OpenAI SDK при запросе модели {model}") from exc

    logger.info(
        "Raw OpenRouter completion before extraction (%s): %s",
        model,
        completion.model_dump_json(exclude_none=True)[:240],
    )
    try:
        choice = completion.choices[0]
        message = choice.message
        content = message.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else getattr(part, "text", "")
                for part in content
            )
        if isinstance(content, str):
            raw_preview = content[:240].replace("\r", "\\r").replace("\n", "\\n")
        else:
            raw_preview = message.model_dump_json(exclude_none=True)[:240]
        logger.info("Raw model response before JSON parsing (%s): %s", model, raw_preview or "<empty>")
        if not isinstance(content, str) or not content.strip():
            refusal = getattr(message, "refusal", None)
            finish_reason = getattr(choice, "finish_reason", None)
            logger.warning("Model returned no text content: finish_reason=%s refusal=%s", finish_reason, refusal)
            raise HTTPException(
                502,
                f"Модель {model} не вернула текстовый ответ (finish_reason={finish_reason}, refusal={refusal or 'нет'}).",
            )
    except HTTPException:
        raise
    except (IndexError, AttributeError, TypeError, ValueError) as exc:
        logger.exception("Unexpected OpenRouter completion format for model %s", model)
        raise HTTPException(502, "OpenRouter вернул ответ без ожидаемого choices[0].message.content") from exc
    return content, completion.usage.model_dump(exclude_none=True) if completion.usage else {}


async def generate(db: AsyncSession, user: User, tags: list[str], period_days: int,
                   extra_request: str = "", model: str | None = None) -> Ration:
    """Retrieve meals by profile+embedding, validate model JSON, persist ration and audit."""
    if not (settings.openrouter_api_key or "").strip():
        raise HTTPException(503, "Добавьте OPENROUTER_API_KEY в backend/.env перед генерацией")
    profile = await _profile(db, user)
    count = int(profile.meals_per_day or 3)
    if count not in MEAL_SLOTS:
        raise HTTPException(422, "Количество приёмов пищи должно быть от 3 до 5; исправьте профиль")
    slots = MEAL_SLOTS[count]
    selected_model = (model or settings.openrouter_model).strip()
    if not selected_model or len(selected_model) > 150:
        raise HTTPException(422, "Некорректный идентификатор модели")
    request_text = ", ".join(tags + ([extra_request.strip()] if extra_request.strip() else []))

    groups: list[dict[str, Any]] = []
    candidates_by_id: dict[str, dict[str, Any]] = {}
    allowed_slots: dict[str, str] = {}
    retrieved_by_type: dict[str, list[dict[str, Any]]] = {}
    next_id = 1
    goal = _normalize_goal(profile.goal) or "без заданной цели"
    for label, meal_type, ration_meal_type in slots:
        if meal_type in retrieved_by_type:
            # The notebook uses the same breakfast candidate pool for both breakfast slots.
            rows = retrieved_by_type[meal_type]
        else:
            query = ". ".join(part for part in (label, goal, profile.preferences or "", request_text) if part)
            try:
                rows = await _retrieve_candidates(db, profile, meal_type, query)
            except RuntimeError as exc:
                raise HTTPException(503, str(exc)) from exc
            retrieved_by_type[meal_type] = rows
        candidates = []
        for row in rows:
            candidate_id = f"M{next_id:03d}"
            next_id += 1
            candidate = {"candidate_id": candidate_id, **row}
            candidates.append(candidate)
            candidates_by_id[candidate_id] = candidate
            allowed_slots[candidate_id] = ration_meal_type
        if not candidates:
            raise HTTPException(422, f"Не найдено подходящих блюд для слота «{label}». Проверьте цель, диету и ограничения профиля.")
        groups.append({"slot": label, "meal_type": meal_type, "candidates": candidates})

    prompt = _build_prompt(profile, period_days, request_text, groups)
    output, usage = await _ask_model(prompt, selected_model)
    try:
        plan = _parse_model_output(output)
        days = plan["days"]
        if len(days) != period_days:
            raise ValueError(f"Ожидалось дней: {period_days}, получено: {len(days)}")
        parsed_days: dict[int, list[str]] = {}
        for item in days:
            day_number = int(item["day"])
            if day_number in parsed_days or not 1 <= day_number <= period_days:
                raise ValueError("Номера дней должны быть уникальными и идти в диапазоне плана")
            meal_ids = item["meals"]
            if not isinstance(meal_ids, list) or not 1 <= len(meal_ids) <= len(slots):
                raise ValueError(f"В день {day_number} должно быть от 1 до {len(slots)} блюд")
            used_slots: set[str] = set()
            for candidate_id in meal_ids:
                if candidate_id not in candidates_by_id:
                    raise ValueError(f"Неизвестный candidate_id: {candidate_id}")
                meal_slot = allowed_slots[candidate_id]
                if meal_slot in used_slots:
                    raise ValueError(f"В день {day_number} повторяется слот {meal_slot}")
                used_slots.add(meal_slot)
            parsed_days[day_number] = meal_ids
        if sorted(parsed_days) != list(range(1, period_days + 1)):
            raise ValueError("Модель пропустила один или несколько дней")
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(502, f"Не удалось проверить ответ модели: {exc}") from exc

    today = date.today()
    target_calories = {"maintain": 1800, "lose_weight": 1400, "gain_weight": 2200}.get(profile.goal, 1800)
    ration = Ration(user_id=user.id, date_from=today, date_to=today + timedelta(days=period_days - 1),
                    calories_target=target_calories, status="active")
    db.add(ration)
    await db.flush()
    for day_number, candidate_ids in parsed_days.items():
        meal_date = today + timedelta(days=day_number - 1)
        for candidate_id in candidate_ids:
            meal_type = allowed_slots[candidate_id]
            db.add(RationMeal(ration_id=ration.id, meal_id=str(candidates_by_id[candidate_id]["id"]),
                              date=meal_date, meal_type=meal_type, servings=1))
    db.add(AIGeneration(user_id=user.id, ration_id=ration.id, prompt=prompt, response=output,
                        provider="openrouter", model=selected_model, status="completed",
                        input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
                        completed_at=datetime.now(timezone.utc)))
    return ration
