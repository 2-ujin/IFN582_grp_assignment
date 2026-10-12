"""Authentication routes and reusable access-control decorators."""

from functools import wraps
from urllib.parse import urlsplit

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from MySQLdb import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from . import database, login_manager
from .forms import LoginForm, RegisterForm
from .models import AccountStatus, User


main = Blueprint("main", __name__)


# login fields for the marker. Each account is seeded in
# database.sql that stores Werkzeug hashes, while this list supplies the
# matching readable assessment passwords to login.html
TEST_LOGIN_ACCOUNTS = (
    {
        "role": "Fundraiser",
        "email": "queenie.work@gmail.com",
        "password": "artistone",
    },
    {
        "role": "Fundraiser",
        "email": "marcokhc22@gmail.com",
        "password": "artisttwo",
    },
    {
        "role": "Supporter",
        "email": "m.brant@gmail.com",
        "password": "supporterone",
    },
    {
        "role": "Supporter",
        "email": "ebao@hotmail.com",
        "password": "supportertwo",
    },
    {
        "role": "Administrator",
        "email": "admin2@makeartsfund.com",
        "password": "adminone",
    },
    {
        "role": "Administrator",
        "email": "admin23@makeartsfund.com",
        "password": "admintwo",
    },
)

#Part 2- reload singed in user from database (user loader)
@login_manager.user_loader
def load_user(user_id):
    """Reload a session user from the account and role tables."""
    return User.get_by_id(user_id)

#Part 2- confirm post login redirects stay on same site
def _safe_local_url(target):
    """Allow only a relative same-site destination from the login redirect."""
    if not target:
        return False
    # Reject absolute or protocol-relative URLs so that a login cannot redirect a user
    # to another site after authentication
    parsed = urlsplit(target)
    return (
        not parsed.scheme
        and not parsed.netloc
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
        and not any(ord(character) < 32 for character in target)
    )

#Part 2- role access control decorator
def _role_required(required_role):
    """Build a login-protected decorator for a single account role.

    Use the returned decorators on routes that belong to one role. Authentication
    is checked first; then a mismatched role receives the shared 403 page.
    """

    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if getattr(current_user, "role", None) != required_role:
                abort(403)
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


admin_required = _role_required("Administrator")
fundraiser_required = _role_required("Fundraiser")
supporter_required = _role_required("Supporter")

#Part 2- end session check for suspended/ deactivated accounts
@main.before_app_request
def end_inactive_sessions():
    """Revoke an existing session if its account was suspended or deactivated."""
    # status reloaded from MySQL for each request by Flask-Login's
    # user_loader, so an administrator's status change can take effect mid-session
    if current_user.is_authenticated and not current_user.is_active:
        status = current_user.accountStatus
        logout_user()
        if status is AccountStatus.SUSPENDED:
            flash("This account is suspended. Please contact a platform administrator.", "danger")
        else:
            flash("This account is deactivated. Please contact support if you need assistance.", "danger")

#Part 2- temporary database check / route
@main.route("/")
def index():
    """Temporary database check; Part 3 should replace this route with the home page."""
    cursor = database.connection.cursor()
    try:
        cursor.execute("SELECT projectName FROM project")
        projects = cursor.fetchall()
    finally:
        cursor.close()
    return str(projects)

#Part 2- login route
@main.route("/login", methods=["GET", "POST"])
def login():
    """Display the login form and authenticate a submitted account."""
    # An already-authenticated user no need to submit the form again
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        # Normalise whitespace around email before looking up the account
        email = form.email.data.strip()
        user = User.get_by_email(email)

        # Keep the response generic for unknown emails and incorrect passwords
        if user is None or not check_password_hash(user.password, form.password.data):
            flash("Email or password is incorrect.", "danger")
        elif user.accountStatus is AccountStatus.SUSPENDED:
            flash("This account is suspended. Please contact a platform administrator.", "danger")
        elif user.accountStatus is AccountStatus.DEACTIVATED:
            flash("This account is deactivated. Please contact support if you need assistance.", "danger")
        elif not login_user(user):
            # Flask-Login also checks User.is_active, which only accepts Active.
            flash("This account cannot sign in at this time.", "danger")
        else:
            flash(f"Welcome back, {user.firstname}.", "success")
            next_url = request.args.get("next", "")
            # Return to the requested page only when it is a safe local URL.
            if _safe_local_url(next_url):
                return redirect(next_url)
            return redirect(url_for("main.index"))

    return render_template(
        "login.html",
        form=form,
        test_accounts=TEST_LOGIN_ACCOUNTS,
    )

#Part 2- registration route
@main.route("/register", methods=["GET", "POST"])
def register():
    """Validate a new account and create its user and role rows together."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Store a trimmed, lowercase email for consistent unique-account check
        email = form.email.data.strip().lower()
        if User.get_by_email(email) is not None:
            form.email.errors.append("An account already uses this email address.")
        else:
            role_table = {
                "fundraiser": "artist",
                "supporter": "supporter",
            }.get(form.role.data)
            # fixed form choices, but reject any unexpected value explicitly
            if role_table is None:
                abort(400)

            cursor = database.connection.cursor()
            try:
                # Create the shared account row, then its role row. Both inserts are
                # committed together so registration cannot leave a half-account
                cursor.execute(
                    """
                    INSERT INTO user
                        (firstname, surname, email, password, accountStatus)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        form.firstname.data.strip(),
                        form.surname.data.strip(),
                        email,
                        generate_password_hash(form.password.data),
                        AccountStatus.ACTIVE.value,
                    ),
                )
                new_user_id = cursor.lastrowid
                # role_table can only be one of the two fixed names above.
                cursor.execute(
                    f"INSERT INTO {role_table} (userId) VALUES (%s)",
                    (new_user_id,),
                )
                database.connection.commit()
            except IntegrityError:
                # The unique email constraint is the final protection if two
                # registrations race after the earlier lookup
                database.connection.rollback()
                form.email.errors.append("An account already uses this email address.")
            except Exception:
                # Roll back either insert if the database operation fails
                database.connection.rollback()
                current_app.logger.exception("Account registration failed.")
                flash("We could not create your account. Please try again.", "danger")
            else:
                # Registration succeeded, load the complete role-aware user
                # object, then start a session to sign in new user
                user = User.get_by_id(new_user_id)
                if user is None or not login_user(user):
                    flash("Your account was created. Please sign in to continue.", "success")
                    return redirect(url_for("main.login"))
                flash("Your account is ready. Welcome to MakeArtsFund.", "success")
                return redirect(url_for("main.index"))
            finally:
                cursor.close()

    return render_template("register.html", form=form)

#Part 2- logout route
@main.route("/logout", methods=["POST"])
@login_required
def logout():
    """End the current login session; POST plus CSRF prevents a forged logout."""
    logout_user()
    flash("You have signed out.", "info")
    return redirect(url_for("main.index"))
