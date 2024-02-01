from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app


def now():
    return datetime.now(ZoneInfo(current_app.config["TIMEZONE"]))
