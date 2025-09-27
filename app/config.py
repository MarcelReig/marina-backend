"""
Application configuration settings
"""

import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""
    # Use env SECRET_KEY in prod; otherwise generate a strong random key
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(32)
    MONGO_CLUSTER = os.getenv('ATLAS_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET')
    # Increase access token lifetime to reduce unexpected logouts
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # WTF Forms
    WTF_CSRF_ENABLED = True
    
    # Password policy
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    PASSWORD_PATTERN = r'^(?=.*[A-Za-z])(?=.*\d).+$'  # At least one letter and one number
    
    # Role hierarchy
    ROLE_USER = "user"           # Public users - read only
    ROLE_ADMIN = "admin"         # React app users - content management
    ROLE_SUPER_ADMIN = "super_admin"  # Flask app access - user management
    
    # Admin creation
    ADMIN_CREATION_KEY = os.getenv('ADMIN_CREATION_KEY')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
