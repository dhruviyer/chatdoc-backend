from fastapi import Depends, HTTPException, status
from .database import SessionLocal, engine, Base
from typing import Annotated
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

load_dotenv()

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
AUTH_ALGORITHM = os.getenv("AUTH_ALGORITHM")

# Database dependencies

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# User auth dependencies

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
oauth2_bearer_dependency = Annotated[str, Depends(oauth2_bearer)]

async def get_current_user(token: oauth2_bearer_dependency):
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return {"username": username, "id": user_id}
    except:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
user_dependency = Annotated[dict, Depends(get_current_user)]