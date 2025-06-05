import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

HOSTNAME = "http://127.0.0.1:80"

BASE_DIR = os.path.abspath(__file__)

DEBUG = False

DATABASE = {"URL": os.getenv("DATABASE_URL"), "MANGODB_URL": os.getenv("MANGODB_URL")}

SUPER_USER = {"ACCESS_PASSWORD": os.getenv("CREATE_SUPERUSER_PASSWORD")}

# For Token Authentication
JWT = {
    "ACCESS_TOKEN_EXPIRES": timedelta(minutes=25),
    "REFRESH_TOKEN_EXPIRES": timedelta(days=30),
    "SECRET_KEY": os.getenv("SECRET_KEY"),
    "ALGORITHM": "HS256",
}

STATIC = "files"

STATICFILES_DIR = os.path.join(BASE_DIR, STATIC)
