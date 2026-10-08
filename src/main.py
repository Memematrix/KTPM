from fastapi.staticfiles import StaticFiles
from fastapi import status
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
import uuid
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
from src.modules.auth.routers import register_and_login, movies, reviews

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

app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(register_and_login.router, prefix="/api/auth", tags=["auth"])
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(reviews.router, prefix="/api", tags=["reviews"])

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

@app.get("/movies")
async def get_all_movies(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Movie))
    movies = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="movies.html",
        context= {
            "movies": movies
        }
    )

@app.get("/movies/{movie_id}")
async def get_movie_detail(movie_id: uuid.UUID, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Movie).options(selectinload(models.Movie.showtimes)).where(models.Movie.id == movie_id))
    movie = result.scalars().first()

    return templates.TemplateResponse(
        request=request,
        name="movie_detail.html",
        context= {
            "movie": movie
        }
    )
@app.get("/showtimes")
async def get_all_showtimes(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Showtime))
    showtimes = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="showtimes.html",
        context= {
            "showtimes": showtimes
        }
    )

@app.get("/showtimes/{showtime_id}", name="get_showtime_detail_html")
async def get_showtime_detail(request: Request, showtime_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Showtime).where(models.Showtime.id == showtime_id).options(selectinload(models.Showtime.screen).selectinload(models.Screen.seats), selectinload(models.Showtime.tickets)))
    showtime = result.scalars().first()
    if not showtime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Showtime not exist"
        )
    booked_seat_ids = {ticket.seat_id for ticket in showtime.tickets}

    available_seats = [
        {
            "seat": seat,
            "is_available": seat.id not in booked_seat_ids
        } 
        for seat in showtime.screen.seats
    ]

    return templates.TemplateResponse(
        request=request,
        name="showtime_detail.html",
        context= {
        "showtime": showtime,
        "available_seats": available_seats
        }
    )

@app.get("/login", name="login_html", include_in_schema=False)
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.get("/register", name="register_html", include_in_schema=False)
async def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.get("/me", name="account_html", include_in_schema=False)
async def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account.html"
    )
