from decimal import Decimal

from app import models
from tests.conftest import TestingSessionLocal

# =========================================================
# HELPERS
# =========================================================


def create_product_variant(
    base_price=Decimal("50.00"), variant_price=None, stock_quantity=10
):
    db = TestingSessionLocal()

    try:
        product = models.Product(
            name="Checkout Test Product",
            slug="checkout-test-product",
            description="Product used for checkout testing",
            base_price=base_price,
            is_active=True,
            is_featured=False,
        )

        db.add(product)
        db.flush()

        variant = models.ProductVariant(
            product_id=product.id,
            sku="CHECKOUT-BLK-M",
            size="M",
            color="Black",
            price=variant_price,
            stock_quantity=stock_quantity,
            is_active=True,
        )

        db.add(variant)
        db.commit()
        db.refresh(variant)

        return variant.id

    finally:
        db.close()


def create_address(client, headers):
    response = client.post(
        "/addresses",
        json={
            "label": "Home",
            "full_name": "Checkout Customer",
            "line1": "123 Checkout Street",
            "line2": None,
            "city": "Los Angeles",
            "state": "CA",
            "postal_code": "90001",
            "country": "US",
            "phone": "5551234567",
            "is_default": True,
        },
        headers=headers,
    )

    assert response.status_code == 201

    return response.json()["id"]


def add_to_cart(client, headers, variant_id, quantity=1):
    response = client.post(
        "/cart", json={"variant_id": variant_id, "quantity": quantity}, headers=headers
    )

    assert response.status_code == 201

    return response.json()


def create_coupon(
    code="SAVE20", percent_off=20, amount_off=None, minimum_subtotal=Decimal("0.00")
):
    db = TestingSessionLocal()

    try:
        coupon = models.Coupon(
            code=code,
            percent_off=percent_off,
            amount_off=amount_off,
            minimum_subtotal=minimum_subtotal,
            is_active=True,
        )

        db.add(coupon)
        db.commit()
        db.refresh(coupon)

        return coupon.id

    finally:
        db.close()


def register_and_login(client, number):
    user_data = {
        "email": f"orderuser{number}@example.com",
        "username": f"orderuser{number}",
        "password": "SecurePassword123!",
        "first_name": "Order",
        "last_name": f"User{number}",
    }

    register_response = client.post("/auth/register", json=user_data)

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


# =========================================================
# AUTHENTICATION
# =========================================================


def test_orders_require_authentication(client):
    response = client.get("/orders")

    assert response.status_code == 401


def test_checkout_requires_authentication(client):
    response = client.post("/orders/checkout", json={"address_id": 1})

    assert response.status_code == 401


# =========================================================
# CHECKOUT
# =========================================================


def test_checkout_creates_order(client, authorized_client):
    variant_id = create_product_variant(base_price=Decimal("50.00"))

    add_to_cart(client, authorized_client.headers, variant_id, quantity=1)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert response.status_code == 201

    order = response.json()

    assert order["order_number"].startswith("VX-")
    assert order["status"]
    assert order["payment_status"]

    assert Decimal(order["subtotal"]) == Decimal("50.00")
    assert Decimal(order["shipping"]) == Decimal("10.00")
    assert Decimal(order["discount"]) == Decimal("0.00")
    assert Decimal(order["tax"]) == Decimal("0.00")
    assert Decimal(order["total"]) == Decimal("60.00")

    assert len(order["items"]) == 1
    assert order["items"][0]["sku"] == "CHECKOUT-BLK-M"
    assert order["items"][0]["quantity"] == 1


def test_checkout_uses_variant_price(client, authorized_client):
    variant_id = create_product_variant(
        base_price=Decimal("50.00"), variant_price=Decimal("65.00")
    )

    add_to_cart(client, authorized_client.headers, variant_id, quantity=2)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert response.status_code == 201

    order = response.json()

    assert Decimal(order["subtotal"]) == Decimal("130.00")

    # Free shipping at $100+
    assert Decimal(order["shipping"]) == Decimal("0.00")

    assert Decimal(order["total"]) == Decimal("130.00")


def test_checkout_reduces_inventory(client, authorized_client):
    variant_id = create_product_variant(stock_quantity=10)

    add_to_cart(client, authorized_client.headers, variant_id, quantity=3)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert response.status_code == 201

    db = TestingSessionLocal()

    try:
        variant = db.get(models.ProductVariant, variant_id)

        assert variant.stock_quantity == 7

    finally:
        db.close()


