"""Validated forms used by the Part 2 authentication pages."""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
)
#Part 2- login form + email/pw validation

class LoginForm(FlaskForm):
    # validators run on server when validate_on_submit() is called
    # The browser can help with input, but server-side validation is authoritative
    email = StringField(
        "Email address",
        validators=[
            DataRequired(message="Enter the email address for your account."),
            Email(message="Enter a valid email address."),
            Length(max=100, message="Email addresses must be 100 characters or fewer."),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Enter your password.")],
    )
    submit = SubmitField("Sign in")

#Part 2- registration form
class RegisterForm(FlaskForm):
    # Registration fields mirror the personal details stored in user table
    firstname = StringField(
        "First name",
        validators=[
            DataRequired(message="Enter your first name."),
            Length(min=1, max=50, message="Use 1 to 50 characters."),
        ],
    )
    surname = StringField(
        "Surname",
        validators=[
            DataRequired(message="Enter your surname."),
            Length(min=1, max=50, message="Use 1 to 50 characters."),
        ],
    )
    email = StringField(
        "Email address",
        validators=[
            DataRequired(message="Enter your email address."),
            Email(message="Enter a valid email address."),
            Length(max=100, message="Email addresses must be 100 characters or fewer."),
        ],
    )
    role = SelectField(
        "I want to join as a",
        choices=[
            ("supporter", "Supporter"),
            ("fundraiser", "Fundraiser"),
        ],
        validators=[DataRequired(message="Choose Supporter or Fundraiser.")],
    )
    # Password rules are repeated as help text in register.html for user
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Create a password."),
            Length(
                min=10,
                max=255,
                message="Use a password between 10 and 255 characters.",
            ),
            Regexp(
                r"^[A-Za-z0-9]+$",
                message="Use only uppercase letters, lowercase letters, and numbers.",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(message="Enter your password again."),
            EqualTo("password", message="The passwords do not match."),
        ],
    )
    submit = SubmitField("Create account")


# ----- Part 5. Admin Dashboard -----
# Empty form used by admin for action such as approve, delete, etc.
class AdminActionForm(FlaskForm):
    pass
# Dropdown for choosing a project to add to featured section
class FeatureProjectForm(FlaskForm):
    project_id = SelectField('Select a project to feature', coerce=int)
