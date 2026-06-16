# app/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class API_Resolution(BaseModel):
    status: int
    error_code: str
    message: str

# database/schemas.py - Update UserBase and UserResponse
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Union
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None
    roles: Optional[str] = None
    last_login: Optional[datetime] = None
    login_count: Optional[Union[str, int]] = "0"
    failed_login_attempts: Optional[Union[str, int]] = "0"
    account_locked: Optional[bool] = False
    mfa_enabled: Optional[bool] = False
    
    @field_validator('login_count', 'failed_login_attempts', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        if v is None:
            return "0"
        return str(v)

class UserResponse(UserBase):
    id: int
    app_user_id: int
    hashed_password: str
    password_salt: Optional[bytes] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(UserBase):
    new_username: Optional[str] 
    app_user_id: int
    new_password: str

class UserCreate(UserBase):
    # this is the most important id to get the user from the database
    app_user_id: int
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    hashed_password: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    app_user_id: str

class TokenData(BaseModel):
    username: Optional[str] 

class User(BaseModel):
    username: str
    email: Optional[str] 
    full_name: Optional[str] 
    disabled: Optional[bool] 

