from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session,selectinload
from ..database import get_db
from .. import models,schemas
from ..dependencies import require_admin
router=APIRouter(prefix="/admin",tags=["Admin"],dependencies=[Depends(require_admin)])
@router.get("/orders",response_model=list[schemas.OrderOut])
def orders(db:Session=Depends(get_db)): return db.query(models.Order).options(selectinload(models.Order.items)).order_by(models.Order.created_at.desc()).all()
@router.patch("/orders/{order_id}",response_model=schemas.OrderOut)
def order_status(order_id:int,data:schemas.OrderStatusUpdate,db:Session=Depends(get_db)):
    o=db.get(models.Order,order_id)
    if not o: raise HTTPException(404,"Order not found")
    o.status=data.status
    if data.payment_status is not None:o.payment_status=data.payment_status
    if data.tracking_number is not None:o.tracking_number=data.tracking_number
    db.commit(); return db.query(models.Order).options(selectinload(models.Order.items)).filter_by(id=o.id).first()
@router.patch("/inventory/{variant_id}",response_model=schemas.VariantOut)
def inventory(variant_id:int,data:schemas.InventoryUpdate,db:Session=Depends(get_db)):
    v=db.get(models.ProductVariant,variant_id)
    if not v: raise HTTPException(404,"Variant not found")
    v.stock_quantity=data.stock_quantity; db.commit(); db.refresh(v); return v
@router.post("/coupons",response_model=schemas.CouponOut,status_code=201)
def coupon(data:schemas.CouponCreate,db:Session=Depends(get_db)):
    if bool(data.percent_off)==bool(data.amount_off): raise HTTPException(400,"Provide exactly one discount type")
    obj=models.Coupon(**data.model_dump()); obj.code=obj.code.upper(); db.add(obj); db.commit(); db.refresh(obj); return obj
