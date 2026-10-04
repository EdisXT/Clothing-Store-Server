# Clothing Store Backend

A FastAPI e-commerce backend rebuilt from the supplied starter project. It preserves the useful ideas from the original (FastAPI, SQLAlchemy, password hashing, OAuth2/JWT) and replaces the blog domain with a clothing-commerce domain.

## Included
- Customer registration/login and JWT auth
- Admin role authorization
- Categories, collections, products, product images and size/color/SKU variants
- Inventory tracking
- Product search/filter/sort/pagination
- Wishlist
- Persistent shopping cart
- Addresses
- Checkout/order creation with inventory reservation
- Order history and order detail
- Admin order status updates and inventory adjustment
- Coupon model and validation endpoint
- Review model and product review endpoints
- CORS and health endpoint
- SQLite by default; PostgreSQL through `DATABASE_URL`

## Run
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Open `/docs` for Swagger UI.

## First admin
Register normally, then for local development promote a user in the database by setting `is_admin = true`. In production, do not expose a public admin-registration endpoint.

## Production notes
This project intentionally does not store card numbers. Add Stripe/another payment provider at checkout and verify payment webhooks before marking orders paid. Replace `create_all()` with Alembic migrations before production. Add Redis/rate limiting, object storage/CDN for images, email service, tax/shipping integrations, observability and background jobs as the store grows.
