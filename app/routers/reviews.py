from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models,schemas
from ..dependencies import get_current_user
router=APIRouter(prefix="/reviews",tags=["Reviews"])
@router.get("/product/{product_id}",response_model=list[schemas.ReviewOut])
def list_reviews(product_id:int,db:Session=Depends(get_db)): return db.query(models.Review).filter_by(product_id=product_id).order_by(models.Review.created_at.desc()).all()
@router.post("/product/{product_id}",response_model=schemas.ReviewOut,status_code=201)
def review(product_id:int,data:schemas.ReviewCreate,db:Session=Depends(get_db),user=Depends(get_current_user)):
    if not db.get(models.Product,product_id): raise HTTPException(404,"Product not found")
    if db.query(models.Review).filter_by(user_id=user.id,product_id=product_id).first(): raise HTTPException(409,"You already reviewed this product")
    obj=models.Review(user_id=user.id,product_id=product_id,**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
