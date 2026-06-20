# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from constants import AUTH_DATABASE_URL
import datetime

# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = AUTH_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in AUTH_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AppUser(Base):
    __tablename__ = 'app_user'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    # this is the most important id to get the user from the database
    app_user_id = Column(Integer, nullable=True, index=True)
    email = Column(String(255), index=True, nullable=True)
    phone_number = Column(String(20), index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    password_salt = Column(LargeBinary, nullable=True)
    profile_picture = Column(LargeBinary, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    roles = Column(String(255), nullable=True)  # Comma-separated roles
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime, default=datetime.datetime.now)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    # Add any relationships here if needed
    
    def __repr__(self):
        return f"<AppUser(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username
    
    @property
    def is_active(self) -> bool:
        """Check if user is active (not deleted and not locked)"""
        return self.deleted_at is None and not self.account_locked
    
    @property
    def role_list(self) -> list:
        """Get roles as a list"""
        if not self.roles:
            return []
        return [r.strip() for r in self.roles.split(',') if r.strip()]
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.role_list


# Optional: Add a Session model for tracking sessions if needed
class UserSession(Base):
    __tablename__ = 'user_session'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('app_user.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(500), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("AppUser", backref=backref("sessions", lazy="dynamic"))


# Optional: Add an AuditLog model for tracking actions
class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('app_user.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    # Relationship
    user = relationship("AppUser", backref=backref("audit_logs", lazy="dynamic"))