import jwt
import logging
import random
from datetime import timedelta

import graphene

import conf
from auth import (Token, authenticate_user, create_access_token,
                  create_volunteer, get_volunteer, verify_password, SECRET_KEY, ALGORITHM)
from db import Volunteer
from graphql import GraphQLError
from schema import Phone
from uuid import UUID


logger = logging.getLogger(__name__)


def create_token(user_id: UUID) -> dict:
    access_token_expires = timedelta(minutes=conf.TOKEN_EXP_MINUTES)
    access_token, expires = create_access_token(
        data={
            "sub": user_id,
            "refr": False,
            "https://hasura.io/jwt/claims": {
                "x-hasura-default-role": "volunteer",
                "x-hasura-role": "volunteer",
                "x-hasura-user-id": user_id,
                "x-hasura-allowed-roles": ["volunteer"]
            }
        },
        expires_delta=access_token_expires
    )
    return {"access_token": access_token,
            "token_type": "bearer",
            "jwt_token_expiry": expires.timestamp()}


def create_refresh_token(user_id: UUID) -> dict:
    access_token_expires = timedelta(minutes=conf.TOKEN_EXP_MINUTES * 10)
    access_token, expires = create_access_token(
        data={
            "sub": user_id,
            "refr": True
        },
        expires_delta=access_token_expires
    )
    return access_token


class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))

    def resolve_hello(self, info, name):
        return "Hello " + name


class VolunteerSignUp(graphene.Mutation):
    class Arguments:
        phone = graphene.String()

    status = graphene.String()
    code = graphene.String(required=False, default_value="")

    @staticmethod
    async def mutate(root, info, phone):
        # raises error if not valid.
        Phone(phone=phone)
        if await get_volunteer(phone):
            return VolunteerSignUp(status="exists")
        tpassword = "test" #str(random.randint(1000, 9999))
        logger.warn(tpassword)
        sent = True
        # sent = await aero.send_bool(
        #     phone,
        #     "NEWS",
        #     f"Your anticorona volunteer code is: {tpassword}")
        if not sent:
            return VolunteerSignUp(status="failed")
        else:
            volunteer = await create_volunteer(phone, tpassword)
            return VolunteerSignUp(status="ok", code=tpassword)


class GetJWT(graphene.Mutation):
    class Arguments:
        phone = graphene.String()
        password = graphene.String()

    authenticated = graphene.Boolean()
    access_token = graphene.String()
    token_type = graphene.String()

    @staticmethod
    async def mutate(root, info, phone, password):
        user = await get_volunteer(phone)
        if not user:
            raise GraphQLError("Нет такого пользователя")
        if not verify_password(password, user.password):
            raise GraphQLError("Неверный пароль")
        token = create_token(user.uid)
        refresh_token = create_refresh_token(user.uid)

        # set refresh token as cookie
        info.context["cookies"] = {"refresh_token": refresh_token}

        return GetJWT(authenticated=True,
                      access_token=token["access_token"].decode("utf-8"),
                      token_type=token["token_type"])



class RefreshJWT(graphene.Mutation):
    class Arguments:
        token = graphene.String()

    authenticated = graphene.Boolean()
    access_token = graphene.String()
    token_type = graphene.String()

    @staticmethod
    async def mutate(root, info, token):
        try:
            decoded = jwt.decode(token,
                                 SECRET_KEY,
                                 algorithm=ALGORITHM)
        except:
            raise GraphQLError("Token verification failed.")
        else:
            if not decoded["refr"]:
                raise GraphQLError("This is not a refresh token.")
            token = create_token(decoded["sub"])
            return GetJWT(authenticated=True,
                          access_token=token["access_token"].decode("utf-8"),
                          token_type=token["token_type"])


class Mutations(graphene.ObjectType):
    signUp = VolunteerSignUp.Field()
    getToken = GetJWT.Field()
    refreshToken = RefreshJWT.Field()
