from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.database import get_db
from src.modules.auth.models import User, Review
from src.common.auth.middleware import get_current_user
from src.modules.scheduling.models import Movie
from src.modules.auth.schemas import ReviewCreate, ReviewResponse


router = APIRouter()


@router.get(
    "/movies/{movie_id}/reviews",
    response_model=list[ReviewResponse],
    status_code=status.HTTP_200_OK,
)
async def get_movie_reviews(
    movie_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    result = await db.execute(
        select(Review)
        .where(Review.movie_id == movie_id)
        .order_by(Review.created_at.desc())
    )

    return result.scalars().all()


@router.post(
    "/movies/{movie_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    movie_id: UUID,
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )

    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    review = Review(
        user_id=current_user.id,
        movie_id=movie_id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    db.add(review)

    await db.commit()
    await db.refresh(review)

    return review


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Review).where(Review.id == review_id)
    )

    review = result.scalar_one_or_none()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    is_owner = review.user_id == current_user.id
    is_admin = current_user.role == "admin"

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this review",
        )

    await db.delete(review)
    await db.commit()