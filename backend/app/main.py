import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.v1 import api_router

app = FastAPI(
    title="Meal Planner API",
    description="""
API сервиса умного планирования питания и диет «Витя, где ням-ням?».

### Возможности:
* **Аутентификация:** регистрация (`/auth/register`), вход (`/auth/login`), JWT access/refresh токены.
* **Пользователи и профиль:** настройки калорийности, целей, аллергий и бюджета (`/users/me`).
* **Каталог блюд:** рецепты, БЖУ, время готовки, стоимость, аллергены (`/recipes`).
* **ИИ-генерация рационов:** генерация меню без повторов на 1–7 дней через Google Gemini (`/rations/generate`).
* **ИИ-нутрициолог:** онлайн-консультации по питанию (`/ai/consult`).
* **Дневник питания:** трекинг приёмов пищи и прогресс по калориям (`/diary`).

*Для тестирования защищённых эндпоинтов нажмите **Authorize** вверху справа и введите access-токен.*
""",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
@app.get("/swagger", include_in_schema=False)
@app.get("/api/docs", include_in_schema=False)
@app.get("/api/v1/docs", include_in_schema=False)
async def redirect_to_swagger():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}
