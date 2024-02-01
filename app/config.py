import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
CLIENT_ID = os.getenv("OPENID_CLIENT_ID")
CLIENT_SECRET = os.getenv("OPENID_CLIENT_SECRET")

TIMEZONE = "Asia/Tokyo"
