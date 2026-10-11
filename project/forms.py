# TODO: forms split across Parts 2-4 - see TASKS.md

# ----- Part 5. Admin Dashboard -----
from flask_wtf import FlaskForm

# Empty form used by admin for action such as approve, delete, etc.
class AdminActionForm(FlaskForm):
    pass