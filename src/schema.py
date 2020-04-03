from pydantic import BaseModel, validator
import phonenumbers
from auth import Token
from typing import Literal


class Phone(BaseModel):
    phone: str

    @validator("phone")
    def validate_phone(cls, v):
        try:
            number = phonenumbers.parse(v, "RU")
        except phonenumbers.NumberParseException as e:
            raise ValueError("Could not parse phone")
        else:
            return phonenumbers.format_number(
                number,
                phonenumbers.PhoneNumberFormat.E164)


class Registration(BaseModel):
    status: Literal["exists", "failed", "ok"]
    token: Token = None
    code_: str = None

