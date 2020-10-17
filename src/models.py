import uuid
from datetime import datetime

from pydantic import BaseModel


class Volunteer(BaseModel):
    uid: uuid.UUID
    fname: str = ""
    mname: str = ""
    lname: str = ""
    phone: str
    email: str = ""
    role: str = "volunteer"
    password: str = ""
    password_expires_at: datetime = None
