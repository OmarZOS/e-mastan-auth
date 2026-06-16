# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import models, crud, schemas
from server import app
from database.models import Base
import os
from datetime import datetime

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_auth.db")

# Create engine and session factory
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency in FastAPI app
from dependencies import get_db

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Fixture to create database tables before tests and drop after
@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

# Fixture for TestClient
@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c

# Fixture for direct DB access
@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

# In conftest.py - if you want to keep fixture approach
@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from database import schemas, crud
    from datetime import datetime
    
    # Delete if exists first
    existing = crud.get_user_by_username(db_session, "testuser")
    if existing:
        db_session.delete(existing)
        db_session.commit()
    
    user_data = schemas.UserCreate(
        username="testuser",
        password="password123",
        app_user_id=1,
        email="test@example.com",
        login_count="0",
        failed_login_attempts="0"
    )
    return crud.create_user(db_session, user_data)


# Fixture for authentication headers
@pytest.fixture()
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    login_data = {
        "username": "testuser",
        "password": "secret123"
    }
    response = client.post("/auth/token", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}