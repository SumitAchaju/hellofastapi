import os
from datetime import timedelta

from dotenv import find_dotenv, dotenv_values

env_path = find_dotenv()
config = dotenv_values(env_path)

HOSTNAME = "http://ec2-52-73-151-151.compute-1.amazonaws.com"

BASE_DIR = os.path.abspath(__file__)

DEBUG = False

DATABASE = {"URL": config["DATABASE_URL"], "MANGODB_URL": config["MANGODB_URL"]}

SUPER_USER = {"ACCESS_PASSWORD": config["CREATE_SUPERUSER_PASSWORD"]}

# For Token Authentication
JWT = {
    "ACCESS_TOKEN_EXPIRES": timedelta(minutes=25),
    "REFRESH_TOKEN_EXPIRES": timedelta(days=30),
    "SECRET_KEY": config["SECRET_KEY"],
    "ALGORITHM": "HS256",
}

STATIC = "files"

STATICFILES_DIR = os.path.join(BASE_DIR, STATIC)
