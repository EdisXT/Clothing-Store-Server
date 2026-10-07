from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import (
    admin,
    auth,
    cart,
    catalog,
    customers,
    orders,
    reviews,
)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Clothing commerce API: catalog, variants, inventory, "
        "cart, wishlist, orders, reviews and admin."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

routers = (
    auth.router,
    catalog.router,
    cart.router,
    customers.router,
    orders.router,
    reviews.router,
    admin.router,
)

for router in routers:
    app.include_router(router)


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
    }
