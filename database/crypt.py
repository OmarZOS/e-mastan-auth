from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import hashlib
import os
import binascii

# Create a CryptContext object for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def generate_salt() -> bytes:
    return os.urandom(16)

def hash_with_salt(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return binascii.hexlify(dk).decode()

def get_password_hash(password: str, salt: bytes) -> str:
    return hash_with_salt(password, salt)

def verify_password(plain_password: str, hashed_password: str, salt: bytes) -> bool:
    return hashed_password == hash_with_salt(plain_password, salt)
