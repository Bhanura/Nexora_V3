"""
Security utilities for authentication and token management.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import hashlib
import os

# Configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# This tells FastAPI where to look for the token (the URL /api/auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if password matches the hash (using your existing SHA256 logic)."""
    # NOTE: In production, switch to bcrypt. We use SHA256 here to match your Console App.
    attempt_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return attempt_hash == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token (the 'passport')."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt