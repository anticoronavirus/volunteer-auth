import conf
import databases
import sqlalchemy
from sqlalchemy.dialects.postgresql import UUID


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
    sqlalchemy.Column("password_expires_at", sqlalchemy.TIMESTAMP(timezone=True)),
)

miserables = sqlalchemy.Table(
    "miserables",
    metadata,
    sqlalchemy.Column("token", sqlalchemy.String, primary_key=True),
    schema=conf.TOKEN_SCHEMA_NAME
    # sqlalchemy.Column("expires", sqlalchemy.TIMESTAMP(timezone=True)),
)

# engine = sqlalchemy.create_engine(str(conf.DATABASE_URL))
# metadata.create_all(engine)
