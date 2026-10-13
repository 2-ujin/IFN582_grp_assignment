from flask import Blueprint, render_template
from . import database

management_bp = Blueprint("management", __name__)


@management_bp.route("/management")
def management():
    # Temporary test user until the login function is completed
    creator_id = 1

    cursor = database.connection.cursor()

    query = """
        SELECT projectId, projectName, approvalStatus, projectStatus
        FROM project
        WHERE creatorId = %s
    """

    cursor.execute(query, (creator_id,))
    campaigns = cursor.fetchall()
    cursor.close()

    return render_template(
        "management.html",
        campaigns=campaigns
    )