import logging
import random
from datetime import timedelta

import graphene

import conf
from auth import (Token, authenticate_user, create_access_token,
                  create_volunteer, get_volunteer)
from db import Volunteer
from graphql import GraphQLError


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
        if await get_volunteer(phone):
            return VolunteerSignUp(status="exists")
        tpassword = str(random.randint(1000, 9999))
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

    access_token = graphene.String()
    token_type = graphene.String()

    @staticmethod
    async def mutate(root, info, phone, password):
        user = await authenticate_user(phone, password)
        if not user:
            raise GraphQLError("Неверный пользователь или пароль")
            # raise HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED,
            #     detail="Incorrect username or password",
            #     headers={"WWW-Authenticate": "Bearer"},
            # )
        return GetJWT(
            **generate_token(user)
        )


class Mutations(graphene.ObjectType):
    signUp = VolunteerSignUp.Field()
    getToken = GetJWT.Field()
