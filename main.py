from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.database import get_db_session, get_engine

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _ = get_engine()
    yield
    await get_engine().dispose()

app = FastAPI(title="TechPanel", lifespan=lifespan)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/db")
async def health_db(session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}