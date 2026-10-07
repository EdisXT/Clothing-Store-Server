from app import models
from tests.conftest import TestingSessionLocal


def create_variant(stock_quantity=10, is_active=True):
    db = TestingSessionLocal()

    try:
        product = models.Product(
            name="Test T-Shirt",
            slug="test-t-shirt",
            description="Test product",
            base_price=40,
            is_active=True,
            is_featured=False,
        )

        db.add(product)
        db.flush()

        variant = models.ProductVariant(
            product_id=product.id,
            sku="TEST-BLK-M",
            size="M",
            color="Black",
            price=40,
            stock_quantity=stock_quantity,
            is_active=is_active,
        )

        db.add(variant)
        db.commit()
        db.refresh(variant)

        return variant.id

    finally:
        db.close()


def test_cart_requires_authentication(client):
    response = client.get("/cart")

    assert response.status_code == 401


def test_cart_starts_empty(authorized_client):
    response = authorized_client.get("/cart")

    assert response.status_code == 200
    assert response.json() == []


def test_add_item_to_cart(authorized_client):
    variant_id = create_variant()

    response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 2}
    )

    assert response.status_code == 201

    data = response.json()

    assert data["quantity"] == 2
    assert data["variant"]["id"] == variant_id
    assert data["variant"]["size"] == "M"
    assert data["variant"]["color"] == "Black"


def test_cart_returns_saved_items(authorized_client):
    variant_id = create_variant()

    add_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 2}
    )

    assert add_response.status_code == 201

    response = authorized_client.get("/cart")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["quantity"] == 2
    assert data[0]["variant"]["id"] == variant_id


def test_adding_same_variant_increases_quantity(authorized_client):
    variant_id = create_variant(stock_quantity=10)

    first_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 2}
    )

    assert first_response.status_code == 201

    second_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 3}
    )

    assert second_response.status_code == 201
    assert second_response.json()["quantity"] == 5


def test_cannot_add_more_than_available_stock(authorized_client):
    variant_id = create_variant(stock_quantity=3)

    response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 4}
    )

    assert response.status_code == 409


def test_cannot_exceed_stock_when_adding_again(authorized_client):
    variant_id = create_variant(stock_quantity=5)

    first_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 3}
    )

    assert first_response.status_code == 201

    second_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 3}
    )

    assert second_response.status_code == 409


def test_invalid_variant_returns_404(authorized_client):
    response = authorized_client.post(
        "/cart", json={"variant_id": 999999, "quantity": 1}
    )

    assert response.status_code == 404


def test_inactive_variant_cannot_be_added(authorized_client):
    variant_id = create_variant(stock_quantity=10, is_active=False)

    response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 1}
    )

    assert response.status_code == 404


def test_zero_quantity_rejected(authorized_client):
    variant_id = create_variant()

    response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 0}
    )

    assert response.status_code == 422


def test_quantity_above_schema_limit_rejected(authorized_client):
    variant_id = create_variant(stock_quantity=100)

    response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 21}
    )

    assert response.status_code == 422


def test_update_cart_quantity(authorized_client):
    variant_id = create_variant(stock_quantity=10)

    create_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 1}
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = authorized_client.patch(f"/cart/{item_id}", json={"quantity": 5})

    assert response.status_code == 200
    assert response.json()["quantity"] == 5


def test_update_cart_cannot_exceed_inventory(authorized_client):
    variant_id = create_variant(stock_quantity=3)

    create_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 1}
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = authorized_client.patch(f"/cart/{item_id}", json={"quantity": 4})

    assert response.status_code == 409


def test_delete_cart_item(authorized_client):
    variant_id = create_variant()

    create_response = authorized_client.post(
        "/cart", json={"variant_id": variant_id, "quantity": 1}
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = authorized_client.delete(f"/cart/{item_id}")

    assert response.status_code == 204

    cart_response = authorized_client.get("/cart")

    assert cart_response.status_code == 200
    assert cart_response.json() == []


def test_update_unknown_cart_item_returns_404(authorized_client):
    response = authorized_client.patch("/cart/999999", json={"quantity": 2})

    assert response.status_code == 404


def test_delete_unknown_cart_item_returns_404(authorized_client):
    response = authorized_client.delete("/cart/999999")

    assert response.status_code == 404
