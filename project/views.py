"""Application routes for authentication, fundraising pages, and administration."""

from functools import wraps
from urllib.parse import urlsplit

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from MySQLdb import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from . import database, login_manager
from .forms import AdminActionForm, FeatureProjectForm, LoginForm, RegisterForm
from .models import (
    AccountStatus,
    User,
    add_to_featured,
    change_project_status,
    get_campaign_stats,
    get_creator_count,
    get_feature_candidates,
    get_featured_projects,
    get_pending_projects,
    get_report_stats,
    get_reviewed_projects,
    get_supporter_count,
    remove_from_featured,
    review_project_approval,
    soft_delete_project,
)

# Main routes use extensions initialized by the shared app factory.
main = Blueprint("main", __name__)


# ----- Part 2: Authentication and shared access control -----

@login_manager.user_loader
def load_user(user_id):
    """Reload the account on each request so role and status changes take effect."""
    return User.get_by_id(user_id)


def _safe_local_url(target):
    """Only allow same-site redirects after successful authentication."""
    if not target:
        return False
    parsed = urlsplit(target)
    return (
        not parsed.scheme
        and not parsed.netloc
        and target.startswith("/")
        and not target.startswith("//")
        and "\\" not in target
        and not any(ord(character) < 32 for character in target)
    )


def _role_required(required_role):
    """Require authentication and the single role assigned to the account."""

    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            # Treat a missing role as unauthorized instead of raising an error.
            if getattr(current_user, "role", None) != required_role:
                abort(403)
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


admin_required = _role_required("Administrator")
fundraiser_required = _role_required("Fundraiser")
supporter_required = _role_required("Supporter")


@main.before_app_request
def end_inactive_sessions():
    """End an existing session if the account was suspended or deactivated."""
    if current_user.is_authenticated and not current_user.is_active:
        # Flask-Login reloads the user's current status before this hook runs.
        was_suspended = current_user.is_suspended
        logout_user()
        if was_suspended:
            flash(
                "This account is suspended. Please contact a platform administrator.",
                "danger",
            )
        else:
            flash(
                "This account is deactivated. Please contact support if you need assistance.",
                "danger",
            )


# These six assessment credentials are displayed on the login page. Their
# matching password hashes are assigned to the same email addresses in database.sql.
TEST_LOGIN_ACCOUNTS = (
    {"role": "Fundraiser", "email": "queenie.work@gmail.com", "password": "artistone"},
    {"role": "Fundraiser", "email": "marcokhc22@gmail.com", "password": "artisttwo"},
    {"role": "Supporter", "email": "m.brant@gmail.com", "password": "supporterone"},
    {"role": "Supporter", "email": "ebao@hotmail.com", "password": "supportertwo"},
    {"role": "Administrator", "email": "admin2@makeartsfund.com", "password": "adminone"},
    {"role": "Administrator", "email": "admin23@makeartsfund.com", "password": "admintwo"},
)


@main.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate with email/password and reject inactive account statuses."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.get_by_email(email)

        # Use one message for unknown accounts and incorrect passwords so the
        # form does not reveal whether an email address is registered.
        if user is None or not check_password_hash(user.password, form.password.data):
            flash("Email or password is incorrect.", "danger")
        elif user.is_suspended:
            flash(
                "This account is suspended. Please contact a platform administrator.",
                "danger",
            )
        elif user.is_deactivated:
            flash(
                "This account is deactivated. Please contact support if you need assistance.",
                "danger",
            )
        elif not login_user(user):
            flash("This account cannot sign in at this time.", "danger")
        else:
            flash("Welcome back, {}.".format(user.firstname), "success")
            next_url = request.args.get("next", "")
            if _safe_local_url(next_url):
                return redirect(next_url)
            return redirect(url_for("main.index"))

    return render_template(
        "login.html",
        form=form,
        test_accounts=TEST_LOGIN_ACCOUNTS,
    )


