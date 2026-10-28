"""Request and response schemas for movies and reviews."""

from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# Movies

class MovieCreate(BaseModel):
    title: str
    description: str | None = None
    duration: int
    release_date: date
    poster_url: str | None = None


class MovieUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    duration: int | None = None
    release_date: date | None = None
    poster_url: str | None = None


class MovieResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    duration: int
    release_date: date | None
    poster_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Reviews

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    movie_id: UUID
    rating: int
    comment: str | None
    created_at: datetime