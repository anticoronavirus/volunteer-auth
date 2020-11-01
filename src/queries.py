import uuid
from datetime import timedelta

import conf
import db
import sqlalchemy
from dates import aware_now
from db import database
from models import Volunteer


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


async def create_volunteer(phone: str) -> uuid.UUID:
    query = db.volunteer.insert().values(
        uid=uuid.uuid4(),
        fname="",
        mname="",
        lname="",
        email="",
        phone=phone,
        role="volunteer",
    ).returning(db.volunteer.c.uid)

    uid = await database.execute(query)
    return uid


async def is_blacklisted(token):
    query = db.miserables.select().where(db.miserables.c.token==token)
    found = await database.fetch_one(query)
    return bool(found)


async def get_last_volunteer_passwords(phone, limit):
    query = """
        select p.volunteer_id, p.password, p.expires_at, p.ctime
        from volunteer v
        left outer join les.password p
          on p.volunteer_id = v.uid
        where
          v.phone = :phone
        order by
          p.expires_at desc
        limit :limit
    """
    return await database.fetch_all(query, {"phone": phone,  "limit": limit})


async def add_password(volunteer_id: uuid.UUID, password_hash: str):
    query = db.password.insert().values(
        uid=uuid.uuid4(),
        volunteer_id=volunteer_id,
        password=password_hash,
        expires_at=aware_now() + timedelta(seconds=conf.PASSWORD_EXP_SEC),
        ctime=aware_now(),
    )
    return await database.execute(query)


async def get_last_login_attempts(phone: str, limit: int):
    query = """
        select ctime
        from
          les.login
        where
          phone = :phone
        order by
           ctime asc
        limit
          :limit
    """
    return await database.fetch_all(query, {"phone": phone, "limit": limit})


async def log_login_attempt(phone: str):
    query = """
        insert into les.login (phone, ctime)
        values (:phone, :now)
    """
    return await database.execute(query, {"phone": phone, "now": aware_now()})

