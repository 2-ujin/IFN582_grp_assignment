#Application routes for authentication, fundraising pages, and administration

from datetime import date
from pathlib import Path
from uuid import uuid4
from functools import wraps
from urllib.parse import urlsplit
from datetime import datetime
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
from werkzeug.utils import secure_filename

from . import database, login_manager
from .forms import AdminActionForm, EditUserForm, FeatureProjectForm, LoginForm, RegisterForm, SuccessStoryForm, CampaignStatusForm, CreateCampaignForm, DeleteProjectUpdateForm, EditCampaignForm, EditProjectUpdateForm, ProjectUpdateForm
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
    create_campaign,
    create_owned_project_update,
    delete_owned_project_update,
    edit_owned_project_update,
    get_campaign_categories,
    get_campaign_donation_statistics,
    get_campaign_supporter_messages,
    get_campaign_updates,
    get_fundraiser_campaigns,
    get_recent_campaign_donations,
    update_owned_campaign,
    update_owned_campaign_status
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
# define route from home page
@main.route('/')
def index():
    # pick search keyword from URL query(q or search)
    search_query = (request.args.get('q') or request.args.get('search', '')).strip()
    # pick category from URL query
    category_filter = request.args.get('category', '').strip()
    # if user click "Discover more" show all feature projets
    show_all = request.args.get('all') == 'true'
    # open databse cursor to apply SQL queries
    cursor = database.connection.cursor()

    # SQL query with projects, category names, creator names and sum of donation
    # LEFT JOIN means it display project even this project does not have donation
    query = """
        SELECT p.*, u.firstname, u.surname, c.categoryName,
               SUM(d.amount) AS totalRaised
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        LEFT JOIN donation d ON p.projectId = d.projectId           
        WHERE p.approvalStatus = 'Approved'
    """
    # list to store queries safe to prevent SQL attack
    params = []
    # if user enter keyword it filter project name or description
    if search_query:
        query += " AND (p.projectName LIKE %s OR p.projectDescription LIKE %s)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    # filter category name when select a category
    elif category_filter:
        query += " AND c.categoryName = %s"
        params.append(category_filter)
    # only show feature projects if no click anything
    else:
        query += " AND p.featured = TRUE"

    # group by project id and sort by number small to big
    query += " GROUP BY p.projectId ORDER BY p.projectId ASC"
    
    # excute query and match information from fetchall()
    cursor.execute(query, tuple(params))
    projects = cursor.fetchall()

    # Calculate display fields in Python
    # get today's date
    today = datetime.now().date()
    # use loop to display details in project
    for p in projects:
        p['artistName'] = p['firstname'] + ' ' + p['surname']
        if p['totalRaised'] is None:
            p['totalRaised'] = 0
        if p['goal'] and p['goal'] > 0:
            p['progressPercentage'] = round(p['totalRaised'] / p['goal'] * 100)
        else:
            p['progressPercentage'] = 0
        # calculate remaining days
        days = (p['deadline'] - today).days
        p['daysRemaining'] = days if days > 0 else 0

    # only show 3 projects if not click "discover more"
    if not search_query and not category_filter and not show_all:
        projects = projects[:3]

    # Show success stories when click "discover more"
    show_all_stories = request.args.get('all_stories') == 'true'

    # search all successStoryFeatured = TRUE in database
    stories_query = """
        SELECT p.*, u.firstname, u.surname, c.categoryName
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        WHERE p.successStoryFeatured = TRUE
        ORDER BY p.projectId ASC
    """
    # get all success stories and close database cursor
    cursor.execute(stories_query)
    success_stories = cursor.fetchall()
    cursor.close()
    # artist name in success stories
    for s in success_stories:
        s['artistName'] = s['firstname'] + ' ' + s['surname']
    # show 2 success stories if no click on "discover more"
    if not show_all_stories:
        success_stories = success_stories[:2]
    # put in home.html and pass data to the front end
    return render_template(
        'home.html', 
        projects=projects, 
        success_stories=success_stories,
        selected_category_filter=category_filter,
        search_query=search_query
    )
    

