from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from constants import AUTH_DATABASE_URL
import datetime
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = AUTH_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AppUser(Base):
    __tablename__ = 'app_user'

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    # this is the most important id to get the user from the database
    app_user_id = Column(Integer,  nullable=True)
    email = Column(String, index=True, nullable=True)
    phone_number = Column(String, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    password_salt = Column(LargeBinary, nullable=True)
    profile_picture = Column(LargeBinary, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    roles = Column(String, nullable=True)  # Comma-separated roles
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime, default=datetime.datetime.now())
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    deleted_at = Column(DateTime, nullable=True)

