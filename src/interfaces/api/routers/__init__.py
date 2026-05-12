from fastapi import APIRouter

from src.interfaces.api.routers.auth import router as auth_router
from src.interfaces.api.routers.executions import router as executions_router
from src.interfaces.api.routers.health import router as health_router
from src.interfaces.api.routers.projects import router as projects_router
from src.interfaces.api.routers.servers import router as servers_router
from src.interfaces.api.routers.pipelines import router as pipelines_router
from src.interfaces.api.routers.github import router as github_router
from src.interfaces.api.routers.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(executions_router)
api_router.include_router(servers_router)
api_router.include_router(projects_router)
api_router.include_router(pipelines_router)
api_router.include_router(github_router)

__all__ = ["api_router"]
