from datetime import datetime, timedelta
from uuid import uuid4

import conf
import db
import jwt
from dates import aware_now
from db import database
from models import Volunteer
from jencoder import UUIDEncoder
from passlib.context import CryptContext
from pydantic import BaseModel
from queries import get_volunteer


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def millitimestamp(dt):
    return int(dt.timestamp() * 10**3)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None


class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    disabled: bool = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(*,
                        data: dict,
                        expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expires = datetime.now() + expires_delta
    to_encode.update({"exp": expires.timestamp()})
    encoded_jwt = jwt.encode(to_encode,
                             conf.SECRET_KEY,
                             algorithm=conf.ALGORITHM,
                             json_encoder=UUIDEncoder)
    return encoded_jwt, millitimestamp(expires)




async def authenticate_user(phone: str, password: str):
    user = await get_volunteer(phone)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


