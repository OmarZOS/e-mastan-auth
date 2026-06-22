# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import relationship, backref
import datetime

# Import Base from database, not from sqlalchemy directly
from database.database import Base

class AppUser(Base):
    __tablename__ = 'app_user'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
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
    roles = Column(String(255), nullable=True)
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime, default=datetime.datetime.now)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AppUser(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username
    
    @property
    def is_active(self) -> bool:
        return self.deleted_at is None and not self.account_locked
    
    @property
    def role_list(self) -> list:
        if not self.roles:
            return []
        return [r.strip() for r in self.roles.split(',') if r.strip()]
    
    def has_role(self, role: str) -> bool:
        return role in self.role_list


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
    
    user = relationship("AppUser", back_populates="sessions")


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
    
    user = relationship("AppUser", back_populates="audit_logs")