import logging
import random
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import conf
from auth import (Token, authenticate_user, create_access_token,
                  create_volunteer, get_volunteer)
from db import database, Volunteer
from schema import Phone, Registration
from sms import aero
import graphene
from gqlapp import LessCrappyGQLApp
import gql
from graphql.execution.executors.asyncio import AsyncioExecutor


logger = logging.getLogger(__name__)


app = FastAPI()
app.add_route("/",
              LessCrappyGQLApp(
                  schema=graphene.Schema(query=gql.Query,
                                         mutation=gql.Mutations),
                  executor_class=AsyncioExecutor))


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
