import uuid

import databases
import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID

import conf


# SQLAlchemy specific code, as with any other app
database = databases.Database(conf.DATABASE_URL)

metadata = sqlalchemy.MetaData()

volunteer = sqlalchemy.Table(
    "volunteer",
    metadata,
    sqlalchemy.Column("uid", UUID, primary_key=True),
    sqlalchemy.Column("fname", sqlalchemy.String),
    sqlalchemy.Column("mname", sqlalchemy.String),
    sqlalchemy.Column("lname", sqlalchemy.String),
    sqlalchemy.Column("phone", sqlalchemy.String),
    sqlalchemy.Column("email", sqlalchemy.String),
    sqlalchemy.Column("blacklisted", sqlalchemy.Boolean),
    sqlalchemy.Column("blacklist_comment", sqlalchemy.String),
    sqlalchemy.Column("role", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String),
)


engine = sqlalchemy.create_engine(
    conf.DATABASE_URL, connect_args={"check_same_thread": False}
)
# metadata.create_all(engine)

class Volunteer(BaseModel):
    uid: uuid.UUID
    fname: str
    mname: str
    lname: str
    phone: str
    email: str
    blacklisted: bool
    blacklist_comment: str
    role: str
    password: str
