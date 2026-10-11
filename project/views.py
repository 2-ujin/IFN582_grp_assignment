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
from flask import render_template, redirect, url_for, flash
from .models import (get_pending_projects, review_project_approval,
                     get_reviewed_projects, change_project_status, soft_delete_project,
                     get_featured_projects, get_feature_candidates,
                     add_to_featured, remove_from_featured)
from .forms import AdminActionForm, FeatureProjectForm

def create_feature_form():
    # Build a dopdown with the projects that can be featured
    feature_form = FeatureProjectForm()
    options = []
    for project in get_feature_candidates():
        options.append((project['projectId'], project['projectName']))
    feature_form.project_id.choices = options
    return feature_form

# TODO: add login function for admin
@main.route('/admin')
def admin_dashboard():
    pending_projects = get_pending_projects()
    reviewed_projects = get_reviewed_projects()
    fetured_projects = get_featured_projects()
    form = AdminActionForm()
    feature_form = create_feature_form()
    return render_template('admin_dashboard.html',
                           pending_projects = pending_projects,
                           reviewed_projects = reviewed_projects,
                           featured_projects = fetured_projects,
                           form = form,
                           feature_form = feature_form)

@main.route('/admin/projects/<int:project_id>/approve', methods = ['POST'])
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

    