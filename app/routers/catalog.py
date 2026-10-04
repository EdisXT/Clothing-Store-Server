from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_
from ..database import get_db
from .. import models, schemas
from ..dependencies import require_admin
router=APIRouter(prefix="/catalog",tags=["Catalog"])

def product_query(db): return db.query(models.Product).options(selectinload(models.Product.variants),selectinload(models.Product.images),selectinload(models.Product.category),selectinload(models.Product.collection))

@router.get("/products",response_model=list[schemas.ProductOut])
def products(q:str|None=None,category:str|None=None,collection:str|None=None,gender:str|None=None,size:str|None=None,color:str|None=None,min_price:float|None=None,max_price:float|None=None,featured:bool|None=None,sort:str="newest",limit:int=Query(24,ge=1,le=100),offset:int=Query(0,ge=0),db:Session=Depends(get_db)):
    query=product_query(db).filter(models.Product.is_active.is_(True))
    if q: query=query.filter(or_(models.Product.name.ilike(f"%{q}%"),models.Product.description.ilike(f"%{q}%")))
    if category: query=query.join(models.Category).filter(models.Category.slug==category)
    if collection: query=query.join(models.Collection).filter(models.Collection.slug==collection)
    if gender: query=query.filter(models.Product.gender==gender)
    if min_price is not None: query=query.filter(models.Product.base_price>=min_price)
    if max_price is not None: query=query.filter(models.Product.base_price<=max_price)
    if featured is not None: query=query.filter(models.Product.is_featured==featured)
    if size or color:
        query=query.join(models.ProductVariant)
        if size: query=query.filter(models.ProductVariant.size==size)
        if color: query=query.filter(models.ProductVariant.color==color)
    if sort=="price_asc": query=query.order_by(models.Product.base_price.asc())
    elif sort=="price_desc": query=query.order_by(models.Product.base_price.desc())
    elif sort=="name": query=query.order_by(models.Product.name.asc())
    else: query=query.order_by(models.Product.created_at.desc())
    return query.distinct().offset(offset).limit(limit).all()

@router.get("/products/{slug}",response_model=schemas.ProductOut)
def product(slug:str,db:Session=Depends(get_db)):
    p=product_query(db).filter(models.Product.slug==slug,models.Product.is_active.is_(True)).first()
    if not p: raise HTTPException(404,"Product not found")
    return p

@router.get("/categories",response_model=list[schemas.CategoryOut])
def categories(db:Session=Depends(get_db)): return db.query(models.Category).order_by(models.Category.name).all()
@router.get("/collections",response_model=list[schemas.CollectionOut])
def collections(db:Session=Depends(get_db)): return db.query(models.Collection).order_by(models.Collection.name).all()

@router.post("/categories",response_model=schemas.CategoryOut,status_code=201,dependencies=[Depends(require_admin)])
def create_category(data:schemas.CategoryCreate,db:Session=Depends(get_db)):
    obj=models.Category(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.post("/collections",response_model=schemas.CollectionOut,status_code=201,dependencies=[Depends(require_admin)])
def create_collection(data:schemas.CollectionCreate,db:Session=Depends(get_db)):
    obj=models.Collection(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.post("/products",response_model=schemas.ProductOut,status_code=201,dependencies=[Depends(require_admin)])
def create_product(data:schemas.ProductCreate,db:Session=Depends(get_db)):
    payload=data.model_dump(exclude={"variants","images"}); p=models.Product(**payload); db.add(p); db.flush()
    for v in data.variants: db.add(models.ProductVariant(product_id=p.id,**v.model_dump()))
    for i in data.images: db.add(models.ProductImage(product_id=p.id,**i.model_dump()))
    db.commit(); return product_query(db).filter(models.Product.id==p.id).first()
@router.patch("/products/{product_id}",response_model=schemas.ProductOut,dependencies=[Depends(require_admin)])
def update_product(product_id:int,data:schemas.ProductUpdate,db:Session=Depends(get_db)):
    p=db.get(models.Product,product_id)
    if not p: raise HTTPException(404,"Product not found")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v)
    db.commit(); return product_query(db).filter(models.Product.id==p.id).first()
