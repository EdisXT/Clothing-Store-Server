from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..oauth2 import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/product/{product_id}", response_model=list[schemas.ReviewOut])
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Review)
        .filter_by(product_id=product_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )


@router.post("/product/{product_id}", response_model=schemas.ReviewOut, status_code=201)
def review(
    product_id: int,
    data: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    product = db.get(models.Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_review = (
        db.query(models.Review)
        .filter_by(user_id=user.id, product_id=product_id)
        .first()
    )

    if existing_review:
        raise HTTPException(status_code=409, detail="You already reviewed this product")

    review = models.Review(user_id=user.id, product_id=product_id, **data.model_dump())

    db.add(review)
    db.commit()
    db.refresh(review)

    return review
