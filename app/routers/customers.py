from fastapi import APIRouter,Depends,HTTPException,Response,status
from sqlalchemy.orm import Session,selectinload
from ..database import get_db
from .. import models,schemas
from ..dependencies import get_current_user
router=APIRouter(tags=["Customer"])
@router.get("/addresses",response_model=list[schemas.AddressOut])
def addresses(db:Session=Depends(get_db),user=Depends(get_current_user)): return db.query(models.Address).filter_by(user_id=user.id).all()
@router.post("/addresses",response_model=schemas.AddressOut,status_code=201)
def add_address(data:schemas.AddressCreate,db:Session=Depends(get_db),user=Depends(get_current_user)):
    if data.is_default: db.query(models.Address).filter_by(user_id=user.id).update({"is_default":False})
    obj=models.Address(user_id=user.id,**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.get("/wishlist",response_model=list[schemas.WishlistOut])
def wishlist(db:Session=Depends(get_db),user=Depends(get_current_user)): return db.query(models.WishlistItem).options(selectinload(models.WishlistItem.product).selectinload(models.Product.variants),selectinload(models.WishlistItem.product).selectinload(models.Product.images),selectinload(models.WishlistItem.product).selectinload(models.Product.category),selectinload(models.WishlistItem.product).selectinload(models.Product.collection)).filter_by(user_id=user.id).all()
@router.post("/wishlist/{product_id}",status_code=201)
def add_wishlist(product_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    if not db.get(models.Product,product_id): raise HTTPException(404,"Product not found")
    if db.query(models.WishlistItem).filter_by(user_id=user.id,product_id=product_id).first(): return {"message":"Already saved"}
    db.add(models.WishlistItem(user_id=user.id,product_id=product_id)); db.commit(); return {"message":"Saved"}
@router.delete("/wishlist/{product_id}",status_code=204)
def remove_wishlist(product_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    obj=db.query(models.WishlistItem).filter_by(user_id=user.id,product_id=product_id).first()
    if obj: db.delete(obj); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
