from app import models
from tests.conftest import TestingSessionLocal

# =========================================================
# HELPERS
# =========================================================


def register_and_login(client, number: int):
    user = {
        "email": f"user{number}@example.com",
        "username": f"user{number}",
        "password": "SecurePassword123!",
        "first_name": f"User{number}",
        "last_name": "Test",
    }

    register_response = client.post("/auth/register", json=user)

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login", data={"username": user["email"], "password": user["password"]}
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "user": register_response.json(),
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


def create_variant():
    db = TestingSessionLocal()

    try:
        product = models.Product(
            name="Isolation Test Product",
            slug="isolation-test-product",
            description="Used for multi-user security tests",
            base_price=50,
            is_active=True,
            is_featured=False,
        )

        db.add(product)
        db.flush()

        variant = models.ProductVariant(
            product_id=product.id,
            sku="ISOLATION-BLK-M",
            size="M",
            color="Black",
            price=50,
            stock_quantity=20,
            is_active=True,
        )

        db.add(variant)
        db.commit()

        db.refresh(product)
        db.refresh(variant)

        return product.id, variant.id

    finally:
        db.close()


def address_payload():
    return {
        "label": "Home",
        "full_name": "User One",
        "line1": "123 Private Street",
        "line2": None,
        "city": "Los Angeles",
        "state": "CA",
        "postal_code": "90001",
        "country": "US",
        "phone": "5551234567",
        "is_default": True,
    }


# =========================================================
# JWT / USER IDENTITY
# =========================================================


def test_two_tokens_identify_different_users(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    response_a = client.get("/auth/me", headers=user_a["headers"])

    response_b = client.get("/auth/me", headers=user_b["headers"])

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert response_a.json()["id"] != response_b.json()["id"]

    assert response_a.json()["email"] != response_b.json()["email"]


# =========================================================
# CART ISOLATION
# =========================================================


def test_user_b_cannot_see_user_a_cart(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    _, variant_id = create_variant()

    add_response = client.post(
        "/cart",
        json={"variant_id": variant_id, "quantity": 2},
        headers=user_a["headers"],
    )

    assert add_response.status_code == 201

    response = client.get("/cart", headers=user_b["headers"])

    assert response.status_code == 200
    assert response.json() == []


def test_user_b_cannot_update_user_a_cart_item(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    _, variant_id = create_variant()

    create_response = client.post(
        "/cart",
        json={"variant_id": variant_id, "quantity": 2},
        headers=user_a["headers"],
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.patch(
        f"/cart/{item_id}", json={"quantity": 10}, headers=user_b["headers"]
    )

    assert response.status_code == 404

    # Verify User A's quantity was NOT changed.
    user_a_cart = client.get("/cart", headers=user_a["headers"])

    assert user_a_cart.status_code == 200
    assert len(user_a_cart.json()) == 1
    assert user_a_cart.json()[0]["quantity"] == 2


def test_user_b_cannot_delete_user_a_cart_item(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    _, variant_id = create_variant()

    create_response = client.post(
        "/cart",
        json={"variant_id": variant_id, "quantity": 2},
        headers=user_a["headers"],
    )

    assert create_response.status_code == 201

    item_id = create_response.json()["id"]

    response = client.delete(f"/cart/{item_id}", headers=user_b["headers"])

    assert response.status_code == 404

    # Verify User A still owns the cart item.
    user_a_cart = client.get("/cart", headers=user_a["headers"])

    assert user_a_cart.status_code == 200
    assert len(user_a_cart.json()) == 1
    assert user_a_cart.json()[0]["id"] == item_id


# =========================================================
# ADDRESS ISOLATION
# =========================================================


def test_user_b_cannot_see_user_a_addresses(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    create_response = client.post(
        "/addresses", json=address_payload(), headers=user_a["headers"]
    )

    assert create_response.status_code == 201

    response = client.get("/addresses", headers=user_b["headers"])

    assert response.status_code == 200
    assert response.json() == []

    # Verify the address still belongs to User A.
    user_a_addresses = client.get("/addresses", headers=user_a["headers"])

    assert user_a_addresses.status_code == 200
    assert len(user_a_addresses.json()) == 1


# =========================================================
# WISHLIST ISOLATION
# =========================================================


def test_user_b_cannot_see_user_a_wishlist(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    product_id, _ = create_variant()

    add_response = client.post(f"/wishlist/{product_id}", headers=user_a["headers"])

    assert add_response.status_code == 201

    response = client.get("/wishlist", headers=user_b["headers"])

    assert response.status_code == 200
    assert response.json() == []

    user_a_wishlist = client.get("/wishlist", headers=user_a["headers"])

    assert user_a_wishlist.status_code == 200
    assert len(user_a_wishlist.json()) == 1


def test_user_b_removing_product_does_not_remove_user_a_wishlist(client):
    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    product_id, _ = create_variant()

    add_response = client.post(f"/wishlist/{product_id}", headers=user_a["headers"])

    assert add_response.status_code == 201

    # User B tries to remove the same product,
    # but User B never added it.
    delete_response = client.delete(
        f"/wishlist/{product_id}", headers=user_b["headers"]
    )

    assert delete_response.status_code == 204

    # User A's wishlist must remain untouched.
    user_a_wishlist = client.get("/wishlist", headers=user_a["headers"])

    assert user_a_wishlist.status_code == 200
    assert len(user_a_wishlist.json()) == 1

    assert user_a_wishlist.json()[0]["product"]["id"] == product_id
