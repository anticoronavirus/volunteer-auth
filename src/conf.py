import os


# FIXME: ENV must be preferred over local config.
AERO_URL = "https://gate.smsaero.ru/v2"
AERO_LOGIN = os.getenv("AERO_LOGIN", "")
AERO_TOKEN = os.getenv("AERO_TOKEN", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
TOKEN_EXP_MINUTES = int(os.getenv("TOKEN_EXP_MINUTES", 3000))
DATABASE_URL = os.getenv("DATABASE_URL", "")


try:
    from local import *
except ImportError:
    pass


