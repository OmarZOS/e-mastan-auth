# # tests/test_auth_endpoints.py - Fixed
# import pytest
# from fastapi.testclient import TestClient
# from database import schemas, crud
# from sqlalchemy.orm import Session
# from datetime import datetime

# # Fixtures from conftest.py




# def create_test_user(db_session, username="testuser", app_user_id=1):
#     """Helper to create a test user."""
#     # Delete if exists
#     existing_user = crud.get_user_by_username(db_session, username)
#     if existing_user:
#         db_session.delete(existing_user)
#         db_session.commit()
    
#     # Create new user
#     user_data = schemas.UserCreate(
#         username=username,
#         password="secret123",
#         app_user_id=app_user_id,
#         email=f"{username}@example.com",
#         first_name="Test",
#         last_name="User",
#         phone_number="1234567890",
#         date_of_birth=datetime(2000, 1, 1),
#         gender="male",
#         roles="user",
#         login_count="0",
#         failed_login_attempts="0",
#         profile_picture=None
#     )
#     return crud.create_user(db_session, user_data)

# @pytest.mark.order(1)
# def test_create_user(client: TestClient, db_session: Session):
#     """Test user registration."""
#     # Clean up first
#     existing_user = crud.get_user_by_username(db_session, "testuser")
#     if existing_user:
#         db_session.delete(existing_user)
#         db_session.commit()
    
#     user_data = {
#         "username": "testuser",
#         "email": "test@example.com",
#         "first_name": "Test",
#         "last_name": "User",
#         "phone_number": "1234567890",
#         "date_of_birth": "2000-01-01T00:00:00",
#         "gender": "male",
#         "roles": "user",
#         "app_user_id": 1,
#         "password": "secret123",
#         "login_count": "0",
#         "failed_login_attempts": "0"
#     }

#     response = client.post("/auth/users/", json=user_data)
#     print(f"Response status: {response.status_code}")
#     print(f"Response body: {response.text}")
#     assert response.status_code == 200
#     data = response.json()
#     assert data["username"] == "testuser"
#     assert "hashed_password" in data

# @pytest.mark.order(2)
# def test_login_for_access_token(client: TestClient, db_session: Session):
#     """Test login endpoint."""
#     # Create user
#     create_test_user(db_session, "testuser", 1)
    
#     data = {
#         "username": "testuser",
#         "password": "secret123"
#     }
#     response = client.post("/auth/token", data=data)
#     print(f"Login response status: {response.status_code}")
#     print(f"Login response body: {response.text}")
#     assert response.status_code == 200
#     token_data = response.json()
#     assert "access_token" in token_data
#     assert token_data["token_type"] == "bearer"

# @pytest.mark.order(3)
# def test_read_users_me(client: TestClient, db_session: Session):
#     """Test fetching current user info."""
#     from server import app
#     from auth import get_current_user  # Correct import
    
#     # Create user
#     user = create_test_user(db_session, "testuser", 1)
    
#     # Create a proper mock that matches UserResponse schema
#     class MockUser:
#         def __init__(self, user):
#             self.id = user.id
#             self.username = user.username
#             self.email = user.email
#             self.app_user_id = user.app_user_id
#             self.phone_number = user.phone_number
#             self.hashed_password = user.hashed_password
#             self.first_name = user.first_name
#             self.last_name = user.last_name
#             self.date_of_birth = user.date_of_birth
#             self.gender = user.gender
#             self.profile_picture = user.profile_picture
#             self.roles = user.roles
#             self.last_login = user.last_login
#             self.login_count = user.login_count if hasattr(user, 'login_count') else 0
#             self.failed_login_attempts = user.failed_login_attempts if hasattr(user, 'failed_login_attempts') else 0
#             self.account_locked = user.account_locked if hasattr(user, 'account_locked') else False
#             self.mfa_enabled = user.mfa_enabled if hasattr(user, 'mfa_enabled') else False
#             self.created_at = user.created_at
#             self.updated_at = user.updated_at
#             self.deleted_at = user.deleted_at
    
