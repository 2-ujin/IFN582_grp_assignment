from flask import Blueprint, render_template
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

    # Return as plain text so it shows in the browser without a template
    return render_template('home.html', projects=projects, success_stories=success_stories)
