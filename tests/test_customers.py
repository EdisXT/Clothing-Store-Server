from app import models
from tests.conftest import TestingSessionLocal

# =========================================================
# HELPERS
# =========================================================


def create_product():
    db = TestingSessionLocal()

    try:
        product = models.Product(
            name="Wishlist Test Hoodie",
            slug="wishlist-test-hoodie",
            description="Product used for wishlist testing",
            base_price=65,
            is_active=True,
            is_featured=False,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product.id

    finally:
        db.close()


def address_payload(label="Home", is_default=False):
    return {
        "label": label,
        "full_name": "Test Customer",
        "line1": "123 Test Street",
        "line2": None,
        "city": "Los Angeles",
        "state": "CA",
        "postal_code": "90001",
        "country": "US",
        "phone": "5551234567",
        "is_default": is_default,
    }


# =========================================================
# ADDRESS TESTS
# =========================================================


def test_addresses_require_authentication(client):
    response = client.get("/addresses")

    assert response.status_code == 401


def test_addresses_start_empty(authorized_client):
    response = authorized_client.get("/addresses")

    assert response.status_code == 200
    assert response.json() == []


def test_create_address(authorized_client):
    response = authorized_client.post("/addresses", json=address_payload())

    assert response.status_code == 201

    data = response.json()

    assert data["label"] == "Home"
    assert data["full_name"] == "Test Customer"
    assert data["city"] == "Los Angeles"
    assert data["state"] == "CA"
    assert data["postal_code"] == "90001"
    assert data["country"] == "US"
    assert data["is_default"] is False
    assert "id" in data


def test_created_address_appears_in_list(authorized_client):
    create_response = authorized_client.post("/addresses", json=address_payload())

    assert create_response.status_code == 201

    response = authorized_client.get("/addresses")

    assert response.status_code == 200

    addresses = response.json()

    assert len(addresses) == 1
    assert addresses[0]["label"] == "Home"


def test_multiple_addresses_can_be_created(authorized_client):
    first_response = authorized_client.post(
        "/addresses", json=address_payload(label="Home")
    )

    assert first_response.status_code == 201

    second_address = address_payload(label="Work")

    second_address["line1"] = "500 Work Avenue"
    second_address["postal_code"] = "90002"

    second_response = authorized_client.post("/addresses", json=second_address)

    assert second_response.status_code == 201

    response = authorized_client.get("/addresses")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_setting_new_default_unsets_old_default(authorized_client):
    first_response = authorized_client.post(
        "/addresses", json=address_payload(label="Home", is_default=True)
    )

    assert first_response.status_code == 201
    assert first_response.json()["is_default"] is True

    second_address = address_payload(label="Work", is_default=True)

    second_address["line1"] = "500 Work Avenue"

    second_response = authorized_client.post("/addresses", json=second_address)

    assert second_response.status_code == 201
    assert second_response.json()["is_default"] is True

    response = authorized_client.get("/addresses")

    assert response.status_code == 200

    addresses = response.json()

    default_addresses = [
        address for address in addresses if address["is_default"] is True
    ]

    assert len(default_addresses) == 1
    assert default_addresses[0]["label"] == "Work"


# =========================================================
# WISHLIST TESTS
# =========================================================


def test_wishlist_requires_authentication(client):
    response = client.get("/wishlist")

    assert response.status_code == 401


def test_wishlist_starts_empty(authorized_client):
    response = authorized_client.get("/wishlist")

    assert response.status_code == 200
    assert response.json() == []


def test_add_product_to_wishlist(authorized_client):
    product_id = create_product()

    response = authorized_client.post(f"/wishlist/{product_id}")

    assert response.status_code == 201
    assert response.json()["message"] == "Saved"


def test_wishlist_returns_saved_product(authorized_client):
    product_id = create_product()

    add_response = authorized_client.post(f"/wishlist/{product_id}")

    assert add_response.status_code == 201

    response = authorized_client.get("/wishlist")

    assert response.status_code == 200

    wishlist = response.json()

    assert len(wishlist) == 1

    assert wishlist[0]["product"]["id"] == product_id

    assert wishlist[0]["product"]["name"] == "Wishlist Test Hoodie"


def test_duplicate_wishlist_product_does_not_duplicate(authorized_client):
    product_id = create_product()

    first_response = authorized_client.post(f"/wishlist/{product_id}")

    assert first_response.status_code == 201

    second_response = authorized_client.post(f"/wishlist/{product_id}")

    assert second_response.status_code == 201
    assert second_response.json()["message"] == "Already saved"

    response = authorized_client.get("/wishlist")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_add_nonexistent_product_to_wishlist_returns_404(authorized_client):
    response = authorized_client.post("/wishlist/999999")

    assert response.status_code == 404


def test_remove_product_from_wishlist(authorized_client):
    product_id = create_product()

    add_response = authorized_client.post(f"/wishlist/{product_id}")

    assert add_response.status_code == 201

    delete_response = authorized_client.delete(f"/wishlist/{product_id}")

    assert delete_response.status_code == 204

    response = authorized_client.get("/wishlist")

    assert response.status_code == 200
    assert response.json() == []


def test_remove_nonexistent_wishlist_item_is_safe(authorized_client):
    response = authorized_client.delete("/wishlist/999999")

    assert response.status_code == 204
