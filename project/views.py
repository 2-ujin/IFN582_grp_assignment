from flask import Blueprint
from . import database

# Blueprint that groups all MakeArtsFund routes
main = Blueprint('main', __name__)



# ===================================================================
# ! @ Sky This part is temporary DB connection test from Part 1.
# Replace this whole route with the Home page (render home.html,
# move the query into models.py). Please keep the function name
# ====================================================================

@main.route('/')
def index():
    # Connection test: fetch every project name from the database
    cursor = database.connection.cursor()
    cursor.execute('SELECT projectName FROM project')
    projects = cursor.fetchall()
    cursor.close()

    # Return as plain text so it shows in the browser without a template
    return str(projects)


# ----- Part 5. Admin Dashboard -----
from flask import render_template
from .models import get_pending_projects

# TODO: add login function for admin
@main.route('/admin')
def admin_dashboard():
    pending_projects = get_pending_projects()
    return render_template('admin_dashboard.html',
                           pending_projects = pending_projects)