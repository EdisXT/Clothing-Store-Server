import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models


from app.config import settings

TEST_DATABASE_URL = settings.test_database_url

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database():
    yield

    with test_engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def user_data():
    return {
        "email": "customer@example.com",
        "username": "customer",
        "password": "CustomerPassword123!",
        "first_name": "Test",
        "last_name": "Customer",
    }


@pytest.fixture()
def test_user(client, user_data):
    response = client.post("/auth/register", json=user_data)

    assert response.status_code == 201

    return response.json()


@pytest.fixture()
def user_token(client, test_user, user_data):
    response = client.post(
        "/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.fixture()
def authorized_client(client, user_token):
    client.headers.update({"Authorization": f"Bearer {user_token}"})

    return client


@pytest.fixture()
def admin_user(client):
    data = {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword123!",
        "first_name": "Store",
        "last_name": "Admin",
    }

    response = client.post("/auth/register", json=data)

    assert response.status_code == 201

    db = TestingSessionLocal()

    try:
        user = db.query(models.User).filter(models.User.email == data["email"]).first()

        user.is_admin = True
        db.commit()
        db.refresh(user)

    finally:
        db.close()

    return data


@pytest.fixture()
def admin_token(client, admin_user):
    response = client.post(
        "/auth/login",
        data={
            "username": admin_user["email"],
            "password": admin_user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.fixture()
def admin_client(client, admin_token):
    client.headers.update({"Authorization": f"Bearer {admin_token}"})

    return client
