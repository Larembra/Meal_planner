"""AI service for automatic price estimation, dish image generation/search, and nutrition consultation."""
from __future__ import annotations

import asyncio
import json
import logging
import re
import urllib.parse
import warnings
from typing import Any, Optional

warnings.filterwarnings("ignore", message=".*renamed to.*ddgs.*")

import httpx
from fastapi import HTTPException
from openai import OpenAI, AuthenticationError, APITimeoutError, APIConnectionError, APIStatusError

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_FOOD_IMAGES = {
    "breakfast": "https://images.unsplash.com/photo-1490474418585-ba9bad8fd0ea?auto=format&fit=crop&w=1200&q=85",
    "lunch": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=85",
    "dinner": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=85",
    "snack": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1200&q=85",
    "default": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1200&q=85",
}


def _clean_json_output(output: str) -> dict[str, Any]:
    """Cleans markdown wrappers and parses JSON from model output."""
    cleaned = re.sub(r"```(?:json)?", "", output, flags=re.IGNORECASE).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Ответ модели не содержит корректного JSON-объекта: {output[:120]}")
    payload_str = cleaned[start : end + 1]
    return json.loads(payload_str)


async def _ask_llm(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = 1000,
) -> str:
    """Sends a request to OpenRouter API."""
    api_key = (settings.openrouter_api_key or "").strip()
    if not api_key:
        raise HTTPException(
            503,
            "Не задан OPENROUTER_API_KEY. Укажите ключ в backend/.env для работы ИИ-функций.",
        )

    target_model = model or settings.openrouter_model

    def _sync_request():
        with OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=settings.openrouter_timeout_seconds,
        ) as client:
            kwargs: dict[str, Any] = {
                "model": target_model,
                "messages": messages,
                "temperature": temperature,
                # Explicitly disable internal reasoning monologue on reasoning models (e.g. Nemotron/DeepSeek)
                # so the model outputs the JSON immediately in 2-3s instead of stalling/truncating.
                "extra_body": {"reasoning": {"max_tokens": 0}},
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            completion = client.chat.completions.create(**kwargs)
            msg = completion.choices[0].message
            content = msg.content or ""
            if not content.strip():
                # Fallback in case a reasoning model placed output in reasoning field
                extra = getattr(msg, "model_extra", {}) or {}
                content = extra.get("reasoning") or ""
            return content

    try:
        return await asyncio.to_thread(_sync_request)
    except AuthenticationError as exc:
        logger.exception("OpenRouter authentication error with model %s", target_model)
        raise HTTPException(
            502,
            "Ошибка авторизации OpenRouter: проверьте правильность OPENROUTER_API_KEY в backend/.env.",
        ) from exc
    except APITimeoutError as exc:
        logger.exception("OpenRouter timeout with model %s", target_model)
        raise HTTPException(504, "ИИ-сервер OpenRouter не ответил вовремя. Попробуйте снова.") from exc
    except (APIConnectionError, APIStatusError) as exc:
        logger.exception("OpenRouter API connection error: %s", exc)
        raise HTTPException(502, f"Сбой обращения к OpenRouter: {getattr(exc, 'message', str(exc))}") from exc


def _search_grocery_prices(dish_name: str, ingredients: Optional[list[str]] = None) -> str:
    """
    Searches DuckDuckGo for actual retail grocery prices of ingredients in supermarkets.
    Returns extracted snippets with pricing context to augment the LLM.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ""

    snippets: list[str] = []
    queries: list[str] = []

    # 1. Base dish grocery query
    clean_dish = dish_name.strip()
    queries.append(f"{clean_dish} цена продукты супермаркет")

    # 2. Extract ingredient queries
    if ingredients:
        for ing in ingredients[:3]:
            # Clean out numbers, units, brackets
            clean_ing = re.sub(r"[\d\(\)\.,/].*", "", str(ing)).strip()
            clean_ing = re.sub(r"(?:г|кг|мл|л|шт|ст\.?\s*л\.?|ч\.?\s*л\.?)$", "", clean_ing, flags=re.IGNORECASE).strip()
            if len(clean_ing) > 2:
                queries.append(f"{clean_ing} цена супермаркет")
    else:
        # Split dish name by Russian prepositions/conjunctions to find key ingredients
        parts = re.split(r"\s+(?:с|со|в|под|из|и|на|по)\s+", clean_dish, flags=re.IGNORECASE)
        for part in parts:
            clean_p = part.strip()
            if len(clean_p) > 2 and clean_p.lower() not in {"по-домашнему", "по-деревенски", "по-французски", "по-итальянски"}:
                queries.append(f"{clean_p} цена супермаркет")

    # Deduplicate queries while preserving order
    seen = set()
    unique_queries: list[str] = []
    for q in queries:
        q_norm = q.lower().strip()
        if q_norm not in seen:
            seen.add(q_norm)
            unique_queries.append(q)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                for q in unique_queries[:3]:
                    try:
                        results = list(ddgs.text(q, max_results=2))
                        for r in results:
                            body = (r.get("body") or "").strip()
                            title = (r.get("title") or "").strip()
                            combined = f"{title}: {body}"
                            if any(k in combined.lower() for k in ["руб", "₽", "цена", "стоим", "купить"]):
                                snippets.append(combined[:180])
                    except Exception:
                        pass
    except Exception as exc:
        logger.debug("Grocery search failed for '%s': %s", dish_name, exc)

    if not snippets:
        return ""
    return "Данные о ценах продуктов из поисковика DuckDuckGo (розничные супермаркеты РФ):\n" + "\n".join(f"- {s}" for s in snippets[:4])


async def estimate_dish_price(
    dish_name: str,
    category: Optional[str] = None,
    ingredients: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Estimates the supermarket grocery cost of preparing the given dish in rubles.
    First searches DuckDuckGo for actual store prices. If search lacks data,
    the LLM calculates the price based on supermarket grocery shelf prices.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Название блюда не может быть пустым")

    ingredients_text = ", ".join(ingredients) if ingredients else "стандартный набор"
    category_text = category or "не указана"

    # Search for actual store grocery prices via DuckDuckGo
    search_context = await asyncio.to_thread(_search_grocery_prices, dish_name, ingredients)
    search_block = f"\n{search_context}\n" if search_context else ""

    prompt = f"""Ты — эксперт по розничным ценам в продуктовых супермаркетах РФ («Пятерочка», «Магнит», «Перекресток»).
Определи РЫНОЧНУЮ СТОИМОСТЬ покупки продуктов в магазине для приготовления блюда «{dish_name}».
Категория: "{category_text}".
Ингредиенты: "{ingredients_text}".
{search_block}
ПРАВИЛА ОЦЕНКИ СТОИМОСТИ (РЫНОЧНАЯ ЦЕНА В МАГАЗИНЕ):
1. Если наименование НЕ является едой/блюдом:
   Верни строго: {{"is_food": false, "error": "«{dish_name}» не является блюдом или продуктом питания."}}
2. Нам нужна именно РЫНОЧНАЯ ЦЕНА ПОКУПКИ В МАГАЗИНЕ, а НЕ микро-себестоимость по граммам (не 100-110 ₽) и НЕ ресторанное меню (не 600-800 ₽):
   - Для стандартных сытных домашних блюд (рис/паста с куриным филе, мясные гарниры, омлеты с беконом) рыночная стоимость покупки продуктов в магазине обычно составляет от 250 до 400 ₽.
   - Для простых каш/гарниров без мяса: 120 – 200 ₽.
   - Для блюд с говядиной или рыбой: 350 – 550 ₽.
3. Если выше представлены данные из поисковика DuckDuckGo — используй эти розничные цены.
4. Если поисковик не нашел цену на нужный товар — рассчитай цену самостоятельно по своим соображениям на основе цен магазинной полки с учетом стандартной торговой наценки супермаркета.

Верни СТРОГО JSON:
{{"is_food": true, "price": 310, "comment": "Рыночная цена продуктов в магазине"}}
ТОЛЬКО JSON без Markdown.
"""

    messages = [
        {"role": "system", "content": "Ты экспертная система по оценке стоимости продуктов в супермаркетах РФ. Отвечай только JSON."},
        {"role": "user", "content": prompt},
    ]

    raw_response = await _ask_llm(messages, temperature=0.0, max_tokens=300)

    try:
        data = _clean_json_output(raw_response)
    except Exception as exc:
        logger.warning("Could not parse LLM price response: %s", raw_response)
        raise HTTPException(502, "ИИ вернул ответ в некорректном формате.") from exc

    if not data.get("is_food", False):
        error_msg = data.get("error") or f"«{dish_name}» не является блюдом или едой."
        raise HTTPException(400, error_msg)

    raw_price = data.get("price")
    try:
        price = round(float(raw_price), 2)
        if price <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise HTTPException(502, "ИИ не смог определить корректную числовую цену блюда.")

    return {
        "price": price,
        "is_food": True,
        "comment": data.get("comment") or "Ориентировочная средняя цена",
    }

WIKI_HEADERS = {
    "User-Agent": "MealPlannerBot/1.0 (https://github.com/mealplanner; contact@mealplanner.com)",
    "Accept": "application/json",
}

NON_FOOD_TERMS = {"map", "flag", "icon", "logo", "diagram", "chart", "symbol", "vector", "drawing", "painting"}


async def _search_wikipedia_pageimages(queries: list[str], lang: str = "en", main_noun: str = "") -> Optional[str]:
    """
    Searches Wikipedia for articles matching the dish name and retrieves
    the official featured article thumbnail image.
    STRICT CHECK: Ignores articles that don't match the main dish noun
    (e.g. rejects article 'Бекон' when searching for 'Омлет с беконом').
    """
    async with httpx.AsyncClient(headers=WIKI_HEADERS, timeout=7.0) as client:
        for q in queries:
            if not q or len(q.strip()) < 2:
                continue
            encoded = urllib.parse.quote(q.strip())
            url = (
                f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=search"
                f"&gsrsearch={encoded}&gsrlimit=5&prop=pageimages&piprop=thumbnail&pithumbsize=800&format=json"
            )
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                pages = resp.json().get("query", {}).get("pages", {})
                # Sort pages by Wikipedia's internal search ranking index
                sorted_pages = sorted(pages.values(), key=lambda p: p.get("index", 999))
                for page in sorted_pages:
                    title = page.get("title", "").lower()
                    # If main dish noun is provided, verify it appears in the article title
                    if main_noun and main_noun.lower() not in title:
                        continue
                    thumb = page.get("thumbnail", {}).get("source")
                    if thumb and thumb.startswith("http"):
                        return thumb
            except Exception as exc:
                logger.debug("Wikipedia (%s) search error for '%s': %s", lang, q, exc)
    return None


async def _search_themealdb(queries: list[str]) -> Optional[str]:
    """Searches TheMealDB for high-quality culinary studio photos."""
    async with httpx.AsyncClient(timeout=6.0) as client:
        for q in queries:
            words = [w for w in re.findall(r"\w+", q) if len(w) > 3]
            for word in words:
                try:
                    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(word)}"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        meals = resp.json().get("meals")
                        if meals and meals[0].get("strMealThumb"):
                            return meals[0]["strMealThumb"]
                except Exception:
                    pass
    return None


async def _search_wikimedia(queries: list[str], main_noun: str = "") -> Optional[str]:
    """Searches Wikimedia Commons for authentic dish photos with main noun verification."""
    async with httpx.AsyncClient(headers=WIKI_HEADERS, timeout=8.0) as client:
        for q in queries:
            if not q or len(q.strip()) < 2:
                continue
            encoded = urllib.parse.quote(q.strip())
            url = (
                "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                f"&gsrsearch={encoded}&gsrnamespace=6&prop=imageinfo&iiprop=url&format=json"
            )
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                pages = resp.json().get("query", {}).get("pages", {})
                candidates = []
                query_words = set(re.findall(r"\w+", q.lower()))
                for page in pages.values():
                    title = page.get("title", "").lower()
                    if any(term in title for term in NON_FOOD_TERMS):
                        continue
                    # Must contain the main dish noun if specified (prevents single ingredient photos)
                    if main_noun and main_noun.lower() not in title:
                        continue
                    for info in page.get("imageinfo", []):
                        raw_url = info.get("url") or ""
                        clean_url = raw_url.split("?")[0].lower()
                        if clean_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                            title_words = set(re.findall(r"\w+", title))
                            score = len(query_words & title_words)
                            candidates.append((score, raw_url))
                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    return candidates[0][1]
            except Exception as exc:
                logger.debug("Wikimedia search error for query '%s': %s", q, exc)
    return None


def _search_pinterest_or_web(query: str, main_noun: str = "") -> Optional[str]:
    """
    Searches for high-aesthetic food/recipe photos from Pinterest and culinary sites
    using duckduckgo_search with strict food filtering.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
    except ImportError:
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with DDGS() as ddgs:
                # 1. Search Pinterest pins for styled recipe photos
                pin_query = f'site:pinterest.com/pin "{query}" recipe'
            results = list(
                ddgs.images(
                    keywords=pin_query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=6,
                )
            )
            for item in results:
                url = item.get("image") or item.get("thumbnail")
                title = (item.get("title") or "").lower()
                if url and "pinimg.com" in url:
                    if not main_noun or main_noun.lower() in title or main_noun.lower() in query.lower():
                        return url

            # 2. Search general food web photography with exact phrase
            web_query = f'"{query}" food recipe dish photography'
            results = list(
                ddgs.images(
                    keywords=web_query,
                    region="wt-wt",
                    safesearch="moderate",
                    max_results=6,
                )
            )
            for item in results:
                url = item.get("image") or item.get("thumbnail")
                title = (item.get("title") or "").lower()
                if url and url.startswith("http") and not url.lower().endswith(".svg"):
                    if not main_noun or main_noun.lower() in title:
                        return url
    except Exception as exc:
        logger.debug("duckduckgo_search call failed for '%s': %s", query, exc)
    return None


async def suggest_or_generate_image(dish_name: str, category: Optional[str] = None) -> dict[str, Any]:
    """
    Finds a suitable, highly accurate image for the dish.
    Prioritizes Pinterest recipe photos, verified Wikipedia dish thumbnails,
    and TheMealDB studio shots.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Название блюда не может быть пустым")

    # Step 1: LLM determines validity and extracts main noun vs toppings
    validity_prompt = f"""Определи, является ли «{dish_name}» едой, напитком или кулинарным блюдом.
Если это НЕ еда (предмет, животное, абстракция, мусорный текст), верни строго JSON:
{{"is_food": false, "error": "«{dish_name}» не является блюдом или продуктом питания."}}
Если это еда, верни строго JSON:
{{
  "is_food": true,
  "main_noun_ru": "главное существительное блюда в именительном падеже на русском (например: омлет, суп, салат, каша, пицца, паста)",
  "main_noun_en": "main dish noun in english (e.g. omelette, soup, salad, porridge, pizza, pasta)",
  "full_dish_en": "exact full english culinary translation (e.g. bacon omelette)",
  "search_terms": ["exact english name", "alternative english culinary name"]
}}
Только JSON без Markdown.
"""
    search_queries: list[str] = []
    main_noun_ru = ""
    main_noun_en = ""
    full_dish_en = ""

    try:
        raw_val = await _ask_llm([{"role": "user", "content": validity_prompt}], temperature=0.0)
        val_data = _clean_json_output(raw_val)
        if not val_data.get("is_food", False):
            raise HTTPException(400, val_data.get("error") or f"«{dish_name}» не является блюдом.")

        main_noun_ru = (val_data.get("main_noun_ru") or "").strip().lower()
        main_noun_en = (val_data.get("main_noun_en") or "").strip().lower()
        full_dish_en = (val_data.get("full_dish_en") or "").strip()
        terms = val_data.get("search_terms") or []
        if full_dish_en:
            search_queries.append(full_dish_en)
        if isinstance(terms, list):
            for t in terms:
                st = str(t).strip()
                if st and st not in search_queries:
                    search_queries.append(st)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Error during validity/translation LLM step: %s", exc)

    if not search_queries:
        search_queries.append(dish_name)

    # Step 2: Pinterest / Styled Recipe Photo Search (beautiful culinary photos requested by user)
    found_url = await asyncio.to_thread(_search_pinterest_or_web, full_dish_en or dish_name, main_noun_en or main_noun_ru)
    if found_url:
        return {
            "image_url": found_url,
            "source": "pinterest_web",
            "comment": "Фото подобрано из кулинарной базы Pinterest / Recipe Search",
        }

    # Step 3: Accurate Wikipedia PageImages (with strict main noun check)
    found_url = await _search_wikipedia_pageimages([dish_name], lang="ru", main_noun=main_noun_ru)
    if found_url:
        return {
            "image_url": found_url,
            "source": "wikipedia_ru",
            "comment": "Фото статьи о блюде из Wikipedia",
        }

    found_url = await _search_wikipedia_pageimages(search_queries, lang="en", main_noun=main_noun_en)
    if found_url:
        return {
            "image_url": found_url,
            "source": "wikipedia_en",
            "comment": "Фото блюда из Wikipedia (en)",
        }

    # Step 4: Search TheMealDB database for culinary studio shots
    found_url = await _search_themealdb(search_queries)
    if found_url:
        return {
            "image_url": found_url,
            "source": "themealdb",
            "comment": "Студийное фото блюда из кулинарной базы TheMealDB",
        }

    # Step 5: Search in Wikimedia Commons with strict main noun verification
    found_url = await _search_wikimedia(search_queries, main_noun=main_noun_en or main_noun_ru)
    if found_url:
        return {
            "image_url": found_url,
            "source": "wikimedia_commons",
            "comment": "Точное фото блюда найдено в Wikimedia Commons",
        }

    # Step 6: Curated thematic food fallback
    cat_key = (category or "").lower()
    fallback_url = DEFAULT_FOOD_IMAGES.get(cat_key, DEFAULT_FOOD_IMAGES["default"])
    return {
        "image_url": fallback_url,
        "source": "curated_catalog",
        "comment": "Тематическое фото из каталога",
    }


VALID_INGREDIENT_CATEGORIES = [
    "🥛 Молочные продукты",
    "🥩 Мясо и рыба",
    "🥬 Бакалея и овощи",
    "🧂 Прочее",
]


async def estimate_ingredients_price(
    dish_name: str,
    ingredients: list[dict],
) -> dict[str, Any]:
    """
    Estimates the individual market prices of each ingredient in rubles for the dish.
    If the provided list of ingredients is empty or blank, suggests a realistic list of ingredients.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Укажите название блюда для расчёта ингредиентов")

    ingredients_summary = []
    for item in ingredients:
        name = str(item.get("name") or "").strip()
        qty = str(item.get("quantity") or "").strip()
        if name:
            ingredients_summary.append(f"{name} ({qty or '1 порция'})")

    ingredients_text = "; ".join(ingredients_summary) if ingredients_summary else "список не указан, предложи стандартный"

    # Search actual store prices in DuckDuckGo
    ing_names_for_search = [str(i.get('name')) for i in ingredients if i.get('name')]
    search_context = await asyncio.to_thread(_search_grocery_prices, dish_name, ing_names_for_search)
    search_block = f"\n{search_context}\n" if search_context else ""

    prompt = f"""Ты — эксперт по розничным ценам в продуктовых супермаркетах РФ («Пятерочка», «Магнит», «Перекресток»).
Рассчитай РЫНОЧНУЮ стоимость покупки продуктов в магазине для приготовления блюда «{dish_name}».
Ингредиенты: {ingredients_text}
{search_block}
ПРАВИЛА ОЦЕНКИ СТОИМОСТИ (РЫНОЧНАЯ ЦЕНА В МАГАЗИНЕ, НЕ МИКРО-ГРАММЫ!):
1. Если «{dish_name}» НЕ является едой:
   Верни строго: {{"is_food": false, "error": "«{dish_name}» не является блюдом."}}
2. Нам нужна РЫНОЧНАЯ ЦЕНА ПОКУПКИ ИНГРЕДИЕНТОВ В МАГАЗИНЕ:
   - Не считай микро-себестоимость граммов (не 100–110 ₽ за всё блюдо)! Человек покупает продукты в розничной фасовке магазина для приготовления этого блюда.
   - Для сытных блюд с мясом или птицей (например, куриное филе с рисом в сухарях, паста с мясом/беконом) суммарная рыночная стоимость покупки продуктов в магазине обычно составляет от 250 до 400 ₽.
   - Распредели реальные рыночные цены супермаркета по ингредиентам блюда (например, упаковка/порция куриного филе для блюда — ~170-220 ₽, рис — ~40-60 ₽, сухари — ~35-50 ₽, масло/специи — ~25-40 ₽).
3. Если выше есть данные из поисковика DuckDuckGo — приоритетно опирайся на найденные цены магазинов.
4. Если поисковик не нашел цену на конкретный ингредиент — рассчитай цену самостоятельно по своим соображениям исходя из магазинной полки с учетом стандартной торговой наценки супермаркета.
5. Поле category для каждого ингредиента должно быть СТРОГО одним из 4 значений:
   - "🥛 Молочные продукты"
   - "🥩 Мясо и рыба"
   - "🥬 Бакалея и овощи"
   - "🧂 Прочее"
6. Рассчитай total_price как точную сумму цен всех ингредиентов.

ВЕРНИ СТРОГО JSON:
{{
  "is_food": true,
  "ingredients": [
    {{"name": "...", "quantity": "...", "price": 0, "category": "..."}}
  ],
  "total_price": 0,
  "comment": "Рыночная стоимость покупки ингредиентов в магазине"
}}
ТОЛЬКО JSON без Markdown.
"""
    messages = [
        {"role": "system", "content": "Ты эксперт по калькуляции розничной стоимости продуктов в РФ. Отвечай только JSON."},
        {"role": "user", "content": prompt},
    ]

    raw_response = await _ask_llm(messages, temperature=0.1, max_tokens=600)
    data = _clean_json_output(raw_response)

    if not data.get("is_food", False):
        raise HTTPException(400, data.get("error") or f"«{dish_name}» не является блюдом.")

    raw_ingredients = data.get("ingredients") or []
    cleaned_ingredients = []
    total = 0.0

    for item in raw_ingredients:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        qty = str(item.get("quantity") or "").strip()
        try:
            item_price = round(float(item.get("price") or 0), 2)
            if item_price < 0:
                item_price = 0.0
        except (ValueError, TypeError):
            item_price = 10.0
        cat = str(item.get("category") or "").strip()
        if cat not in VALID_INGREDIENT_CATEGORIES:
            cat = "🥬 Бакалея и овощи"

        cleaned_ingredients.append({
            "name": name,
            "quantity": qty or "по вкусу",
            "price": item_price,
            "category": cat,
        })
        total += item_price

    total = round(total, 2)
    return {
        "ingredients": cleaned_ingredients,
        "total_price": total,
        "comment": data.get("comment") or "Автоматический расчёт цен ингредиентов",
    }


async def estimate_nutrition(
    dish_name: str,
    ingredients: list[dict],
) -> dict[str, Any]:
    """
    Calculates calories (ккал), protein (г), fat (г), and carbs (г) per 100g of the prepared dish.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Укажите название блюда для расчёта КБЖУ")

    ing_names = [str(i.get("name") or "").strip() for i in ingredients if i.get("name")]
    ing_text = ", ".join(ing_names) if ing_names else "стандартный рецепт"

    prompt = f"""Ты — профессиональный нутрициолог и диетолог.
Рассчитай пищевую ценность (КБЖУ) на 100 грамм ГОТОВОГО блюда «{dish_name}».
Ингредиенты: {ing_text}.

ПРАВИЛА:
1. Если «{dish_name}» не является едой:
   Верни: {{"is_food": false, "error": "«{dish_name}» не является блюдом."}}
2. Верни реалистичные показатели на 100 грамм готового блюда с учётом термообработки:
   - calories: ккал на 100г (число, округлить до целого)
   - protein: белки в граммах (число, до 1 знака после запятой)
   - fat: жиры в граммах (число, до 1 знака после запятой)
   - carbs: углеводы в граммах (число, до 1 знака после запятой)

ВЕРНИ СТРОГО JSON:
{{
  "is_food": true,
  "calories": 210,
  "protein": 14.5,
  "fat": 12.0,
  "carbs": 8.5,
  "comment": "КБЖУ на 100г готового блюда"
}}
ТОЛЬКО JSON без Markdown.
"""
    messages = [
        {"role": "system", "content": "Ты нутрициолог. Отвечай только JSON."},
        {"role": "user", "content": prompt},
    ]

    raw = await _ask_llm(messages, temperature=0.0)
    data = _clean_json_output(raw)

    if not data.get("is_food", False):
        raise HTTPException(400, data.get("error") or f"«{dish_name}» не является блюдом.")

    try:
        calories = round(float(data.get("calories") or 0))
        protein = round(float(data.get("protein") or 0), 1)
        fat = round(float(data.get("fat") or 0), 1)
        carbs = round(float(data.get("carbs") or 0), 1)
    except (ValueError, TypeError) as exc:
        raise HTTPException(502, "ИИ вернул некорректные численные значения КБЖУ.") from exc

    return {
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs,
        "comment": data.get("comment") or "КБЖУ рассчитано на 100г готового блюда",
    }


async def generate_cooking_steps(
    dish_name: str,
    ingredients: list[dict],
) -> dict[str, Any]:
    """
    Generates 3 to 5 clear, structured, practical cooking steps for the dish in Russian.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Укажите название блюда для генерации шагов")

    ing_names = [f"{i.get('name')} {i.get('quantity', '')}".strip() for i in ingredients if i.get("name")]
    ing_text = "; ".join(ing_names) if ing_names else "стандартные ингредиенты"

    prompt = f"""Ты — профессиональный шеф-повар.
Составь лаконичные, понятные пошаговые инструкции приготовления блюда «{dish_name}».
Ингредиенты: {ing_text}.

ПРАВИЛА:
1. Если «{dish_name}» не является едой:
   Верни: {{"is_food": false, "error": "«{dish_name}» не является блюдом."}}
2. Составь от 3 до 5 последовательных шагов.
3. Каждый шаг — конкретное кулинарное действие: подготовка, нарезка, термообработка, подача.
4. Пиши на русском языке, без лишней воды.

ВЕРНИ СТРОГО JSON:
{{
  "is_food": true,
  "steps": [
    "Нарезать ингредиенты...",
    "Разогреть сковороду и обжарить...",
    "Довести до готовности и подавать..."
  ],
  "comment": "Пошаговый рецепт приготовления"
}}
ТОЛЬКО JSON без Markdown.
"""
    messages = [
        {"role": "system", "content": "Ты шеф-повар. Отвечай только JSON."},
        {"role": "user", "content": prompt},
    ]

    raw = await _ask_llm(messages, temperature=0.2)
    data = _clean_json_output(raw)

    if not data.get("is_food", False):
        raise HTTPException(400, data.get("error") or f"«{dish_name}» не является блюдом.")

    steps = [str(s).strip() for s in (data.get("steps") or []) if str(s).strip()]
    if not steps:
        raise HTTPException(502, "ИИ не смог сгенерировать шаги приготовления.")

    return {
        "steps": steps,
        "comment": data.get("comment") or f"Сгенерировано {len(steps)} шагов приготовления",
    }


async def estimate_cooking_time(
    dish_name: str,
    steps: list[str],
    ingredients: list[dict],
) -> dict[str, Any]:
    """
    Estimates the realistic total cooking time in minutes.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Укажите название блюда для расчёта времени готовки")

    steps_text = " | ".join([s for s in steps if s.strip()]) if steps else "стандартный алгоритм"

    prompt = f"""Ты — кулинарный тайм-менеджер.
Определи реалистичное общее время приготовления (в минутах) для блюда «{dish_name}».
Шаги приготовления: {steps_text}.

ПРАВИЛА:
1. Если «{dish_name}» не является едой:
   Верни: {{"is_food": false, "error": "«{dish_name}» не является блюдом."}}
2. Верни реальное время (подготовка + процесс термообработки), целое число минут от 5 до 180.

ВЕРНИ СТРОГО JSON:
{{
  "is_food": true,
  "cooking_time": 25,
  "comment": "Время с учётом подготовки и термической обработки"
}}
ТОЛЬКО JSON без Markdown.
"""
    messages = [
        {"role": "system", "content": "Ты кулинарный тайм-менеджер. Отвечай только JSON."},
        {"role": "user", "content": prompt},
    ]

    raw = await _ask_llm(messages, temperature=0.0)
    data = _clean_json_output(raw)

    if not data.get("is_food", False):
        raise HTTPException(400, data.get("error") or f"«{dish_name}» не является блюдом.")

    try:
        cooking_time = int(data.get("cooking_time") or 0)
        if cooking_time <= 0:
            cooking_time = 20
    except (ValueError, TypeError):
        cooking_time = 25

    return {
        "cooking_time": cooking_time,
        "comment": data.get("comment") or f"{cooking_time} минут",
    }


async def generate_full_recipe(
    dish_name: str,
    category: Optional[str] = "Ужин",
) -> dict[str, Any]:
    """
    Comprehensive all-in-one generator: generates ingredients with market prices,
    total price, calories/protein/fat/carbs, cooking steps, cooking time, and dish photo.
    First checks DuckDuckGo for live grocery supermarket prices.
    """
    dish_name = dish_name.strip()
    if not dish_name:
        raise HTTPException(400, "Название блюда не может быть пустым")

    # Start DuckDuckGo grocery search and image search in parallel
    search_task = asyncio.create_task(asyncio.to_thread(_search_grocery_prices, dish_name))
    image_task = asyncio.create_task(suggest_or_generate_image(dish_name, category))

    # Await search results to augment the LLM prompt with real supermarket prices
    search_context = await search_task
    search_block = f"\n{search_context}\n" if search_context else ""

    prompt = f"""Ты — шеф-повар и эксперт по розничным ценам в продуктовых супермаркетах РФ («Пятерочка», «Магнит», «Перекресток»).
Создай сбалансированный рецепт для блюда «{dish_name}» (категория: {category or 'Ужин'}).
{search_block}
ПРАВИЛА И ЦЕНОВЫЕ ОРИЕНТИРЫ (РЫНОЧНАЯ ЦЕНА В МАГАЗИНЕ, НЕ МИКРО-ГРАММЫ И НЕ РЕСТОРАН!):
1. Если «{dish_name}» не является блюдом:
   Верни: {{"is_food": false, "error": "«{dish_name}» не является кулинарным блюдом."}}
2. Создай от 3 до 6 качественных ингредиентов с точными граммовками на блюдо.
3. ЦЕНЫ ИНГРЕДИЕНТОВ: Нам нужна РЫНОЧНАЯ СТОИМОСТЬ ПОКУПКИ В МАГАЗИНЕ, а НЕ микро-себестоимость 70 граммов крупы (не 100-110 ₽)!
   - Для стандартных сытных домашних блюд (рис/паста/картофель с куриным филе или мясом, омлеты с беконом) реальная рыночная стоимость покупки продуктов в магазине обычно составляет от 250 до 400 ₽ (для риса с куриным филе — около 280–360 ₽, строго до 400 ₽!).
   - Не завышай до ресторанных 600–800 ₽! Это цена покупки продуктов в супермаркете у дома.
   - Оценивай каждый ингредиент по реальной магазинной стоимости покупки для приготовления блюда с учетом наценки супермаркета (например: куриное филе — ~170-220 ₽, рис — ~40-60 ₽, панировочные сухари — ~35-50 ₽, масло и специи — ~25-40 ₽).
4. Если выше приведены данные из поисковика DuckDuckGo — используй найденные розничные цены.
5. Если поисковик не нашел цену на конкретный товар — рассчитай цену самостоятельно по своим соображениям на основе цен магазинной полки с учетом стандартной торговой наценки супермаркета.
6. Категория ингредиентов строго одна из: "🥛 Молочные продукты", "🥩 Мясо и рыба", "🥬 Бакалея и овощи", "🧂 Прочее".
7. Посчитай price как ТОЧНУЮ сумму цен указанных ингредиентов.
8. Рассчитай КБЖУ на 100 грамм готового блюда (calories, protein, fat, carbs).
9. Напиши от 3 до 5 понятных практических шагов приготовления (steps).
10. Укажи время приготовления в минутах (time).

ВЕРНИ СТРОГО JSON:
{{
  "is_food": true,
  "name": "{dish_name}",
  "category": "{category or 'Ужин'}",
  "time": 25,
  "calories": 210,
  "protein": 14.5,
  "fat": 15.0,
  "carbs": 3.5,
  "price": 310,
  "ingredients": [
    {{"name": "...", "quantity": "...", "price": 0, "category": "..."}}
  ],
  "steps": [
    "..."
  ],
  "comment": "Рыночная цена покупки продуктов в супермаркете"
}}
ТОЛЬКО JSON без Markdown.
"""
    messages = [
        {"role": "system", "content": "Ты профессиональный шеф-повар и эксперт по себестоимости продуктов в супермаркетах РФ. Отвечай только JSON."},
        {"role": "user", "content": prompt},
    ]

    # Generate recipe while image search is already running in parallel
    recipe_task = asyncio.create_task(_ask_llm(messages, temperature=0.1, max_tokens=850))

    results = await asyncio.gather(recipe_task, image_task, return_exceptions=True)
    raw_recipe, img_res = results[0], results[1]

    if isinstance(raw_recipe, Exception):
        logger.exception("Recipe generation task error: %s", raw_recipe)
        raise HTTPException(502, f"Ошибка генерации рецепта через ИИ: {raw_recipe}") from raw_recipe

    try:
        data = _clean_json_output(raw_recipe)
    except Exception as exc:
        logger.warning("Could not parse LLM recipe JSON: %s", raw_recipe)
        raise HTTPException(502, "ИИ вернул ответ в некорректном формате. Попробуйте еще раз.") from exc

    if not data.get("is_food", False):
        raise HTTPException(400, data.get("error") or f"«{dish_name}» не является блюдом.")

    image_url = None
    if isinstance(img_res, dict):
        image_url = img_res.get("image_url")
    elif isinstance(img_res, Exception):
        logger.debug("Image search task error: %s", img_res)

    raw_ingredients = data.get("ingredients") or []
    cleaned_ingredients = []
    total_price = 0.0

    for item in raw_ingredients:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        qty = str(item.get("quantity") or "по вкусу").strip()
        try:
            pr = round(float(item.get("price") or 0), 2)
        except (ValueError, TypeError):
            pr = 20.0
        cat = str(item.get("category") or "").strip()
        if cat not in VALID_INGREDIENT_CATEGORIES:
            cat = "🥬 Бакалея и овощи"
        cleaned_ingredients.append({
            "name": name,
            "quantity": qty,
            "price": pr,
            "category": cat,
        })
        total_price += pr

    total_price = round(total_price, 2)
    final_price = total_price if total_price > 0 else round(float(data.get("price") or 0), 2)

    return {
        "name": dish_name,
        "category": data.get("category") or category or "Ужин",
        "time": int(data.get("time") or 25),
        "calories": round(float(data.get("calories") or 0)),
        "protein": round(float(data.get("protein") or 0), 1),
        "fat": round(float(data.get("fat") or 0), 1),
        "carbs": round(float(data.get("carbs") or 0), 1),
        "price": final_price,
        "ingredients": cleaned_ingredients,
        "steps": [str(s).strip() for s in (data.get("steps") or []) if str(s).strip()],
        "image_url": image_url,
        "comment": data.get("comment") or "Рецепт успешно сформирован ИИ на основе цен супермаркетов",
    }





async def consult_nutrition(query: str) -> dict[str, str]:
    """
    Provides concise, dry advice and consultation for meal planning, nutrition, recipes, and diet.
    Rejects any queries not related to the application domain.
    Single-turn query, no context is preserved.
    """
    query = query.strip()
    if not query:
        raise HTTPException(400, "Запрос для консультации не может быть пустым")

    system_instruction = """Ты — сухой, строгий и компетентный консультант по питанию и кулинарии сервиса «Витя, где ням-ням?».
Твоя задача — давать сухие, деловые, четкие рекомендации и факты.

РАЗРЕШЁННЫЕ ТЕМЫ:
- Составление меню, рационов питания и планирование приёмов пищи.
- Рецепты, кулинарные техники, совместимость и замена ингредиентов.
- Пищевая ценность (калории, белки, жиры, углеводы), витамины и макронутриенты.
- Диеты, коррекция веса (похудение, набор массы), аллергии и пищевые непереносимости.
- Бюджетное и практичное питание.

СТРОГИЕ ПРАВИЛА:
1. ТЕМАТИЧЕСКИЙ ФИЛЬТР:
   Если вопрос пользователя НЕ ОТНОСИТСЯ к питанию, кулинарии, продуктам, рациону или пищевой ценности (например: вопросы о технологиях, коде, политике, погоде, спорте без питания, личной жизни, анекдотах, развлечениях и т.п.):
   Верни СТРОГО JSON:
   {"is_relevant": false, "error": "Запрос не относится к тематике приложения. Консультация доступна только по вопросам питания, рационов и кулинарии."}

2. СТИЛЬ ОТВЕТА ДЛЯ РАЗРЕШЁННЫХ ТЕМ:
   - Никаких приветствий («Здравствуйте», «Приветствую»).
   - Никаких вводных фраз («Рад помочь», «Конечно, вот ответ», «Обратите внимание»).
   - Никаких заключений («Надеюсь это поможет», «Приятного аппетита»).
   - ТОЛЬКО сухой, лаконичный совет по пунктам или в 2-4 предложениях: цифры, факты, прямые действия.
   Верни СТРОГО JSON:
   {"is_relevant": true, "answer": "<сухой текст совета>"}

Ответь ТОЛЬКО валидным JSON без Markdown.
"""

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": query},
    ]

    raw_response = await _ask_llm(messages, temperature=0.2)

    try:
        data = _clean_json_output(raw_response)
    except Exception as exc:
        logger.warning("Could not parse LLM consult response: %s", raw_response)
        raise HTTPException(502, "ИИ-консультант вернул ответ в некорректном формате.") from exc

    if not data.get("is_relevant", False):
        error_message = data.get("error") or "Запрос не относится к тематике приложения. Консультация доступна только по вопросам питания, рационов и кулинарии."
        raise HTTPException(400, error_message)

    answer = (data.get("answer") or "").strip()
    if not answer:
        raise HTTPException(502, "ИИ-консультант вернул пустой ответ.")

    return {"answer": answer}
