"""
Marina Portfolio Application

A professional Flask application with clean architecture:
- API endpoints for React frontend
- Admin panel for user management
- JWT authentication with role-based access
- Cloudinary integration for image management
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
import cloudinary
import os
from dotenv import load_dotenv

load_dotenv()

# Global variables for database and JWT
mongo = None
jwt = None


def create_app(config_name='development'):
    """Application factory pattern"""
    # Configure Flask to find static files and templates in the correct locations
    app = Flask(__name__, 
                static_folder='../static',  # Static files in project root
                template_folder='templates')  # Templates in app/templates
    
    # Load configuration
    if config_name == 'development':
        from .config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    elif config_name == 'production':
        from .config import ProductionConfig
        app.config.from_object(ProductionConfig)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def init_extensions(app):
    """Initialize Flask extensions"""
    global mongo, jwt
    
    # CORS
    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "https://marina-ibarra.netlify.app",
                ]
            }
        },
    )
    
    # JWT
    jwt = JWTManager(app)
    
    # Configure JWT to use cookies
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable for simplicity
    
    # MongoDB
    cluster = MongoClient(app.config['MONGO_CLUSTER'])
    mongo = cluster["marina_db"]
    
    # Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )


def register_blueprints(app):
    """Register application blueprints"""
    
    # API blueprints (for React)
    from .api.auth import auth_bp
    from .api.portfolio import portfolio_bp
    from .api.store import store_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(portfolio_bp, url_prefix='/api')
    app.register_blueprint(store_bp, url_prefix='/api')
    
    # Admin blueprints (for Flask templates)
    from .admin.routes import admin_bp
    app.register_blueprint(admin_bp)


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import jsonify, request
        message = {"message": f"Resource Not Found: {request.url}", "status": 404}
        return jsonify(message), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import jsonify
        message = {"message": "Internal server error", "status": 500}
        return jsonify(message), 500
