from datetime import timedelta
from uuid import uuid4

import conf
import db
from dates import aware_now
from db import database
from models import Volunteer, Password
import sqlalchemy


async def get_volunteer(phone: str):
    query = db.volunteer.select().where(db.volunteer.c.phone==phone)
    # username is guaranteed to be unique
    volnt = await database.fetch_one(query)
    if volnt:
        return Volunteer(**volnt)


async def flush_password(user_with_password):
    query = (
        db.password.delete().
        where(
            sqlalchemy.and_(
                db.password.c.volunteer_id==user_with_password["volunteer_id"],
                db.password.c.password==user_with_password["password"],
                db.password.c.expires_at==user_with_password["expires_at"],
            )
        )
    )
    result = await database.execute(query)


async def create_volunteer(phone: str) -> Volunteer:
    query = db.volunteer.insert().values(
        uid=uuid4(),
        fname="",
        mname="",
        lname="",
        email="",
        phone=phone,
        role="volunteer",
    ).returning(db.volunteer.c.uid)

    uid = await database.execute(query)
    return Volunteer(phone=phone, uid=uid)


async def is_blacklisted(token):
    query = db.miserables.select().where(db.miserables.c.token==token)
    found = await database.fetch_one(query)
    return bool(found)


async def get_active_password(phone):
    j = sqlalchemy.join(db.volunteer, db.password, isouter=True)
    query = sqlalchemy.select([j]).where(
        db.volunteer.c.phone==phone,
    ).order_by(db.password.c.expires_at.desc())
    return await database.fetch_one(query)


async def add_password(volunteer: Volunteer, password_hash: str):
    query = db.password.insert().values(
        uid=uuid4(),
        volunteer_id=volunteer.uid,
        password=password_hash,
        expires_at=aware_now() + timedelta(seconds=conf.PASSWORD_EXP_SEC),
    )
    return await database.execute(query)
