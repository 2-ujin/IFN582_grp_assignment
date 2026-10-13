# TODO: forms split across Parts 2-4 - see TASKS.md

# ----- Part 5. Admin Dashboard -----
from flask_wtf import FlaskForm
from wtforms import SelectField

# Empty form used by admin for action such as approve, delete, etc.
class AdminActionForm(FlaskForm):
    pass
# Dropdown for choosing a project to add to featured section
class FeatureProjectForm(FlaskForm):
    project_id = SelectField('Select a project to feature', coerce=int)
