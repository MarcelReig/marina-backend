# settings.py
import os
from os import environ, path
from dotenv import load_dotenv
import secrets


basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
    MONGO_CLUSTER = os.getenv("ATLAS_URI")
    JWT_KEY = os.getenv("JWT_SECRET")


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False




