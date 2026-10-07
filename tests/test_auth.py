from app import models
from app.utils import verify_password

USER_DATA = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User",
}


def test_register_user(client):
    response = client.post("/auth/register", json=USER_DATA)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == USER_DATA["email"]
    assert data["username"] == USER_DATA["username"]
    assert data["first_name"] == USER_DATA["first_name"]
    assert data["last_name"] == USER_DATA["last_name"]

    assert "password" not in data
    assert "hashed_password" not in data


def test_password_is_hashed(client):
    client.post(
        "/auth/register",
        json={
            "email": "hash@example.com",
            "username": "hashuser",
            "password": "SecurePassword123!",
            "first_name": "Hash",
            "last_name": "Test",
        },
    )

    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()

    try:
        user = (
            db.query(models.User)
            .filter(models.User.email == "hash@example.com")
            .first()
        )

        assert user is not None

        assert user.hashed_password != "SecurePassword123!"

        assert verify_password("SecurePassword123!", user.hashed_password)

    finally:
        db.close()


def test_duplicate_email_rejected(client):
    user = {
        "email": "duplicate@example.com",
        "username": "duplicate1",
        "password": "Password123!",
        "first_name": "Duplicate",
        "last_name": "User",
    }

    first_response = client.post("/auth/register", json=user)

    assert first_response.status_code == 201

    user["username"] = "duplicate2"

    second_response = client.post("/auth/register", json=user)

    assert second_response.status_code == 409


def test_duplicate_username_rejected(client):
    first_user = {
        "email": "first@example.com",
        "username": "sameusername",
        "password": "Password123!",
        "first_name": "First",
        "last_name": "User",
    }

    second_user = {
        "email": "second@example.com",
        "username": "sameusername",
        "password": "Password123!",
        "first_name": "Second",
        "last_name": "User",
    }

    response = client.post("/auth/register", json=first_user)

    assert response.status_code == 201

    response = client.post("/auth/register", json=second_user)

    assert response.status_code == 409


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "Password123!",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "Password123!"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_username(client):
    client.post(
        "/auth/register",
        json={
            "email": "username@example.com",
            "username": "usernameuser",
            "password": "Password123!",
            "first_name": "Username",
            "last_name": "Login",
        },
    )

    response = client.post(
        "/auth/login", data={"username": "usernameuser", "password": "Password123!"}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_wrong_password_rejected(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpassword@example.com",
            "username": "wrongpassword",
            "password": "CorrectPassword123!",
            "first_name": "Wrong",
            "last_name": "Password",
        },
    )

    response = client.post(
        "/auth/login",
        data={"username": "wrongpassword@example.com", "password": "WRONGPASSWORD"},
    )

    assert response.status_code == 401


def test_get_current_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "current@example.com",
            "username": "currentuser",
            "password": "Password123!",
            "first_name": "Current",
            "last_name": "User",
        },
    )

    login_response = client.post(
        "/auth/login",
        data={"username": "current@example.com", "password": "Password123!"},
    )

    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "current@example.com"
    assert data["username"] == "currentuser"


def test_auth_me_without_token_rejected(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_invalid_token_rejected(client):
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer definitely-not-a-real-token"}
    )

    assert response.status_code == 401
