"""API endpoints for AI services: price estimation, dish image suggestion, and nutrition consultation."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends

from app.api.deps import optional_user
from app.models import User
from app.schemas.schemas import (
    ConsultRequest,
    ConsultResponse,
    CookingStepsRequest,
    CookingStepsResponse,
    CookingTimeRequest,
    CookingTimeResponse,
    FullRecipeGenerateRequest,
    FullRecipeGenerateResponse,
    ImageSuggestRequest,
    ImageSuggestResponse,
    IngredientsEstimateRequest,
    IngredientsEstimateResponse,
    NutritionEstimateRequest,
    NutritionEstimateResponse,
    PriceEstimateRequest,
    PriceEstimateResponse,
)
from app.services.ai_service import (
    consult_nutrition,
    estimate_cooking_time,
    estimate_dish_price,
    estimate_ingredients_price,
    estimate_nutrition,
    generate_cooking_steps,
    generate_full_recipe,
    suggest_or_generate_image,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/estimate-price", response_model=PriceEstimateResponse)
async def api_estimate_price(
    data: PriceEstimateRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Автоматическая оценка средней стоимости блюда с помощью ИИ.
    Если переданный текст не является едой или блюдом — возвращает HTTP 400 с ошибкой.
    """
    result = await estimate_dish_price(
        dish_name=data.dish_name,
        category=data.category,
        ingredients=data.ingredients,
    )
    return PriceEstimateResponse(
        price=result["price"],
        is_food=result["is_food"],
        comment=result.get("comment"),
    )


@router.post("/suggest-image", response_model=ImageSuggestResponse)
async def api_suggest_image(
    data: ImageSuggestRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Автоматический подбор изображения блюда через Pinterest, Wikipedia и TheMealDB.
    Если переданный текст не является едой — возвращает HTTP 400.
    """
    result = await suggest_or_generate_image(
        dish_name=data.dish_name,
        category=data.category,
    )
    return ImageSuggestResponse(
        image_url=result["image_url"],
        source=result["source"],
        comment=result.get("comment"),
    )


@router.post("/estimate-ingredients-price", response_model=IngredientsEstimateResponse)
async def api_estimate_ingredients_price(
    data: IngredientsEstimateRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Автоматическая оценка цен каждого ингредиента и подбор категорий через ИИ.
    """
    result = await estimate_ingredients_price(
        dish_name=data.dish_name,
        ingredients=data.ingredients,
    )
    return IngredientsEstimateResponse(
        ingredients=result["ingredients"],
        total_price=result["total_price"],
        comment=result.get("comment"),
    )


@router.post("/estimate-nutrition", response_model=NutritionEstimateResponse)
async def api_estimate_nutrition(
    data: NutritionEstimateRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Автоматический расчет КБЖУ блюда на 100 грамм через ИИ.
    """
    result = await estimate_nutrition(
        dish_name=data.dish_name,
        ingredients=data.ingredients,
    )
    return NutritionEstimateResponse(
        calories=result["calories"],
        protein=result["protein"],
        fat=result["fat"],
        carbs=result["carbs"],
        comment=result.get("comment"),
    )


@router.post("/generate-cooking-steps", response_model=CookingStepsResponse)
async def api_generate_cooking_steps(
    data: CookingStepsRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Автоматическая генерация пошагового алгоритма приготовления блюда через ИИ.
    """
    result = await generate_cooking_steps(
        dish_name=data.dish_name,
        ingredients=data.ingredients,
    )
    return CookingStepsResponse(
        steps=result["steps"],
        comment=result.get("comment"),
    )


@router.post("/estimate-cooking-time", response_model=CookingTimeResponse)
async def api_estimate_cooking_time(
    data: CookingTimeRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Автоматический расчет времени приготовления (в минутах) через ИИ.
    """
    result = await estimate_cooking_time(
        dish_name=data.dish_name,
        steps=data.steps,
        ingredients=data.ingredients,
    )
    return CookingTimeResponse(
        cooking_time=result["cooking_time"],
        comment=result.get("comment"),
    )


@router.post("/generate-full-recipe", response_model=FullRecipeGenerateResponse)
async def api_generate_full_recipe(
    data: FullRecipeGenerateRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Комплексная генерация полного рецепта (ингредиенты, цены, КБЖУ, шаги, время, фото) в 1 клик.
    """
    result = await generate_full_recipe(
        dish_name=data.dish_name,
        category=data.category,
    )
    return FullRecipeGenerateResponse(
        name=result["name"],
        category=result["category"],
        time=result["time"],
        calories=result["calories"],
        protein=result["protein"],
        fat=result["fat"],
        carbs=result["carbs"],
        price=result["price"],
        ingredients=result["ingredients"],
        steps=result["steps"],
        image_url=result.get("image_url"),
        comment=result.get("comment"),
    )


@router.post("/consult", response_model=ConsultResponse)
async def api_consult(
    data: ConsultRequest,
    _: Optional[User] = Depends(optional_user),
):
    """
    Строка для консультации пользователя.
    Модель сухо и емко консультирует исключительно по теме приложения (питание, рацион, КБЖУ, рецепты).
    На любые другие темы возвращает HTTP 400 с ошибкой.
    Работает как одиночный запрос, контекст не сохраняется.
    """
    result = await consult_nutrition(query=data.query)
    return ConsultResponse(answer=result["answer"])

