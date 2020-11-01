import conf
import databases
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


database = databases.Database(conf.DATABASE_URL)

metadata = sa.MetaData()

volunteer = sa.Table(
    "volunteer",
    metadata,
    sa.Column("uid", UUID, primary_key=True),
    sa.Column("fname", sa.String),
    sa.Column("mname", sa.String),
    sa.Column("lname", sa.String),
    sa.Column("phone", sa.String),
    sa.Column("email", sa.String),
    sa.Column("role", sa.String),
)

miserables = sa.Table(
    "miserables",
    metadata,
    sa.Column("token", sa.String, primary_key=True),
    schema=conf.TOKEN_SCHEMA_NAME
    # sa.Column("expires", sa.TIMESTAMP(timezone=True)),
)

password = sa.Table(
    "password",
    metadata,
    sa.Column("uid", UUID, primary_key=True),
    sa.Column("volunteer_id", UUID, sa.ForeignKey("volunteer.uid")),
    sa.Column("password", sa.String, nullable=True),
    sa.Column(
        "expires_at",
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    ),
    sa.Column(
        "ctime",
        sa.TIMESTAMP(timezone=True),
    ),
    schema=conf.TOKEN_SCHEMA_NAME,
)
