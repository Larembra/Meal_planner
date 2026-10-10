import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.session import get_db
from app.models import Product, Ration, ShoppingItem, ShoppingList, User

router = APIRouter(prefix="/shopping", tags=["shopping"])


class ShoppingItemCreate(BaseModel):
    product_id: Optional[str] = None
    name: Optional[str] = None
    quantity: float = Field(default=1, gt=0)
    unit: str = "шт."
    price: float = Field(default=0, ge=0)
    category: str = "other"


class ShoppingItemUpdate(BaseModel):
    quantity: Optional[float] = Field(default=None, gt=0)
    is_purchased: Optional[bool] = None


async def active_list(db: AsyncSession, user: User) -> ShoppingList:
    value = (await db.execute(select(ShoppingList).where(
        ShoppingList.user_id == user.id, ShoppingList.status == "active"
    ).order_by(ShoppingList.created_at.desc()).execution_options(autoflush=False))).scalars().first()
    if value is not None and value.ration_id is not None:
        ration = (await db.execute(
            select(Ration).where(Ration.id == value.ration_id).execution_options(autoflush=False)
        )).scalar_one_or_none()
        if ration is None:
            await db.execute(update(ShoppingList).where(ShoppingList.id == value.id).values(ration_id=None))
            value.ration_id = None
    if value is None:
        value = ShoppingList(user_id=user.id)
        db.add(value)
        await db.flush()
    return value


def payload(item: ShoppingItem, product: Product) -> dict:
    unit = re.sub(r"^\s*\d+(?:[.,]\d+)?\s*", "", product.unit or "").strip() or "шт."
    return {"id": item.id, "product_id": product.id, "name": product.name,
            "category": product.category, "quantity": float(item.quantity),
            "unit": unit, "price": float(item.total_cost or product.cost or 0),
            "is_purchased": item.is_purchased}


@router.get("")
async def list_items(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    shopping_list = await active_list(db, user)
    rows = (await db.execute(select(ShoppingItem, Product)
        .join(Product, Product.id == ShoppingItem.product_id)
        .where(ShoppingItem.shopping_list_id == shopping_list.id)
        .order_by(Product.category, Product.name))).all()
    await db.commit()
    return [payload(item, product) for item, product in rows]


@router.post("/items", status_code=201)
async def add_item(data: ShoppingItemCreate, db: AsyncSession = Depends(get_db),
                   user: User = Depends(current_user)):
    shopping_list = await active_list(db, user)
    product = await db.get(Product, data.product_id) if data.product_id else None
    if product is None:
        name = (data.name or "").strip()[:150]
        if not name:
            raise HTTPException(422, "Укажите название товара")
        product = (await db.execute(select(Product).where(
            func.lower(Product.name) == name.casefold()))).scalar_one_or_none()
        if product is None:
            await db.execute(insert(Product).values(
                name=name, category=data.category[:50], unit=data.unit[:20], cost=data.price
            ).on_conflict_do_nothing(index_elements=["name"]))
            product = (await db.execute(select(Product).where(
                func.lower(Product.name) == name.casefold()))).scalar_one()
        elif data.category != "other":
            product.category = data.category[:50]
    item = (await db.execute(select(ShoppingItem).where(
        ShoppingItem.shopping_list_id == shopping_list.id,
        ShoppingItem.product_id == product.id
    ))).scalar_one_or_none()
    item_price = data.price if data.price > 0 else float(product.cost or 0)
    if item:
        item.quantity = float(item.quantity) + data.quantity
        item.total_cost = float(item.total_cost or 0) + item_price
    else:
        item = ShoppingItem(shopping_list_id=shopping_list.id, product_id=product.id,
                            quantity=data.quantity, total_cost=item_price)
        db.add(item)
    await db.commit()
    await db.refresh(item)
    return payload(item, product)


@router.patch("/items/{item_id}")
async def update_item(item_id: str, data: ShoppingItemUpdate,
                      db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    item = await db.get(ShoppingItem, item_id)
    shopping_list = await db.get(ShoppingList, item.shopping_list_id) if item else None
    if item is None or shopping_list is None or shopping_list.user_id != user.id:
        raise HTTPException(404, "Товар не найден")
    if data.quantity is not None:
        item.quantity = data.quantity
    if data.is_purchased is not None:
        item.is_purchased = data.is_purchased
    await db.commit()
    return payload(item, await db.get(Product, item.product_id))


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: str, db: AsyncSession = Depends(get_db),
                      user: User = Depends(current_user)):
    item = await db.get(ShoppingItem, item_id)
    shopping_list = await db.get(ShoppingList, item.shopping_list_id) if item else None
    if item is None or shopping_list is None or shopping_list.user_id != user.id:
        raise HTTPException(404, "Товар не найден")
    await db.delete(item)
    await db.commit()


@router.delete("", status_code=204)
async def delete_all_items(db: AsyncSession = Depends(get_db),
                           user: User = Depends(current_user)):
    shopping_list = await active_list(db, user)
    items = (await db.execute(select(ShoppingItem).where(
        ShoppingItem.shopping_list_id == shopping_list.id))).scalars().all()
    for item in items:
        await db.delete(item)
    await db.commit()
