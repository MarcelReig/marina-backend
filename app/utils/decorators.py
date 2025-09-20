"""
Authentication and authorization decorators
"""

from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import mongo


def super_admin_required(f):
    """Decorator for Flask app endpoints - requires super_admin role"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, request, redirect, url_for, flash
        
        # Try session authentication first (simpler and more reliable)
        if 'user_email' in session:
            try:
                user_email = session['user_email']
                user = mongo.users.find_one({"email": user_email})
                
                if user and user.get("role") == current_app.config['ROLE_SUPER_ADMIN']:
                    return f(*args, **kwargs)
                else:
                    session.clear()  # Clear invalid session
                    flash("Acceso denegado: Se requiere rol super admin", "error")
                    return redirect(url_for('admin.index'))
            except Exception as e:
                session.clear()  # Clear broken session
                flash(f"Error de autenticación", "error")
                return redirect(url_for('admin.index'))
        
        # No session found, redirect to login
        flash("Por favor, inicie sesión para acceder", "info")
        return redirect(url_for('admin.index'))
    
    return decorated_function


def admin_required(f):
    """Decorator for React app content management - requires admin or super_admin"""
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_email = get_jwt_identity()
            user = mongo.users.find_one({"email": current_user_email})
            
            allowed_roles = [
                current_app.config['ROLE_ADMIN'], 
                current_app.config['ROLE_SUPER_ADMIN']
            ]
            
            if not user or user.get("role") not in allowed_roles:
                return jsonify({"error": "Admin access required"}), 403
                
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated_function


def user_required(f):
    """Decorator for authenticated users - any valid user"""
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            current_user_email = get_jwt_identity()
            user = mongo.users.find_one({"email": current_user_email})
            
            if not user:
                return jsonify({"error": "Valid user account required"}), 403
                
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated_function
