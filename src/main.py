from sys import prefix
from src.modules.scheduling.routers import screens, seats, showtimes
from src.common.database import get_db, engine, Base
from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from src.modules.ordering.routers import food, orders
from src.modules.scheduling import models
from contextlib import asynccontextmanager
from src.modules.auth import routers

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup -> scan all models(Base) and create missing db tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown -> close all connection pools
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(food.router, prefix="/food", tags=["food"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])

templates = Jinja2Templates(directory="templates")


app.include_router(routers.router, prefix="/api", tags=["auth"])

app.include_router(screens.router, prefix="/api/screens", tags=["screens"])
app.include_router(seats.router, prefix="/api/seats", tags=["seats"])
app.include_router(showtimes.router, prefix="/api/showtimes", tags=["showtimes"])

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}