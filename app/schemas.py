from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)

    first_name: str | None = None
    last_name: str | None = None


class UserOut(ORM):
    id: int
    email: EmailStr
    username: str

    first_name: str | None
    last_name: str | None

    is_admin: bool
    created_at: datetime


class CategoryCreate(BaseModel):
    name: str
    slug: str


class CategoryOut(ORM):
    id: int
    name: str
    slug: str


# =========================================================


class CollectionCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    is_featured: bool = False


class CollectionOut(ORM):
    id: int
    name: str
    slug: str
    description: str | None
    is_featured: bool


class ImageCreate(BaseModel):
    url: str
    alt_text: str | None = None
    position: int = 0


class ImageOut(ORM):
    id: int
    url: str
    alt_text: str | None
    position: int


class VariantCreate(BaseModel):
    sku: str

    size: str | None = None
    color: str | None = None
    price: Decimal | None = None

    stock_quantity: int = Field(default=0, ge=0)

    is_active: bool = True


class VariantOut(ORM):
    id: int
    sku: str

    size: str | None
    color: str | None
    price: Decimal | None

    stock_quantity: int
    is_active: bool


class ProductCreate(BaseModel):
    name: str
    slug: str
    description: str = ""

    base_price: Decimal = Field(gt=0)
    compare_at_price: Decimal | None = None

    gender: str | None = None

    category_id: int | None = None
    collection_id: int | None = None

    is_active: bool = True
    is_featured: bool = False

    variants: list[VariantCreate] = []
    images: list[ImageCreate] = []


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    base_price: Decimal | None = Field(default=None, gt=0)

    compare_at_price: Decimal | None = None

    gender: str | None = None

    category_id: int | None = None
    collection_id: int | None = None

    is_active: bool | None = None
    is_featured: bool | None = None


class ProductOut(ORM):
    id: int
    name: str
    slug: str
    description: str

    base_price: Decimal
    compare_at_price: Decimal | None

    gender: str | None

    is_active: bool
    is_featured: bool

    category: CategoryOut | None
    collection: CollectionOut | None

    variants: list[VariantOut]
    images: list[ImageOut]

    created_at: datetime


class CartAdd(BaseModel):
    variant_id: int

    quantity: int = Field(default=1, ge=1, le=20)


class CartUpdate(BaseModel):
    quantity: int = Field(ge=1, le=20)


class CartItemOut(ORM):
    id: int
    quantity: int
    variant: VariantOut


class AddressCreate(BaseModel):
    label: str = "Home"

    full_name: str

    line1: str
    line2: str | None = None

    city: str
    state: str
    postal_code: str
    country: str = "US"

    phone: str | None = None

    is_default: bool = False


class AddressOut(AddressCreate, ORM):
    id: int


class WishlistOut(ORM):
    id: int
    product: ProductOut


class CheckoutRequest(BaseModel):
    address_id: int
    coupon_code: str | None = None


class OrderItemOut(ORM):
    id: int

    product_name: str
    sku: str

    size: str | None
    color: str | None

    unit_price: Decimal
    quantity: int


class OrderOut(ORM):
    id: int
    order_number: str

    status: str
    payment_status: str

    subtotal: Decimal
    discount: Decimal
    shipping: Decimal
    tax: Decimal
    total: Decimal

    tracking_number: str | None

    created_at: datetime

    items: list[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: str

    payment_status: str | None = None
    tracking_number: str | None = None


class InventoryUpdate(BaseModel):
    stock_quantity: int = Field(ge=0)


class CouponCreate(BaseModel):
    code: str

    percent_off: int | None = Field(default=None, ge=1, le=100)

    amount_off: Decimal | None = None
    minimum_subtotal: Decimal = Decimal("0")

    is_active: bool = True


class CouponOut(CouponCreate, ORM):
    id: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)

    title: str | None = None
    body: str | None = None


class ReviewOut(ReviewCreate, ORM):
    id: int
    user_id: int
    product_id: int

    created_at: datetime
