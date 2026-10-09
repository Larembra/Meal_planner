"""SQLAlchemy mappings for the schema shipped in ``data/seed.sql``."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.types import JSON, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TextArray(TypeDecorator):
    """PostgreSQL text[] with JSON storage in SQLite-based local checks."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String()))
        return dialect.type_descriptor(JSON())


def uuid_column(*args, **kwargs):
    return mapped_column(UUID(as_uuid=False), *args, default=lambda: str(uuid4()), **kwargs)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column("password_hash", Text, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[str] = uuid_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(String(30))
    budget: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    diet_type: Mapped[str] = mapped_column(String(30), default="omnivore", server_default="omnivore", nullable=False)
    restrictions: Mapped[Optional[str]] = mapped_column(Text)
    meals_per_day: Mapped[int] = mapped_column(SmallInteger, default=3, server_default="3", nullable=False)
    max_cooking_time: Mapped[Optional[int]] = mapped_column(Integer)
    preferences: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Meal(Base):
    __tablename__ = "meals"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    cooking_time: Mapped[int] = mapped_column(Integer, nullable=False)
    servings: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    calories: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    protein: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    fat: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    carbs: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    diet_type: Mapped[str] = mapped_column(String(30), default="omnivore", server_default="omnivore", nullable=False)
    allergens: Mapped[list[str]] = mapped_column(TextArray, default=list, server_default="{}", nullable=False)
    tags: Mapped[list[str]] = mapped_column(TextArray, default=list, server_default="{}", nullable=False)
    created_by: Mapped[Optional[str]] = uuid_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="published", server_default="published", nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0", nullable=False)
    goal: Mapped[str] = mapped_column(String(30), default="maintain", server_default="maintain", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    calories: Mapped[float] = mapped_column(Numeric(7, 2), default=0, server_default="0", nullable=False)
    protein: Mapped[float] = mapped_column(Numeric(7, 2), default=0, server_default="0", nullable=False)
    fat: Mapped[float] = mapped_column(Numeric(7, 2), default=0, server_default="0", nullable=False)
    carbs: Mapped[float] = mapped_column(Numeric(7, 2), default=0, server_default="0", nullable=False)
    cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MealProduct(Base):
    __tablename__ = "meal_products"
    __table_args__ = (UniqueConstraint("meal_id", "product_id"),)
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    meal_id: Mapped[str] = uuid_column(ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = uuid_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)


class Ration(Base):
    __tablename__ = "rations"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[str] = uuid_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    calories_target: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft", nullable=False)
    protein_target: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    fat_target: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    carbs_target: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RationMeal(Base):
    __tablename__ = "ration_meals"
    __table_args__ = (UniqueConstraint("ration_id", "date", "meal_type"),)
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    ration_id: Mapped[str] = uuid_column(ForeignKey("rations.id", ondelete="CASCADE"), nullable=False)
    meal_id: Mapped[str] = uuid_column(ForeignKey("meals.id", ondelete="RESTRICT"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    servings: Mapped[float] = mapped_column(Numeric(5, 2), default=1, server_default="1", nullable=False)


class Tracking(Base):
    __tablename__ = "tracking"
    __table_args__ = (UniqueConstraint("user_id", "ration_meal_id"),)
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[str] = uuid_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ration_meal_id: Mapped[str] = uuid_column(ForeignKey("ration_meals.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="planned", server_default="planned", nullable=False)
    eaten_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Request(Base):
    __tablename__ = "requests"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[str] = uuid_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", server_default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ShoppingList(Base):
    __tablename__ = "shopping_lists"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[str] = uuid_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ration_id: Mapped[Optional[str]] = uuid_column(ForeignKey("rations.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    __table_args__ = (UniqueConstraint("shopping_list_id", "product_id"),)
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    shopping_list_id: Mapped[str] = uuid_column(ForeignKey("shopping_lists.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[str] = uuid_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)


class AIGeneration(Base):
    __tablename__ = "ai_generations"
    id: Mapped[str] = uuid_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[str] = uuid_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ration_id: Mapped[Optional[str]] = uuid_column(ForeignKey("rations.id", ondelete="SET NULL"))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text)
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    model: Mapped[Optional[str]] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending", nullable=False)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
