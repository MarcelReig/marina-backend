"""
Application configuration settings
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', '6+8zZ69dzChLZCU9h=XE+Gren}fnRV')
    MONGO_CLUSTER = os.getenv('ATLAS_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET')
    
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
