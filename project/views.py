#Application routes for authentication, fundraising pages, and administration

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
from .forms import AdminActionForm, EditUserForm, FeatureProjectForm, LoginForm, RegisterForm, SuccessStoryForm
from .models import (
    AccountStatus,
    User,
    add_to_featured,
    add_to_success_stories,
    change_project_status,
    change_user_status,
    email_in_use,
    get_campaign_stats,
    get_creator_count,
    get_feature_candidates,
    get_featured_projects,
    get_pending_projects,
    get_reports,
    get_report_stats,
    get_reviewed_projects,
    get_success_stories,
    get_success_story_candidates,
    get_supporter_count,
    get_user,
    get_users,
    remove_from_featured,
    remove_from_success_stories,
    review_report,
    review_project_approval,
    soft_delete_project,
    soft_delete_user,
    update_user_details,
)

# Main routes use extensions initialized by the shared app factory.
main = Blueprint("main", __name__)


# Part 2: Authentication and shared access control

@login_manager.user_loader
def load_user(user_id):
    #Reload account on each request so role and status changes take effect
    return User.get_by_id(user_id)


def _safe_local_url(target):
    #Only allow same-site redirects after successful authentication
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
    #Require authentication & single role assigned to the account

    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            # Treat a missing role as unauthorized instead of raising an error
            if not current_user.is_active or getattr(current_user, "role", None) != required_role:
                abort(403)
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


admin_required = _role_required("Administrator")
fundraiser_required = _role_required("Fundraiser")
supporter_required = _role_required("Supporter")


@main.before_app_request
def end_inactive_sessions():
    #End existing session if the account was suspended or deactivated
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


# Assessment passwords verified against the unchanged database.sql hashes.
# Their numbers follow SQL user-row order, not the order of this display table.
TEST_LOGIN_ACCOUNTS = (
    {"role": "Fundraiser", "email": "queenie.work@gmail.com", "password": "Password1"},
    {"role": "Fundraiser", "email": "marcokhc22@gmail.com", "password": "Password3"},
    {"role": "Supporter", "email": "m.brant@gmail.com", "password": "Password2"},
    {"role": "Supporter", "email": "ebao@hotmail.com", "password": "Password7"},
    {"role": "Administrator", "email": "admin2@makeartsfund.com", "password": "Password9"},
    {"role": "Administrator", "email": "admin23@makeartsfund.com", "password": "Password10"},
)


@main.route("/login", methods=["GET", "POST"])
def login():
    #Authenticate with email/password & reject inactive account statuses
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
    #Create one shared user row & exactly one selected role row
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
    #End the current session; POST plus CSRF protects the action
    logout_user()
    flash("You have signed out.", "info")
    return redirect(url_for("main.index"))



# ----- Part 3. Home page -----
# Keep the temporary Part 2 database check at its own path. The Part 3 home
# page owns `/`, so both pieces remain available without a duplicate route.

@main.route('/')

def index():
    search_query = (request.args.get('q') or request.args.get('search', '')).strip()
    category_filter = request.args.get('category', '').strip()
    show_all = request.args.get('all') == 'true'
    # Load the featured projects and success stories for the home page.
    cursor = database.connection.cursor()

    query = """
        SELECT p.*, CONCAT(u.firstname, ' ', u.surname) AS artistName,
                c.categoryName,
                IFNULL(SUM(d.amount), 0) AS totalRaised,
                ROUND(IFNULL(SUM(d.amount), 0) / p.goal * 100) AS progressPercentage,
                GREATEST(DATEDIFF(p.deadline, CURDATE()), 0) AS daysRemaining         
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        LEFT JOIN donation d ON p.projectId = d.projectId           
        WHERE p.approvalStatus = 'Approved'
    """
    params = []
    if search_query:
        query += " AND (p.projectName LIKE %s OR p.projectDescription LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    elif category_filter:
        query += " AND c.categoryName = %s"
        params.append(category_filter)

    else:
        query += " AND p.featured = TRUE"
    query += " GROUP BY p.projectId ORDER BY p.projectId ASC"
    
    if not search_query and not category_filter and not show_all:
        query += " LIMIT 3"
    
    
    cursor.execute(query, tuple(params))
    projects = cursor.fetchall()

    # show success stories with botton
    show_all_stories = request.args.get('all_stories') == 'true'

    stories_query="""
        SELECT p.*, CONCAT(u.firstname, ' ', u.surname) AS artistName,
            c.categoryName
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        WHERE p.successStoryFeatured = TRUE
        ORDER BY p.projectId ASC
    """
    if not show_all_stories:
        stories_query += " LIMIT 2"

    cursor.execute(stories_query)
    success_stories = cursor.fetchall()
    cursor.close()

    # Keep the existing Part 3 home page and its template intact.
    return render_template(
        'home.html', 
        projects=projects, 
        success_stories=success_stories,
        selected_category_filter=category_filter,
        search_query=search_query
        )
    

