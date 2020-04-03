import logging
import random
from datetime import timedelta

import graphene

import conf
from auth import (Token, authenticate_user, create_access_token,
                  create_volunteer, get_volunteer, verify_password)
from db import Volunteer
from graphql import GraphQLError
from schema import Phone


logger = logging.getLogger(__name__)


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

    @staticmethod
    async def mutate(root, info, phone, password):
        user = await get_volunteer(phone)
        if not user:
            raise GraphQLError("Нет такого пользователя")
        if not verify_password(password, user.password):
            raise GraphQLError("Неверный пароль")
        token = generate_token(user)
        GetJWT.set_token_as_cookie(root, info, token)
        return GetJWT(authenticated=True)

    @staticmethod
    def set_token_as_cookie(root, info, token):
        info.context["cookies"] = {"jwt": token["access_token"]}


class Mutations(graphene.ObjectType):
    signUp = VolunteerSignUp.Field()
    getToken = GetJWT.Field()
