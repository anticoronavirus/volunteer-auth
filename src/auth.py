from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from jencoder import UUIDEncoder

import conf
import db
from db import database


SECRET_KEY = conf.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = conf.TOKEN_EXP_MINUTES
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expires = datetime.utcnow() + expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode,
                             SECRET_KEY,
                             algorithm=ALGORITHM,
                             json_encoder=UUIDEncoder)
    return encoded_jwt, expires


async def get_volunteer(phone: str):
    query = db.volunteer.select().where(db.volunteer.c.phone==phone)
    # username is guaranteed to be unique
    volnt = await database.fetch_one(query)
    if volnt:
        return db.Volunteer(**volnt)


async def authenticate_user(phone: str, password: str):
    user = await get_volunteer(phone)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def create_volunteer(phone: str, password: str) -> db.Volunteer:
    query = db.volunteer.insert().values(
        fname="",
        mname="",
        lname="",
        email="",
        phone=phone,
        role="volunteer",
        password=get_password_hash(password)).returning(db.volunteer.c.uid)
    uid = await database.execute(query)
    return db.Volunteer(phone=phone, uid=uid)
