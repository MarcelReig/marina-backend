"""
Custom validators and validation functions
"""

import re
from flask import current_app


def validate_password(password):
    """Validate password meets requirements
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    min_length = current_app.config['PASSWORD_MIN_LENGTH']
    max_length = current_app.config['PASSWORD_MAX_LENGTH']
    pattern = current_app.config['PASSWORD_PATTERN']
    
    if len(password) < min_length:
        return False, f"Mínimo {min_length} caracteres"
    if len(password) > max_length:
        return False, f"Máximo {max_length} caracteres"
    if not re.match(pattern, password):
        return False, "Debe contener al menos una letra y un número"
    return True, ""


def validate_email(email):
    """Validate email format
    
    Returns:
        bool: True if valid email format
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None