# ----- Part 3. Fundraiser details and donation page -----
# define route from donation page and support GET & POST
@main.route('/donation/<int:project_id>', methods=['GET', 'POST'])
def project_detail(project_id):

    # recieved POST when click "pay" button
    if request.method == 'POST':
        # Check login first if not show "Please log in or register as a Supporter to make a donation.", "warning"
        if not current_user.is_authenticated:
            flash("Please log in or register as a Supporter to make a donation.", "warning")
            return redirect(url_for('main.login', next=url_for('main.project_detail', project_id=project_id)))
        
        # Only supporter can donate
        if current_user.role != 'Supporter':
            flash("Only registered Supporters can make donations.", "warning")
            return redirect(url_for('main.project_detail', project_id=project_id))
        
        # get pledge amount and message from supporters submitted in HTML
        amount = request.form.get('pledge-amount')
        message_text = request.form.get('artist-message', '').strip()
        # payment
        payment_method_raw = request.form.get('payment-method', 'card')
        method_map = {
            'card': 'Card',
            'paypal': 'PayPal',
            'bank-transfer': 'BankTransfer'
        }
        payment_method = method_map.get(payment_method_raw, 'Card')
        
        # Check donation number > 0
        try:
            amount_num = float(amount)
            if amount_num <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash("Please enter a valid donation amount greater than 0.", "danger")
            return redirect(url_for('main.project_detail', project_id=project_id))

        # open cursor to save donation data into database
        cursor = database.connection.cursor()
        try:
            # get log in user id and today's date
            supporter_id = current_user.id
            today = datetime.now().date()
            
            # insert new donation data into "donation" table
            cursor.execute(
                "INSERT INTO donation (projectId, supporterId, amount, donationDate, paymentMethod, paymentStatus) VALUES (%s, %s, %s, %s, %s, 'Received')",
                (project_id, supporter_id, amount_num, today, payment_method)
            )
            
            # if supporter have message save it too
            if message_text:
                cursor.execute("SELECT MAX(donationId) AS id FROM donation")
                new_donation = cursor.fetchone()
                donation_id = new_donation['id']
                # insert message into "supporterMessage" table and set visibility to TRUE
                cursor.execute(
                    "INSERT INTO supporterMessage (donationId, postedDate, message, visibility) VALUES (%s, %s, %s, TRUE)",
                    (donation_id, today, message_text)
                )

            # save changes to database
            database.connection.commit()
            flash('Thank you for your generous support!', 'success')
        except Exception:
            # if there is any error rollback database
            database.connection.rollback()
            flash('Donation failed, please try again.', 'danger')
        finally:
            # close database 
            cursor.close()
        # return projets detail page and update new details
        return redirect(url_for('main.project_detail', project_id=project_id))
    
    # get request
    cursor = database.connection.cursor()
    # define selected project details, creator name, category, and total amount raised
    cursor.execute("""
        SELECT p.*, u.firstname, u.surname, c.categoryName,
               SUM(d.amount) AS totalRaised
        FROM project p
        JOIN user u ON p.creatorId = u.userId
        JOIN category c ON p.categoryId = c.categoryId
        LEFT JOIN donation d ON p.projectId = d.projectId           
        WHERE p.projectId = %s AND p.approvalStatus = 'Approved'
        GROUP BY p.projectId
    """, (project_id,))
    project_data = cursor.fetchone()

    # if project not exist show 404 page
    if not project_data:
        cursor.close()
        abort(404)

    # coculate all details(artistName, totalRaised, progressPercentage, daysRemaining)
    today = datetime.now().date()
    project_data['artistName'] = project_data['firstname'] + ' ' + project_data['surname']
    if project_data['totalRaised'] is None:
        project_data['totalRaised'] = 0
    if project_data['goal'] and project_data['goal'] > 0:
        project_data['progressPercentage'] = round(project_data['totalRaised'] / project_data['goal'] * 100)
    else:
        project_data['progressPercentage'] = 0

    days = (project_data['deadline'] - today).days
    project_data['daysRemaining'] = days if days > 0 else 0

    # Project updates, from new to old
    cursor.execute("""
        SELECT pu.*, MIN(im.imagePath) AS imagePath
        FROM projectUpdate pu
        LEFT JOIN image im ON pu.updateId = im.updateId
        WHERE pu.projectId = %s
        GROUP BY pu.updateId
        ORDER BY pu.publishedDate DESC
    """, (project_id,))
    updates = cursor.fetchall()

    # define supporter messages  
    cursor.execute("""
        SELECT sm.*, d.amount, u.firstname, u.surname
        FROM supporterMessage sm
        JOIN donation d ON sm.donationId = d.donationId
        JOIN user u ON d.supporterId = u.userId
        WHERE d.projectId = %s AND sm.visibility = TRUE
        ORDER BY sm.postedDate DESC
    """, (project_id,))
    donations = cursor.fetchall()
    for msg in donations:
        msg['donorName'] = msg['firstname'] + ' ' + msg['surname']

    # count total number of danation
    cursor.execute("SELECT COUNT(donationId) AS count FROM donation WHERE projectId = %s", (project_id,))
    count_res = cursor.fetchone()
    supporter_count = count_res['count'] if count_res else 0
    # close cursor
    cursor.close()
    # put in donation.html and pass data to the front end
    return render_template(
        'donation.html',
        project=project_data,
        updates=updates,
        donations=donations,
        supporter_count=supporter_count
    )  

