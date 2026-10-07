from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db
from ..oauth2 import require_admin

router = APIRouter(
    prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)]
)


@router.get("/orders", response_model=list[schemas.OrderOut])
def orders(db: Session = Depends(get_db)):
    return (
        db.query(models.Order)
        .options(selectinload(models.Order.items))
        .order_by(models.Order.created_at.desc())
        .all()
    )


@router.patch("/orders/{order_id}", response_model=schemas.OrderOut)
def order_status(
    order_id: int, data: schemas.OrderStatusUpdate, db: Session = Depends(get_db)
):
    order = db.get(models.Order, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = data.status

    if data.payment_status is not None:
        order.payment_status = data.payment_status

    if data.tracking_number is not None:
        order.tracking_number = data.tracking_number

    db.commit()

    return (
        db.query(models.Order)
        .options(selectinload(models.Order.items))
        .filter_by(id=order.id)
        .first()
    )


@router.patch("/inventory/{variant_id}", response_model=schemas.VariantOut)
def inventory(
    variant_id: int, data: schemas.InventoryUpdate, db: Session = Depends(get_db)
):
    variant = db.get(models.ProductVariant, variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    variant.stock_quantity = data.stock_quantity

    db.commit()
    db.refresh(variant)

    return variant


@router.post("/coupons", response_model=schemas.CouponOut, status_code=201)
def coupon(data: schemas.CouponCreate, db: Session = Depends(get_db)):
    if bool(data.percent_off) == bool(data.amount_off):
        raise HTTPException(status_code=400, detail="Provide exactly one discount type")

    coupon = models.Coupon(**data.model_dump())
    coupon.code = coupon.code.upper()

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return coupon
