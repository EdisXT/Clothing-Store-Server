from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now_utc(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    username: Mapped[str]=mapped_column(String(80), unique=True, index=True)
    hashed_password: Mapped[str]=mapped_column(String(255))
    first_name: Mapped[str|None]=mapped_column(String(80), nullable=True)
    last_name: Mapped[str|None]=mapped_column(String(80), nullable=True)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    is_admin: Mapped[bool]=mapped_column(Boolean, default=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc)
    addresses=relationship("Address", back_populates="user", cascade="all, delete-orphan")
    orders=relationship("Order", back_populates="user")

class Category(Base):
    __tablename__="categories"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(100), unique=True)
    slug: Mapped[str]=mapped_column(String(120), unique=True, index=True)
    products=relationship("Product", back_populates="category")

class Collection(Base):
    __tablename__="collections"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(120), unique=True)
    slug: Mapped[str]=mapped_column(String(140), unique=True, index=True)
    description: Mapped[str|None]=mapped_column(Text, nullable=True)
    is_featured: Mapped[bool]=mapped_column(Boolean, default=False)

class Product(Base):
    __tablename__="products"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(180), index=True)
    slug: Mapped[str]=mapped_column(String(200), unique=True, index=True)
    description: Mapped[str]=mapped_column(Text, default="")
    base_price: Mapped[Decimal]=mapped_column(Numeric(10,2))
    compare_at_price: Mapped[Decimal|None]=mapped_column(Numeric(10,2), nullable=True)
    gender: Mapped[str|None]=mapped_column(String(30), nullable=True, index=True)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True, index=True)
    is_featured: Mapped[bool]=mapped_column(Boolean, default=False, index=True)
    category_id: Mapped[int|None]=mapped_column(ForeignKey("categories.id"), nullable=True)
    collection_id: Mapped[int|None]=mapped_column(ForeignKey("collections.id"), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc)
    category=relationship("Category", back_populates="products")
    collection=relationship("Collection")
    variants=relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    images=relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.position")
    reviews=relationship("Review", back_populates="product", cascade="all, delete-orphan")

class ProductImage(Base):
    __tablename__="product_images"
    id: Mapped[int]=mapped_column(primary_key=True)
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    url: Mapped[str]=mapped_column(String(1000))
    alt_text: Mapped[str|None]=mapped_column(String(255), nullable=True)
    position: Mapped[int]=mapped_column(Integer, default=0)
    product=relationship("Product", back_populates="images")

class ProductVariant(Base):
    __tablename__="product_variants"
    id: Mapped[int]=mapped_column(primary_key=True)
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str]=mapped_column(String(100), unique=True, index=True)
    size: Mapped[str|None]=mapped_column(String(30), nullable=True, index=True)
    color: Mapped[str|None]=mapped_column(String(60), nullable=True, index=True)
    price: Mapped[Decimal|None]=mapped_column(Numeric(10,2), nullable=True)
    stock_quantity: Mapped[int]=mapped_column(Integer, default=0)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)
    product=relationship("Product", back_populates="variants")

class Address(Base):
    __tablename__="addresses"
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    label: Mapped[str]=mapped_column(String(50), default="Home")
    full_name: Mapped[str]=mapped_column(String(160))
    line1: Mapped[str]=mapped_column(String(255))
    line2: Mapped[str|None]=mapped_column(String(255), nullable=True)
    city: Mapped[str]=mapped_column(String(100))
    state: Mapped[str]=mapped_column(String(100))
    postal_code: Mapped[str]=mapped_column(String(30))
    country: Mapped[str]=mapped_column(String(80), default="US")
    phone: Mapped[str|None]=mapped_column(String(40), nullable=True)
    is_default: Mapped[bool]=mapped_column(Boolean, default=False)
    user=relationship("User", back_populates="addresses")

class CartItem(Base):
    __tablename__="cart_items"
    __table_args__=(UniqueConstraint("user_id","variant_id",name="uq_cart_user_variant"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[int]=mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
    quantity: Mapped[int]=mapped_column(Integer, default=1)
    variant=relationship("ProductVariant")

class WishlistItem(Base):
    __tablename__="wishlist_items"
    __table_args__=(UniqueConstraint("user_id","product_id",name="uq_wishlist_user_product"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    product=relationship("Product")

class Coupon(Base):
    __tablename__="coupons"
    id: Mapped[int]=mapped_column(primary_key=True)
    code: Mapped[str]=mapped_column(String(50), unique=True, index=True)
    percent_off: Mapped[int|None]=mapped_column(Integer, nullable=True)
    amount_off: Mapped[Decimal|None]=mapped_column(Numeric(10,2), nullable=True)
    minimum_subtotal: Mapped[Decimal]=mapped_column(Numeric(10,2), default=0)
    is_active: Mapped[bool]=mapped_column(Boolean, default=True)

class Order(Base):
    __tablename__="orders"
    id: Mapped[int]=mapped_column(primary_key=True)
    order_number: Mapped[str]=mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str]=mapped_column(String(30), default="pending", index=True)
    payment_status: Mapped[str]=mapped_column(String(30), default="unpaid")
    subtotal: Mapped[Decimal]=mapped_column(Numeric(10,2))
    discount: Mapped[Decimal]=mapped_column(Numeric(10,2), default=0)
    shipping: Mapped[Decimal]=mapped_column(Numeric(10,2), default=0)
    tax: Mapped[Decimal]=mapped_column(Numeric(10,2), default=0)
    total: Mapped[Decimal]=mapped_column(Numeric(10,2))
    shipping_name: Mapped[str]=mapped_column(String(160))
    shipping_line1: Mapped[str]=mapped_column(String(255))
    shipping_line2: Mapped[str|None]=mapped_column(String(255), nullable=True)
    shipping_city: Mapped[str]=mapped_column(String(100))
    shipping_state: Mapped[str]=mapped_column(String(100))
    shipping_postal_code: Mapped[str]=mapped_column(String(30))
    shipping_country: Mapped[str]=mapped_column(String(80))
    tracking_number: Mapped[str|None]=mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc)
    user=relationship("User", back_populates="orders")
    items=relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__="order_items"
    id: Mapped[int]=mapped_column(primary_key=True)
    order_id: Mapped[int]=mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    variant_id: Mapped[int|None]=mapped_column(ForeignKey("product_variants.id"), nullable=True)
    product_name: Mapped[str]=mapped_column(String(180))
    sku: Mapped[str]=mapped_column(String(100))
    size: Mapped[str|None]=mapped_column(String(30), nullable=True)
    color: Mapped[str|None]=mapped_column(String(60), nullable=True)
    unit_price: Mapped[Decimal]=mapped_column(Numeric(10,2))
    quantity: Mapped[int]=mapped_column(Integer)
    order=relationship("Order", back_populates="items")

class Review(Base):
    __tablename__="reviews"
    __table_args__=(UniqueConstraint("user_id","product_id",name="uq_review_user_product"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int]=mapped_column(Integer)
    title: Mapped[str|None]=mapped_column(String(150), nullable=True)
    body: Mapped[str|None]=mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc)
    product=relationship("Product", back_populates="reviews")