# ----- Part 3. Fundraiser details and donation page -----
@main.route('/donation/<int:project_id>', methods=['GET', 'POST'])
def project_detail(project_id):

    if request.method == 'POST':
        # check log in, if not need log in first
        if not current_user.is_authenticated:
            flash("Please log in or register as a Supporter to make a donation.", "warning")
            return redirect(url_for('main.login', next=url_for('main.project_detail', project_id=project_id)))
        # check only supporter can donation
        if getattr(current_user, 'role', None) != 'Supporter':
            flash("Only registered Supporters can make donations.", "warning")
            return redirect(url_for('main.project_detail', project_id=project_id))
        
        
        amount = request.form.get('pledge-amount')
        message_text = request.form.get('artist-message', '').strip()
        
        payment_method_raw = request.form.get('payment-method', 'card')
        method_map = {
            'card': 'Card',
            'paypal': 'PayPal',
            'bank-transfer': 'BankTransfer'
        }
        payment_method = method_map.get(payment_method_raw, 'Card')
        
        # check donation number>0
        try:
            amount_num = float(amount)
            if amount_num <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash("Please enter a valid donation amount greater than 0.", "danger")
            return redirect(url_for('main.project_detail', project_id=project_id))

        cursor = database.connection.cursor()
        try:
            supporter_id = current_user.id
            
            cursor.execute("INSERT IGNORE INTO supporter (userId) VALUES (%s)", (supporter_id,))
            
            cursor.execute(
                "INSERT INTO donation (projectId, supporterId, amount, donationDate, paymentMethod, paymentStatus) VALUES (%s, %s, %s, NOW(), %s, 'Received')",
                (project_id, supporter_id, amount_num, payment_method)
            )
            donation_id = cursor.lastrowid
            

            if message_text:
                cursor.execute(
                    "INSERT INTO supporterMessage (donationId, postedDate, message, visibility) VALUES (%s, NOW(), %s, TRUE)",
                    (donation_id, message_text)
                )

            database.connection.commit()
            flash('Thank you for your generous support!', 'success')
        except Exception:
            database.connection.rollback()
            flash('Donation failed, please try again.', 'danger')
        finally:
            cursor.close()

        return redirect(url_for('main.project_detail', project_id=project_id))
    

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
        WHERE p.projectId = %s AND p.approvalStatus = 'Approved'
        GROUP BY p.projectId
                         
    """,(project_id,))
    project_data = cursor.fetchone()

    if not project_data:
        cursor.close()
        abort(404)
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
    cursor.execute("SELECT COUNT(donationId) AS count FROM donation WHERE projectId = %s", (project_id,))
    count_res = cursor.fetchone()
    supporter_count = count_res['count'] if isinstance(count_res, dict) else (count_res[0] if count_res else 0)
    cursor.close()

    

    return render_template(
        'donation.html',
        project=project_data,
        updates=updates,
        donations=donations,
        supporter_count=supporter_count
    )  


# ----- Part 5. Admin Dashboard -----
"""Every route has @admin_required, so only administrators can open it.
Action routes (approve, suspend, delete, etc.) all follow the same pattern:
1. The button in admin_dashboard.html sends a POST request with a CSRF token.
2. form.validate_on_submit() checks it is a POST request with a valid token.
3. The model function runs the UPDATE and returns rowcount (1 = success, 0 = nothing changed).
4. flash() stores the message and redirect() sends the admin back to the dashboard.
"""

def create_feature_form():
    """Build a dropdown with the projects that can be featured.
    The dropdown shows the name, but sends the project ID. 
    """
    feature_form = FeatureProjectForm()
    options = []
    for project in get_feature_candidates():
        options.append((project['projectId'], project['projectName']))
    feature_form.project_id.choices = options
    return feature_form

def create_success_story_form():
    """Build a dropdown with the completed projects (same approach as above).
    """
    success_story_form = SuccessStoryForm()
    options = []
    for project in get_success_story_candidates():
        options.append((project['projectId'], project['projectName']))
    success_story_form.project_id.choices = options
    return success_story_form

@main.route('/admin')
@admin_required
def admin_dashboard():
    """Show the admin dashboard.
    Get every list and statistic from the model functions, then pass them to the template.
    AdminActionForm provides the CSRF token for all action buttons.
    """
    campaign_stats = get_campaign_stats()
    creator_count = get_creator_count()
    feature_form = create_feature_form()
    featured_projects = get_featured_projects()
    form = AdminActionForm()
    pending_projects = get_pending_projects()
    report_stats = get_report_stats()
    reports = get_reports()
    reviewed_projects = get_reviewed_projects()
    success_stories = get_success_stories()
    success_story_form = create_success_story_form()
    supporter_count = get_supporter_count()
    users = get_users()
    
    return render_template('admin_dashboard.html',
                           campaign_stats = campaign_stats,
                           creator_count = creator_count,
                           feature_form = feature_form,
                           featured_projects = featured_projects,
                           form = form,
                           pending_projects = pending_projects,
                           report_stats = report_stats,
                           reports = reports,
                           reviewed_projects = reviewed_projects,
                           success_stories = success_stories,
                           success_story_form = success_story_form,
                           supporter_count = supporter_count,
                           users = users
                           )


# ----- Pending Project Approvals -----

@main.route('/admin/projects/<int:project_id>/approve', methods = ['POST'])
@admin_required
def approve_project(project_id):
    """Approve a pending project (Pending -> Approved)."""
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
    """Reject a pending project (Pending -> Rejected)."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if review_project_approval(project_id, 'Rejected') == 1:
            flash('The project has been rejected.', 'success') 
        else: 
            flash('This project could not be found or is no longer pending approval.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


# ----- Project Management -----

@main.route('/admin/projects/<int:project_id>/suspend', methods = ['POST'])
@admin_required
def suspend_project(project_id):
    """Suspend an approved project (Approved -> Suspended). 
    It is also removed from featured.
    """
    form = AdminActionForm()
    if form.validate_on_submit():
        if change_project_status(project_id, 'Approved', 'Suspended') == 1:
           flash('The project has been suspended and is no longer visible to supporters.', 'success') 
        else: 
            flash('Only approved projects can be suspended.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/projects/<int:project_id>/restore', methods = ['POST'])
@admin_required
def restore_project(project_id):
    """Restore a suspended project (Suspended -> Approved)."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if change_project_status(project_id, 'Suspended', 'Approved') == 1:
           flash('The project has been restored and is visible to supporters again.', 'success') 
        else: 
            flash('Only suspended projects can be restored.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/projects/<int:project_id>/delete', methods = ['POST'])
@admin_required
def delete_project(project_id):
    """Soft delete a reviewed project.
    Project status becomes 'Deleted', but the data stays in the database."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if soft_delete_project(project_id) == 1:
           flash('The project has been deleted.', 'success') 
        else: 
            flash('This project could not be found or cannot be deleted.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


# ----- User Management -----

@main.route('/admin/users/<int:user_id>/suspend', methods = ['POST'])
@admin_required
def suspend_user(user_id):
    """Suspend an active artist/supporter account (Active -> Suspended)."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if change_user_status(user_id, 'Active', 'Suspended') == 1:
           flash('The account has been suspended.', 'success') 
        else: 
            flash('This account could not be suspended.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/users/<int:user_id>/reactivate', methods = ['POST'])
@admin_required
def reactivate_user(user_id):
    """Reactivate a suspended account (Suspended -> Active)."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if change_user_status(user_id, 'Suspended', 'Active') == 1:
           flash('The account has been reactivated.', 'success') 
        else: 
            flash('This account could not be reactivated.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/users/<int:user_id>/delete', methods = ['POST'])
@admin_required
def delete_user(user_id):
    """Soft delete an artist/supporter account.
    Account status becomes 'Deleted', but the data stays in the database."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if soft_delete_user(user_id) == 1:
           flash('The account has been deleted.', 'success') 
        else: 
            flash('This account could not be found or cannot be deleted.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Show and save the edit user form.
    GET: fill the form with the user's current details.
    POST: validate the form, check the email isn't used by another account, 
    then save the changes and go back to the dashboard.
    If validation fails, the form is shown again with error messages.
    """

    # First, check the account exists and is not deleted or an admin
    user = get_user(user_id)
    if user is None:
        flash('This account could not be found.', 'warning')
        return redirect(url_for('main.admin_dashboard'))

    form = EditUserForm()
    if form.validate_on_submit():
        if email_in_use(form.email.data, user_id):
            flash('This email address is already used by another account.', 'danger')
        else:
            update_user_details(user_id, form.firstname.data, form.surname.data, form.email.data)
            flash('The account details have been updated.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        
    # Input fields are prefilled with the current details 
    if request.method == 'GET':
        form.firstname.data = user['firstname']
        form.surname.data = user['surname']
        form.email.data = user['email']

    return render_template('admin_edit_user.html', form=form, user=user)


# ----- Reported Content -----

@main.route('/admin/reports/<int:report_id>/dismiss', methods = ['POST'])
@admin_required
def dismiss_report(report_id):
    """Dismiss a pending report (Pending -> Dismissed)."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if review_report(report_id, 'Dismissed') == 1:
            flash('The report has been dismissed.', 'success') 
        else: 
            flash('This report could not be found or has already been reviewed.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/reports/<int:report_id>/resolve', methods = ['POST'])
@admin_required
def resolve_report(report_id):
    """Resolve a pending report (Pending -> Resolved)."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if review_report(report_id, 'Resolved') == 1:
            flash('The report has been resolved.', 'success') 
        else: 
            flash('This report could not be found or has already been reviewed.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


# ----- Featured Projects -----
@main.route('/admin/featured/add', methods=['POST'])
@admin_required
def add_featured_project():
    """Add the project chosen in the dropdown to the featured section."""
    feature_form = create_feature_form()
    if feature_form.validate_on_submit():
        if add_to_featured(feature_form.project_id.data) == 1:
            flash('This project has been added to the Featured section.', 'success')
        else:
            flash('This project cannot be added to the Featured section.', 'warning')
    else:
        flash('Please choose a valid project to feature.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/featured/<int:project_id>/remove', methods=['POST'])
@admin_required
def remove_featured_project(project_id):
    """Remove a project from the featured section"""
    form = AdminActionForm()
    if form.validate_on_submit():
        if remove_from_featured(project_id) == 1:
            flash('This project has been removed from the Featured section.', 'success')
        else:
            flash('This project is not in the Featured section.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))        


# ----- Success Stories -----

@main.route('/admin/success-stories/add', methods=['POST'])
@admin_required
def add_success_story():
    """Add the project chosen in the dropdown to success stories (same approach as featured)."""
    success_story_form = create_success_story_form()
    if success_story_form.validate_on_submit():
        if add_to_success_stories(success_story_form.project_id.data) == 1:
            flash('This project has been added to the Success Stories section.', 'success')
        else:
            flash('This project cannot be added to the Success Stories.', 'warning')
    else:
        flash('Please choose a valid project.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/success-stories/<int:project_id>/remove', methods=['POST'])
@admin_required
def remove_success_story(project_id):
    """Remove a project from success stories section."""
    form = AdminActionForm()
    if form.validate_on_submit():
        if remove_from_success_stories(project_id) == 1:
            flash('This project has been removed from the Success Stories section.', 'success')
        else:
            flash('This project is not in the Success Stories section.', 'warning')
    else:
        flash('Something went wrong. Please try again.', 'danger')
    return redirect(url_for('main.admin_dashboard'))       


# ---- Testing only: shows the 500 error page. Remove before final submission if not documented in README ----
@main.route('/error-eg-500')
def error_eg_500():
    abort(500)