# ----- Part 4. Campaign Management Page -----

# ----- Part 4. Campaign Management -----

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _save_management_image(uploaded_file, folder_name):
    """Save a validated campaign image using a unique safe filename."""

    if uploaded_file is None or not uploaded_file.filename:
        return None

    original_filename = secure_filename(uploaded_file.filename)

    if not original_filename or "." not in original_filename:
        raise ValueError("Please select a valid image file.")

    extension = original_filename.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Upload a PNG, JPG, JPEG, GIF or WEBP image."
        )

    unique_filename = f"{uuid4().hex}.{extension}"

    upload_folder = (
        Path(current_app.static_folder)
        / "img"
        / folder_name
    )
    upload_folder.mkdir(parents=True, exist_ok=True)

    full_path = upload_folder / unique_filename
    uploaded_file.save(full_path)

    return f"img/{folder_name}/{unique_filename}"


def _delete_management_image(image_path):
    """Safely delete an uploaded image located inside the static folder."""

    if not image_path:
        return

    static_folder = Path(current_app.static_folder).resolve()
    full_path = (static_folder / image_path).resolve()

    # Do not allow a database path to delete something outside /static.
    if not full_path.is_relative_to(static_folder):
        current_app.logger.warning(
            "Unsafe image deletion path rejected: %s",
            image_path,
        )
        return

    if full_path.is_file():
        full_path.unlink()

def _flash_management_form_errors(form):
    """Display the first validation error from a management form."""

    for field_errors in form.errors.values():
        if field_errors:
            flash(field_errors[0], "danger")
            return

    flash("Please check the submitted information.", "danger")

