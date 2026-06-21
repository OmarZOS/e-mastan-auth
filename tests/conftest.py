# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import time

from database import models
from database.models import Base
from dependencies import get_db
from server import app


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "gender": "male",
        "phone_number": "+1234567890",
        "app_user_id": 12345,
    }

@pytest.fixture
def test_user_credentials():
    """Sample user credentials for login"""
    return {
        "username": "testuser",
        "password": "TestPassword123!"
    }

@pytest.fixture
def auth_header(client, test_user_data, test_user_credentials):
    """Create authenticated user and return auth header"""
    # Create user with unique data to avoid conflicts
    unique_suffix = str(int(time.time() * 1000))
    test_data = test_user_data.copy()
    test_data["username"] = f"auth_{unique_suffix}"
    test_data["email"] = f"auth_{unique_suffix}@example.com"
    test_data["app_user_id"] = 12345 + int(unique_suffix) % 1000
    
    # Register user
    register_response = client.post("/auth/register", json=test_data)
    if register_response.status_code != 200:
        pytest.fail(f"User creation failed: {register_response.status_code} - {register_response.text}")
    
    # Login with the credentials
    login_response = client.post(
        "/auth/token",
        data={
            "username": test_data["username"],
            "password": test_user_credentials["password"]
        }
    )
    
    if login_response.status_code != 200:
        pytest.fail(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    
    if not token:
        pytest.fail(f"No access token in response: {login_data}")
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
        "gender": "male",
        "phone_number": "+1234567890",
        "app_user_id": 12345,
    }

