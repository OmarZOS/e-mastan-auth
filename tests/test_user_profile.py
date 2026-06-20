# tests/test_user_profile.py
import pytest

class TestUserProfile:
    
    def test_get_current_user(self, client, auth_header):
        """Test getting current user profile"""
        response = client.get(
            "/auth/users/me/",
            headers=auth_header
        )
        
        # Print debug info if test fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.json()}")
            print(f"Auth header: {auth_header}")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "app_user_id" in data
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting profile without token"""
        response = client.get("/auth/users/me/")
        
        assert response.status_code == 401
        data = response.json()
        
        # Check for the APIException format
        if "code" in data:
            assert data["code"] == "UNAUTHORIZED"
        elif "detail" in data:
            assert "Not authenticated" in data["detail"] or "credentials" in data["detail"].lower()
        else:
            # Fallback: just ensure it's a 401 error
            pass