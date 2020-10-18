import logging

import conf
import gql
import graphene
import sqlalchemy
from db import database, metadata
from fastapi import FastAPI
from gqlapp import LessCrappyGQLApp
from graphql.execution.executors.asyncio import AsyncioExecutor


logger = logging.getLogger(__name__)


app = FastAPI()
app.add_route(
    "/",
    LessCrappyGQLApp(
        schema=graphene.Schema(mutation=gql.Mutations),
        executor_class=AsyncioExecutor,
    ),
)


@app.on_event("startup")
async def startup():
    engine = sqlalchemy.create_engine(str(conf.DATABASE_URL))
    metadata.create_all(engine)
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
