from fastapi import APIRouter
from app.api.v1 import applications, auth, catalog, diary, moderator, rations, recipes, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(users.profile_router)
api_router.include_router(recipes.router)
api_router.include_router(rations.router)
api_router.include_router(applications.router)
api_router.include_router(catalog.router)
api_router.include_router(diary.router)
api_router.include_router(moderator.router)
