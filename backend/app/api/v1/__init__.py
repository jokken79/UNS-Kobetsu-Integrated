"""
API v1 Router
Aggregates all API endpoints under versioned prefix.
"""
from fastapi import APIRouter

from .kobetsu import router as kobetsu_router
from .auth import router as auth_router
from .factories import router as factories_router
from .companies import router as companies_router
from .employees import router as employees_router
from .imports import router as imports_router
from .documents import router as documents_router
from .settings import router as settings_router
from .endpoints.sync import router as sync_router

api_router = APIRouter()

# Include routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    kobetsu_router,
    prefix="/kobetsu",
    tags=["Kobetsu Keiyakusho (個別契約書)"]
)

api_router.include_router(
    factories_router,
    prefix="/factories",
    tags=["Factories (派遣先/工場)"]
)

api_router.include_router(
    companies_router,
    prefix="",
    tags=["Companies & Plants (Base Madre)"]
)

api_router.include_router(
    employees_router,
    prefix="/employees",
    tags=["Employees (派遣社員)"]
)

api_router.include_router(
    imports_router,
    prefix="/import",
    tags=["Data Import (データインポート)"]
)

api_router.include_router(
    documents_router,
    prefix="/documents",
    tags=["Document Generation (書類生成)"]
)

api_router.include_router(
    sync_router,
    prefix="/sync",
    tags=["Data Sync (データ同期)"]
)

api_router.include_router(
    settings_router,
    prefix="/settings",
    tags=["Settings (設定)"]
)
