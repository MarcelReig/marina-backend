"""
Authentication service
"""

import os
from flask import current_app
from flask_jwt_extended import create_access_token, decode_token
from app.models.user import UserModel


class AuthService:
    """Service for handling authentication logic"""
    
    @staticmethod
    def create_token(email, password):
        """Create JWT token for user
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            tuple: (response_dict, status_code)
        """
        if not email or not password:
            return {"msg": "Email and password required"}, 400
        
        # Verify credentials
        user = UserModel.verify_credentials(email, password)
        if not user:
            return {"msg": "Wrong email or password"}, 401
        
        access_token = create_access_token(identity=email)
        response = {
            "access_token": access_token,
            "user": {
                "email": user["email"],
                "username": user["username"],
                "role": user.get("role", current_app.config['ROLE_USER'])
            }
        }
        return response, 200
    
    @staticmethod
    def create_admin_user(email, password, username="admin", role=None):
        """Create admin user with proper authorization checks
        
        Args:
            email (str): Admin email
            password (str): Admin password  
            username (str): Admin display name
            role (str): Admin role (defaults to ROLE_SUPER_ADMIN)
            
        Returns:
            tuple: (response_dict, status_code)
        """
        if role is None:
            role = current_app.config['ROLE_SUPER_ADMIN']
        
        return UserModel.create_user(username, email, password, role)
    
    @staticmethod
    def verify_admin_creation_permission(auth_header=None, creation_key=None):
        """Verify permission to create admin users
        
        Args:
            auth_header (str): Authorization header with JWT
            creation_key (str): Bootstrap creation key
            
        Returns:
            tuple: (is_allowed: bool, error_message: str, status_code: int)
        """
        # Check if this is the first super admin (bootstrap case)
        admin_count = UserModel.count_super_admins()
        
        if admin_count > 0:
            # If admins exist, require admin authentication
            if not auth_header or not auth_header.startswith('Bearer '):
                return False, "Admin authentication required", 401
            
            try:
                token = auth_header.split(' ')[1]
                decoded_token = decode_token(token)
                current_user_email = decoded_token['sub']
                
                user = UserModel.get_user_by_email(current_user_email)
                if not user or user.get("role") != current_app.config['ROLE_SUPER_ADMIN']:
                    return False, "Super admin access required", 403
                    
            except Exception:
                return False, "Invalid authentication", 401
        else:
            # Bootstrap case: require special creation key
            expected_key = os.getenv('ADMIN_CREATION_KEY')
            
            if not expected_key:
                return False, "Admin creation not configured", 500
            
            if not creation_key or creation_key != expected_key:
                return False, "Valid admin creation key required", 401
        
        return True, "", 200
