import logging

import graphene
from fastapi import FastAPI
from graphql.execution.executors.asyncio import AsyncioExecutor

import gql
from auth import (Token, authenticate_user, create_access_token,
                  create_volunteer, get_volunteer)
from db import database
from gqlapp import LessCrappyGQLApp


logger = logging.getLogger(__name__)


app = FastAPI()
app.add_route("/",
              LessCrappyGQLApp(
                  schema=graphene.Schema(mutation=gql.Mutations),
                  executor_class=AsyncioExecutor))


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
