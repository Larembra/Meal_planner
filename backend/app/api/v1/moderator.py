import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_roles
from app.api.v1.catalog import meal_payload
from app.db.session import get_db
from app.models import Meal, MealProduct, Product, RationMeal, User
from app.schemas.schemas import RecipeCreate

router = APIRouter(prefix="/moderator", tags=["moderator"])
ROLE = Depends(require_roles("admin", "moderator"))


@router.get("/users")
async def moderator_users(db: AsyncSession = Depends(get_db), _: User = ROLE):
    return list((await db.execute(select(User).order_by(User.created_at.desc()))).scalars())


@router.get("/recipes")
async def list_moderator_recipes(db: AsyncSession = Depends(get_db), _: User = ROLE):
    meals = (await db.execute(select(Meal).where(Meal.status != "archived").order_by(Meal.name))).scalars().all()
    return [await meal_payload(db, meal) for meal in meals]


@router.post("/recipes", status_code=201)
async def create_recipe(data: RecipeCreate, db: AsyncSession = Depends(get_db), user: User = ROLE):
    category = {"завтрак": "breakfast", "обед": "lunch", "ужин": "dinner", "перекус": "snack"}.get(data.category.lower(), data.category.lower())
    if category not in {"breakfast", "lunch", "dinner", "snack"}:
        raise HTTPException(422, "Категория должна быть: Завтрак, Обед, Ужин или Перекус")
    meal = Meal(created_by=user.id, name=data.name, description=data.name,
                instructions="\n".join(data.steps),
                meal_type=category, cooking_time=max(0, data.time), servings=1,
                calories=data.calories, protein=data.protein, fat=data.fat, carbs=data.carbs,
                cost=data.price, status="published", allergens=[], tags=data.tags)
    db.add(meal)
    await db.flush()
    for ingredient in data.ingredients:
        name = str(ingredient.get("name", "")).strip()
        if not name:
            continue
        product = (await db.execute(select(Product).where(func.lower(Product.name) == name.casefold()))).scalar_one_or_none()
        if product is None:
            quantity_text = str(ingredient.get("quantity", ""))
            category_name = str(ingredient.get("category") or "other")[:50]
            await db.execute(insert(Product).values(
                name=name[:150], category=category_name, unit=quantity_text[-10:] or "g",
                cost=float(ingredient.get("price") or 0)
            ).on_conflict_do_nothing(index_elements=["name"]))
            product = (await db.execute(select(Product).where(func.lower(Product.name) == name.casefold()))).scalar_one()
        else:
            category_name = str(ingredient.get("category") or "").strip()
            if category_name and category_name != "other":
                product.category = category_name[:50]
            quantity_text = str(ingredient.get("quantity") or "").strip()
            if quantity_text:
                product.unit = quantity_text[-10:]
            if ingredient.get("price") is not None:
                product.cost = float(ingredient.get("price") or 0)
        quantity_text = str(ingredient.get("quantity") or "").strip()
        qty_value = ingredient.get("amount")
        if qty_value is None:
            match = re.search(r"\d+(?:[.,]\d+)?", quantity_text)
            qty_value = match.group(0).replace(",", ".") if match else 1
        try:
            qty = float(qty_value)
        except (TypeError, ValueError):
            qty = 1
        db.add(MealProduct(meal_id=meal.id, product_id=product.id, quantity=qty))
    await db.commit()
    await db.refresh(meal)
    return await meal_payload(db, meal)


@router.patch("/recipes/{recipe_id}")
async def update_recipe(recipe_id: str, data: RecipeCreate, db: AsyncSession = Depends(get_db), user: User = ROLE):
    meal = await db.get(Meal, recipe_id)
    if meal is None:
        raise HTTPException(404, "Рецепт не найден")
    if meal.created_by != user.id and user.role != "admin":
        raise HTTPException(403, "Нельзя изменить чужой рецепт")
    meal.name = data.name
    meal.meal_type = {"завтрак": "breakfast", "обед": "lunch", "ужин": "dinner", "перекус": "snack"}.get(data.category.lower(), data.category.lower())
    meal.description = data.name
    meal.instructions = "\n".join(data.steps)
    meal.tags = data.tags
    meal.cooking_time, meal.calories = max(0, data.time), data.calories
    meal.protein, meal.fat, meal.carbs, meal.cost = data.protein, data.fat, data.carbs, data.price
    await db.commit()
    return await meal_payload(db, meal)


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str, db: AsyncSession = Depends(get_db), user: User = ROLE):
    meal = await db.get(Meal, recipe_id)
    if meal is None:
        raise HTTPException(404, "Рецепт не найден")
    if user.role not in {"admin", "moderator"}:
        raise HTTPException(403, "Недостаточно прав")
    await db.execute(
        RationMeal.__table__.delete().where(RationMeal.meal_id == meal.id)
    )
    await db.delete(meal)
    await db.commit()
