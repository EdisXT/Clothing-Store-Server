# Backend architecture

The uploaded starter was a small blog API with `User` and `Blog`, SQLite, bcrypt hashing and JWT authentication. This rebuild keeps those core learning concepts but reorganizes them into a commerce API.

## Main domains
- **Identity:** users, JWT, customer/admin authorization
- **Catalog:** categories, collections, products, images, variants
- **Merchandising:** featured products, gender/category/collection filters, search and sorting
- **Inventory:** stock per SKU/size/color variant
- **Customer:** addresses, wishlist, cart
- **Commerce:** coupons, checkout, immutable order-line snapshots, order status
- **Community:** product reviews
- **Operations:** admin order and inventory endpoints

## Important next production upgrades
1. Alembic migrations instead of `create_all`.
2. PostgreSQL in production.
3. Stripe/payment-provider checkout + signed webhook handling.
4. Tax calculation provider and shipping/rate provider.
5. S3/Cloudinary-style object storage for product media.
6. Email verification, password reset and transactional order email.
7. Refresh tokens/session revocation, rate limiting and brute-force protection.
8. Redis/background workers for email, stock events and webhooks.
9. Structured logs, error monitoring and metrics.
10. A fuller test suite before accepting real orders.
