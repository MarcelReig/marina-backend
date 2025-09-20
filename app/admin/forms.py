"""
Flask-WTF forms for admin interface
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, Optional
from flask import current_app


class UserForm(FlaskForm):
    """Form for creating new users"""
    username = StringField('Username', validators=[
        DataRequired(message="El nombre de usuario es obligatorio"),
        Length(min=2, max=50, message="El nombre debe tener entre 2 y 50 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Email inválido")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="La contraseña es obligatoria"),
        Length(min=8, max=128, message="Debe tener entre 8 y 128 caracteres"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d).+$', message="Debe contener al menos una letra y un número")
    ])
    submit = SubmitField('Add User')


class UpdateUserForm(FlaskForm):
    """Form for updating existing users"""
    username = StringField('Username', validators=[
        DataRequired(message="El nombre de usuario es obligatorio"),
        Length(min=2, max=50, message="El nombre debe tener entre 2 y 50 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio"),
        Email(message="Email inválido")
    ])
    password = PasswordField('Nueva Contraseña', validators=[
        Optional(),
        Length(min=8, max=128, message="Debe tener entre 8 y 128 caracteres"),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d).+$', message="Debe contener al menos una letra y un número")
    ], render_kw={"placeholder": "Dejar vacío para mantener la actual"})
    submit = SubmitField('Actualizar Usuario')
