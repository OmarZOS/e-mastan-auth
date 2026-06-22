# app/main.py
from datetime import datetime, timedelta, timezone
import logging
from core.exception_handler import APIException
from core.error_codes import ErrorCode
from core.messages import *
from fastapi import FastAPI, Depends, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALLOWED_ORIGINS
from database.database import engine
import auth, dependencies
from database import schemas, crud, models
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import os

# ==================== Database Setup ====================
# Create database tables
models.Base.metadata.create_all(bind=engine)

# ==================== Logging Configuration ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ==================== FastAPI App ====================
app = FastAPI(
    title="Emastan Auth Server",
    description="Authentication server for Verdelia platforms",
    version="1.0.0",
    openapi_url="/auth/openapi.json",
    docs_url="/auth/docs",
    redoc_url="/auth/redoc"
)

# ==================== Prometheus Instrumentation ====================

# Initialize Instrumentator with default metrics
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument the app
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Optional: Add custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Custom metrics
USER_REGISTRATIONS = Counter('auth_user_registrations_total', 'Total number of user registrations')
USER_LOGINS = Counter('auth_user_logins_total', 'Total number of user logins')
USER_LOGIN_FAILURES = Counter('auth_user_login_failures_total', 'Total number of failed login attempts')
PASSWORD_CHANGES = Counter('auth_password_changes_total', 'Total number of password changes')
USER_DELETIONS = Counter('auth_user_deletions_total', 'Total number of user deletions')

AUTH_REQUEST_DURATION = Histogram(
    'auth_request_duration_seconds',
    'Duration of authentication requests',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_USERS = Gauge('auth_active_users', 'Number of active users')

# ==================== CORS Middleware ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Exception Handlers ====================

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle APIException specifically"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for consistent error responses"""
    
    # Handle known APIException (should be caught by the specific handler above)
    if isinstance(exc, APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )
    
    # Handle HTTP exceptions from FastAPI
    if hasattr(exc, 'status_code'):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "status_code": exc.status_code,
                "code": _get_error_code_from_status(exc.status_code),
                "message": str(exc.detail) if hasattr(exc, 'detail') else str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    # Handle validation errors (Pydantic)
    if hasattr(exc, 'errors') and callable(getattr(exc, 'errors', None)):
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "status_code": HTTP_422_UNPROCESSABLE_ENTITY,
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    # Handle SQLAlchemy integrity errors
    if hasattr(exc, 'orig') and hasattr(exc.orig, 'args'):
        error_msg = str(exc.orig.args)
        if 'UNIQUE constraint failed' in error_msg or 'Duplicate entry' in error_msg:
            field = "unknown"
            if 'username' in error_msg.lower():
                field = "username"
            elif 'email' in error_msg.lower():
                field = "email"
            
            return JSONResponse(
                status_code=HTTP_409_CONFLICT,
                content={
                    "success": False,
                    "status_code": HTTP_409_CONFLICT,
                    "code": "DUPLICATE_ENTRY",
                    "message": f"{field.capitalize()} already exists",
                    "details": {"field": field},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    
    # Handle unexpected errors
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": HTTP_500_INTERNAL_SERVER_ERROR,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
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


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "Emastan-auth"
    }


# ==================== Routes ====================

@app.post("/auth/register", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    """Register a new user."""
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise APIException(
            status_code=HTTP_409_CONFLICT,
            error_code=ErrorCode.USERNAME_ALREADY_REGISTERED,
            message="Username already registered. Please choose a different username.",
            details={"username": user.username}
        )
    
    # Check if email already exists
    if user.email:
        db_email = crud.get_user_by_email(db, email=user.email)
        if db_email:
            raise APIException(
                status_code=HTTP_409_CONFLICT,
                error_code=ErrorCode.EMAIL_ALREADY_REGISTERED,
                message="Email already registered. Please use a different email address.",
                details={"email": user.email}
            )
    
    try:
        result = crud.create_user(db=db, user=user)
        # Increment registration counter
        USER_REGISTRATIONS.inc()
        # Update active users gauge
        ACTIVE_USERS.inc()
        return result
    except Exception as e:
        logger.error(f"Failed to create user: {e}", exc_info=True)
        raise APIException(
            status_code=HTTP_417_EXPECTATION_FAILED,
            error_code=ErrorCode.USER_CREATION_FAILED,
            message="Failed to create user account. Please try again later.",
            details={"error": str(e)}
        )


@app.post("/auth/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(dependencies.get_db)
):
    """Authenticate user and generate access token."""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        USER_LOGIN_FAILURES.inc()
        raise APIException(
            status_code=HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid username or password",
        )
    
    # Increment login counter
    USER_LOGINS.inc()
    
    # Create access token with username in sub
    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "app_user_id": str(user.app_user_id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    iat = datetime.now(timezone.utc)
    expire = iat + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "iat": iat.isoformat(),
        "expires_at": expire.isoformat(),
        "iss": "Emastan-auth-server",
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
            error_code=ErrorCode.UNAUTHORIZED,
            message="Not authenticated. Please log in to access this resource.",
        )
    return current_user


@app.post("/auth/change-password", response_model=schemas.UserResponse)
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
            error_code=ErrorCode.UNAUTHORIZED,
            message="You are not authorized to update this user's password.",
        )
    
    try:
        result = crud.change_user_password(db=db, user=user)
        PASSWORD_CHANGES.inc()
        return result
    except Exception as e:
        logger.error(f"Failed to update password: {e}", exc_info=True)
        raise APIException(
            status_code=HTTP_417_EXPECTATION_FAILED,
            error_code=ErrorCode.PASSWORD_UPDATE_FAILED,
            message="Failed to update password. Please try again later.",
            details={"error": str(e)}
        )


@app.delete("/auth/delete-user", response_model=schemas.UserResponse)
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
            error_code=ErrorCode.UNAUTHORIZED,
            message="You are not authorized to delete this user account.",
        )
    
    # Get the user first to return full response
    db_user = crud.get_user(db, user.app_user_id)
    if not db_user:
        raise APIException(
            status_code=HTTP_404_NOT_FOUND,
            error_code=ErrorCode.USER_NOT_FOUND,
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
        USER_DELETIONS.inc()
        ACTIVE_USERS.dec()
        logger.info(f"User deleted successfully: {user.username}")
        
        # Return the stored user data as confirmation
        return user_data
    except Exception as e:
        logger.error(f"Failed to delete user: {e}", exc_info=True)
        raise APIException(
            status_code=HTTP_417_EXPECTATION_FAILED,
            error_code=ErrorCode.USER_DELETION_FAILED,
            message="Failed to delete user account. Please try again later.",
            details={"error": str(e)}
        )


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("🚀 Auth Server starting up...")
    logger.info(f"📊 Database URL: {os.getenv('AUTH_DATABASE_URL', 'default SQLite')}")
    logger.info(f"📈 Metrics endpoint: /metrics")
    logger.info(f"📚 API Docs: /auth/docs")
    logger.info("✅ Auth Server ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("🛑 Auth Server shutting down...")