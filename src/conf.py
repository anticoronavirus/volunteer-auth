import os
import json


# FIXME: ENV must be preferred over local config.
AERO_URL = "https://gate.smsaero.ru/v2"
AERO_LOGIN = os.getenv("AERO_LOGIN", "")
AERO_TOKEN = os.getenv("AERO_TOKEN", "")
TOKEN_EXP_MINUTES = int(os.getenv("TOKEN_EXP_MINUTES", 3000))
DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SETTINGS = json.loads(os.getenv("JWT_TOKEN",
                                    '{"type": "HS256", "key": "test"}'))
SECRET_KEY = JWT_SETTINGS["key"]
ALGORITHM = JWT_SETTINGS["type"]

try:
    from local import *
except ImportError:
    pass


