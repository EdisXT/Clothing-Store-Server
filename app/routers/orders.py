from decimal import Decimal
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session,selectinload
from ..database import get_db
from .. import models,schemas
from ..dependencies import get_current_user
router=APIRouter(prefix="/orders",tags=["Orders"])

def oq(db): return db.query(models.Order).options(selectinload(models.Order.items))
@router.post("/checkout",response_model=schemas.OrderOut,status_code=201)
def checkout(data:schemas.CheckoutRequest,db:Session=Depends(get_db),user=Depends(get_current_user)):
    address=db.query(models.Address).filter_by(id=data.address_id,user_id=user.id).first()
    if not address: raise HTTPException(404,"Shipping address not found")
    cart=db.query(models.CartItem).options(selectinload(models.CartItem.variant).selectinload(models.ProductVariant.product)).filter_by(user_id=user.id).all()
    if not cart: raise HTTPException(400,"Cart is empty")
    subtotal=Decimal("0.00")
    for item in cart:
        if item.quantity>item.variant.stock_quantity: raise HTTPException(409,f"Insufficient stock for {item.variant.sku}")
        price=item.variant.price if item.variant.price is not None else item.variant.product.base_price; subtotal += price*item.quantity
    discount=Decimal("0.00")
    if data.coupon_code:
        c=db.query(models.Coupon).filter(models.Coupon.code==data.coupon_code.upper(),models.Coupon.is_active.is_(True)).first()
        if not c: raise HTTPException(400,"Invalid coupon")
        if subtotal<c.minimum_subtotal: raise HTTPException(400,"Coupon minimum not reached")
        discount=(subtotal*Decimal(c.percent_off)/Decimal(100)) if c.percent_off else (c.amount_off or Decimal("0")); discount=min(discount,subtotal)
    shipping=Decimal("0.00") if subtotal>=Decimal("100") else Decimal("10.00")
    tax=Decimal("0.00")  # integrate a tax service before production
    total=subtotal-discount+shipping+tax
    order=models.Order(order_number=f"VX-{uuid4().hex[:10].upper()}",user_id=user.id,subtotal=subtotal,discount=discount,shipping=shipping,tax=tax,total=total,shipping_name=address.full_name,shipping_line1=address.line1,shipping_line2=address.line2,shipping_city=address.city,shipping_state=address.state,shipping_postal_code=address.postal_code,shipping_country=address.country)
    db.add(order); db.flush()
    for item in cart:
        v=item.variant; price=v.price if v.price is not None else v.product.base_price; v.stock_quantity-=item.quantity
        db.add(models.OrderItem(order_id=order.id,variant_id=v.id,product_name=v.product.name,sku=v.sku,size=v.size,color=v.color,unit_price=price,quantity=item.quantity)); db.delete(item)
    db.commit(); return oq(db).filter(models.Order.id==order.id).first()
@router.get("",response_model=list[schemas.OrderOut])
def history(db:Session=Depends(get_db),user=Depends(get_current_user)): return oq(db).filter(models.Order.user_id==user.id).order_by(models.Order.created_at.desc()).all()
@router.get("/{order_id}",response_model=schemas.OrderOut)
def detail(order_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    o=oq(db).filter(models.Order.id==order_id,models.Order.user_id==user.id).first()
    if not o: raise HTTPException(404,"Order not found")
    return o
