import logging
import random
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import conf
from auth import Token, authenticate_user, create_access_token, get_volunteer
from db import database
from schema import Phone
from sms import aero


app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/send-code")
async def send_registration_code(body: Phone):
    if await get_volunteer(body.phone):
        return {"status": "exists"}
    sent = await aero.send_bool(
        body.phone,
        "NEWS",
        f"Your anticorona volunteer code is: {random.randint(1000, 9999)}")
    if not sent:
        logging.warn(f"delivering sms to {body.phone} failed permanently.")
    return {"status": "ok" if sent else "failed"}


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
    access_token_expires = timedelta(minutes=conf.TOKEN_EXP_MINUTES)
    access_token = create_access_token(
        data={
            "sub": "65055ff2-1334-4821-9e8f-a9cdc9dc634c", #user.username,
            "x-hasura-default-role": "volunteer",
            "x-hasura-role": "volunteer",
            "x-hasura-allowed-roles": ["volunteer", "manager"]
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
