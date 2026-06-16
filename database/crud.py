# app/crud.py
from core.exception_handler import APIException
from core.messages import *
from sqlalchemy.orm import Session
from database.crypt import generate_salt, hash_with_salt
import database.models as models 
import database.schemas as schemas 
from passlib.context import CryptContext
import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.AppUser).filter(models.AppUser.app_user_id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.AppUser).filter(models.AppUser.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.AppUser).filter(models.AppUser.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    salt = generate_salt()
    hashed_password = hash_with_salt(user.password, salt)
    db_user = models.AppUser(
        username = user.username,
        email = user.email,
        app_user_id = user.app_user_id,
        phone_number = user.phone_number,
        hashed_password = hashed_password,
        password_salt = salt,
        first_name = user.first_name,
        last_name = user.last_name,
        date_of_birth = user.date_of_birth,
        gender = user.gender,
        profile_picture = user.profile_picture,
        roles = user.roles,
        last_login = datetime.datetime.now(),
        login_count = str(user.login_count),
        failed_login_attempts = str(user.failed_login_attempts),
        account_locked = False,
        mfa_enabled = False,
        created_at = datetime.datetime.now(),
        updated_at = datetime.datetime.now(),
        deleted_at = None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_object(db: Session, user):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user_object(db: Session, user):
    data= db.delete(user)
    db.commit()
    return data

# In crud.py, fix the delete_user function
def delete_user(db: Session, user:schemas.UserUpdate):
    db_user = get_user(db, user.app_user_id)
    if not db_user:
        raise APIException(status=HTTP_401_UNAUTHORIZED,code=USER_DELETE_FAILED,message=f"{USER_DELETE_FAILED}: {user.username}")
    try:
        # Store user data before deletion
        user_data = {
            "app_user_id": db_user.app_user_id,
            "username": db_user.username,
            "email": db_user.email
        }
        # Delete the user
        db.delete(db_user)
        db.commit()
        # Return the deleted user data
        return user_data
    except Exception as e:
        db.rollback()
        raise APIException(status=HTTP_417_EXPECTATION_FAILED,code=USER_DELETE_FAILED,message=str(e))

def change_user_password(db: Session, user:schemas.UserUpdate):
    db_user = get_user(db, user.app_user_id)
    if not db_user:
        # print(db_user)
        raise APIException(status=HTTP_401_UNAUTHORIZED,code=USER_NOT_FOUND,message=f"{USER_NOT_FOUND}: {user.username}")
    db_user.password_salt = generate_salt()
    db_user.hashed_password = hash_with_salt(user.new_password, db_user.password_salt)
    try:
        updated_user = update_user_object(db,db_user)
    except Exception as e:
        raise APIException(status=HTTP_417_EXPECTATION_FAILED,code=DATABASE_ERROR,message=str(e))
    return updated_user

def change_username(db: Session, user:schemas.UserUpdate):
    
    
    
    db_user = get_user_by_username(db, user.username)
    if not db_user:
        raise APIException(status=HTTP_404_NOT_FOUND,code=USER_NOT_FOUND,message=str(e))
    
    db_user.username = user.new_username
    
    try:
        updated_user = update_user_object(db,user)
    except Exception as e:
        raise APIException(status=HTTP_409_CONFLICT,code=DATABASE_ERROR,message=str(e))
    
    return updated_user