#     mock_user = MockUser(user)
    
#     async def override_get_current_user():
#         return mock_user
    
#     app.dependency_overrides[get_current_user] = override_get_current_user
    
#     try:
#         response = client.get("/auth/users/me/")
#         print(f"Current user response status: {response.status_code}")
#         print(f"Current user response body: {response.text}")
#         assert response.status_code == 200
#         user_data = response.json()
#         assert user_data["username"] == "testuser"
#     finally:
#         # Clean up
#         if get_current_user in app.dependency_overrides:
#             del app.dependency_overrides[get_current_user]

# @pytest.mark.order(4)
# def test_update_user_password(client: TestClient, db_session: Session):
#     """Test updating user password."""
#     from server import app
#     from auth import get_current_user  # Correct import
    
#     # Create user
#     user = create_test_user(db_session, "testuser", 1)
    
#     # Create a proper mock
#     class MockUser:
#         def __init__(self):
#             self.username = "testuser"
#             self.email = "test@example.com"
#             self.full_name = "Test User"
#             self.disabled = False
    
#     mock_user = MockUser()
    
#     async def override_get_current_user():
#         return mock_user
    
#     app.dependency_overrides[get_current_user] = override_get_current_user
    
#     update_data = {
#         "username": "testuser",
#         "app_user_id": 1,
#         "new_password": "newsecret123",
#         "new_username": None,
#         "email": "test@example.com",
#         "first_name": "Test",
#         "last_name": "User",
#         "phone_number": "1234567890",
#         "date_of_birth": "2000-01-01T00:00:00",
#         "gender": "male",
#         "roles": "user",
#         "last_login": None,
#         "login_count": "0",
#         "failed_login_attempts": "0",
#         "account_locked": False,
#         "mfa_enabled": False,
#         "profile_picture": None
#     }

#     try:
#         response = client.post("/auth/users/update-password/", json=update_data)
#         print(f"Update password response status: {response.status_code}")
#         print(f"Update password response body: {response.text}")
#         assert response.status_code == 200
#         data = response.json()
#         assert data["username"] == "testuser"

#         # Verify that login works with new password
#         login_data_new = {"username": "testuser", "password": "newsecret123"}
#         login_res_new = client.post("/auth/token", data=login_data_new)
#         assert login_res_new.status_code == 200
#         assert "access_token" in login_res_new.json()
#     finally:
#         # Clean up
#         if get_current_user in app.dependency_overrides:
#             del app.dependency_overrides[get_current_user]

# @pytest.mark.order(5)
# def test_delete_user(client: TestClient, db_session: Session):
#     """Test deleting a user."""
#     # Create a fresh user
#     user = create_test_user(db_session, "deletetestuser", 999)
    
#     delete_data = {
#         "username": "deletetestuser",
#         "app_user_id": 999,
#         "new_password": "newsecret123",
#         "new_username": None,
#         "email": "deletetestuser@example.com",
#         "first_name": "Test",
#         "last_name": "User",
#         "phone_number": "1234567890",
#         "date_of_birth": "2000-01-01T00:00:00",
#         "gender": "male",
#         "roles": "user",
#         "last_login": None,
#         "login_count": "0",
#         "failed_login_attempts": "0",
#         "account_locked": False,
#         "mfa_enabled": False,
#         "profile_picture": None
#     }

#     # Use client.request() for DELETE with body
#     response = client.request(
#         "DELETE",
#         "/auth/users",
#         json=delete_data
#     )
    
#     print(f"Delete response status: {response.status_code}")
#     print(f"Delete response body: {response.text}")
#     assert response.status_code == 200
#     data = response.json()
#     assert data["username"] == "deletetestuser"

#     # Check database directly instead of trying to login
#     db_user = crud.get_user_by_username(db_session, "deletetestuser")
#     print(f"User in database after deletion: {db_user}")
#     assert db_user is None, "User should be deleted from database"