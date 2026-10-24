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
    5: [("Завтрак", "breakfast", "breakfast"), ("2-й завтрак", "snack", "second_breakfast"),
        ("Обед", "lunch", "lunch"), ("Полдник", "snack", "snack"), ("Ужин", "dinner", "dinner")],
}
EXCLUSION_SYNONYMS: dict[str, list[str]] = {
    # Яйца
    "яйц": ["яйц", "яиц", "яич", "омлет", "шакшук", "фриттат"],
    "яиц": ["яйц", "яиц", "яич", "омлет", "шакшук", "фриттат"],
    "яич": ["яйц", "яиц", "яич", "омлет", "шакшук", "фриттат"],
    "омлет": ["яйц", "яиц", "яич", "омлет", "шакшук", "фриттат"],
    "шакшук": ["яйц", "яиц", "яич", "омлет", "шакшук"],
    "фриттат": ["яйц", "яиц", "яич", "омлет", "фриттат"],
    # Молочные продукты и лактоза
    "молок": ["молок", "молоч", "творог", "йогурт", "сыр", "сливк", "кефир", "ряженк"],
    "молоч": ["молок", "молоч", "творог", "йогурт", "сыр", "сливк", "кефир", "ряженк"],
    "лактоз": ["молок", "молоч", "творог", "йогурт", "сыр", "сливк", "лактоз"],
    "творог": ["творог", "сырник", "запеканк"],
    "сырник": ["творог", "сырник"],
    "сыр": ["сыр"],
    # Рыба и морепродукты
    "рыб": ["рыб", "лосос", "тунец", "треск", "форел", "горбуш", "судак", "хек", "семг"],
    "тунец": ["тунец", "рыб"],
    "форел": ["форел", "рыб"],
    "лосос": ["лосос", "семг", "рыб"],
    "треск": ["треск", "рыб"],
    "морепродукт": ["морепродукт", "креветк", "кальмар", "миди", "осьминог"],
    "креветк": ["креветк", "морепродукт"],
    # Мясо и птица
    "мяс": ["мяс", "курин", "куриц", "индейк", "говядин", "свин", "баран", "фарш"],
    "куриц": ["курин", "куриц"],
    "курин": ["курин", "куриц"],
    "индейк": ["индейк"],
    "говядин": ["говядин"],
    "свин": ["свин"],
    # Орехи
    "орех": ["орех", "миндал", "фундук", "кешью", "грецк", "арахис", "фисташк"],
    "арахис": ["арахис", "орех"],
    "миндал": ["миндал", "орех"],
    # Глютен и злаки
    "глютен": ["глютен", "хлеб", "макарон", "пшениц", "мук", "выпечк"],
    "пшениц": ["глютен", "хлеб", "макарон", "пшениц", "мук"],
    # Соя
    "соя": ["соя", "соев"],
    # Грибы
    "гриб": ["гриб", "шампиньон"],
}
EXCLUSION_PREFIX_RE = re.compile(
    r"(?:у меня\s+)?(?:аллергия(?:\s+на)?|без|исключить|исключи|не\s+употреблять|не\s+ем|не\s+есть|нельзя|запрет(?:\s+на)?)\s+([^,;\n]+)",
    re.IGNORECASE,
)
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


def _extract_restriction_patterns(profile_restrictions: str | None, *free_texts: str | None) -> list[str]:
    roots: set[str] = set()

    # 1. From dedicated profile restrictions/allergies
    if profile_restrictions:
        fragments = re.split(r"[,;\n]+|\s+и\s+", str(profile_restrictions).casefold())
        for fragment in fragments:
            clean = re.sub(
                r"^\s*(?:у меня\s+)?(?:аллергия(?:\s+на)?|без|исключить|исключи|не\s+употреблять|не\s+ем|не\s+есть|нельзя)\s+",
                "",
                fragment,
            ).strip()
            if not clean:
                continue
            matched = False
            for key, variants in EXCLUSION_SYNONYMS.items():
                if key in clean:
                    roots.update(variants)
                    matched = True
            if not matched and len(clean) >= 3:
                stem = clean[:5] if len(clean) > 5 else clean
                roots.add(stem)

    # 2. From free-form texts (extra_request, preferences text, tags)
    for text_val in free_texts:
        if not text_val:
            continue
        text_lower = str(text_val).casefold()

        # Check explicit prefixes like 'аллергия на яйца', 'без яиц', 'не ем яйца'
        for match in EXCLUSION_PREFIX_RE.finditer(text_lower):
            target = match.group(1).strip()
            words = [w for w in re.split(r"[\s,;]+", target) if len(w) >= 3]
            for w in words:
                matched = False
                for key, variants in EXCLUSION_SYNONYMS.items():
                    if key in w:
                        roots.update(variants)
                        matched = True
                if not matched and len(w) >= 3:
                    roots.add(w[:5] if len(w) > 5 else w)

        # Check if user mentioned allergen alongside allergy/negative words
        has_negative_context = any(
            marker in text_lower
            for marker in ("аллерг", "не ем", "не есть", "без ", "исключ", "нельзя", "запрет")
        )
        if has_negative_context:
            for key, variants in EXCLUSION_SYNONYMS.items():
                if re.search(rf"\b{key}", text_lower) or (f" {key}" in text_lower):
                    roots.update(variants)

    return [f"%{root}%" for root in sorted(roots)]


