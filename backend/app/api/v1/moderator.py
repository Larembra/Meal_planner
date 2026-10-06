"""Маршруты модератора для операционной работы с контентом."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Application, Dish, ModeratorRecipe, Ration, User
from app.schemas.schemas import ApplicationRead, ModeratorRecipeCreate, ModeratorRecipeRead, UserRead

router = APIRouter(prefix="/moderator", tags=["moderator"])


@router.get("/users", response_model=list[UserRead])
async def moderator_users(db: AsyncSession = Depends(get_db),
                          _: User = Depends(require_roles("admin", "moderator"))):
    return list((await db.execute(select(User).order_by(User.created_at.desc()))).scalars())


@router.get("/applications", response_model=list[ApplicationRead])
async def moderator_applications(db: AsyncSession = Depends(get_db),
                                 _: User = Depends(require_roles("admin", "moderator"))):
    return list((await db.execute(select(Application).order_by(Application.created_at.desc()))).scalars())


@router.post("/recipes", response_model=ModeratorRecipeRead, status_code=201)
async def create_recipe(data: ModeratorRecipeCreate, db: AsyncSession = Depends(get_db),
                        user: User = Depends(require_roles("moderator"))):
    """Создаёт рецепт, доступный модерации."""
    recipe = ModeratorRecipe(**data.model_dump(), moderator_id=user.id)
    db.add(recipe)
    ration = (await db.execute(select(Ration).where(Ration.user_id == user.id))).scalar_one_or_none()
    if ration is None:
        ration = Ration(user_id=user.id, period_days=1, tags=["catalog"], status="active")
        db.add(ration)
        await db.flush()
    details = data.recipe
    macros = details.get("macros", {})
    db.add(Dish(
        ration_id=ration.id,
        name=data.name,
        meal_type=details.get("category", "Ужин"),
        day_number=1,
        macros=macros,
        recipe=details,
        image_url=details.get("image") or details.get("image_url"),
        calories=float(details.get("calories", 0)),
        proteins=float(details.get("protein", details.get("proteins", 0))),
        fats=float(details.get("fat", details.get("fats", 0))),
        carbs=float(details.get("carbs", 0)),
        price=float(details.get("price", 0)),
    ))
    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.get("/recipes", response_model=list[ModeratorRecipeRead])
async def list_moderator_recipes(db: AsyncSession = Depends(get_db),
                                 _: User = Depends(require_roles("moderator"))):
    return list((await db.execute(select(ModeratorRecipe).order_by(ModeratorRecipe.name))).scalars())


@router.patch("/recipes/{recipe_id}", response_model=ModeratorRecipeRead)
async def update_recipe(recipe_id: str, data: ModeratorRecipeCreate, db: AsyncSession = Depends(get_db),
                        _: User = Depends(require_roles("moderator"))):
    recipe = await db.get(ModeratorRecipe, recipe_id)
    if recipe is None:
        raise HTTPException(404, "Рецепт не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(recipe, key, value)
    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.delete("/recipes/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: str, db: AsyncSession = Depends(get_db),
                        _: User = Depends(require_roles("moderator"))):
    recipe = await db.get(ModeratorRecipe, recipe_id)
    if recipe is None:
        raise HTTPException(404, "Рецепт не найден")
    await db.delete(recipe)
    await db.commit()
