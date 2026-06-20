# tests/test_authentication.py
import pytest

class TestAuthentication:
    
    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        import time
        unique_suffix = str(int(time.time() * 1000))
        test_data = test_user_data.copy()
        test_data["username"] = f"login_{unique_suffix}"
        test_data["email"] = f"login_{unique_suffix}@example.com"
        test_data["app_user_id"] = 12345 + int(unique_suffix) % 1000
        
        # Create user
        client.post("/auth/users/", json=test_data)
        
        # Login
        response = client.post(
            "/auth/token",
            data={
                "username": test_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == test_data["username"]
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/token",
            data={
                "username": "nonexistent",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_CREDENTIALS"