from uuid import uuid4

import conf
import pytest
from db import metadata
from main import app
from models import Volunteer
from sqlalchemy import create_engine, schema
from sqlalchemy_utils import create_database, database_exists, drop_database
from starlette.testclient import TestClient


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