@main.route("/management", methods=["GET", "POST"])
@fundraiser_required
def management():
    """Display and process the logged-in fundraiser's campaign dashboard."""

    creator_id = current_user.id
    campaigns = get_fundraiser_campaigns(creator_id)
    categories = get_campaign_categories()

    category_choices = [
        (category["categoryId"], category["categoryName"])
        for category in categories
    ]

    create_form = CreateCampaignForm()
    edit_form = EditCampaignForm()
    status_form = CampaignStatusForm()
    update_form = ProjectUpdateForm()
    edit_update_form = EditProjectUpdateForm()
    delete_update_form = DeleteProjectUpdateForm()

    create_form.category_id.choices = category_choices
    edit_form.category_id.choices = category_choices

    owned_campaigns = {
        campaign["projectId"]: campaign
        for campaign in campaigns
    }

    # Process create, edit, status and project-update submissions.
    if request.method == "POST":
        form_action = request.form.get("form_action", "")
        project_id = request.form.get("project_id", type=int)
        saved_image_path = None

        try:
            if form_action == "create_campaign":
                if not create_form.validate_on_submit():
                    _flash_management_form_errors(create_form)

                elif (
                    create_form.deadline.data is None
                    or create_form.deadline.data < date.today()
                ):
                    flash(
                        "The campaign deadline cannot be in the past.",
                        "danger",
                    )

                else:
                    saved_image_path = _save_management_image(
                        create_form.project_image.data,
                        "campaigns",
                    )

                    project_id = create_campaign(
                        creator_id=creator_id,
                        category_id=create_form.category_id.data,
                        project_name=create_form.project_name.data,
                        location=create_form.location.data,
                        goal=create_form.goal.data,
                        deadline=create_form.deadline.data,
                        project_description=create_form.project_description.data,
                        artist_intro=create_form.artist_intro.data,
                        image_path=saved_image_path,
                    )

                    flash(
                        "Campaign created successfully and submitted "
                        "for administrator approval.",
                        "success",
                    )

            elif form_action == "update_project":
                if (
                    project_id is None
                    or project_id not in owned_campaigns
                ):
                    flash(
                        "You are not authorised to edit this campaign.",
                        "danger",
                    )

                elif not edit_form.validate_on_submit():
                    _flash_management_form_errors(edit_form)

                else:
                    existing_campaign = owned_campaigns[project_id]

                    # Keep the existing deadline when the edit form does not
                    # contain a deadline input.
                    deadline = (
                        edit_form.deadline.data
                        or existing_campaign["deadline"]
                    )

                    affected_rows = update_owned_campaign(
                        project_id=project_id,
                        creator_id=creator_id,
                        category_id=edit_form.category_id.data,
                        project_name=edit_form.project_name.data,
                        location=edit_form.location.data,
                        goal=edit_form.goal.data,
                        deadline=deadline,
                        project_description=edit_form.project_description.data,
                        artist_intro=edit_form.artist_intro.data,
                    )

                    if affected_rows:
                        flash(
                            "Project information updated successfully.",
                            "success",
                        )
                    else:
                        flash(
                            "No project information was changed.",
                            "info",
                        )

            elif form_action == "update_status":
                if (
                    project_id is None
                    or project_id not in owned_campaigns
                ):
                    flash(
                        "You are not authorised to manage this campaign.",
                        "danger",
                    )

                elif not status_form.validate_on_submit():
                    _flash_management_form_errors(status_form)

                elif (
                    owned_campaigns[project_id]["approvalStatus"]
                    != "Approved"
                ):
                    flash(
                        "The operational status cannot be changed because "
                        "this campaign is not approved.",
                        "danger",
                    )

                else:
                    affected_rows = update_owned_campaign_status(
                        project_id=project_id,
                        creator_id=creator_id,
                        new_status=status_form.project_status.data,
                    )

                    if affected_rows:
                        flash(
                            "Campaign status updated successfully.",
                            "success",
                        )
                    else:
                        flash(
                            "The campaign status could not be changed.",
                            "warning",
                        )

            elif form_action == "post_update":
                if (
                    project_id is None
                    or project_id not in owned_campaigns
                ):
                    flash(
                        "You are not authorised to update this campaign.",
                        "danger",
                    )

                elif not update_form.validate_on_submit():
                    _flash_management_form_errors(update_form)

                else:
                    saved_image_path = _save_management_image(
                        update_form.update_image.data,
                        "updates",
                    )

                    new_update_id = create_owned_project_update(
                        project_id=project_id,
                        creator_id=creator_id,
                        update_title=update_form.update_title.data,
                        update_description=update_form.update_description.data,
                        image_path=saved_image_path,
                    )

                    if new_update_id is None:
                        _delete_management_image(saved_image_path)
                        flash(
                            "You are not authorised to update this campaign.",
                            "danger",
                        )
                    else:
                        flash(
                            "Project update published successfully.",
                            "success",
                        )

            elif form_action == "edit_update":
                update_id = request.form.get("update_id", type=int)

                if (
                    project_id is None
                    or project_id not in owned_campaigns
                ):
                    flash(
                        "You are not authorised to manage this campaign.",
                        "danger",
                    )

                elif update_id is None:
                    flash("Invalid project update.", "danger")

                elif not edit_update_form.validate_on_submit():
                    _flash_management_form_errors(edit_update_form)

                else:
                    affected_rows = edit_owned_project_update(
                        update_id=update_id,
                        project_id=project_id,
                        creator_id=creator_id,
                        edited_title=edit_update_form.edited_title.data,
                        edited_description=(
                            edit_update_form.edited_description.data
                        ),
                    )

                    if affected_rows:
                        flash(
                            "Project update edited successfully.",
                            "success",
                        )
                    else:
                        flash(
                            "The project update was not found or no "
                            "information was changed.",
                            "warning",
                        )

            elif form_action == "delete_update":
                update_id = request.form.get("update_id", type=int)

                if (
                    project_id is None
                    or project_id not in owned_campaigns
                ):
                    flash(
                        "You are not authorised to manage this campaign.",
                        "danger",
                    )

                elif update_id is None:
                    flash("Invalid project update.", "danger")

                elif not delete_update_form.validate_on_submit():
                    _flash_management_form_errors(delete_update_form)

                else:
                    deletion_result = delete_owned_project_update(
                        update_id=update_id,
                        project_id=project_id,
                        creator_id=creator_id,
                    )

                    if (
                        deletion_result
                        and deletion_result["deleted"]
                    ):
                        for image_path in deletion_result["image_paths"]:
                            _delete_management_image(image_path)

                        flash(
                            "Project update deleted successfully.",
                            "success",
                        )
                    else:
                        flash(
                            "You are not authorised to delete this update.",
                            "danger",
                        )

            else:
                flash("Invalid campaign management action.", "danger")

        except ValueError as error:
            if saved_image_path:
                _delete_management_image(saved_image_path)

            flash(str(error), "danger")

        except Exception:
            if saved_image_path:
                _delete_management_image(saved_image_path)

            current_app.logger.exception(
                "Campaign management operation failed."
            )
            flash(
                "An unexpected error occurred. Please try again.",
                "danger",
            )

        if project_id in owned_campaigns or form_action == "create_campaign":
            return redirect(
                url_for("main.management", project_id=project_id)
            )

        return redirect(url_for("main.management"))

    # Select only a campaign owned by the logged-in fundraiser.
    selected_id = request.args.get("project_id", type=int)

    selected_campaign = None

    if campaigns:
        if selected_id in owned_campaigns:
            selected_campaign = owned_campaigns[selected_id]
        else:
            selected_campaign = campaigns[0]

    days_remaining = 0
    fund_raised = 0
    supporter_count = 0
    donation_count = 0
    average_donation = 0
    progress = 0
    remaining_target = 0
    recent_donation = []
    project_updates = []
    supporter_messages = []

    campaign_message = "Your campaign is ready to begin."

    if selected_campaign:
        project_id = selected_campaign["projectId"]

        if selected_campaign["deadline"]:
            days_remaining = max(
                (
                    selected_campaign["deadline"]
                    - date.today()
                ).days,
                0,
            )

        donation_statistics = get_campaign_donation_statistics(
            project_id,
            creator_id,
        )

        fund_raised = donation_statistics["fundRaised"]
        supporter_count = donation_statistics["supporterCount"]
        donation_count = donation_statistics["donationCount"]
        average_donation = donation_statistics["averageDonation"]

        goal = selected_campaign["goal"] or 0

        if goal > 0:
            progress = round(
                float(fund_raised / goal * 100),
                1,
            )

        remaining_target = max(goal - fund_raised, 0)

        if progress >= 100:
            campaign_message = (
                "Congratulations! Your campaign has reached "
                "its fundraising goal."
            )
        elif progress >= 50:
            campaign_message = (
                "Great progress! Your campaign is more than "
                "halfway to its goal."
            )
        elif progress > 0:
            campaign_message = (
                "Your campaign is gaining support. "
                "Keep sharing project updates."
            )

        recent_donation = get_recent_campaign_donations(
            project_id,
            creator_id,
        )

        project_updates = get_campaign_updates(
            project_id,
            creator_id,
        )

        supporter_messages = get_campaign_supporter_messages(
            project_id,
            creator_id,
        )

    return render_template(
        "management.html",
        campaigns=campaigns,
        selected_campaign=selected_campaign,
        categories=categories,
        today=date.today(),
        days_remaining=days_remaining,
        fund_raised=fund_raised,
        supporter_count=supporter_count,
        donation_count=donation_count,
        average_donation=average_donation,
        progress=progress,
        remaining_target=remaining_target,
        campaign_message=campaign_message,
        recent_donation=recent_donation,
        project_updates=project_updates,
        supporter_messages=supporter_messages,
        create_form=create_form,
        edit_form=edit_form,
        status_form=status_form,
        update_form=update_form,
        edit_update_form=edit_update_form,
        delete_update_form=delete_update_form,
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
