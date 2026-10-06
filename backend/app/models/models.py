"""Модели предметной области планировщика питания."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Union
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def uuid_value() -> str:
    return str(uuid4())


class JSONBCompat(TypeDecorator):
    """JSONB в PostgreSQL и совместимый JSON в тестовой SQLite-базе."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSONB() if dialect.name == "postgresql" else JSON())


class StrEnum(str, Enum):
    """Совместимая с Python 3.9 реализация строкового enum."""


class UserRole(StrEnum):
    GUEST = "guest"
    CLIENT = "client"
    MODERATOR = "moderator"


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(30), default=UserRole.CLIENT.value)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    goal: Mapped[Optional[str]] = mapped_column(String(50))
    allergies: Mapped[Optional[Union[dict, list]]] = mapped_column(JSONBCompat)
    preferences: Mapped[Optional[Union[dict, list]]] = mapped_column(JSONBCompat)
    cooking_time_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Ration(Base):
    __tablename__ = "rations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    period_days: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[Optional[list]] = mapped_column(JSONBCompat)
    total_calories: Mapped[float] = mapped_column(Float, default=0)
    total_price: Mapped[float] = mapped_column(Float, default=0)
    total_protein: Mapped[float] = mapped_column(Float, default=0)
    total_fat: Mapped[float] = mapped_column(Float, default=0)
    total_carbs: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dish(Base):
    __tablename__ = "dishes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    ration_id: Mapped[str] = mapped_column(ForeignKey("rations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    meal_type: Mapped[str] = mapped_column(String(50))
    day_number: Mapped[int] = mapped_column(Integer)
    macros: Mapped[dict] = mapped_column(JSONBCompat, default=dict)
    recipe: Mapped[Optional[dict]] = mapped_column(JSONBCompat)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    calories: Mapped[float] = mapped_column(Float, default=0)
    proteins: Mapped[float] = mapped_column(Float, default=0)
    fats: Mapped[float] = mapped_column(Float, default=0)
    carbs: Mapped[float] = mapped_column(Float, default=0)
    price: Mapped[float] = mapped_column(Float, default=0)

    @property
    def title(self) -> str:
        return self.name

    @property
    def category(self) -> str:
        return self.meal_type

    @property
    def tag(self) -> Optional[str]:
        return None

    @property
    def time(self) -> int:
        return 0

    @property
    def image(self) -> Optional[str]:
        return self.image_url

    @property
    def protein(self) -> float:
        return self.proteins

    @property
    def fat(self) -> float:
        return self.fats


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[float] = mapped_column(Float, default=1)
    unit: Mapped[str] = mapped_column(String(30), default="шт")
    calories_per_100g: Mapped[float] = mapped_column(Float, default=0)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float, default=0)


class ModeratorRecipe(Base):
    __tablename__ = "moderator_recipes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    moderator_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    recipe: Mapped[dict] = mapped_column(JSONBCompat, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="draft")


class FoodDiary(Base):
    __tablename__ = "food_diary"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dish_id: Mapped[Optional[str]] = mapped_column(ForeignKey("dishes.id", ondelete="SET NULL"))
    entry_date: Mapped[str] = mapped_column(String(10), index=True)
    meal_type: Mapped[str] = mapped_column(String(50))
    calories: Mapped[float] = mapped_column(Float, default=0)
    note: Mapped[Optional[str]] = mapped_column(Text)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    ration_id: Mapped[Optional[str]] = mapped_column(ForeignKey("rations.id", ondelete="SET NULL"))
    items: Mapped[Union[list, dict]] = mapped_column(JSONBCompat, default=list)
    status: Mapped[str] = mapped_column(String(30), default=ApplicationStatus.DRAFT.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_value)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
