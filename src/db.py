import uuid

import databases
import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import UUID

import conf


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
    sqlalchemy.Column("role", sqlalchemy.String),
    sqlalchemy.Column("password", sqlalchemy.String),
)

miserables = sqlalchemy.Table(
    "miserables",
    metadata,
    sqlalchemy.Column("token", sqlalchemy.String, primary_key=True),
    schema=conf.TOKEN_SCHEMA_NAME
    # sqlalchemy.Column("expires", sqlalchemy.TIMESTAMP(timezone=True)),
)

# engine = sqlalchemy.create_engine(conf.DATABASE_URL)
# metadata.create_all(engine)

class Volunteer(BaseModel):
    uid: uuid.UUID
    fname: str = ""
    mname: str = ""
    lname: str = ""
    phone: str
    email: str = ""
    role: str = "volunteer"
    password: str = ""