@main.route("/register", methods=["GET", "POST"])
def register():
    """Create one shared user row and exactly one selected role row."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.get_by_email(email) is not None:
            form.email.errors.append("An account already uses this email address.")
        else:
            # Only the two public registration choices can select a role table.
            role_table = {
                "fundraiser": "artist",
                "supporter": "supporter",
            }.get(form.role.data)
            if role_table is None:
                abort(400)

            cursor = database.connection.cursor()
            try:
                # Create both rows in one transaction to avoid half-created accounts.
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
                cursor.execute(
                    "INSERT INTO {} (userId) VALUES (%s)".format(role_table),
                    (new_user_id,),
                )
                database.connection.commit()
            except IntegrityError:
                database.connection.rollback()
                form.email.errors.append("An account already uses this email address.")
            except Exception:
                database.connection.rollback()
                current_app.logger.exception("Account registration failed.")
                flash("We could not create your account. Please try again.", "danger")
            else:
                user = User.get_by_id(new_user_id)
                if user is None or not login_user(user):
                    flash("Your account was created. Please sign in to continue.", "success")
                    return redirect(url_for("main.login"))
                flash("Your account is ready. Welcome to MakeArtsFund.", "success")
                return redirect(url_for("main.index"))
            finally:
                cursor.close()

    return render_template("register.html", form=form)


@main.route("/logout", methods=["POST"])
@login_required
def logout():
    """End the current session; POST plus CSRF protects the action."""
    logout_user()
    flash("You have signed out.", "info")
    return redirect(url_for("main.index"))


# ----- Part 3. Home page -----
# Keep the temporary Part 2 database check at its own path. The Part 3 home
# page owns `/`, so both pieces remain available without a duplicate route.
@main.route("/db-check")
def database_check():
    """Return a small query result for checking the local database connection."""
    cursor = database.connection.cursor()
    try:
        cursor.execute("SELECT projectName FROM project")
        projects = cursor.fetchall()
    finally:
        cursor.close()
    return str(projects)


@main.route('/')
def index():
    # Load the featured projects and success stories for the home page.
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT p.*, CONCAT(u.firstname, ' ', u.surname) AS artistName,
        c.categoryName,
        IFNULL(SUM(d.amount), 0) AS totalRaised,
        ROUND(IFNULL(SUM(d.amount), 0) / p.goal * 100) AS progressPercentage,
        GREATEST(DATEDIFF(p.deadline, CURDATE()), 0) AS daysRemaining         
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        LEFT JOIN donation d ON p.projectId = d.projectId           
        WHERE p.featured = TRUE 
        GROUP BY p.projectId
        ORDER BY p.projectId ASC           
        LIMIT 3
                         
    """)
    projects = cursor.fetchall()

    cursor.execute("""
        SELECT p.*, CONCAT(u.firstname, ' ', u.surname) AS artistName,
               c.categoryName
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        WHERE p.successStoryFeatured = TRUE
        ORDER BY p.projectId ASC
        LIMIT 2
    """)
    success_stories = cursor.fetchall()
    cursor.close()

    # Keep the existing Part 3 home page and its template intact.
    return render_template('home.html', projects=projects, success_stories=success_stories)
    

