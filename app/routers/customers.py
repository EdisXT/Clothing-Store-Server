from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db
from ..oauth2 import get_current_user

router = APIRouter(tags=["Customer"])


@router.get("/addresses", response_model=list[schemas.AddressOut])
def addresses(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Address).filter_by(user_id=user.id).all()


@router.post("/addresses", response_model=schemas.AddressOut, status_code=201)
def add_address(
    data: schemas.AddressCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if data.is_default:
        (
            db.query(models.Address)
            .filter_by(user_id=user.id)
            .update({"is_default": False})
        )

    address = models.Address(user_id=user.id, **data.model_dump())

    db.add(address)
    db.commit()
    db.refresh(address)

    return address


@router.get("/wishlist", response_model=list[schemas.WishlistOut])
def wishlist(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return (
        db.query(models.WishlistItem)
        .options(
            selectinload(models.WishlistItem.product).selectinload(
                models.Product.variants
            ),
            selectinload(models.WishlistItem.product).selectinload(
                models.Product.images
            ),
            selectinload(models.WishlistItem.product).selectinload(
                models.Product.category
            ),
            selectinload(models.WishlistItem.product).selectinload(
                models.Product.collection
            ),
        )
        .filter_by(user_id=user.id)
        .all()
    )


@router.post("/wishlist/{product_id}", status_code=201)
def add_wishlist(
    product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    product = db.get(models.Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_item = (
        db.query(models.WishlistItem)
        .filter_by(user_id=user.id, product_id=product_id)
        .first()
    )

    if existing_item:
        return {"message": "Already saved"}

    wishlist_item = models.WishlistItem(user_id=user.id, product_id=product_id)

    db.add(wishlist_item)
    db.commit()

    return {"message": "Saved"}


@router.delete("/wishlist/{product_id}", status_code=204)
def remove_wishlist(
    product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    wishlist_item = (
        db.query(models.WishlistItem)
        .filter_by(user_id=user.id, product_id=product_id)
        .first()
    )

    if wishlist_item:
        db.delete(wishlist_item)
        db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
