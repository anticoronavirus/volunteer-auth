from pydantic import BaseModel, validator
import phonenumbers


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
