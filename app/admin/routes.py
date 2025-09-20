"""
Admin interface routes (Flask templates)
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_jwt_extended import get_jwt_identity
from bson.objectid import ObjectId
from bson import json_util
from flask import Response

from app.utils.decorators import super_admin_required
from app.models.user import UserModel
from app.admin.forms import UserForm, UpdateUserForm

admin_bp = Blueprint('admin', __name__)


@admin_bp.app_context_processor
def inject_current_username():
    """Inject current username into templates.
    Falls back to fetching by email if username missing in session.
    """
    from flask import session as flask_session
    username = flask_session.get('username')
    if not username:
        email = flask_session.get('user_email')
        if email:
            user = UserModel.get_user_by_email(email)
            if user:
                username = user.get('username')
                if username:
                    flask_session['username'] = username
    return {"current_username": username}


@admin_bp.route('/')
def index():
    """Landing page - redirects to login template"""
    return render_template("login.html")


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login endpoint for Flask admin panel"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Email y contraseña son requeridos", "error")
            return render_template("login.html")
        
        # Verify credentials using the user model
        from app.models.user import UserModel
        user = UserModel.verify_credentials(email, password)
        
        if user and user.get('role') == current_app.config['ROLE_SUPER_ADMIN']:
            # Store user info in session
            session['user_email'] = email
            session['user_role'] = user.get('role')
            session['username'] = user.get('username')

            # Create JWT token and store in secure cookie
            from flask_jwt_extended import create_access_token
            access_token = create_access_token(identity=email)

            # Create response and set JWT in httponly cookie
            response = redirect(url_for('admin.portfolio_manager'))
            response.set_cookie('access_token_cookie', access_token,
                              httponly=True, secure=False, max_age=3600, path='/')  # 1 hour

            return response
        else:
            flash("Credenciales inválidas o permisos insuficientes", "error")
            return render_template("login.html")
    
    return render_template("login.html")


@admin_bp.route('/logout')
def logout():
    """Logout endpoint - clear JWT cookie"""
    response = redirect(url_for('admin.index'))
    response.set_cookie('access_token_cookie', '', expires=0)
    # Clear session to ensure admin access is removed
    session.clear()
    flash("Sesión cerrada exitosamente", "success")
    return response


@admin_bp.route('/manager', methods=['GET', 'POST'])
@super_admin_required
def portfolio_manager():
    """Admin dashboard for user management (super admin only)"""
    # Get current user info from session (admin panel uses session)
    current_user_email = session.get('user_email')
    current_user = UserModel.get_user_by_email(current_user_email) if current_user_email else None
    
    form = UserForm()
    
    # Handle user creation
    if form.validate_on_submit():
        try:
            result, status_code = UserModel.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            if status_code == 201:
                flash(f"Usuario '{form.username.data}' creado exitosamente", "success")
                return redirect(url_for("admin.portfolio_manager"))
            else:
                flash(result.get("error", "Error al crear usuario"), "error")
                
        except Exception as e:
            flash(f"Error al crear usuario: {str(e)}", "error")
    
    # Show validation errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
    
    users = UserModel.get_all_users()
    return render_template("manager.html", users=users, form=form)


@admin_bp.route('/update/<id>', methods=['GET', 'POST'])
@super_admin_required
def update_user(id):
    """Update user form and handler (super admin only)"""
    
    # Get user to update
    user = UserModel.get_user_by_id(id)
    if not user:
        flash("Usuario no encontrado", "error")
        return redirect(url_for("admin.portfolio_manager"))
    
    form = UpdateUserForm()
    
    if form.validate_on_submit():
        try:
            # Check for email conflicts (except current user)
            existing_user = UserModel.get_user_by_email(form.email.data)
            if existing_user and str(existing_user["_id"]) != id:
                flash("Ya existe otro usuario con ese email", "error")
            else:
                # Prepare update data
                update_data = {
                    "username": form.username.data,
                    "email": form.email.data
                }
                
                # Only update password if provided
                if form.password.data and form.password.data.strip():
                    update_data["password"] = form.password.data
                
                # Update user
                success = UserModel.update_user(id, update_data)
                if success:
                    # If the current logged-in user updated their own profile, sync session
                    if 'user_email' in session and session['user_email'] == user['email']:
                        session['user_email'] = update_data.get('email', user['email'])
                        session['username'] = update_data.get('username', user['username'])
                    flash(f"Usuario '{form.username.data}' actualizado exitosamente", "success")
                    return redirect(url_for("admin.portfolio_manager"))
                else:
                    flash("Error al actualizar usuario", "error")
                    
        except Exception as e:
            flash(f"Error al actualizar usuario: {str(e)}", "error")
    
    # Pre-fill form with current data
    if request.method == "GET":
        form.username.data = user["username"]
        form.email.data = user["email"]
    
    # Show validation errors
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "error")
    
    return render_template("update.html", user=user, form=form)


@admin_bp.route('/delete/<id>', methods=['DELETE', 'GET'])
@super_admin_required
def delete_user(id):
    """Delete user (super admin only)"""
    success = UserModel.delete_user(id)
    if success:
        flash(f"Usuario eliminado exitosamente", "success")
    else:
        flash("Error al eliminar usuario", "error")
    
    return redirect(url_for("admin.portfolio_manager"))


# API endpoints for admin (for consistency with old structure)
@admin_bp.route('/users', methods=['GET'])
@super_admin_required
def get_users():
    """Get all users as JSON (super admin only)"""
    users = UserModel.get_all_users()
    response = json_util.dumps(users)
    return Response(response, mimetype="application/json")


@admin_bp.route('/users/<id>', methods=['GET'])
@super_admin_required
def get_user(id):
    """Get single user as JSON (super admin only)"""
    user = UserModel.get_user_by_id(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    response = json_util.dumps(user)
    return Response(response, mimetype="application/json")
