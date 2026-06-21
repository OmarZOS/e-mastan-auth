# tests/test_registration.py
import pytest
import json


class TestUserRegistration:
    
    def test_create_user_success(self, client, test_user_data):
        """Test successful user registration"""
        # Ensure unique data for each test
        import time
        unique_suffix = str(int(time.time() * 1000))
        test_data = test_user_data.copy()
        test_data["username"] = f"testuser_{unique_suffix}"
        test_data["email"] = f"test_{unique_suffix}@example.com"
        test_data["app_user_id"] = 12345 + int(unique_suffix) % 1000
        
        response = client.post("/auth/register", json=test_data)
        
        # Print response for debugging if needed
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_data["username"]
        assert data["email"] == test_data["email"]
        assert "id" in data
        assert "app_user_id" in data
        assert "hashed_password" in data
        assert "password" not in data  # Password should not be returned
    
    def test_create_user_duplicate_username(self, client, test_user_data):
        """Test registration with duplicate username"""
        # Create unique user first
        import time
        unique_suffix = str(int(time.time() * 1000))
        test_data = test_user_data.copy()
        test_data["username"] = f"duplicate_test_{unique_suffix}"
        test_data["email"] = f"dup_{unique_suffix}@example.com"
        test_data["app_user_id"] = 12345 + int(unique_suffix) % 1000
        
        # First registration should succeed
        response1 = client.post("/auth/register", json=test_data)
        assert response1.status_code == 200
        
        # Second registration with same username should fail
        duplicate_data = test_data.copy()
        duplicate_data["email"] = f"dup2_{unique_suffix}@example.com"
        duplicate_data["app_user_id"] = 12346 + int(unique_suffix) % 1000
        
        response2 = client.post("/auth/register", json=duplicate_data)
        
        assert response2.status_code == 409
        data = response2.json()
        assert data["code"] == "USERNAME_ALREADY_REGISTERED"
        assert "username" in data["details"]
    
    def test_create_user_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email"""
        import time
        unique_suffix = str(int(time.time() * 1000))
        test_data = test_user_data.copy()
        test_data["username"] = f"email_test_{unique_suffix}"
        test_data["email"] = f"email_dup_{unique_suffix}@example.com"
        test_data["app_user_id"] = 12345 + int(unique_suffix) % 1000
        
        # First registration should succeed
        response1 = client.post("/auth/register", json=test_data)
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        duplicate_data = test_data.copy()
        duplicate_data["username"] = f"email_test2_{unique_suffix}"
        duplicate_data["app_user_id"] = 12346 + int(unique_suffix) % 1000
        
        response2 = client.post("/auth/register", json=duplicate_data)
        
        assert response2.status_code == 409
        data = response2.json()
        assert data["code"] == "EMAIL_ALREADY_REGISTERED"
        assert "email" in data["details"]
    
    def test_create_user_missing_required_fields(self, client):
        """Test registration with missing required fields"""
        invalid_data = {
            "username": "testuser",
            "app_user_id": 12345,
            # Missing password field
        }
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        
        # Check for validation error format (FastAPI/Pydantic uses 'detail' field)
        assert "detail" in data
        assert len(data["detail"]) > 0
        # Check that the error is about missing password
        errors = data["detail"]
        assert any("password" in str(error.get("loc", [])) for error in errors)
    
    def test_create_user_invalid_email(self, client):
        """Test registration with invalid email format"""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "TestPassword123!",
            "app_user_id": 12345,
        }
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        
        # Check for validation error format
        assert "detail" in data
        assert len(data["detail"]) > 0
        # Check that the error is about invalid email
        errors = data["detail"]
        assert any("email" in str(error.get("loc", [])) for error in errors)
        assert any("Invalid email" in str(error.get("msg", "")) for error in errors)
    
    def test_create_user_weak_password(self, client):
        """Test registration with weak password"""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # Too short (< 6 characters)
            "app_user_id": 12345,
        }
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        
        # Check for validation error format
        assert "detail" in data
        assert len(data["detail"]) > 0
        # Check that the error is about password being too short
        errors = data["detail"]
        assert any("password" in str(error.get("loc", [])) for error in errors)
        assert any("at least 6 characters" in str(error.get("msg", "")) for error in errors)
    
    def test_create_user_without_app_user_id(self, client, test_user_data):
        """Test registration without app_user_id"""
        invalid_data = test_user_data.copy()
        del invalid_data["app_user_id"]
        
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0
        # Check that the error is about missing app_user_id
        errors = data["detail"]
        assert any("app_user_id" in str(error.get("loc", [])) for error in errors)