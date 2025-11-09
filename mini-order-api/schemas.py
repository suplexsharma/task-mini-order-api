from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from models import OrderStatus
import re

# User Schemas
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=50)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Order Schemas
class OrderCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_name: str
    amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Error Response
class ErrorResponse(BaseModel):
    detail: str

# Example for UserRegister
example_user_register = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "Viraj123"
}