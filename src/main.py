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

app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/send-code", response_model=Registration)
async def send_registration_code(body: Phone):
    if await get_volunteer(body.phone):
        return {"status": "exists"}
    tpassword = str(random.randint(1000, 9999))
    logger.warn(tpassword)
    sent = True
    # sent = await aero.send_bool(
    #     body.phone,
    #     "NEWS",
    #     f"Your anticorona volunteer code is: {tpassword}")
    if not sent:
        return {"status": "failed"}
    else:
        volunteer = await create_volunteer(body.phone, tpassword)
        return {"status": "ok",
                "token": generate_token(volunteer),
                "code_": tpassword}


def generate_token(user: Volunteer) -> dict:
    access_token_expires = timedelta(minutes=conf.TOKEN_EXP_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.uid,
            "https://hasura.io/jwt/claims": {
                "x-hasura-default-role": "volunteer",
                "x-hasura-user-id": user.uid,
                "x-hasura-allowed-roles": ["volunteer"]
            }
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return generate_token(user)
