from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from src.common.database import get_db
from src.common.auth.role_guard import require_role, CurrentUser

from src.modules.auth.schemas import MovieCreate, MovieUpdate, MovieResponse
from src.modules.scheduling.models import Movie


router = APIRouter()


@router.get(
    "",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK
)
async def get_movies(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(Movie))
    movies = result.scalars().all()
    return movies

@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    status_code=status.HTTP_200_OK
)
async def get_movie_id(
    movie_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(Movie).where(
        Movie.id == movie_id
    ))
    movie = result.scalars().first()
    if movie:
        return movie

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Movie does not exist"
    )


@router.post(
    "/create",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
    movies: MovieCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser = Depends(require_role("admin"))
):
    result = await db.execute(
    select(Movie).where(
        Movie.title == movies.title,
        Movie.release_date == movies.release_date,
    )
)

    existing_movie = result.scalar_one_or_none()

    if existing_movie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already exists"
        )

    new_movie = Movie(
        title = movies.title,
        description = movies.description,
        duration = movies.duration,
        release_date = movies.release_date,
        poster_url = movies.poster_url
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)
    return new_movie


@router.patch(
    "/update/{movie_id}",
    response_model=MovieResponse,
    status_code= status.HTTP_200_OK
)
async def update_movie_id(
    movie_id: UUID,
    movie_update: MovieUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser = Depends(require_role("admin"))
):
    result = await db.execute(select(Movie).where(
        Movie.id == movie_id
    ))
    movie = result.scalars().first()
    if movie:
        update_data = movie_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(movie, field, value)

        await db.commit()
        await db.refresh(movie)

        return movie

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Movie not found"
    )

@router.delete(
    "/delete/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_movie_id(
    movie_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    curren_user: CurrentUser = Depends(require_role("admin"))
):
    result = await db.execute(select(Movie).where(
        Movie.id == movie_id
    ))
    movie = result.scalars().first()
    if movie:
        await db.delete(movie)
        await db.commit()

        return None

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Movie does not exist"
    )