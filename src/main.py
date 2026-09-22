from src.common.database import get_db
from sqlalchemy import select
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from src import models
from src.modules.ordering.routers.food import router as food_router
app = FastAPI()

app.include_router(food_router, prefix="/food", tags=["food"])

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/movies")
async def get_all_movies(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Movie))

    movies = result.scalars().all()

    return movies