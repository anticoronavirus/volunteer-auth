import logging
import random
from datetime import datetime, timedelta
from typing import Union
from uuid import UUID

import conf
import db
import graphene
import jwt
from auth import (Token, authenticate_user, create_access_token,
                  get_password_hash, verify_password)
from dates import aware_now
from db import database
from graphql import GraphQLError
from queries import (add_password, create_volunteer, flush_password,
                     get_last_volunteer_passwords, get_volunteer, is_blacklisted,
                     get_last_login_attempts, log_login_attempt)
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
    timeout = graphene.DateTime()

    @staticmethod
    async def mutate(root, info, phone):
        parsed_phone = Phone(phone=phone).phone

        attempts = await get_last_volunteer_passwords(parsed_phone, 3)
        last_attempt = attempts[0]
        volunteer_id = last_attempt['uid']
        if not volunteer_id:
            volunteer_id = await create_volunteer(parsed_phone)
        elif last_attempt["ctime"]:
            timeout_end = last_attempt["ctime"] + timedelta(minutes=1)
            if timeout_end >= aware_now():
                return RequestPassword(
                    status="failed",
                    timeout=timeout_end,
                )
            if (
                len(attempts) >= 3
                and attempts[-1]["ctime"] >= aware_now() - timedelta(minutes=5)
            ):
                return RequestPassword(
                    status="failed",
                    timeout=last_attempt["ctime"] + timedelta(minutes=30),
                )

        password = make_password()
        password_hash = get_password_hash(password)
        await add_password(volunteer_id, password_hash)
        message = await aero.send_bool(
            phone,
            "NEWS",
            f"{password} is your memedic volunteer code <3",
        )
        if not message:
            return RequestPassword(status="failed")
        else:
            return RequestPassword(status="ok")


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

    timeout = graphene.DateTime()

    @staticmethod
    async def mutate(root, info, phone, password):
        phone164 = Phone(phone=phone).phone
        await log_login_attempt(phone164)
        user_passwords = await get_last_volunteer_passwords(phone164, 1)

        if not user_passwords:
            raise GraphQLError("Нет такого пользователя.")

        attempts = await get_last_login_attempts(phone164, 5)
        if (
            len(attempts) >= 5
            and attempts[0]["ctime"] > aware_now() - timedelta(minutes=5)
        ):
            return GetJWT(
                timeout=attempts[0]["ctime"] + timedelta(minutes=30),
                authenticated=False
            )

        user_with_password = user_passwords[0]
        if (
                user_with_password["expires_at"] is None
                or user_with_password["expires_at"] <= aware_now()
        ):
            raise GraphQLError("Пароль просрочен. Запросите новый.")
        elif not verify_password(password, user_with_password['password']):
            raise GraphQLError("Неверный пароль")

        await flush_password(user_with_password)
        return GetJWT.create_tokens(info, user_with_password["volunteer_id"])


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


class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))

    def resolve_hello(self, info, name):
        return "Hello " + name


class Mutations(graphene.ObjectType):
    requestPassword = RequestPassword.Field()
    getToken = GetJWT.Field()
    refreshToken = RefreshJWT.Field()
    logoff = Logoff.Field()
