from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    goal: Optional[str] = None
    allergies: Optional[list[str]] = None
    preferences: Optional[dict] = None
    cooking_time_minutes: Optional[int] = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    name: str
    role: str
    goal: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    cooking_time_minutes: Optional[int] = None
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


class RationCreate(BaseModel):
    tags: list[str] = Field(default_factory=list)
    period_days: int = Field(ge=1, le=7)
    extra_request: str = Field(default="", max_length=1500)
    model: Optional[str] = Field(default=None, min_length=3, max_length=150)


class RationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    date_from: date
    date_to: date
    calories_target: int
    status: str
    protein_target: Optional[float] = None
    fat_target: Optional[float] = None
    carbs_target: Optional[float] = None
    created_at: Optional[datetime] = None


class RationMealCreate(BaseModel):
    meal_id: str
    entry_date: date
    meal_type: str


class DiaryCreate(BaseModel):
    entry_date: date
    meal_type: str
    meal_id: Optional[str] = None
    calories: float = 0
    note: Optional[str] = None
    completed: bool = False


class MealRead(BaseModel):
    id: str
    name: str
    description: str
    meal_type: str
    cooking_time: int
    servings: int
    calories: float
    protein: float
    fat: float
    carbs: float
    diet_type: str
    allergens: list[str]
    tags: list[str]
    cost: float
    ingredients: list[dict] = Field(default_factory=list)


class RecipeCreate(BaseModel):
    name: str
    category: str = "dinner"
    time: int = 0
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0
    price: float = 0
    image: Optional[str] = None
    ingredients: list[dict] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
