from decimal import Decimal

from app import models
from tests.conftest import TestingSessionLocal

# =========================================================
# HELPERS
# =========================================================


def create_variant(stock_quantity=10):
    db = TestingSessionLocal()

    try:
        product = models.Product(
            name="Admin Test Product",
            slug="admin-test-product",
            description="Product used for admin testing",
            base_price=Decimal("50.00"),
            is_active=True,
            is_featured=False,
        )

        db.add(product)
        db.flush()

        variant = models.ProductVariant(
            product_id=product.id,
            sku="ADMIN-BLK-M",
            size="M",
            color="Black",
            price=Decimal("50.00"),
            stock_quantity=stock_quantity,
            is_active=True,
        )

        db.add(variant)
        db.commit()
        db.refresh(variant)

        return variant.id

    finally:
        db.close()


def create_order():
    db = TestingSessionLocal()

    try:
        user = models.User(
            email="order-owner@example.com",
            username="orderowner",
            hashed_password="not-used-in-this-test",
            first_name="Order",
            last_name="Owner",
        )

        db.add(user)
        db.flush()

        order = models.Order(
            order_number="VX-ADMINTEST",
            user_id=user.id,
            subtotal=Decimal("50.00"),
            discount=Decimal("0.00"),
            shipping=Decimal("10.00"),
            tax=Decimal("0.00"),
            total=Decimal("60.00"),
            shipping_name="Order Owner",
            shipping_line1="123 Test Street",
            shipping_city="Los Angeles",
            shipping_state="CA",
            shipping_postal_code="90001",
            shipping_country="US",
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return order.id

    finally:
        db.close()


# =========================================================
# ADMIN AUTHORIZATION
# =========================================================


def test_admin_routes_require_authentication(client):
    response = client.get("/admin/orders")

    assert response.status_code == 401


def test_normal_user_cannot_access_admin_orders(authorized_client):
    response = authorized_client.get("/admin/orders")

    assert response.status_code == 403


def test_normal_user_cannot_update_inventory(authorized_client):
    variant_id = create_variant()

    response = authorized_client.patch(
        f"/admin/inventory/{variant_id}", json={"stock_quantity": 100}
    )

    assert response.status_code == 403


def test_normal_user_cannot_create_coupon(authorized_client):
    response = authorized_client.post(
        "/admin/coupons",
        json={
            "code": "HACKED",
            "percent_off": 50,
            "amount_off": None,
            "minimum_subtotal": "0.00",
            "is_active": True,
        },
    )

    assert response.status_code == 403


# =========================================================
# ORDERS
# =========================================================


def test_admin_can_get_orders(admin_client):
    order_id = create_order()

    response = admin_client.get("/admin/orders")

    assert response.status_code == 200

    orders = response.json()

    assert len(orders) == 1
    assert orders[0]["id"] == order_id


def test_admin_can_update_order_status(admin_client):
    order_id = create_order()

    response = admin_client.patch(
        f"/admin/orders/{order_id}",
        json={
            "status": "shipped",
            "payment_status": "paid",
            "tracking_number": "TRACK123456",
        },
    )

    assert response.status_code == 200

    order = response.json()

    assert order["status"] == "shipped"
    assert order["payment_status"] == "paid"
    assert order["tracking_number"] == "TRACK123456"


def test_admin_update_unknown_order_returns_404(admin_client):
    response = admin_client.patch("/admin/orders/999999", json={"status": "shipped"})

    assert response.status_code == 404


# =========================================================
# INVENTORY
# =========================================================


def test_admin_can_update_inventory(admin_client):
    variant_id = create_variant(stock_quantity=10)

    response = admin_client.patch(
        f"/admin/inventory/{variant_id}", json={"stock_quantity": 75}
    )

    assert response.status_code == 200
    assert response.json()["stock_quantity"] == 75


def test_negative_inventory_rejected(admin_client):
    variant_id = create_variant()

    response = admin_client.patch(
        f"/admin/inventory/{variant_id}", json={"stock_quantity": -1}
    )

    assert response.status_code == 422


def test_update_unknown_variant_returns_404(admin_client):
    response = admin_client.patch(
        "/admin/inventory/999999", json={"stock_quantity": 10}
    )

    assert response.status_code == 404


# =========================================================
# COUPONS
# =========================================================


def test_admin_can_create_percent_coupon(admin_client):
    response = admin_client.post(
        "/admin/coupons",
        json={
            "code": "save20",
            "percent_off": 20,
            "amount_off": None,
            "minimum_subtotal": "50.00",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    coupon = response.json()

    assert coupon["code"] == "SAVE20"
    assert coupon["percent_off"] == 20
    assert Decimal(coupon["minimum_subtotal"]) == Decimal("50.00")


def test_admin_can_create_fixed_coupon(admin_client):
    response = admin_client.post(
        "/admin/coupons",
        json={
            "code": "tenoff",
            "percent_off": None,
            "amount_off": "10.00",
            "minimum_subtotal": "25.00",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    coupon = response.json()

    assert coupon["code"] == "TENOFF"
    assert Decimal(coupon["amount_off"]) == Decimal("10.00")


def test_coupon_cannot_have_both_discount_types(admin_client):
    response = admin_client.post(
        "/admin/coupons",
        json={
            "code": "INVALID",
            "percent_off": 20,
            "amount_off": "10.00",
            "minimum_subtotal": "0.00",
            "is_active": True,
        },
    )

    assert response.status_code == 400


def test_coupon_requires_discount_type(admin_client):
    response = admin_client.post(
        "/admin/coupons",
        json={
            "code": "INVALID",
            "percent_off": None,
            "amount_off": None,
            "minimum_subtotal": "0.00",
            "is_active": True,
        },
    )

    assert response.status_code == 400


def test_coupon_percent_above_100_rejected(admin_client):
    response = admin_client.post(
        "/admin/coupons",
        json={
            "code": "TOOMUCH",
            "percent_off": 101,
            "amount_off": None,
            "minimum_subtotal": "0.00",
            "is_active": True,
        },
    )

    assert response.status_code == 422
