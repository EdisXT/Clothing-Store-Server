from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db
from ..oauth2 import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_items(db: Session, user_id: int):
    return (
        db.query(models.CartItem)
        .options(
            selectinload(models.CartItem.variant)
            .selectinload(models.ProductVariant.product)
            .selectinload(models.Product.images)
        )
        .filter(models.CartItem.user_id == user_id)
        .all()
    )


@router.get("", response_model=list[schemas.CartItemOut])
def get_cart(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_cart_items(db, user.id)


@router.post("", response_model=schemas.CartItemOut, status_code=201)
def add(
    data: schemas.CartAdd,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    variant = db.get(models.ProductVariant, data.variant_id)

    if not variant or not variant.is_active or not variant.product.is_active:
        raise HTTPException(
            status_code=404,
            detail="Product variant is unavailable",
        )

    existing_item = (
        db.query(models.CartItem)
        .filter_by(user_id=user.id, variant_id=variant.id)
        .first()
    )

    new_quantity = data.quantity + (existing_item.quantity if existing_item else 0)

    if new_quantity > variant.stock_quantity:
        raise HTTPException(
            status_code=409,
            detail="Not enough inventory",
        )

    if existing_item:
        existing_item.quantity = new_quantity
        cart_item = existing_item
    else:
        cart_item = models.CartItem(
            user_id=user.id,
            variant_id=variant.id,
            quantity=data.quantity,
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.patch("/{item_id}", response_model=schemas.CartItemOut)
def update(
    item_id: int,
    data: schemas.CartUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cart_item = db.query(models.CartItem).filter_by(id=item_id, user_id=user.id).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    variant = db.get(models.ProductVariant, cart_item.variant_id)

    if not variant or not variant.is_active or not variant.product.is_active:
        raise HTTPException(
            status_code=409,
            detail="Product variant is no longer available",
        )

    if data.quantity > variant.stock_quantity:
        raise HTTPException(
            status_code=409,
            detail="Not enough inventory",
        )

    cart_item.quantity = data.quantity

    db.commit()
    db.refresh(cart_item)

    return cart_item


@router.delete("/{item_id}", status_code=204)
def delete(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    cart_item = db.query(models.CartItem).filter_by(id=item_id, user_id=user.id).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    db.delete(cart_item)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