def _is_meal_excluded(meal: dict[str, Any], exclusion_patterns: list[str]) -> bool:
    if not exclusion_patterns:
        return False
    name = (meal.get("name") or "").lower()
    desc = (meal.get("description") or "").lower()
    allergens = [str(a).lower() for a in (meal.get("allergens") or [])]
    for pattern in exclusion_patterns:
        raw_root = pattern.strip("%").lower()
        if not raw_root:
            continue
        if raw_root in name or raw_root in desc:
            return True
        for allergen in allergens:
            if raw_root in allergen:
                return True
    return False


async def _profile(db: AsyncSession, user: User) -> Profile:
    value = (await db.execute(text("SELECT * FROM profiles WHERE user_id = :user_id"), {"user_id": user.id})).mappings().first()
    if value is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        await db.flush()
        return profile
    return Profile(**dict(value))


async def _retrieve_candidates(db: AsyncSession, profile: Profile, meal_type: str,
                               query: str, exclusions: list[str], limit: int = 16) -> list[dict[str, Any]]:
    vector = await asyncio.to_thread(_encode, query)
    vector_literal = "[" + ",".join(f"{number:.8f}" for number in vector) + "]"
    goal = _normalize_goal(profile.goal)
    diets = DIET_COMPATIBILITY.get(profile.diet_type, [profile.diet_type])
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
            """NOT (lower(m.name) LIKE ANY(CAST(:exclusions AS text[])))""",
            """NOT (lower(COALESCE(m.description, '')) LIKE ANY(CAST(:exclusions AS text[])))""",
        ])
        params["exclusions"] = exclusions
    statement = text(f"""
        SELECT m.id, m.name, m.meal_type, m.calories, m.protein, m.fat, m.carbs,
               m.cost, m.cooking_time, m.servings, m.allergens, m.description,
               1 - (m.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM meals m
        WHERE {' AND '.join(filters)}
        ORDER BY m.embedding <=> CAST(:embedding AS vector)
        LIMIT :limit
    """)
    rows = [dict(row) for row in (await db.execute(statement, params)).mappings().all()]
    rows = [r for r in rows if not _is_meal_excluded(r, exclusions)]

    # If strict goal/cooking_time filter returned too few candidates, relax goal to ensure variety
    if len(rows) < min(5, limit) and "goal" in params:
        relaxed_filters = [f for f in filters if f != "m.goal = :goal"]
        relaxed_params = {k: v for k, v in params.items() if k != "goal"}
        existing_ids = {r["id"] for r in rows}
        statement_relaxed = text(f"""
            SELECT m.id, m.name, m.meal_type, m.calories, m.protein, m.fat, m.carbs,
                   m.cost, m.cooking_time, m.servings, m.allergens, m.description,
                   1 - (m.embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM meals m
            WHERE {' AND '.join(relaxed_filters)}
            ORDER BY m.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        extra_rows = (await db.execute(statement_relaxed, relaxed_params)).mappings().all()
        for r in extra_rows:
            row_dict = dict(r)
            if row_dict["id"] not in existing_ids and not _is_meal_excluded(row_dict, exclusions):
                rows.append(row_dict)
                existing_ids.add(row_dict["id"])
                if len(rows) >= limit:
                    break

    return rows


def _parse_model_output(output: str) -> dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?", "", output, flags=re.IGNORECASE).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("В ответе модели не найден JSON")
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("Модель вернула некорректный JSON") from exc
    if not isinstance(value, dict) or not isinstance(value.get("days"), list):
        raise ValueError("В JSON модели отсутствует массив days")
    return value


def _build_prompt(profile: Profile, days: int, extra_request: str,
                  groups: list[dict[str, Any]], exclusions: list[str]) -> str:
    slots = MEAL_SLOTS[profile.meals_per_day]
    budget = f"до {profile.budget} рублей в день" if profile.budget is not None else "без ограничений"
    preferences = profile.preferences or "не указаны"
    slot_names = [label for label, _, _ in slots]

    lines = [
        "Ты — профессиональный шеф-диетолог. Составь гармоничный и разнообразный рацион питания на русском языке.",
        f"Период плана: ровно {days} дней (с 1 по {days}).",
        f"Количество приёмов пищи в день: ровно {len(slots)}.",
        f"Слоты на каждый день: {', '.join(slot_names)}.",
        f"Цель: {profile.goal or 'maintain'}. Тип питания: {profile.diet_type}.",
        f"Дневной бюджет: {budget}. Предпочтения профиля: {preferences}.",
        f"Особые пожелания к рациону: {extra_request.strip() or 'не указаны'}.",
    ]
    if exclusions:
        clean_ex = [r.strip("%") for r in exclusions]
        lines.append(f"СТРОГИЕ АЛЛЕРГИИ И ИСКЛЮЧЕНИЯ: {', '.join(clean_ex)}.")
        lines.append("КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО включать блюда, содержащие эти аллергены/продукты (яйца, омлеты и т.д.)!")

    lines.extend([
        "",
        "ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА СОСТАВЛЕНИЯ:",
        f"1. В КАЖДОМ дне (от day 1 до day {days}) выбери РОВНО по одному блюду для каждого слота: {', '.join(slot_names)} (всего ровно {len(slots)} блюда в день).",
        "2. Используй ТОЛЬКО candidate_id из списка кандидатов ниже. Не выдумывай несуществующие ID.",
        f"3. БЕЗ ПОВТОРОВ (СТРОГО УНИКАЛЬНЫЕ БЛЮДА): Каждое выбранное блюдо (candidate_id) должно встречаться в плане МАКСИМУМ 1 РАЗ за весь период ({days} дней). Все завтраки должны быть РАЗНЫМИ, все обеды — РАЗНЫМИ, все ужины — РАЗНЫМИ! Ни одно блюдо не должно повторяться в разные дни.",
        "4. Для каждого слота выбирай candidate_id строго из списка кандидатов, относящихся к этому слоту.",
        "5. Ни при каких обстоятельствах не включай блюда, нарушающие указанные аллергии или диету.",
        "",
        "ФОРМАТ ОТВЕТА (СТРОГО JSON БЕЗ MARKDOWN):",
        "{\"days\":[{\"day\":1,\"meals\":[\"M001\",\"M006\",\"M011\"]},{\"day\":2,\"meals\":[\"...\"]}],\"notes\":[]}",
        "",
        "КАНДИДАТЫ ПО СЛОТАМ:",
    ])
    for group in groups:
        lines.append(f"Слот «{group['slot']}» ({group['meal_type']}):")
        for candidate in group["candidates"]:
            allergens_info = f"; аллергены: {', '.join(candidate['allergens'])}" if candidate.get("allergens") else ""
            lines.append(
                f"  [{candidate['candidate_id']}] {candidate['name']} — {candidate['calories']} ккал; "
                f"Б: {candidate['protein']}г, Ж: {candidate['fat']}г, У: {candidate['carbs']}г; "
                f"цена {candidate['cost']} ₽{allergens_info}"
            )
    lines.append("")
    lines.append(f"ВНИМАНИЕ: массив days должен содержать ровно {days} элементов (day 1 .. day {days}).")
    lines.append(f"В каждом дне массив meals должен содержать ровно {len(slots)} ID (по одному на слот).")
    lines.append("Все выбранные candidate_id по всему рациону должны быть УНИКАЛЬНЫМИ (без дубликатов).")
    return "\n".join(lines)


async def _ask_model(prompt: str, model: str) -> tuple[str, dict[str, Any]]:
    api_key = (settings.gemini_api_key or "").strip()
    if not api_key:
        raise HTTPException(503, "Не задан GEMINI_API_KEY для генерации рациона. Укажите ключ в backend/.env")
    try:
        def request_completion():
            with OpenAI(
                api_key=api_key,
                base_url=settings.gemini_base_url,
                timeout=settings.gemini_timeout_seconds,
            ) as client:
                return client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )

        completion = await asyncio.to_thread(request_completion)
    except AuthenticationError as exc:
        logger.exception("Google Gemini authentication failed for model %s", model)
        raise HTTPException(
            502,
            "Google Gemini отклонил GEMINI_API_KEY. Проверьте ключ в backend/.env "
            "и перезапустите API.",
        ) from exc
    except APITimeoutError as exc:
        raise HTTPException(504, "Модель не ответила за отведённое время") from exc
    except APIConnectionError as exc:
        raise HTTPException(502, "Не удалось подключиться к Google Gemini") from exc
    except APIStatusError as exc:
        logger.exception("Google Gemini returned HTTP %s for model %s", exc.status_code, model)
        raise HTTPException(502, f"Google Gemini вернул HTTP {exc.status_code} для модели {model}") from exc
    except OpenAIError as exc:
        logger.exception("OpenAI SDK request failed for model %s", model)
        raise HTTPException(502, f"Ошибка OpenAI SDK при запросе модели {model}") from exc

    logger.info(
        "Raw Gemini completion before extraction (%s): %s",
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
        logger.exception("Unexpected Gemini completion format for model %s", model)
        raise HTTPException(502, "Google Gemini вернул ответ без ожидаемого choices[0].message.content") from exc
    return content, completion.usage.model_dump(exclude_none=True) if completion.usage else {}


async def generate(db: AsyncSession, user: User, tags: list[str], period_days: int,
                   extra_request: str = "", model: str | None = None) -> Ration:
    """Retrieve meals by profile+embedding, validate model JSON, persist ration and audit."""
    if not (settings.gemini_api_key or "").strip():
        raise HTTPException(503, "Добавьте GEMINI_API_KEY в backend/.env перед генерацией")
    profile = await _profile(db, user)
    count = int(profile.meals_per_day or 3)
    if count not in MEAL_SLOTS:
        raise HTTPException(422, "Количество приёмов пищи должно быть от 3 до 5; исправьте профиль")
    slots = MEAL_SLOTS[count]

    # Sanitize model parameter (ignore legacy OpenRouter slugs from older frontend states)
    raw_model = (model or "").strip()
    if not raw_model or "/" in raw_model or "free" in raw_model.lower():
        selected_model = settings.gemini_model
    else:
        selected_model = raw_model

    request_text = ", ".join(tags + ([extra_request.strip()] if extra_request.strip() else []))

    # Extract all restrictions/allergies from profile restrictions, preferences text, and generation request
    exclusions = _extract_restriction_patterns(
        profile.restrictions,
        profile.preferences,
        extra_request,
        *tags
    )
    logger.info("Extracted exclusions for user %s: %s", user.id, exclusions)

    groups: list[dict[str, Any]] = []
    candidates_by_id: dict[str, dict[str, Any]] = {}
    allowed_slots: dict[str, str] = {}
    retrieved_by_type: dict[str, list[dict[str, Any]]] = {}
    next_id = 1
    goal = _normalize_goal(profile.goal) or "без заданной цели"

    # Fetch plenty of candidates so every single day can have a completely unique dish
    candidate_limit = max(14, period_days * 2 + 4)

    # Count how many slots use each meal_type to fetch non-overlapping candidate pools
    slots_per_meal_type: dict[str, int] = {}
    for _, meal_type, _ in slots:
        slots_per_meal_type[meal_type] = slots_per_meal_type.get(meal_type, 0) + 1

    slot_offset_by_type: dict[str, int] = {}
    for label, meal_type, ration_meal_type in slots:
        if meal_type not in retrieved_by_type:
            needed_count = candidate_limit * slots_per_meal_type[meal_type]
            query = ". ".join(part for part in (label, goal, profile.preferences or "", request_text) if part)
            try:
                rows = await _retrieve_candidates(db, profile, meal_type, query, exclusions, limit=needed_count)
            except RuntimeError as exc:
                raise HTTPException(503, str(exc)) from exc
            retrieved_by_type[meal_type] = rows
            slot_offset_by_type[meal_type] = 0

        # Disjoint slice for this specific slot to ensure distinct dishes across slots
        offset = slot_offset_by_type[meal_type]
        slot_rows = retrieved_by_type[meal_type][offset : offset + candidate_limit]
        if not slot_rows:
            slot_rows = retrieved_by_type[meal_type]
        slot_offset_by_type[meal_type] = offset + len(slot_rows)

        candidates = []
        for row in slot_rows:
            candidate_id = f"M{next_id:03d}"
            next_id += 1
            candidate = {"candidate_id": candidate_id, **row}
            candidates.append(candidate)
            candidates_by_id[candidate_id] = candidate
            allowed_slots[candidate_id] = ration_meal_type
        if not candidates:
            raise HTTPException(422, f"Не найдено подходящих блюд (без аллергенов) для слота «{label}». Проверьте настройки профиля.")
        groups.append({"slot": label, "meal_type": meal_type, "candidates": candidates})

    prompt = _build_prompt(profile, period_days, request_text, groups, exclusions)
    output, usage = await _ask_model(prompt, selected_model)

    # Resilient parsing with automatic gap-filling for missing slots/days
    parsed_days: dict[int, list[str]] = {}
    try:
        plan = _parse_model_output(output)
        raw_days = plan.get("days") or []
        for item in raw_days:
            try:
                day_num = int(item.get("day") or 0)
                if 1 <= day_num <= period_days:
                    meals_arr = item.get("meals") or []
                    if isinstance(meals_arr, list):
                        parsed_days[day_num] = [cid for cid in meals_arr if cid in candidates_by_id]
            except (ValueError, TypeError):
                continue
    except Exception as exc:
        logger.warning("Could not parse model JSON cleanly (%s): %s", exc, output[:240])

    # STRICT DEDUPLICATION:
    # 1. Intra-day: NO TWO MEALS on the same day can EVER be identical
    # 2. Inter-day: As long as candidates are available, every meal across the entire week is unique
    global_used_meal_ids: set[str] = set()

    for day_number in range(1, period_days + 1):
        existing_meals = parsed_days.get(day_number, [])
        day_slot_filled: set[str] = set()
        day_meal_ids: set[str] = set()
        clean_day_meals: list[str] = []

        # 1. Accept valid model recommendations that have not been used today or previously
        for cid in existing_meals:
            slot = allowed_slots.get(cid)
            cand = candidates_by_id.get(cid)
            if not slot or not cand:
                continue
            meal_id = str(cand["id"])
            if (
                slot not in day_slot_filled
                and meal_id not in day_meal_ids
                and meal_id not in global_used_meal_ids
                and not _is_meal_excluded(cand, exclusions)
            ):
                day_slot_filled.add(slot)
                day_meal_ids.add(meal_id)
                global_used_meal_ids.add(meal_id)
                clean_day_meals.append(cid)

        # 2. Fill any missing slot with a guaranteed unique dish
        for label, meal_type, ration_meal_type in slots:
            if ration_meal_type not in day_slot_filled:
                slot_pool = [
                    cid for cid, s in allowed_slots.items()
                    if s == ration_meal_type and not _is_meal_excluded(candidates_by_id[cid], exclusions)
                ]
                # Priority 1: Unused globally AND unused today
                available = [
                    cid for cid in slot_pool
                    if str(candidates_by_id[cid]["id"]) not in global_used_meal_ids
                    and str(candidates_by_id[cid]["id"]) not in day_meal_ids
                ]
                if available:
                    chosen = available[0]
                else:
                    # Priority 2: Unused today (prevents same-day duplicates even if pool is smaller than whole week)
                    fallback_pool = [
                        cid for cid in slot_pool
                        if str(candidates_by_id[cid]["id"]) not in day_meal_ids
                    ]
                    if fallback_pool:
                        chosen = fallback_pool[(day_number - 1) % len(fallback_pool)]
                    elif slot_pool:
                        chosen = slot_pool[0]
                    else:
                        raise HTTPException(422, f"Не найдено подходящих блюд без аллергенов для слота «{label}».")

                chosen_meal_id = str(candidates_by_id[chosen]["id"])
                day_slot_filled.add(ration_meal_type)
                day_meal_ids.add(chosen_meal_id)
                global_used_meal_ids.add(chosen_meal_id)
                clean_day_meals.append(chosen)

        parsed_days[day_number] = clean_day_meals

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
                        provider="gemini", model=selected_model, status="completed",
                        input_tokens=usage.get("prompt_tokens"), output_tokens=usage.get("completion_tokens"),
                        completed_at=datetime.now(timezone.utc)))
    return ration
