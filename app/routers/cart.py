from fastapi import APIRouter,Depends,HTTPException,Response,status
from sqlalchemy.orm import Session,selectinload
from ..database import get_db
from .. import models,schemas
from ..dependencies import get_current_user
router=APIRouter(prefix="/cart",tags=["Cart"])

def items(db,user_id): return db.query(models.CartItem).options(selectinload(models.CartItem.variant)).filter(models.CartItem.user_id==user_id).all()
@router.get("",response_model=list[schemas.CartItemOut])
def get_cart(db:Session=Depends(get_db),user=Depends(get_current_user)): return items(db,user.id)
@router.post("",response_model=schemas.CartItemOut,status_code=201)
def add(data:schemas.CartAdd,db:Session=Depends(get_db),user=Depends(get_current_user)):
    v=db.get(models.ProductVariant,data.variant_id)
    if not v or not v.is_active: raise HTTPException(404,"Variant not found")
    existing=db.query(models.CartItem).filter_by(user_id=user.id,variant_id=v.id).first(); new_qty=data.quantity+(existing.quantity if existing else 0)
    if new_qty>v.stock_quantity: raise HTTPException(409,"Not enough inventory")
    if existing: existing.quantity=new_qty; obj=existing
    else: obj=models.CartItem(user_id=user.id,variant_id=v.id,quantity=data.quantity); db.add(obj)
    db.commit(); db.refresh(obj); return obj
@router.patch("/{item_id}",response_model=schemas.CartItemOut)
def update(item_id:int,data:schemas.CartUpdate,db:Session=Depends(get_db),user=Depends(get_current_user)):
    obj=db.query(models.CartItem).filter_by(id=item_id,user_id=user.id).first()
    if not obj: raise HTTPException(404,"Cart item not found")
    v=db.get(models.ProductVariant,obj.variant_id)
    if data.quantity>v.stock_quantity: raise HTTPException(409,"Not enough inventory")
    obj.quantity=data.quantity; db.commit(); db.refresh(obj); return obj
@router.delete("/{item_id}",status_code=204)
def delete(item_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    obj=db.query(models.CartItem).filter_by(id=item_id,user_id=user.id).first()
    if not obj: raise HTTPException(404,"Cart item not found")
    db.delete(obj); db.commit(); return Response(status_code=status.HTTP_204_NO_CONTENT)
