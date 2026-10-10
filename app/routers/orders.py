from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db
from ..oauth2 import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


def order_query(db: Session):
    return db.query(models.Order).options(selectinload(models.Order.items))


@router.post("/checkout", response_model=schemas.OrderOut, status_code=201)
def checkout(
    data: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        address = (
            db.query(models.Address)
            .filter_by(id=data.address_id, user_id=user.id)
            .first()
        )

        if not address:
            raise HTTPException(
                status_code=404,
                detail="Shipping address not found",
            )

        cart = (
            db.query(models.CartItem)
            .options(
                selectinload(models.CartItem.variant).selectinload(
                    models.ProductVariant.product
                )
            )
            .filter_by(user_id=user.id)
            .order_by(models.CartItem.variant_id)
            .all()
        )

        if not cart:
            raise HTTPException(
                status_code=400,
                detail="Cart is empty",
            )

        subtotal = Decimal("0.00")
        checkout_items = []

        for item in cart:
            variant = (
                db.query(models.ProductVariant)
                .filter(models.ProductVariant.id == item.variant_id)
                .with_for_update()
                .first()
            )

            if not variant:
                raise HTTPException(
                    status_code=404,
                    detail="Product variant not found",
                )

            if not variant.is_active or not variant.product.is_active:
                raise HTTPException(
                    status_code=409,
                    detail=f"Product variant {variant.sku} is no longer available",
                )

            if item.quantity < 1:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid cart quantity",
                )

            if item.quantity > variant.stock_quantity:
                raise HTTPException(
                    status_code=409,
                    detail=f"Insufficient stock for {variant.sku}",
                )

            price = (
                variant.price
                if variant.price is not None
                else variant.product.base_price
            )

            subtotal += price * item.quantity

            checkout_items.append(
                {
                    "cart_item": item,
                    "variant": variant,
                    "price": price,
                }
            )

        discount = Decimal("0.00")

        if data.coupon_code:
            coupon = (
                db.query(models.Coupon)
                .filter(
                    models.Coupon.code == data.coupon_code.upper(),
                    models.Coupon.is_active.is_(True),
                )
                .first()
            )

            if not coupon:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid coupon",
                )

            if subtotal < coupon.minimum_subtotal:
                raise HTTPException(
                    status_code=400,
                    detail="Coupon minimum not reached",
                )

            if coupon.percent_off:
                discount = subtotal * Decimal(coupon.percent_off) / Decimal("100")
            else:
                discount = coupon.amount_off or Decimal("0.00")

            discount = min(discount, subtotal)

        shipping = (
            Decimal("0.00") if subtotal >= Decimal("100.00") else Decimal("10.00")
        )

        tax = Decimal("0.00")
        total = subtotal - discount + shipping + tax

        order = models.Order(
            order_number=f"VX-{uuid4().hex[:10].upper()}",
            user_id=user.id,
            subtotal=subtotal,
            discount=discount,
            shipping=shipping,
            tax=tax,
            total=total,
            shipping_name=address.full_name,
            shipping_line1=address.line1,
            shipping_line2=address.line2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
        )

        db.add(order)
        db.flush()

        for checkout_item in checkout_items:
            item = checkout_item["cart_item"]
            variant = checkout_item["variant"]
            price = checkout_item["price"]

            variant.stock_quantity -= item.quantity

            order_item = models.OrderItem(
                order_id=order.id,
                variant_id=variant.id,
                product_name=variant.product.name,
                sku=variant.sku,
                size=variant.size,
                color=variant.color,
                unit_price=price,
                quantity=item.quantity,
            )

            db.add(order_item)
            db.delete(item)

        db.commit()

        return order_query(db).filter(models.Order.id == order.id).first()

    except Exception:
        db.rollback()
        raise


@router.get("", response_model=list[schemas.OrderOut])
def history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return (
        order_query(db)
        .filter(models.Order.user_id == user.id)
        .order_by(models.Order.created_at.desc())
        .all()
    )


@router.get("/{order_id}", response_model=schemas.OrderOut)
def detail(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    order = (
        order_query(db)
        .filter(
            models.Order.id == order_id,
            models.Order.user_id == user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order
