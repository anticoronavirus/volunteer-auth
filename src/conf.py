import json
import databases
from starlette.config import Config


config = Config(".env")

AERO_URL = config("AERO_URL", default="https://gate.smsaero.ru/v2")
AERO_LOGIN = config("AERO_LOGIN", default="")
AERO_TOKEN = config("AERO_TOKEN", default="")
TOKEN_EXP_MINUTES = config("TOKEN_EXP_MINUTES", cast=int, default=15)
REFRESH_TOKEN_EXP_MINUTES = config("REFRESH_TOKEN_EXP_MINUTES", cast=int, default=60 * 127)
DATABASE_URL = config("DATABASE_URL", cast=databases.DatabaseURL)
if config("TESTING", cast=bool, default=False):
    DATABASE_URL = DATABASE_URL.replace(database="test_" + DATABASE_URL.database)
TOKEN_SCHEMA_NAME = config("TOKEN_SCHEMA_NAME", default="les")
JWT_SETTINGS = config("JWT_SECRET", cast=json.loads, default='{"type": "HS256", "key": "test"}')
SECRET_KEY = JWT_SETTINGS["key"]
ALGORITHM = JWT_SETTINGS["type"]
