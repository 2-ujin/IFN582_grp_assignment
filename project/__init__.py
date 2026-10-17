#Application factory and shared Flask extensions for MakeArtsFund

from datetime import date
import os
import secrets

from flask import Flask, render_template
from flask_login import AnonymousUserMixin, LoginManager, current_user
# Use mysqlclient from the supplied requirements on a clean installation.
# Preserve compatibility with existing local environments using PyMySQL.
try:
    import MySQLdb
except ModuleNotFoundError:
    import pymysql
    pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFError, CSRFProtect


database = MySQL()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    """Create the Flask app and connect the extensions used by every page.

    Keeping setup here means route files can import shared services without
    creating a second database connection or login manager.
    """
    app = Flask(__name__)
    # Environment variables keep machine-specific database credentials and
    # the session signing key out of the source code. Defaults are for local use.
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
        MYSQL_HOST=os.environ.get("MYSQL_HOST", "localhost"),
        MYSQL_USER=os.environ.get("MYSQL_USER", "root"),
        MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", "123456"),
        MYSQL_DB=os.environ.get("MYSQL_DB", "maf"),
        MYSQL_CURSORCLASS="DictCursor",
        WTF_CSRF_TIME_LIMIT=3600,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=5* 1024 *1024,
    )
    if test_config:
        # A caller can override settings before extensions are initialised.
        app.config.update(test_config)

    
    # Debug mode is off so detailed error pages are never shown to users
    app.debug = False

    database.init_app(app)
    login_manager.init_app(app, add_context_processor=False)
    csrf.init_app(app)

    # Flask-Login sends anonymous users here when a protected route is opened.
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please sign in to access that page."
    login_manager.login_message_category = "info"

    from .views import main
    from .management import management_bp

    app.register_blueprint(main)
    app.register_blueprint(management_bp)

    @app.context_processor
    def inject_current_year():
        # Makes the current year available to the shared footer in base.html.
        # Keep the user lazy so the 500 handler can render without retrying a failed DB lookup.
        return {"current_year": date.today().year, "current_user": current_user}

    @app.errorhandler(CSRFError)
    def invalid_form_token(_error):
        return render_template(
            "error.html", status_code=400,
            page_title="Please reload the form",
            page_message="The form session expired or its security token is missing. Reload the original page and submit again.",
        ), 400

    # These handlers show a consistent branded page instead of a raw server page.
    @app.errorhandler(403)
    def forbidden(_error):
        return (
            render_template(
                "error.html",
                status_code=403,
                page_title="Access denied",
                page_message="You do not have permission to view this page.",
            ),
            403,
        )
#Part 2- 404 handler
    @app.errorhandler(404)
    def page_not_found(_error):
        return (
            render_template(
                "error.html",
                status_code=404,
                page_title="Whoops! Page not found :(",
                page_message="The page you are looking for cannot be found on this server",
            ),
            404,
        )
#Part 2- 500 handler
    @app.errorhandler(500)
    def internal_server_error(_error):
        return (
            render_template(
                "error.html",
                current_user=AnonymousUserMixin(),  # Render even if loading the session user failed.
                status_code=500,
                page_title="Something went wrong",
                page_message="Sorry, your request cannot be completed. Please try again shortly.",
            ),
            500,
        )

    return app
