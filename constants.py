
import os


# Secret key for JWT encoding/decoding
SECRET_KEY = os.getenv("API_SECRET_KEY", "supersecret_default_key_123!")

# Algorithm used for JWT
ALGORITHM = os.getenv("API_ALGORITHM", "HS256")

# Token expiry time in minutes
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10))

# Database URL for the auth server
# Using SQLite in-memory as default for testing/dev purposes
AUTH_DATABASE_URL = os.getenv(
    "AUTH_DATABASE_URL",
    "sqlite:///./auth_db_test.db"  # local SQLite file if nothing provided
)

# specify the allowed origins to access the auth provider
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS",'*').split(',')