# ----- Part 3. Fundraiser details and donation page -----
@main.route('/donation')
@main.route('/donation/<int:project_id>')
def project_detail(project_id = 1):
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT p.*, CONCAT(u.firstname, ' ', u.surname) AS artistName,
        c.categoryName,
        IFNULL(SUM(d.amount), 0) AS totalRaised,
        ROUND(IFNULL(SUM(d.amount), 0) / p.goal * 100) AS progressPercentage,
        GREATEST(DATEDIFF(p.deadline, CURDATE()), 0) AS daysRemaining         
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        LEFT JOIN donation d ON p.projectId = d.projectId           
        WHERE p.projectId = %s
        GROUP BY p.projectId
                         
    """,(project_id,))
    project_data = cursor.fetchone()
# update project
    cursor.execute("""
        SELECT pu.*, MIN(im.imagePath) AS imagePath
        FROM projectUpdate pu
        LEFT JOIN image im ON pu.updateId = im.updateId
        WHERE pu.projectId = %s
        GROUP BY pu.updateId
        ORDER BY pu.publishedDate DESC
    """, (project_id,))
    updates = cursor.fetchall()

#supporter message  
    cursor.execute("""
            SELECT sm.*, d.amount, CONCAT(u.firstname, ' ', u.surname) AS donorName
            FROM supporterMessage sm
            JOIN donation d ON sm.donationId = d.donationId
            JOIN user u ON d.supporterId = u.userId
            WHERE d.projectId = %s AND sm.visibility = TRUE
            ORDER BY sm.postedDate DESC
        """, (project_id,))
    donations = cursor.fetchall()
    cursor.close()

    supporter_count = len(donations)

    return render_template(
        'donation.html',
        project=project_data,
        updates=updates,
        donations=donations,
        supporter_count=supporter_count
    )  

# ----- Part 5. Admin Dashboard -----

def create_feature_form():
    # Build a dopdown with the projects that can be featured
    feature_form = FeatureProjectForm()
    options = []
    for project in get_feature_candidates():
        options.append((project['projectId'], project['projectName']))
    feature_form.project_id.choices = options
    return feature_form

@main.route('/admin')
@admin_required
def admin_dashboard():
    campaign_stats = get_campaign_stats()
    creator_count = get_creator_count()
    supporter_count = get_supporter_count()
    report_stats = get_report_stats()
    pending_projects = get_pending_projects()
    reviewed_projects = get_reviewed_projects()
    fetured_projects = get_featured_projects()
    form = AdminActionForm()
    feature_form = create_feature_form()
    return render_template('admin_dashboard.html',
                           campaign_stats = campaign_stats,
                           creator_count = creator_count,
                           supporter_count = supporter_count,
                           report_stats = report_stats,
                           pending_projects = pending_projects,
                           reviewed_projects = reviewed_projects,
                           featured_projects = fetured_projects,
                           form = form,
                           feature_form = feature_form)

@main.route('/admin/projects/<int:project_id>/approve', methods = ['POST'])
@admin_required
def approve_project(project_id):
    form = AdminActionForm()
    if form.validate_on_submit():
        if review_project_approval(project_id, 'Approved') == 1:
           flash('The project has been approved.', 'success') 
        else: 
            flash('This project could not be found or is no longer pending approval.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/projects/<int:project_id>/reject', methods = ['POST'])
@admin_required
def reject_project(project_id):
    form = AdminActionForm()
    if form.validate_on_submit():
        if review_project_approval(project_id, 'Rejected') == 1:
            flash('The project has been rejected.', 'success') 
        else: 
            flash('This project could not be found or is no longer pending approval.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

# Change project status from 'Approved' to 'Suspended'
@main.route('/admin/projects/<int:project_id>/suspend', methods = ['POST'])
@admin_required
def suspend_project(project_id):
    form = AdminActionForm()
    if form.validate_on_submit():
        if change_project_status(project_id, 'Approved', 'Suspended') == 1:
           flash('The project has been suspended and is no longer visible to supporters.', 'success') 
        else: 
            flash('Only approved projects can be suspended.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

# Change project status from 'Suspended' to 'Approved'
@main.route('/admin/projects/<int:project_id>/restore', methods = ['POST'])
@admin_required
def restore_project(project_id):
    form = AdminActionForm()
    if form.validate_on_submit():
        if change_project_status(project_id, 'Suspended', 'Approved') == 1:
           flash('The project has been restored and is visible to supporters again.', 'success') 
        else: 
            flash('Only suspended projects can be restored.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

# Soft delete projects from admin dashboard
@main.route('/admin/projects/<int:project_id>/delete', methods = ['POST'])
@admin_required
def delete_project(project_id):
    form = AdminActionForm()
    if form.validate_on_submit():
        if soft_delete_project(project_id) == 1:
           flash('The project has been deleted.', 'success') 
        else: 
            flash('This project could not be found or cannot be deleted.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

# Add featured projects
@main.route('/admin/featured/add', methods=['POST'])
@admin_required
def add_featured_project():
    feature_form = create_feature_form()
    if feature_form.validate_on_submit():
        if add_to_featured(feature_form.project_id.data) == 1:
            flash('This project has been added to the Featured section.', 'success')
        else:
            flash('This project cannot be featured.', 'warning')
    else:
        flash('Please choose a valid project to feature.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

# Remove from featured section
@main.route('/admin/featured/<int:project_id>/remove', methods=['POST'])
@admin_required
def remove_featured_project(project_id):
    form = AdminActionForm()
    if form.validate_on_submit():
        if remove_from_featured(project_id) == 1:
            flash('This project has been removed from the Featured section.', 'success')
        else:
            flash('This project is not in the Featured section.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))        

    
