from app import models
from tests.conftest import TestingSessionLocal

# =========================================================
# HELPERS
# =========================================================


def create_product():
    db = TestingSessionLocal()

    try:
        product = models.Product(
            name="Review Test Product",
            slug="review-test-product",
            description="Product used for review testing",
            base_price=50,
            is_active=True,
            is_featured=False,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return product.id

    finally:
        db.close()


def register_and_login(client, number):
    user_data = {
        "email": f"reviewuser{number}@example.com",
        "username": f"reviewuser{number}",
        "password": "SecurePassword123!",
        "first_name": "Review",
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
# PUBLIC REVIEW ACCESS
# =========================================================


def test_reviews_are_public(client):
    product_id = create_product()

    response = client.get(f"/reviews/product/{product_id}")

    assert response.status_code == 200
    assert response.json() == []


def test_nonexistent_product_review_list_is_empty(client):
    response = client.get("/reviews/product/999999")

    assert response.status_code == 200
    assert response.json() == []


# =========================================================
# CREATE REVIEW
# =========================================================


def test_review_requires_authentication(client):
    product_id = create_product()

    response = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 5, "title": "Great", "body": "Excellent product."},
    )

    assert response.status_code == 401


def test_user_can_create_review(client, authorized_client):
    product_id = create_product()

    response = client.post(
        f"/reviews/product/{product_id}",
        json={
            "rating": 5,
            "title": "Great quality",
            "body": "Really liked this product.",
        },
        headers=authorized_client.headers,
    )

    assert response.status_code == 201

    review = response.json()

    assert review["product_id"] == product_id
    assert review["rating"] == 5
    assert review["title"] == "Great quality"
    assert review["body"] == "Really liked this product."
    assert "user_id" in review
    assert "created_at" in review


def test_created_review_appears_publicly(client, authorized_client):
    product_id = create_product()

    create_response = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 4, "title": "Good", "body": "Solid product."},
        headers=authorized_client.headers,
    )

    assert create_response.status_code == 201

    response = client.get(f"/reviews/product/{product_id}")

    assert response.status_code == 200

    reviews = response.json()

    assert len(reviews) == 1
    assert reviews[0]["rating"] == 4
    assert reviews[0]["product_id"] == product_id


def test_review_nonexistent_product_returns_404(client, authorized_client):
    response = client.post(
        "/reviews/product/999999",
        json={
            "rating": 5,
            "title": "Impossible",
            "body": "This product does not exist.",
        },
        headers=authorized_client.headers,
    )

    assert response.status_code == 404


# =========================================================
# REVIEW VALIDATION
# =========================================================


def test_rating_below_one_rejected(client, authorized_client):
    product_id = create_product()

    response = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 0, "title": "Invalid", "body": "Invalid rating."},
        headers=authorized_client.headers,
    )

    assert response.status_code == 422


def test_rating_above_five_rejected(client, authorized_client):
    product_id = create_product()

    response = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 6, "title": "Invalid", "body": "Invalid rating."},
        headers=authorized_client.headers,
    )

    assert response.status_code == 422


# =========================================================
# DUPLICATES / MULTI-USER
# =========================================================


def test_same_user_cannot_review_product_twice(client, authorized_client):
    product_id = create_product()

    first_response = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 5, "title": "First review", "body": "First review body."},
        headers=authorized_client.headers,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 3, "title": "Second review", "body": "Trying again."},
        headers=authorized_client.headers,
    )

    assert second_response.status_code == 409


def test_different_users_can_review_same_product(client):
    product_id = create_product()

    user_a = register_and_login(client, 1)
    user_b = register_and_login(client, 2)

    response_a = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 5, "title": "User A", "body": "User A review."},
        headers=user_a,
    )

    assert response_a.status_code == 201

    response_b = client.post(
        f"/reviews/product/{product_id}",
        json={"rating": 4, "title": "User B", "body": "User B review."},
        headers=user_b,
    )

    assert response_b.status_code == 201

    response = client.get(f"/reviews/product/{product_id}")

    assert response.status_code == 200
    assert len(response.json()) == 2
