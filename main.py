from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette import status as http_status

from src.infrastructure.config.settings import get_settings
from src.infrastructure.persistence.database import get_engine
from src.interfaces import api_router
from src.interfaces.api.error_handler import register_error_handlers

DIST_INDEX = (
    Path(__file__).resolve().parent
    / "src"
    / "interfaces"
    / "static"
    / "dist"
    / "index.html"
)


def _spa_index() -> FileResponse | JSONResponse:
    if not DIST_INDEX.is_file():
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Frontend não compilado. Execute: make frontend-build",
            },
        )
    return FileResponse(DIST_INDEX)


def _spa_dev_redirect(path: str) -> RedirectResponse | None:
    settings = get_settings()
    if settings.app_env != "development":
        return None
    frontend_dev_server_url = (settings.frontend_dev_server_url or "").rstrip("/")
    if not frontend_dev_server_url:
        return None
    return RedirectResponse(
        url=f"{frontend_dev_server_url}{path}",
        status_code=http_status.HTTP_307_TEMPORARY_REDIRECT,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _ = get_engine()
    yield
    await get_engine().dispose()


app = FastAPI(title="TechPanel", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(api_router, prefix="/api")

app.mount(
    "/static",
    StaticFiles(directory="src/interfaces/static"),
    name="static",
)


@app.get("/", include_in_schema=False, response_model=None)
async def spa_root() -> FileResponse | JSONResponse:
    redirect = _spa_dev_redirect("/")
    if redirect is not None:
        return redirect
    return _spa_index()


@app.get("/login", include_in_schema=False, response_model=None)
async def spa_login() -> FileResponse | JSONResponse:
    redirect = _spa_dev_redirect("/login")
    if redirect is not None:
        return redirect
    return _spa_index()


@app.get("/register", include_in_schema=False, response_model=None)
async def spa_register() -> FileResponse | JSONResponse:
    redirect = _spa_dev_redirect("/register")
    if redirect is not None:
        return redirect
    return _spa_index()


@app.get("/app", include_in_schema=False, response_model=None)
async def spa_app() -> RedirectResponse:
    redirect = _spa_dev_redirect("/dashboard")
    if redirect is not None:
        return redirect
    return RedirectResponse(url="/dashboard", status_code=http_status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/app/{_path:path}", include_in_schema=False, response_model=None)
async def spa_app_nested(_path: str) -> RedirectResponse:
    redirect = _spa_dev_redirect("/dashboard")
    if redirect is not None:
        return redirect
    return RedirectResponse(url="/dashboard", status_code=http_status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/{path:path}", include_in_schema=False, response_model=None)
async def spa_catch_all(path: str) -> FileResponse | JSONResponse:
    if path.startswith("api/") or path.startswith("static/"):
        return JSONResponse(
            status_code=http_status.HTTP_404_NOT_FOUND,
            content={"detail": "Not Found"},
        )
    redirect = _spa_dev_redirect(f"/{path}")
    if redirect is not None:
        return redirect
    return _spa_index()
