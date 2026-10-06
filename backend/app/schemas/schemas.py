"""Pydantic-схемы публичного API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    allergies: Optional[Union[dict, list]] = None
    preferences: Optional[Union[dict, list]] = None
    cooking_time_minutes: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    allergies: Optional[Union[dict, list]] = None
    preferences: Optional[Union[dict, list]] = None
    cooking_time_minutes: Optional[int] = None


class UserRead(UserCreate):
    model_config = ConfigDict(from_attributes=True)
    password: Optional[str] = None
    id: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class DishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    ration_id: str
    name: str
    meal_type: str
    day_number: int
    macros: dict
    recipe: Optional[dict]
    image_url: Optional[str]
    calories: float
    proteins: float
    fats: float
    carbs: float
    price: float


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dish_id: Optional[str]
    name: str
    quantity: float
    unit: str
    calories_per_100g: float
    category: Optional[str]
    price: float


class ProductCreate(BaseModel):
    dish_id: str
    name: str
    quantity: float = 1
    unit: str = "шт"
    calories_per_100g: float = 0
    category: Optional[str] = None
    price: float = 0


class RationCreate(BaseModel):
    tags: list[str] = Field(default_factory=list)
    period_days: int = Field(ge=1, le=7)


class RationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    period_days: int
    tags: Optional[list]
    total_calories: float
    total_price: float
    total_protein: float
    total_fat: float
    total_carbs: float
    status: str
    created_at: Optional[datetime] = None


class DiaryCreate(BaseModel):
    entry_date: str
    meal_type: str
    dish_id: Optional[str] = None
    calories: float = 0
    note: Optional[str] = None
    completed: bool = False


class DiaryRead(DiaryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str


class ApplicationCreate(BaseModel):
    ration_id: Optional[str] = None
    items: Union[list, dict] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|active|completed|cancelled)$")


class ApplicationRead(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    created_at: Optional[datetime] = None


class ModeratorRecipeCreate(BaseModel):
    name: str
    recipe: dict = Field(default_factory=dict)
    status: str = Field(default="draft", pattern="^(draft|active|completed|cancelled)$")


class ModeratorRecipeRead(ModeratorRecipeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: str
    moderator_id: str
