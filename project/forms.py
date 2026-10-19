#Validated forms used by the Part 2 authentication pages

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, SelectField, StringField, SubmitField, DateField, DecimalField, HiddenField, TextAreaField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    NumberRange,
    Optional
)
#Part 2- login form + email/pw validation

class LoginForm(FlaskForm):
    # validators run on server when validate_on_submit() is called
    # The browser can help with input, but server-side validation is authoritative
    email = StringField(
        "Email address",
        filters=[lambda value: value.strip() if value else value],
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
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter your first name."),
            Length(min=1, max=50, message="Use 1 to 50 characters."),
        ],
    )
    surname = StringField(
        "Surname",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter your surname."),
            Length(min=1, max=50, message="Use 1 to 50 characters."),
        ],
    )
    email = StringField(
        "Email address",
        filters=[lambda value: value.strip() if value else value],
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
                r"\A[A-Za-z0-9]+\Z",
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

# ----- Part 4. Campaign Management -----

ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "webp"]


class CreateCampaignForm(FlaskForm):
    """Validate a new campaign created by a fundraiser."""

    form_action = HiddenField(default="create_campaign")

    project_name = StringField(
        "Project title",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter a project title."),
            Length(
                max=100,
                message="Project title must be 100 characters or fewer.",
            ),
        ],
    )

    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired(message="Select a category.")],
    )

    location = StringField(
        "Location",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter the campaign location."),
            Length(
                max=100,
                message="Location must be 100 characters or fewer.",
            ),
        ],
    )

    goal = DecimalField(
        "Fundraising goal",
        places=2,
        validators=[
            DataRequired(message="Enter a fundraising goal."),
            NumberRange(
                min=0.01,
                max=99999999999999.99,
                message="Enter a valid fundraising goal greater than zero.",
            ),
        ],
    )

    deadline = DateField(
        "Campaign deadline",
        validators=[
            DataRequired(message="Select a campaign deadline."),
        ],
    )

    project_description = TextAreaField(
        "Project description",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter a project description."),
        ],
    )

    artist_intro = TextAreaField(
        "Artist introduction",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter an artist introduction."),
        ],
    )

    project_image = FileField(
        "Campaign image",
        validators=[
            Optional(),
            FileAllowed(
                ALLOWED_IMAGE_TYPES,
                "Upload a PNG, JPG, JPEG, GIF or WEBP image.",
            ),
        ],
    )

    submit = SubmitField("Create Campaign")


class EditCampaignForm(FlaskForm):
    """Validate changes to an existing campaign."""

    form_action = HiddenField(default="update_project")
    project_id = HiddenField(validators=[DataRequired()])

    project_name = StringField(
        "Project title",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter a project title."),
            Length(
                max=100,
                message="Project title must be 100 characters or fewer.",
            ),
        ],
    )

    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired(message="Select a category.")],
    )

    location = StringField(
        "Location",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter the campaign location."),
            Length(
                max=100,
                message="Location must be 100 characters or fewer.",
            ),
        ],
    )

    goal = DecimalField(
        "Fundraising goal",
        places=2,
        validators=[
            DataRequired(message="Enter a fundraising goal."),
            NumberRange(
                min=0.01,
                max=99999999999999.99,
                message="Enter a valid fundraising goal greater than zero.",
            ),
        ],
    )

    deadline = DateField(
        "Campaign deadline",
        validators=[Optional()],
    )

    project_description = TextAreaField(
        "Project description",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter a project description."),
        ],
    )

    artist_intro = TextAreaField(
        "Artist introduction",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter an artist introduction."),
        ],
    )

    submit = SubmitField("Save Changes")


class CampaignStatusForm(FlaskForm):
    """Validate an approved campaign's operational status."""

    form_action = HiddenField(default="update_status")
    project_id = HiddenField(validators=[DataRequired()])

    project_status = SelectField(
        "Operational status",
        choices=[
            ("Active", "Active"),
            ("Paused", "Paused"),
            ("Closed", "Closed"),
        ],
        validators=[
            DataRequired(message="Select a campaign status."),
        ],
    )

    submit = SubmitField("Update Status")

class ProjectUpdateForm(FlaskForm):
    """Validate a new project update and optional image."""

    form_action = HiddenField(default="post_update")
    project_id = HiddenField(validators=[DataRequired()])

    update_title = StringField(
        "Update title",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter an update title."),
            Length(
                max=100,
                message="Update title must be 100 characters or fewer.",
            ),
        ],
    )

    update_description = TextAreaField(
        "Update description",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter an update description."),
        ],
    )

    update_image = FileField(
        "Update image",
        validators=[
            Optional(),
            FileAllowed(
                ALLOWED_IMAGE_TYPES,
                "Upload a PNG, JPG, JPEG, GIF or WEBP image.",
            ),
        ],
    )

    submit = SubmitField("Publish Update")


class EditProjectUpdateForm(FlaskForm):
    """Validate changes to an existing project update."""

    form_action = HiddenField(default="edit_update")
    project_id = HiddenField(validators=[DataRequired()])
    update_id = HiddenField(validators=[DataRequired()])

    edited_title = StringField(
        "Update title",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter an update title."),
            Length(
                max=100,
                message="Update title must be 100 characters or fewer.",
            ),
        ],
    )

    edited_description = TextAreaField(
        "Update description",
        filters=[lambda value: value.strip() if value else value],
        validators=[
            DataRequired(message="Enter an update description."),
        ],
    )

    submit = SubmitField("Save Update")


class DeleteProjectUpdateForm(FlaskForm):
    """Provide CSRF validation when deleting a project update."""

    form_action = HiddenField(default="delete_update")
    project_id = HiddenField(validators=[DataRequired()])
    update_id = HiddenField(validators=[DataRequired()])

    submit = SubmitField("Delete")

# ----- Part 5. Admin Dashboard -----


class AdminActionForm(FlaskForm):
    """Empty form used for admin actions such as 'Approve' and 'Delete'.
    It provides the CSRF token, so we can check each action really came from our site."""
    pass

class EditUserForm(FlaskForm):
    # Form for admin to edit user details on the Edit User page.
    firstname = StringField("First name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    email = StringField("Email address", validators=[DataRequired(), Email()])
    submit = SubmitField("Save changes")

class FeatureProjectForm(FlaskForm):
    """Dropdown for adding a project to add to featured section.
    Choices are filled in the view (approved, active, not yet featured)."""
    project_id = SelectField('Select a project to feature', coerce=int)

class SuccessStoryForm(FlaskForm):
    """Dropdown for adding a project to show as a successful story.
    Choices are filled in the view (approved, completed, not yet added)."""
    project_id = SelectField('Select a project for success stories', coerce=int)