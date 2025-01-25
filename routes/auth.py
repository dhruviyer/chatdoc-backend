from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from ..models import User
from ..deps import db_dependency, get_current_user, bcrypt_context
from typing import Annotated
import os
from datetime import datetime, timedelta, timezone

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("AUTH_ALGORITHM")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreateRequest(BaseModel):
    username: str
    password: str

def authenticate_user(username: str, password: str, db: db_dependency):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, id: int, expires_delta: timedelta):
    to_encode = {"sub": username, "id": id, "exp": datetime.now(timezone.utc) + expires_delta}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user_create_request: UserCreateRequest, db: db_dependency):
    user = User(username=user_create_request.username, hashed_password=bcrypt_context.hash(user_create_request.password))
    db.add(user)
    db.commit()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {"access_token": access_token, "token_type": "bearer"}

