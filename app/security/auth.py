import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.models.schemas import TokenData, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def hash_password(password: str) -> str:
    """Generates a secure PBKDF2-SHA256 password hash with salt."""
    salt = "NIGERIA_CLINICAL_GATEWAY_SALT_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Predefined mock users for demonstration and testing
MOCK_USERS = {
    "admin_user": {
        "username": "admin_user",
        "hashed_password": hash_password("AdminPass2026!"),
        "role": UserRole.ADMIN,
    },
    "dr_okonkwo": {
        "username": "dr_okonkwo",
        "hashed_password": hash_password("DoctorPass2026!"),
        "role": UserRole.CLINICIAN,
    },
    "researcher_ade": {
        "username": "researcher_ade",
        "hashed_password": hash_password("ResearchPass2026!"),
        "role": UserRole.RESEARCHER,
    },
    "officer_bello": {
        "username": "officer_bello",
        "hashed_password": hash_password("OfficerPass2026!"),
        "role": UserRole.DATA_OFFICER,
    },
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception
    return token_data

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User role '{user.role}' is not authorized for this operation. Allowed roles: {self.allowed_roles}"
            )
        return user
