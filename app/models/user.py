"""
User model and related functions
"""

from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app import mongo
from app.utils.validators import validate_password, validate_email


class UserModel:
    """User model with CRUD operations"""
    
    @staticmethod
    def create_user(username, email, password, role=None):
        """Create a new user
        
        Args:
            username (str): User's display name
            email (str): User's email (unique identifier)
            password (str): Plain text password (will be hashed)
            role (str): User role (defaults to ROLE_ADMIN for React users)
            
        Returns:
            tuple: (result_dict, status_code)
        """
        try:
            # Check if user already exists
            existing_user = mongo.users.find_one({"email": email})
            if existing_user:
                return {"error": "User already exists"}, 400
            
            # Validate password
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                return {"error": f"Password validation failed: {error_msg}"}, 400
            
            # Validate email
            if not validate_email(email):
                return {"error": "Invalid email format"}, 400
            
            # Set default role
            if role is None:
                role = current_app.config['ROLE_ADMIN']
            
            # Create user with hashed password
            hashed_password = generate_password_hash(password)
            result = mongo.users.insert_one({
                "username": username,
                "email": email,
                "password": hashed_password,
                "role": role,
                "created_at": "now"
            })
            
            return {
                "message": "User created successfully",
                "user_id": str(result.inserted_id),
                "username": username,
                "email": email,
                "role": role
            }, 201
            
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def verify_credentials(email, password):
        """Verify user credentials
        
        Args:
            email (str): User's email
            password (str): Plain text password
            
        Returns:
            dict or None: User document if credentials are valid, None otherwise
        """
        try:
            user = mongo.users.find_one({"email": email})
            if not user:
                return None
            
            if check_password_hash(user["password"], password):
                return user
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email
        
        Args:
            email (str): User's email
            
        Returns:
            dict or None: User document if found
        """
        return mongo.users.find_one({"email": email})
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID
        
        Args:
            user_id (str): User's ObjectId as string
            
        Returns:
            dict or None: User document if found
        """
        from bson.objectid import ObjectId
        try:
            return mongo.users.find_one({"_id": ObjectId(user_id)})
        except:
            return None
    
    @staticmethod
    def update_user(user_id, update_data):
        """Update user information
        
        Args:
            user_id (str): User's ObjectId as string
            update_data (dict): Fields to update
            
        Returns:
            bool: True if update successful
        """
        from bson.objectid import ObjectId
        try:
            # Hash password if provided
            if 'password' in update_data:
                update_data['password'] = generate_password_hash(update_data['password'])
            
            result = mongo.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            # Consider matched but not modified as success (no-op updates)
            return result.matched_count > 0
        except:
            return False
    
    @staticmethod
    def delete_user(user_id):
        """Delete user
        
        Args:
            user_id (str): User's ObjectId as string
            
        Returns:
            bool: True if deletion successful
        """
        from bson.objectid import ObjectId
        try:
            result = mongo.users.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except:
            return False
    
    @staticmethod
    def get_all_users():
        """Get all users
        
        Returns:
            pymongo.cursor.Cursor: All users
        """
        return mongo.users.find()
    
    @staticmethod
    def count_super_admins():
        """Count super admin users
        
        Returns:
            int: Number of super admin users
        """
        return mongo.users.count_documents({"role": current_app.config['ROLE_SUPER_ADMIN']})
