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


async def get_volunteer(phone: str):
    query = db.volunteer.select().where(db.volunteer.c.phone==phone)
    # username is guaranteed to be unique
    volnt = await database.fetch_one(query)
    if volnt:
        return Volunteer(**volnt)


async def flush_password(user: Volunteer):
    query = (
        db.volunteer.update().
        where(db.volunteer.c.uid==user.uid).
        values(
            password='',
            password_expires_at=None,
        )
    )
    result = await database.execute(query)


async def authenticate_user(phone: str, password: str):
    user = await get_volunteer(phone)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def create_volunteer(phone: str, password_hash: str) -> Volunteer:
    query = db.volunteer.insert().values(
        uid=uuid4(),
        fname="",
        mname="",
        lname="",
        email="",
        phone=phone,
        role="volunteer",
        password=password_hash,
        password_expires_at=aware_now() + timedelta(seconds=conf.PASSWORD_EXP_SEC),
    ).returning(db.volunteer.c.uid)

    uid = await database.execute(query)
    return Volunteer(phone=phone, uid=uid)


async def is_blacklisted(token):
    query = db.miserables.select().where(db.miserables.c.token==token)
    found = await database.fetch_one(query)
    return bool(found)
