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
            phone = phonenumbers.format_number(
                number,
                phonenumbers.PhoneNumberFormat.E164)
            if len(phone) != 12:
                raise ValueError("Not a mobile phone")
            return phone
