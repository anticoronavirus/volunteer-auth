from uuid import uuid4
import pytest
from starlette.config import environ
from starlette.testclient import TestClient
from sqlalchemy import create_engine, schema
from sqlalchemy_utils import database_exists, create_database, drop_database
from starlette.config import environ
from models import Volunteer


environ["TESTING"] = "True"


# these imports absolutely have to follow calls to environ.
from main import app
from db import metadata
import conf


@pytest.fixture(scope="session", autouse=True)
def dbe():
    url = str(conf.DATABASE_URL)
    engine = create_engine(url)
    assert not database_exists(url), 'Test database already exists. Aborting tests.'
    create_database(url)
    engine.execute(schema.CreateSchema(conf.TOKEN_SCHEMA_NAME)) # create schema
    metadata.create_all(engine)      # Create tables.
    yield engine
    drop_database(url)


@pytest.fixture(scope="function")
def volunteer():
    return Volunteer(uid=uuid4(), phone="+79261234567", password="1234")


@pytest.fixture(scope="function")
def client():
    # using TestClient as context manager inits database connection.
    with TestClient(app) as client:
        yield client

