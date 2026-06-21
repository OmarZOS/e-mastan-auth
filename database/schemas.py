# app/schemas.py - Updated version without EmailStr
from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Optional, Union, List
from datetime import datetime
import re


class API_Resolution(BaseModel):
    """Standard API response wrapper"""
    status: int = Field(..., description="HTTP status code")
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human readable message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": 200,
                "error_code": "SUCCESS",
                "message": "Operation completed successfully"
            }
        }
    )


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL or base64")
    roles: Optional[str] = Field(None, description="Comma-separated roles")
    login_count: Optional[Union[str, int]] = Field("0", description="Login count")
    failed_login_attempts: Optional[Union[str, int]] = Field("0", description="Failed login attempts")
    account_locked: Optional[bool] = Field(False, description="Account locked status")
    mfa_enabled: Optional[bool] = Field(False, description="MFA enabled status")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]{3,50}$', v):
            raise ValueError('Username must be 3-50 characters and contain only letters, numbers, and underscores')
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format"""
        if v is not None and v.strip():
            # Simple email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v.strip()):
                raise ValueError('Invalid email format')
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is not None and v.strip():
            # Basic phone validation - can be customized
            if not re.match(r'^\+?[0-9]{7,15}$', v.strip()):
                raise ValueError('Phone number must be 7-15 digits with optional + prefix')
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender value"""
        if v is not None and v.strip():
            valid_genders = ['male', 'female', 'other', 'prefer_not_to_say']
            if v.lower() not in valid_genders:
                raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
        return v
    
    @field_validator('login_count', 'failed_login_attempts', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        """Convert values to string for serialization"""
        if v is None:
            return "0"
        return str(v)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01T00:00:00",
                "gender": "male",
                "roles": "user,admin",
                "login_count": "0",
                "failed_login_attempts": "0",
                "account_locked": False,
                "mfa_enabled": False
            }
        }
    )


class UserCreate(UserBase):
    """User creation model"""
    app_user_id: int = Field(..., description="Application user ID from the main app")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        # Optional: Add more password requirements
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "app_user_id": 123,
                "password": "SecurePassword123!",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01T00:00:00",
                "gender": "male",
                "roles": "user",
                "profile_picture": None
            }
        }
    )


class UserUpdate(UserBase):
    """User update model"""
    app_user_id: int = Field(..., description="Application user ID")
    new_password: Optional[str] = Field(None, min_length=6, max_length=100, description="New password")
    new_username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate new password strength"""
        if v is not None and len(v) > 0:
            if len(v) < 6:
                raise ValueError('New password must be at least 6 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('New password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('New password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('New password must contain at least one digit')
        return v
    
    @field_validator('new_username')
    @classmethod
    def validate_new_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate new username format"""
        if v is not None and v.strip():
            if not re.match(r'^[a-zA-Z0-9_]{3,50}$', v):
                raise ValueError('New username must be 3-50 characters and contain only letters, numbers, and underscores')
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "app_user_id": 123,
                "new_username": "john_doe_new",
                "new_password": "NewSecurePassword123!",
                "email": "john_new@example.com",
                "first_name": "Johnathan",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01T00:00:00",
                "gender": "male",
                "roles": "user,admin",
                "profile_picture": None
            }
        }
    )


class UserResponse(UserBase):
    """User response model"""
    id: int = Field(..., description="Internal user ID")
    app_user_id: int = Field(..., description="Application user ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    hashed_password: Optional[str] = Field(None, description="Hashed password (only for internal use)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "app_user_id": 123,
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone_number": "+1234567890",
                "date_of_birth": "1990-01-01T00:00:00",
                "gender": "male",
                "roles": "user,admin",
                "login_count": "10",
                "failed_login_attempts": "0",
                "account_locked": False,
                "mfa_enabled": False,
                "last_login": "2024-01-01T12:00:00",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "deleted_at": None,
                "profile_picture": None
            }
        }
    )


class Token(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    app_user_id: str = Field(..., description="Application user ID")
    expires_in: int = Field(..., description="Token expiration in seconds")
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="User email")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    iat: Optional[str] = Field(None, description="Issued at timestamp")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    iss: Optional[str] = Field(None, description="Issuer")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "app_user_id": "123",
                "expires_in": 3600,
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "iat": "2024-01-01T12:00:00Z",
                "expires_at": "2024-01-01T13:00:00Z",
                "iss": "gluttex-auth-server"
            }
        }
    )


class TokenData(BaseModel):
    """Token data model for internal use"""
    username: Optional[str] = Field(None, description="Username")
    app_user_id: Optional[int] = Field(None, description="Application user ID")
    roles: Optional[List[str]] = Field(None, description="User roles")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
    iat: Optional[int] = Field(None, description="Issued at timestamp")


class User(BaseModel):
    """Simple user model for authentication"""
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    disabled: Optional[bool] = Field(False, description="Disabled status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "disabled": False
            }
        }
    )


class UserLogin(BaseModel):
    """User login request model"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "password": "SecurePassword123!"
            }
        }
    )


# ============ Error Response Classes ============

class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = Field(False, description="Success flag (always false for errors)")
    status_code: int = Field(..., description="HTTP status code")
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "status_code": 401,
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid username or password",
                "details": {"username": "john_doe"},
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    )


class ValidationErrorResponse(ErrorResponse):
    """Validation error response model"""
    details: List[dict] = Field(..., description="Validation error details")


class ConflictErrorResponse(ErrorResponse):
    """Conflict error response model"""
    field: str = Field(..., description="Field that caused the conflict")


class AuthenticationErrorResponse(ErrorResponse):
    """Authentication error response model"""
    pass


class AuthorizationErrorResponse(ErrorResponse):
    """Authorization error response model"""
    required_role: Optional[str] = Field(None, description="Required role for access")


class NotFoundErrorResponse(ErrorResponse):
    """Not found error response model"""
    resource_type: str = Field(..., description="Type of resource not found")
    resource_id: Optional[Union[int, str]] = Field(None, description="ID of the resource not found")


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit error response model"""
    retry_after: int = Field(..., description="Seconds to wait before retrying")


class InternalServerErrorResponse(ErrorResponse):
    """Internal server error response model"""
    request_id: Optional[str] = Field(None, description="Request ID for debugging")