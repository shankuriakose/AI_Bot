import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from src.main import app
from src.models import Base
from src.auth import hash_password


# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[app.get_db] = override_get_db

client = TestClient(app)


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_register_user_success(test_db):
    response = client.post(
        "/register", json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 201
    assert response.json() == {
        "username": "testuser",
        "message": "User registered successfully",
    }


def test_register_user_already_exists(test_db):
    # Register a user first
    client.post("/register", json={"username": "existinguser", "password": "password"})
    # Attempt to register the same user again
    response = client.post(
        "/register", json={"username": "existinguser", "password": "newpassword"}
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Username already exists"}


def test_login_user_success(test_db):
    # Register a user first
    client.post("/register", json={"username": "loginuser", "password": "loginpassword"})
    # Attempt to log in
    response = client.post(
        "/login", json={"username": "loginuser", "password": "loginpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_user_invalid_credentials(test_db):
    # Attempt to log in with incorrect password
    response = client.post(
        "/login", json={"username": "loginuser", "password": "wrongpassword"}
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Invalid username or password"}


    # Attempt to log in with non-existent user
    response = client.post(
        "/login", json={"username": "nonexistentuser", "password": "password"}
    )
    assert response.status_code == 400
    assert response.json() == {"message": "Invalid username or password"}
