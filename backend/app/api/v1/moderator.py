from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_roles
from app.api.v1.catalog import meal_payload
from app.db.session import get_db
from app.models import Meal, MealProduct, Product, User
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
    meal = Meal(created_by=user.id, name=data.name, description="\n".join(data.steps) or data.name,
                meal_type=category, cooking_time=max(0, data.time), servings=1,
                calories=data.calories, protein=data.protein, fat=data.fat, carbs=data.carbs,
                cost=data.price, image_url=data.image, status="published", allergens=[], tags=[])
    db.add(meal)
    await db.flush()
    for ingredient in data.ingredients:
        name = str(ingredient.get("name", "")).strip()
        if not name:
            continue
        product = (await db.execute(select(Product).where(Product.name == name))).scalar_one_or_none()
        if product is None:
            quantity_text = str(ingredient.get("quantity", ""))
            category_name = str(ingredient.get("category") or "other")[:50]
            product = Product(name=name[:150], category=category_name, unit=quantity_text[-10:] or "g",
                              cost=float(ingredient.get("price") or 0))
            db.add(product)
            await db.flush()
        qty = ingredient.get("amount") or 1
        try:
            qty = float(qty)
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
    meal.description = "\n".join(data.steps) or data.name
    meal.cooking_time, meal.calories = max(0, data.time), data.calories
    meal.protein, meal.fat, meal.carbs, meal.cost = data.protein, data.fat, data.carbs, data.price
    meal.image_url = data.image
    await db.commit()
    return await meal_payload(db, meal)


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str, db: AsyncSession = Depends(get_db), user: User = ROLE):
    meal = await db.get(Meal, recipe_id)
    if meal is None:
        raise HTTPException(404, "Рецепт не найден")
    if meal.created_by != user.id and user.role != "admin":
        raise HTTPException(403, "Нельзя удалить чужой рецепт")
    meal.status = "archived"
    await db.commit()
