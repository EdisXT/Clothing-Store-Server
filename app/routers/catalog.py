from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db
from ..oauth2 import require_admin

router = APIRouter(prefix="/catalog", tags=["Catalog"])


def product_query(db: Session):
    return db.query(models.Product).options(
        selectinload(models.Product.variants),
        selectinload(models.Product.images),
        selectinload(models.Product.category),
        selectinload(models.Product.collection),
    )


@router.get("/products", response_model=list[schemas.ProductOut])
def products(
    q: str | None = None,
    category: str | None = None,
    collection: str | None = None,
    gender: str | None = None,
    size: str | None = None,
    color: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    featured: bool | None = None,
    sort: str = "newest",
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = product_query(db).filter(models.Product.is_active.is_(True))

    if q:
        query = query.filter(
            or_(
                models.Product.name.ilike(f"%{q}%"),
                models.Product.description.ilike(f"%{q}%"),
            )
        )

    if category:
        query = query.join(models.Category).filter(models.Category.slug == category)

    if collection:
        query = query.join(models.Collection).filter(
            models.Collection.slug == collection
        )

    if gender:
        query = query.filter(models.Product.gender == gender)

    if min_price is not None:
        query = query.filter(models.Product.base_price >= min_price)

    if max_price is not None:
        query = query.filter(models.Product.base_price <= max_price)

    if featured is not None:
        query = query.filter(models.Product.is_featured == featured)

    if size or color:
        query = query.join(models.ProductVariant)

        if size:
            query = query.filter(models.ProductVariant.size == size)

        if color:
            query = query.filter(models.ProductVariant.color == color)

    if sort == "price_asc":
        query = query.order_by(models.Product.base_price.asc())
    elif sort == "price_desc":
        query = query.order_by(models.Product.base_price.desc())
    elif sort == "name":
        query = query.order_by(models.Product.name.asc())
    else:
        query = query.order_by(models.Product.created_at.desc())

    return query.distinct().offset(offset).limit(limit).all()

@router.get(
    "/admin/products",
    response_model=list[schemas.ProductOut],
    dependencies=[Depends(require_admin)],
)
def admin_products(db: Session = Depends(get_db)):
    return (
        product_query(db)
        .order_by(models.Product.created_at.desc())
        .all()
    )

@router.get("/products/{slug}", response_model=schemas.ProductOut)
def product(slug: str, db: Session = Depends(get_db)):
    product = (
        product_query(db)
        .filter(models.Product.slug == slug, models.Product.is_active.is_(True))
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.get("/categories", response_model=list[schemas.CategoryOut])
def categories(db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.name).all()


@router.get("/collections", response_model=list[schemas.CollectionOut])
def collections(db: Session = Depends(get_db)):
    return db.query(models.Collection).order_by(models.Collection.name).all()


@router.post(
    "/categories",
    response_model=schemas.CategoryOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_category(data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    category = models.Category(**data.model_dump())

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.post(
    "/collections",
    response_model=schemas.CollectionOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_collection(data: schemas.CollectionCreate, db: Session = Depends(get_db)):
    collection = models.Collection(**data.model_dump())

    db.add(collection)
    db.commit()
    db.refresh(collection)

    return collection


@router.post(
    "/products",
    response_model=schemas.ProductOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_product(data: schemas.ProductCreate, db: Session = Depends(get_db)):
    payload = data.model_dump(exclude={"variants", "images"})

    product = models.Product(**payload)

    db.add(product)
    db.flush()

    for variant in data.variants:
        db.add(models.ProductVariant(product_id=product.id, **variant.model_dump()))

    for image in data.images:
        db.add(models.ProductImage(product_id=product.id, **image.model_dump()))

    db.commit()

    return product_query(db).filter(models.Product.id == product.id).first()


@router.patch(
    "/products/{product_id}",
    response_model=schemas.ProductOut,
    dependencies=[Depends(require_admin)],
)
def update_product(
    product_id: int, data: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    product = db.get(models.Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()

    return product_query(db).filter(models.Product.id == product.id).first()

@router.post(
    "/products/{product_id}/variants",
    response_model=schemas.VariantOut,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_product_variant(
    product_id: int,
    data: schemas.VariantCreate,
    db: Session = Depends(get_db),
):
    product = db.get(models.Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_variant = (
        db.query(models.ProductVariant)
        .filter(models.ProductVariant.sku == data.sku)
        .first()
    )

    if existing_variant:
        raise HTTPException(status_code=409, detail="SKU already exists")

    variant = models.ProductVariant(
        product_id=product_id,
        **data.model_dump(),
    )

    db.add(variant)
    db.commit()
    db.refresh(variant)

    return variant

@router.patch(
    "/variants/{variant_id}",
    response_model=schemas.VariantOut,
    dependencies=[Depends(require_admin)],
)
def update_variant(
    variant_id: int,
    data: schemas.VariantUpdate,
    db: Session = Depends(get_db),
):
    variant = db.get(models.ProductVariant, variant_id)

    if not variant:
        raise HTTPException(
            status_code=404,
            detail="Product variant not found",
        )

    variant.is_active = data.is_active

    db.commit()
    db.refresh(variant)

    return variant