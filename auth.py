# app/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from core.messages import *
from core.exception_handler import APIException
from fastapi import Depends,  status
from sqlalchemy.orm import Session
from database.crypt import verify_password
from constants import ALGORITHM, SECRET_KEY
import database.crud as crud
from dependencies import get_db
from database.crypt import oauth2_scheme


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password,user.password_salt):
        return False
    return user

# In auth.py, fix create_access_token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    # Convert ALL datetime objects to ISO format strings
    def convert_datetimes(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetimes(item) for item in obj]
        else:
            return obj
    
    to_encode = convert_datetimes(to_encode)
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = APIException(
        status=HTTP_401_UNAUTHORIZED,
        code=AUTH_REQUIRED,
        details=AUTH_UNAUTHORIZED,
        # headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        app_user_id: str = payload.get("sub")
        if app_user_id is None:
            raise credentials_exception
    except JWTError as e:
        credentials_exception.details = str(e)
        raise credentials_exception
    user = crud.get_user(db, user_id=app_user_id)
    if user is None:
        raise credentials_exception
    return user
