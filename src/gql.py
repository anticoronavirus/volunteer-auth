import logging
import random
from datetime import timedelta
from typing import Union
from uuid import UUID

import conf
import graphene
import jwt
from auth import (ALGORITHM, SECRET_KEY, Token, authenticate_user,
                  create_access_token, create_volunteer, get_volunteer,
                  verify_password)
from graphql import GraphQLError
from schema import Phone
from sms import aero

logger = logging.getLogger(__name__)


def create_token(user_id: Union[UUID, str]) -> dict:
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
    access_token_expires = timedelta(minutes=conf.REFRESH_TOKEN_EXP_MINUTES)
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

    @staticmethod
    async def mutate(root, info, phone):
        # raises error if not valid.
        ph_formatted = Phone(phone=phone).phone
        if await get_volunteer(ph_formatted):
            return VolunteerSignUp(status="exists")
        tpassword = str(random.randint(1000, 9999))
        logger.warn(tpassword)
        sent = await aero.send_bool(
            phone,
            "NEWS",
            f"Your anticorona volunteer code is: {tpassword}")
        if not sent:
            return VolunteerSignUp(status="failed")
        else:
            volunteer = await create_volunteer(ph_formatted, tpassword)
            return VolunteerSignUp(status="ok")


class GetJWT(graphene.Mutation):
    class Arguments:
        phone = graphene.String()
        password = graphene.String()

    authenticated = graphene.Boolean()
    access_token = graphene.String()
    token_type = graphene.String()
    expires = graphene.Float()

    @staticmethod
    async def mutate(root, info, phone, password):
        phone164 = Phone(phone=phone).phone
        user = await get_volunteer(phone164)
        if not user:
            raise GraphQLError("Нет такого пользователя")
        if not verify_password(password, user.password):
            raise GraphQLError("Неверный пароль")

        return GetJWT.create_tokens(info, user.uid)

    @classmethod
    def create_tokens(cls, info, user_id: Union[str, UUID]):
        token = create_token(user_id)
        refresh_token = create_refresh_token(user_id)

        # set refresh token as cookie
        info.context["cookies"] = {"refresh_token": refresh_token.decode("utf-8")}

        return cls(authenticated=True,
                   access_token=token["access_token"].decode("utf-8"),
                   token_type=token["token_type"],
                   expires=token["jwt_token_expiry"])


class RefreshJWT(graphene.Mutation):
    class Arguments:
        pass

    authenticated = graphene.Boolean()
    access_token = graphene.String()
    token_type = graphene.String()
    expires = graphene.Float()

    @staticmethod
    async def mutate(root, info):
        request = info.context['request']
        try:
            decoded = jwt.decode(request.cookies['refresh_token'],
                                 SECRET_KEY,
                                 algorithm=ALGORITHM)
        except KeyError:            
            raise GraphQLError("Refresh token not found in cookies. "
                               "Relogin and try again.")
        except:
            raise GraphQLError("Token verification failed.")
        else:
            return GetJWT.create_tokens(info, decoded["sub"])
        #     raise GraphQLError("Token verification failed.")
        # else:
        #     if not decoded["refr"]:
        #         raise GraphQLError("This is not a refresh token.")
        #     token = create_token(decoded["sub"])
        #     return GetJWT(authenticated=True,
        #                   access_token=token["access_token"].decode("utf-8"),
        #                   token_type=token["token_type"],
        #                   expires=token["jwt_token_expiry"])


class Mutations(graphene.ObjectType):
    signUp = VolunteerSignUp.Field()
    getToken = GetJWT.Field()
    refreshToken = RefreshJWT.Field()
