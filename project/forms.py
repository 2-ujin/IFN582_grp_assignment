# TODO: forms split across Parts 2-4 - see TASKS.md

# ----- Part 5. Admin Dashboard -----
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import InputRequired, Regexp

# Empty form used by admin for action such as approve, delete, etc.
class AdminActionForm(FlaskForm):
    pass

# Form for admin to edit user details
class EditUserForm(FlaskForm):
    firstname = StringField("First name", validators=[InputRequired()])
    surname = StringField("Surname", validators=[InputRequired()])
    email = StringField("Email address", validators=[InputRequired(), Regexp('^..*@..*[.]..*$')])
    submit = SubmitField("Save changes")

# Dropdown for choosing a project to add to featured section
class FeatureProjectForm(FlaskForm):
    project_id = SelectField('Select a project to feature', coerce=int)
