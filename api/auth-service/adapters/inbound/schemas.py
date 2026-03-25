from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterUserRequest(BaseModel):
    nom: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="user", min_length=1, max_length=50)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UpdateUserRequest(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    role: Optional[str] = Field(default=None, min_length=1, max_length=50)


class UserResponse(BaseModel):
    id: str
    nom: str
    email: EmailStr
    role: str
    status: str
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
