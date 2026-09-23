from sys import prefix
from src.modules.auth import routers
from src.common.database import get_db, engine, Base
from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from src.modules.auth import models
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.include_router(routers.router, prefix="/api", tags=["auth"])


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}