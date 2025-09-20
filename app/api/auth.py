"""
Authentication API endpoints
"""

from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.utils.validators import validate_password, validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/token', methods=['POST'])
def create_token():
    """Create JWT token for user authentication"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    email = data.get("email")
    password = data.get("password")
    
    response, status_code = AuthService.create_token(email, password)
    return jsonify(response), status_code


@auth_bp.route('/create-admin', methods=['POST'])
def create_admin():
    """Create admin user with proper authorization"""
    
    # Get authorization data
    auth_header = request.headers.get('Authorization')
    creation_key = request.headers.get('X-Admin-Creation-Key')
    
    # Verify permission
    is_allowed, error_msg, status_code = AuthService.verify_admin_creation_permission(
        auth_header, creation_key
    )
    
    if not is_allowed:
        return jsonify({"error": error_msg}), status_code
    
    # Validate request data
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON data required"}), 400
    
    email = data.get("email")
    password = data.get("password")
    username = data.get("username", "admin")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    # Validate inputs
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({"error": f"Password validation failed: {error_msg}"}), 400
    
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Create admin user
    result, status_code = AuthService.create_admin_user(email, password, username)
    return jsonify(result), status_code
