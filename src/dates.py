import pytz
import datetime


def aware_now():
    return datetime.datetime.now(pytz.UTC)
