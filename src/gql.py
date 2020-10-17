import logging
import random
from datetime import timedelta, datetime
from typing import Union
from uuid import UUID

import graphene
from datetime import datetime
import jwt
from graphql import GraphQLError

import conf
import db
from auth import (Token, authenticate_user, create_access_token,
                  create_volunteer, get_password_hash, get_volunteer,
                  verify_password, is_blacklisted, flush_password)
from db import database
from schema import Phone
from sms import aero


logger = logging.getLogger(__name__)
TokenVerificationFailed = GraphQLError("Token verification failed.")


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
            "jwt_token_expiry": expires}


def create_refresh_token(user_id: UUID) -> dict:
    access_token, _ = create_access_token(
        data={"sub": user_id, "refr": True},
        expires_delta=timedelta(minutes=conf.REFRESH_TOKEN_EXP_MINUTES)
    )
    return access_token


def make_password():
    return str(random.randint(1000, 9999))


class RequestPassword(graphene.Mutation):
    class Arguments:
        phone = graphene.String()

    status = graphene.String()

    @staticmethod
    async def mutate(root, info, phone):
        password = make_password()
        password_hash = get_password_hash(password)
        await RequestPassword.upsert_volunteer_with_password(
            # raises error if phone string is not valid.
            Phone(phone=phone).phone,
            password_hash,
        )
        message = await aero.send_bool(
            phone,
            "NEWS",
            f"{password} is your memedic volunteer code <3",
        )
        if not message:
            return RequestPassword(status="failed")
        else:
            return RequestPassword(status="ok")

    @staticmethod
    async def upsert_volunteer_with_password(phone: str, password_hash: str):
        query = (
            db.volunteer.update().
            where(db.volunteer.c.phone==phone).
            values(
                password=password_hash,
                password_expires_at=datetime.now()+timedelta(seconds=conf.PASSWORD_EXP_SEC),
            ).
            returning(db.volunteer.c.uid)
        )
        result = await database.execute(query)
        if not result:
            await create_volunteer(phone, password_hash)


class JWTMutation(graphene.Mutation):
    authenticated = graphene.Boolean()
    access_token = graphene.String()
    token_type = graphene.String()
    expires_at = graphene.Float()

    def mutate(root, info, phone, password):
        pass

    @classmethod
    def create_tokens(cls, info, user_id: Union[str, UUID]):
        token = create_token(user_id)
        refresh_token = create_refresh_token(user_id)

        # set refresh token as cookie
        info.context["cook"].set_cookie("refresh_token",
                                        refresh_token.decode("utf-8"),
                                        httponly=True)
        return cls(authenticated=True,
                   access_token=token["access_token"].decode("utf-8"),
                   token_type=token["token_type"],
                   expires_at=token["jwt_token_expiry"])


class GetJWT(JWTMutation):
    class Arguments:
        phone = graphene.String()
        password = graphene.String()

    @staticmethod
    async def mutate(root, info, phone, password):
        phone164 = Phone(phone=phone).phone
        user = await get_volunteer(phone164)
        if not user:
            raise GraphQLError("Нет такого пользователя")
        if not verify_password(password, user.password):
            raise GraphQLError("Неверный пароль")
        if user.password_expires_at <= datetime.now():
            raise GraphQLError("Пароль просрочен. Запросите новый.")

        await flush_password(user)
        return GetJWT.create_tokens(info, user.uid)


class RefreshJWT(JWTMutation):
    class Arguments:
        pass

    @staticmethod
    async def mutate(root, info):
        try:
            refresh_token = info.context["request"].cookies["refresh_token"]
        except KeyError:
            raise GraphQLError("Refresh token not found in cookies. "
                               "Relogin and try again.")

        try:
            decoded = jwt.decode(refresh_token,
                                 conf.SECRET_KEY,
                                 algorithm=conf.ALGORITHM)
        except:
            raise TokenVerificationFailed
        else:
            if datetime.fromtimestamp(decoded["exp"]) <= datetime.now():
                raise GraphQLError("Token expired")
            elif await is_blacklisted(refresh_token):
                raise TokenVerificationFailed
            else:
                query = db.miserables.insert().values(token=refresh_token)
                await database.execute(query)
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


class Logoff(graphene.Mutation, graphene.ObjectType):
    status = graphene.String()

    async def mutate(root, info):
        info.context["cook"].delete_cookie("refresh_token")
        try:
            refresh_token = info.context["request"].cookies["refresh_token"]
        except KeyError:
            # token's missing from cookies
            return Logoff(status="ok")

        try:
            decoded = jwt.decode(refresh_token,
                                 conf.SECRET_KEY,
                                 algorithm=conf.ALGORITHM)
        except:
            raise TokenVerificationFailed
        else:
            # token decoded successfully
            query = db.miserables.insert().values(token=refresh_token)
            await database.execute(query)
        finally:
            return Logoff(status="ok")


class Mutations(graphene.ObjectType):
    requestPassword = RequestPassword.Field()
    getToken = GetJWT.Field()
    refreshToken = RefreshJWT.Field()
    logoff = Logoff.Field()
