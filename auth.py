# app/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from core.error_codes import ErrorCode
from core.messages import *
from core.exception_handler import APIException
from fastapi import Depends,  status
from sqlalchemy.orm import Session
from database import schemas
from database.crypt import verify_password
from constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
import database.crud as crud
from database.crypt import oauth2_scheme
from database.database import get_db


def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate a user by username and password.
    """
    user = crud.get_user_by_username(db, username)
    if not user:
        # Use APIException with status_code
        raise APIException(
            status_code=HTTP_401_UNAUTHORIZED,  # Changed from 'status' to 'status_code'
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid username or password",
            details={"username": username}
        )
    
    # Verify password
    if not verify_password(password, user.hashed_password, user.password_salt):
        raise APIException(
            status_code=HTTP_401_UNAUTHORIZED,  # Changed from 'status' to 'status_code'
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid username or password",
            details={"username": username}
        )
    
    return user


# In auth.py, fix create_access_token
def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token."""
    import time
    from datetime import datetime, timedelta, timezone
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Convert datetime to Unix timestamp (integer)
    to_encode.update({"exp": int(expire.timestamp())})
    to_encode.update({"iat": int(datetime.now(timezone.utc).timestamp())})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token."""
    import logging
    logger = logging.getLogger(__name__)
    
    credentials_exception = APIException(
        status_code=HTTP_401_UNAUTHORIZED,
        error_code=ErrorCode.UNAUTHORIZED,
        message="Could not validate credentials",
        details={"token": "Invalid or expired token"}
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Try to get username from token
        username = payload.get("username") or payload.get("sub")
        
        # If username is not found, try to get user by app_user_id
        if username is None:
            app_user_id = payload.get("app_user_id")
            if app_user_id is not None:
                # Try to find user by app_user_id
                user = crud.get_user_by_app_user_id(db, int(app_user_id))
                if user is not None:
                    return user
            raise credentials_exception
        
        token_data = schemas.TokenData(username=username)
    except JWTError as e:
        logger.error(f"JWT Error: {e}")
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


