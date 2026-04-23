from fastapi import APIRouter

from src.interfaces.api.routers.auth import router as auth_router
from src.interfaces.api.routers.executions import router as executions_router
from src.interfaces.api.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(executions_router)

__all__ = ["api_router"]
