from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class user_register_body(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=100, description="User's password")
    name: str | None = Field(default=None, max_length=100, description="User's full name")


class user_login_body(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class user_response(BaseModel):
    id: int
    email: str
    name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class token_response(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: user_response


class user_register_response(user_response):
    access_token: str
    token_type: str = "bearer"


# Schema aliases
UserRegisterRequest = user_register_body
UserLoginRequest = user_login_body
UserResponse = user_response
TokenResponse = token_response
UserRegisterResponse = user_register_response

