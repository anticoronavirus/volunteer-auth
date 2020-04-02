import logging
from datetime import timedelta

import phonenumbers
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import conf
from auth import Token, create_access_token, authenticate_user
from sms import aero
from schema import Phone
import db
from db import database


app = FastAPI()
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/send-code")
async def read_root(body: Phone):
    sent = await aero.send_bool(body.phone, "ANTICORONA", "Your code is: 123")
    if not sent:
        logging.warn(f"delivering sms to {body.phone} failed permanently.")
    return {"status": "ok" if sent else "failed"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
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


# @app.get("/db-test")
# async def login_for_access_token():
#     query = db.volunteer.select()
#     resp = await database.fetch_all(query)
#     import pdb; pdb.set_trace()
    

# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: str = None):
#     return {"item_id": item_id, "q": q}
