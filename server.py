# app/main.py
from datetime import datetime 
import logging
from core.exception_handler import APIException
from core.messages import *
from fastapi import FastAPI, Depends, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALLOWED_ORIGINS
import auth, dependencies
from database import schemas, crud, models
from database.models import engine
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta, timezone
from prometheus_fastapi_instrumentator import Instrumentator

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    openapi_url="/auth/openapi.json",
    docs_url="/auth/docs",
    redoc_url="/auth/redoc"
)

Instrumentator().instrument(app).expose(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for consistent error responses"""
    
    # Handle known APIException
    if isinstance(exc, APIException):
        resolution = schemas.API_Resolution(
            status=exc.status,
            error_code=exc.code,
            message=str(exc.message),
            details=getattr(exc, 'details', None)
        )
        return JSONResponse(
            status_code=exc.status,
            content=resolution.dict(),
        )
    
    # Handle HTTP exceptions from FastAPI
    if hasattr(exc, 'status_code'):
        resolution = schemas.API_Resolution(
            status=exc.status_code,
            error_code=_get_error_code_from_status(exc.status_code),
            message=str(exc.detail) if hasattr(exc, 'detail') else str(exc),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=resolution.dict(),
        )
    
    # Handle unexpected errors
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    resolution = schemas.API_Resolution(
        status=HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=resolution.dict(),
    )


def _get_error_code_from_status(status_code: int) -> str:
    """Map HTTP status codes to error codes"""
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    return error_codes.get(status_code, "UNKNOWN_ERROR")


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/auth/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    """Register a new user."""
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise APIException(
            status_code=HTTP_409_CONFLICT,
            code=USERNAME_ALREADY_REGISTERED,
            message="Username already registered. Please choose a different username.",
            details={"username": user.username}
        )
    
    # Check if email already exists
    db_email = crud.get_user_by_email(db, email=user.email)
    if db_email:
        raise APIException(
            status_code=HTTP_409_CONFLICT,
            code=EMAIL_ALREADY_REGISTERED,
            message="Email already registered. Please use a different email address.",
            details={"email": user.email}
        )
    
    try:
        return crud.create_user(db=db, user=user)
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise APIException(
            status_code=HTTP_417_EXPECTATION_FAILED,
            code=USER_CREATION_FAILED,
            message="Failed to create user account. Please try again later.",
            details={"error": str(e)}
        )


@app.post("/auth/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(dependencies.get_db)
):
    """Authenticate user and generate access token."""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise APIException(
            status_code=HTTP_401_UNAUTHORIZED,
            code=INVALID_CREDENTIALS,
            message="Invalid username or password. Please check your credentials and try again.",
            details={"username": form_data.username}
        )
    
    # Check if account is locked
    if user.account_locked:
        raise APIException(
            status_code=HTTP_403_FORBIDDEN,
            code=ACCOUNT_LOCKED,
            message="Your account has been locked due to too many failed attempts. Please contact support.",
            details={"user_id": user.app_user_id}
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={
            "sub": str(user.app_user_id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_of_birth": str(user.date_of_birth) if user.date_of_birth else None,
            "gender": user.gender,
            "roles": user.roles,
            "mfa_enabled": user.mfa_enabled,
        },
        expires_delta=access_token_expires
    )
    
    iat = datetime.now(timezone.utc)
    expire = iat + access_token_expires

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "iat": iat.isoformat(),
        "expires_at": expire.isoformat(),
        "iss": "gluttex-auth-server",
        "app_user_id": str(user.app_user_id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@app.get("/auth/users/me/", response_model=schemas.UserResponse)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    """Retrieve the currently logged-in user."""
    if not current_user:
        raise APIException(
            status_code=HTTP_401_UNAUTHORIZED,
            code=UNAUTHORIZED,
            message="Not authenticated. Please log in to access this resource.",
        )
    return current_user


@app.post("/auth/users/update-password/", response_model=schemas.UserResponse)
def update_user_password(
    user: schemas.UserUpdate, 
    db: Session = Depends(dependencies.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """Update the password of the authenticated user."""
    logger.info(f"Password update requested for user: {user.username}")
    
    # Verify current user matches the update request
    if current_user.app_user_id != user.app_user_id:
        raise APIException(
            status_code=HTTP_403_FORBIDDEN,
            code=UNAUTHORIZED,
            message="You are not authorized to update this user's password.",
        )
    
    try:
        result = crud.change_user_password(db=db, user=user)
        return result
    except Exception as e:
        logger.error(f"Failed to update password: {e}", exc_info=True)
        raise APIException(
            status_code=HTTP_417_EXPECTATION_FAILED,
            code=PASSWORD_UPDATE_FAILED,
            message="Failed to update password. Please try again later.",
            details={"error": str(e)}
        )


@app.delete("/auth/users", response_model=schemas.UserResponse)
def delete_user(
    user: schemas.UserUpdate, 
    db: Session = Depends(dependencies.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    """Delete the authenticated user."""
    logger.info(f"User deletion requested for: {user.username}")
    
    # Verify current user matches the deletion request
    if current_user.app_user_id != user.app_user_id:
        raise APIException(
            status_code=HTTP_403_FORBIDDEN,
            code=UNAUTHORIZED,
            message="You are not authorized to delete this user account.",
        )
    
    # Get the user first to return full response
    db_user = crud.get_user(db, user.app_user_id)
    if not db_user:
        raise APIException(
            status_code=HTTP_404_NOT_FOUND,
            code=USER_NOT_FOUND,
            message=f"User not found: {user.username}",
            details={"username": user.username}
        )
    
    # Store user data for response before deletion
    user_data = {
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "app_user_id": db_user.app_user_id,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "phone_number": db_user.phone_number,
        "date_of_birth": db_user.date_of_birth,
        "gender": db_user.gender,
        "roles": db_user.roles,
    }
    
    try:
        # Delete the user
        result = crud.delete_user(db=db, user=user)
        logger.info(f"User deleted successfully: {user.username}")
        
        # Return the stored user data as confirmation
        return user_data
    except Exception as e:
        logger.error(f"Failed to delete user: {e}", exc_info=True)
        raise APIException(
            status_code=HTTP_417_EXPECTATION_FAILED,
            code=USER_DELETION_FAILED,
            message="Failed to delete user account. Please try again later.",
            details={"error": str(e)}
        )