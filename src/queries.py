from datetime import timedelta
from uuid import uuid4

import conf
import db
from dates import aware_now
from db import database
from models import Volunteer


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
            password=None,
            password_expires_at=None,
        )
    )
    result = await database.execute(query)


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
