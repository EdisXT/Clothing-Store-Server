from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import Base, engine
from .routers import auth,catalog,cart,customers,orders,reviews,admin
Base.metadata.create_all(bind=engine)
app=FastAPI(title=settings.app_name,version="1.0.0",description="Clothing commerce API: catalog, variants, inventory, cart, wishlist, orders, reviews and admin.")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
for r in (auth.router,catalog.router,cart.router,customers.router,orders.router,reviews.router,admin.router): app.include_router(r)
@app.get("/health",tags=["System"])
def health(): return {"status":"ok","service":settings.app_name}
