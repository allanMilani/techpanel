from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from src.infrastructure.persistence.database import get_engine
from src.interfaces import api_router
from src.interfaces.api.error_handler import register_error_handlers
from src.interfaces.web.router import router as web_router


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
app.include_router(web_router)
