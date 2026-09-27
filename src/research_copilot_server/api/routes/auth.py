from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from research_copilot_server.config.db import get_db
from research_copilot_server.dependencies.auth import get_current_user
from research_copilot_server.models.user import User
from research_copilot_server.schema.auth import (
    token_response,
    user_login_body,
    user_register_body,
    user_register_response,
    user_response,
)
from research_copilot_server.services import auth as auth_service

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=user_register_response)
def register(data: user_register_body, db: Session = Depends(get_db)):
    return auth_service.register_user(db, data)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=token_response)
def login(data: user_login_body, db: Session = Depends(get_db)):
    return auth_service.login_user(db, data)


@router.get("/me", status_code=status.HTTP_200_OK, response_model=user_response)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