def test_checkout_clears_cart(client, authorized_client):
    variant_id = create_product_variant()

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    checkout_response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert checkout_response.status_code == 201

    cart_response = client.get("/cart", headers=authorized_client.headers)

    assert cart_response.status_code == 200
    assert cart_response.json() == []


def test_checkout_empty_cart_rejected(client, authorized_client):
    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert response.status_code == 400


def test_checkout_invalid_address_rejected(client, authorized_client):
    variant_id = create_product_variant()

    add_to_cart(client, authorized_client.headers, variant_id)

    response = client.post(
        "/orders/checkout",
        json={"address_id": 999999},
        headers=authorized_client.headers,
    )

    assert response.status_code == 404


# =========================================================
# COUPONS
# =========================================================


def test_percent_coupon_applies_discount(client, authorized_client):
    create_coupon(code="SAVE20", percent_off=20)

    variant_id = create_product_variant(base_price=Decimal("100.00"))

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id, "coupon_code": "save20"},
        headers=authorized_client.headers,
    )

    assert response.status_code == 201

    order = response.json()

    assert Decimal(order["subtotal"]) == Decimal("100.00")
    assert Decimal(order["discount"]) == Decimal("20.00")
    assert Decimal(order["shipping"]) == Decimal("0.00")
    assert Decimal(order["total"]) == Decimal("80.00")


def test_fixed_amount_coupon_applies_discount(client, authorized_client):
    create_coupon(code="TENOFF", percent_off=None, amount_off=Decimal("10.00"))

    variant_id = create_product_variant(base_price=Decimal("50.00"))

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id, "coupon_code": "TENOFF"},
        headers=authorized_client.headers,
    )

    assert response.status_code == 201

    order = response.json()

    assert Decimal(order["subtotal"]) == Decimal("50.00")
    assert Decimal(order["discount"]) == Decimal("10.00")
    assert Decimal(order["shipping"]) == Decimal("10.00")
    assert Decimal(order["total"]) == Decimal("50.00")


def test_invalid_coupon_rejected(client, authorized_client):
    variant_id = create_product_variant()

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id, "coupon_code": "DOESNOTEXIST"},
        headers=authorized_client.headers,
    )

    assert response.status_code == 400


def test_coupon_minimum_subtotal_enforced(client, authorized_client):
    create_coupon(code="BIGORDER", percent_off=20, minimum_subtotal=Decimal("100.00"))

    variant_id = create_product_variant(base_price=Decimal("50.00"))

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    response = client.post(
        "/orders/checkout",
        json={"address_id": address_id, "coupon_code": "BIGORDER"},
        headers=authorized_client.headers,
    )

    assert response.status_code == 400


# =========================================================
# ORDER HISTORY / OWNERSHIP
# =========================================================


def test_order_appears_in_history(client, authorized_client):
    variant_id = create_product_variant()

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    checkout_response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert checkout_response.status_code == 201

    order_id = checkout_response.json()["id"]

    response = client.get("/orders", headers=authorized_client.headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == order_id


def test_user_can_get_own_order(client, authorized_client):
    variant_id = create_product_variant()

    add_to_cart(client, authorized_client.headers, variant_id)

    address_id = create_address(client, authorized_client.headers)

    checkout_response = client.post(
        "/orders/checkout",
        json={"address_id": address_id},
        headers=authorized_client.headers,
    )

    assert checkout_response.status_code == 201

    order_id = checkout_response.json()["id"]

    response = client.get(f"/orders/{order_id}", headers=authorized_client.headers)

    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_user_cannot_get_another_users_order(client):
    user_a_headers = register_and_login(client, 1)

    user_b_headers = register_and_login(client, 2)

    variant_id = create_product_variant()

    add_to_cart(client, user_a_headers, variant_id)

    address_id = create_address(client, user_a_headers)

    checkout_response = client.post(
        "/orders/checkout", json={"address_id": address_id}, headers=user_a_headers
    )

    assert checkout_response.status_code == 201

    order_id = checkout_response.json()["id"]

    response = client.get(f"/orders/{order_id}", headers=user_b_headers)

    # Do not reveal another customer's order.
    assert response.status_code == 404


def test_user_cannot_checkout_with_another_users_address(client):
    user_a_headers = register_and_login(client, 1)

    user_b_headers = register_and_login(client, 2)

    address_id = create_address(client, user_a_headers)

    variant_id = create_product_variant()

    add_to_cart(client, user_b_headers, variant_id)

    response = client.post(
        "/orders/checkout", json={"address_id": address_id}, headers=user_b_headers
    )

    assert response.status_code == 404


def test_unknown_order_returns_404(client, authorized_client):
    response = client.get("/orders/999999", headers=authorized_client.headers)

    assert response.status_code == 404
