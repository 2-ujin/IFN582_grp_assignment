from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from . import database
from .views import fundraiser_required
from datetime import date
import os
import uuid
#File types accepted for optional project update images.
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
#Blueprint containing all fundaraiser campaign-management
management_bp = Blueprint("management", __name__)


@management_bp.route("/management", methods=["GET", "POST"])
@fundraiser_required
def management():
    """Display and process the logged-in fundraiser"s campaign dashboard."""

    #Use the authenticated user ID instead of a hard-coded creator ID.
    creator_id = current_user.id

    cursor = database.connection.cursor()

    #Load only the campaigns owned by the logged-in fundraiser.
    #This is to prevent fundraiser from viewing another fundraiser's campaigns.
    project_query = """
        SELECT 
            p.projectId, p.categoryId, p.projectName, p.approvalStatus, p.projectStatus, p.location, p.imagePath, p.goal, p.deadline, p.projectDescription, p.artistIntro, p.updateDt, c.categoryName
        FROM project AS P
        JOIN category AS C
            ON p.categoryId = c.categoryId
        WHERE p.creatorId = %s
    """

    cursor.execute(project_query, (creator_id,))
    campaigns = cursor.fetchall()

    #Load categories for the create and edit campaign dropdowns.
    category_query = """
        SELECT 
            categoryId, categoryName
        FROM category
        ORDER BY categoryName
    """

    cursor.execute(category_query)
    categories = cursor.fetchall()

    #Used to reject category IDs that were manually altered in the browser.
    valid_category_ids = {
        category["categoryId"]
        for category in categories
    }

    #Select the campaign requested in the URL.
    #Fall back to the fundraiser's first campaign when no valid ID is supplied.
    selected_id = request.args.get("project_id", type=int)

    selected_campaign = None
    if campaigns:
        if selected_id is None:
            selected_campaign = campaigns[0]
        else:
            selected_campaign = next(
                (
                    campaign
                    for campaign in campaigns
                    if campaign['projectId'] == selected_id
                ),
                campaigns[0]
            )

    days_remaining = 0

    if selected_campaign and selected_campaign["deadline"]:
        days_remaining = max(
            (selected_campaign["deadline"] - date.today()).days,0
        )

    #Initialise campaign statistics so the page also works with no campaign.
    fund_raised = 0
    supporter_count = 0
    donation_count = 0
    progress = 0
    average_donation = 0


    if selected_campaign:
        #Calculate statistics dynamically from received donation only.
        donation_query = """
            SELECT 
                COALESCE(SUM(amount),0) AS fundRaised,
                COUNT(DISTINCT supporterId) AS supporterCount,
                COUNT(donationId) AS donationCount,
                COALESCE(AVG(amount), 0) AS averageDonation
            FROM donation
            WHERE projectId = %s
                AND paymentStatus = 'Received'
        """

        cursor.execute(
            donation_query,
            (selected_campaign["projectId"],)
        )

        donation_stats = cursor.fetchone()

        fund_raised = donation_stats["fundRaised"]
        supporter_count = donation_stats["supporterCount"]
        donation_count = donation_stats["donationCount"]
        average_donation = donation_stats["averageDonation"]

        if selected_campaign["goal"] and selected_campaign["goal"]>0:
            progress = round(
                fund_raised / selected_campaign["goal"]*100,1
            )

    remaining_target = 0

    if selected_campaign:
        remaining_target = max(
            selected_campaign["goal"] - fund_raised,0
        )

    campaign_message = "Your campaign is ready to begin."

    if progress >=100:
        campaign_message = "Congratulations! Your campaign has reacged its fundraising goal."
    elif progress >=50:
        campaign_message = "Great Progress! Your campaign is more than halfway to its goal."
    elif progress > 0:
        campaign_message = "Your campaign is gaining support. Keep sharing project updates."

    #Display the five most recent donations for the selected campaign.
    recent_donation = []

    if selected_campaign:
        recent_donation_query = """
            SELECT 
                d.donationId, d.amount, d.donationDate, d.paymentMethod,d.paymentStatus, u.firstname, u.surname
            FROM donation AS d
            JOIN `user` AS u
                ON d.supporterId = u.userId
            WHERE d.projectId = %s
            ORDER BY d.donationDate DESC
            LIMIT 5
        """
        cursor.execute(
            recent_donation_query,(selected_campaign["projectId"],)
        )
        recent_donation = cursor.fetchall()

    #Load campaign posts and the first image attached to each post.
    project_updates = []

    if selected_campaign:
        update_query = """
            SELECT
                pu.updateId, pu.projectId, pu.publishedDate, pu.title, pu.description,
                (
                    SELECT i.imagepath
                    FROM image AS i
                    WHERE i.updateId = pu.updateId
                    ORDER BY i.imageId
                    LIMIT 1
                ) AS imagePath
            FROM projectUpdate AS pu
            WHERE pu.projectId = %s
            ORDER BY pu.publishedDate DESC
        """
        cursor.execute(
            update_query,(selected_campaign["projectId"],)
        )
        project_updates = cursor.fetchall()

    
    #Process create, edit, status and project-update from submissions.
    if request.method == "POST":
        form_action = request.form.get("form_action")
        project_id = request.form.get("project_id", type=int)

        #Stored the IDs of camapigns owned by the logged-in fundraiser.
        owned_project_ids = {
            campaign["projectId"]
            for campaign in campaigns
        }

        #Never rely only on the campaigns shown in the UI.
        #Verify ownership again before changing existing campaign data.
        #Creating a campaign is excluded because it does not have a project ID yet.
        if(
            form_action != "create_campaign"
            and(
                project_id is None
                or project_id not in owned_project_ids
            )
        ):
            flash(
                "You are not authorised to manage this campaign.","danger"
            )
            return redirect(
                url_for("management.management")
            )

        try:
            #Create a new campaign with pending administrator approval.
            if form_action == "create_campaign":
                project_name = request.form.get(
                    "project_name",
                    ""
                ).strip()

                category_id = request.form.get(
                    "category_id",
                    type=int
                )

                location = request.form.get(
                    "location",
                    ""
                ).strip()

                goal = request.form.get(
                    "goal",
                    type=float
                )

                deadline_text = request.form.get(
                    "deadline",
                    ""
                ).strip()

                project_description = request.form.get(
                    "project_description",
                    ""
                ).strip()

                artist_intro = request.form.get(
                    "artist_intro",
                    ""
                ).strip()

                deadline = None

                if deadline_text:
                    try:
                        deadline = date.fromisoformat(deadline_text)
                    except ValueError:
                        deadline = None

                if (
                    project_name
                    and len(project_name) <= 100
                    and category_id in valid_category_ids
                    and location
                    and len(location) <= 100
                    and goal is not None
                    and 0 < goal <= 99999999999999.99
                    and deadline is not None
                    and deadline >= date.today()
                    and project_description
                    and artist_intro
                ):
                    create_campaign_query = """
                        INSERT INTO project (
                            creatorId,
                            categoryId,
                            projectName,
                            location,
                            goal,
                            deadline,
                            approvalStatus,
                            projectStatus,
                            projectDescription,
                            artistIntro,
                            updateDt
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s,
                            'Pending', 'Active', %s, %s,
                            CURRENT_TIMESTAMP
                        )
                    """

                    cursor.execute(
                        create_campaign_query,
                        (
                            creator_id,
                            category_id,
                            project_name,
                            location,
                            goal,
                            deadline,
                            project_description,
                            artist_intro
                        )
                    )

                    database.connection.commit()

                    project_id = cursor.lastrowid

                    flash(
                        "Campaign created successfully and submitted "
                        "for administrator approval.",
                        "success"
                    )

                else:
                    flash(
                        "Please complete all campaign information correctly. "
                        "The deadline cannot be in the past.",
                        "danger"
                    )
            
            #Update the selected campaign's editable information.                    
            elif form_action == "update_project":
                project_name = request.form.get(
                "project_name",""
                ).strip()
                category_id = request.form.get(
                    "category_id",type=int
                )

                location = request.form.get(
                   "location",""
                ).strip()

                goal = request.form.get(
                    "goal", type=float
                )

                project_description = request.form.get(
                    "project_description",""
                ).strip()

                artist_intro = request.form.get(
                "artist_intro",""
                ).strip()

                if (
                    project_id and project_name and len(project_name) <=100 and category_id in valid_category_ids and location and len(location) <= 100 and goal is not None and goal > 0 and project_description and artist_intro
                ):
                    update_project_query = """
                        UPDATE project
                        SET
                            projectName=%s, categoryId=%s, location=%s, goal=%s, projectDescription=%s, artistIntro=%s, updateDt=CURRENT_TIMESTAMP
                        WHERE projectId=%s
                        AND creatorId=%s
                    """
                    cursor.execute(
                        update_project_query,(
                            project_name, category_id, location, goal, project_description, artist_intro, project_id, creator_id
                        )
                    )
                    database.connection.commit()

                    flash(
                        "Project information updated successfully.","success"
                    )
                else:
                    flash(
                        "Please complete all project information correctly.","danger"
                    )

            #Allow operational status changes only for approved campaigns.
            elif form_action == "update_status":
                new_status = request.form.get("project_status", "").strip()
            
                allowed_statuses = ["Active", "Paused", "Closed"]

                campaign_to_update = next (
                    (
                        campaign for campaign in campaigns if campaign["projectId"] == project_id
                    ),
                    None
                )

                if not campaign_to_update:
                    flash(
                        "Campaign cpuld not be found.","danger"
                    )
                elif campaign_to_update["approvalStatus"] != "Approved":
                    flash(
                        "The operational status cannot be changed because"
                        "this campaign is not approved.",
                        "danger"
                    )
                elif new_status not in allowed_statuses:
                    flash(
                        "Please select a valid campaign status.","danger"
                    )
                else:
                    update_status_query = """
                        UPDATE project
                        SET
                            projectStatus = %s,
                            updateDt = CURRENT_TIMESTAMP
                        WHERE projectId = %s
                        AND creatorId = %s
                        AND approvalStatus = 'Approved'
                    """
            
                    cursor.execute(
                        update_status_query,
                        (new_status, project_id, creator_id)
                    )

                    database.connection.commit()

                    flash(
                        "Campaign status updated successfully.","success"
                    )

            #Publish a campaign update with an optional validated image.
            elif form_action == "post_update":
                update_title = request.form.get("update_title","").strip()
                update_description = request.form.get("update_description", "").strip()
                update_image = request.files.get("update_image")

                if project_id and update_title and len(update_title) <= 100 and update_description:
                    ownership_query = """
                        SELECT projectId
                        FROM project
                        WHERE projectId = %s
                        AND creatorId = %s
                    """
                    cursor.execute(
                        ownership_query,(project_id, creator_id)
                    )

                    owned_project = cursor.fetchone()

                    if owned_project:
                        extension = None
                        if update_image and update_image.filename:
                            filename = secure_filename(
                                update_image.filename
                            )
                            if not filename or "." not in filename:
                                flash(
                                    "Please select a valid image file.", "danger"
                                )
                                return redirect(
                                    url_for(
                                        "management.management", project_id=project_id
                                    )
                                )
                            extension = filename.rsplit(".", 1)[1].lower()
                        
                            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                                flash(
                                "Invalid image type. Please uplosd PNG, JPG, JPEG, GIF or WEBP.", "danger"
                                )
                                return redirect(
                                    url_for(
                                        "management.management", project_id=project_id
                                    )
                                )
                        insert_update_query = """
                            INSERT INTO projectUpdate (
                                projectId, publishedDate, title, description
                            )
                            VALUES (%s, NOW(), %s, %s)
                        """

                        cursor.execute(
                            insert_update_query,
                            (
                                project_id, update_title, update_description
                            )
                        )

                        new_update_id = cursor.lastrowid
                        if update_image and update_image.filename:
                            filename = secure_filename(
                                update_image.filename
                            )
                            if not filename or "." not in filename:
                                return "Invalid image file", 400

                            extension = filename.rsplit(".", 1)[1].lower()
                            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                                return "Invalid image type.", 400

                            unique_filename = f"{uuid.uuid4().hex}.{extension}"

                            upload_folder = os.path.join(
                                current_app.static_folder,
                                "img", "updates"
                            )
                            os.makedirs(upload_folder, exist_ok=True)

                            update_image.save(
                                os.path.join(upload_folder, unique_filename)
                            )

                            image_path = f"img/updates/{unique_filename}"

                            cursor.execute(
                                "INSERT INTO image (updateId, imagePath) VALUES (%s, %s)",
                                (new_update_id, image_path)
                            )
                            database.connection.commit()

                        flash(
                            "Project update published successfully.","success"
                        )
                    else:
                        flash(
                            "You are not authorised to update this campaign.","danger"
                        )

            #Edit an existing update after confirming campaign ownership.
            elif form_action == "edit_update":
                update_id = request.form.get(
                    "update_id",type=int
                )
                edited_title = request.form.get(
                    "edited_title",""
                ).strip()
                edited_description = request.form.get(
                    "edited_description",""
                ).strip()
                if (
                    project_id and update_id and edited_title and len(edited_title) <=100 and edited_description
                ):
                    edit_update_query = """
                        UPDATE projectUpdate AS pu
                        JOIN project AS p
                            ON pu.projectId = p.projectId
                        SET
                            pu.title = %s,
                            pu.description = %s
                        WHERE pu.updateId = %s
                        AND pu.projectId = %s
                        AND p.creatorId = %s
                    """
                    cursor.execute(
                        edit_update_query,
                        (
                            edited_title, edited_description, update_id, project_id,creator_id
                        )
                    )
                    database.connection.commit()
                
                    flash(
                        "Project updated edited successfully.","success"
                    )
                else:
                    flash(
                        "Please enter a valid update title and description.","danger"
                    )

            #Delete the update, its database image records and stored files.
            elif form_action == "delete_update":
                update_id = request.form.get(
                    "update_id",type=int
                )

                if project_id and update_id:
                    ownership_query = """
                        SELECT pu.updateId
                        FROM projectUpdate AS pu
                        JOIN project AS p
                            ON pu.projectId = p.projectId
                        WHERE pu.updateId = %s
                        AND pu.projectId = %s
                        AND p.creatorId = %s
                    """
                    cursor.execute(
                        ownership_query,
                        (update_id, project_id, creator_id)
                    )
                    owned_update = cursor.fetchone()

                    if owned_update:
                        image_query = """
                            SELECT imagePath
                            FROM image
                            WHERE updateId = %s
                        """
                        cursor.execute(
                            image_query,
                            (update_id,)
                        )
                        image_records = cursor.fetchall()
                        cursor.execute(
                            """
                            DELETE FROM image
                            WHERE updateId = %s
                            """,
                            (update_id,)
                        )
                        delete_update_query = """
                            DELETE pu
                            FROM projectUpdate AS pu
                            JOIN project AS p
                                ON pu.projectId = p.projectId
                            WHERE pu.updateId = %s
                            AND pu.projectId = %s
                            AND p.creatorId = %s
                        """    
                        cursor.execute(
                            delete_update_query,
                            (update_id, project_id, creator_id)
                        )

                        database.connection.commit()

                        for image_record in image_records:
                            image_path = image_record["imagePath"]
                            if image_path:
                                full_image_path = os.path.join(
                                    current_app.static_folder,image_path
                                )
                                if os.path.isfile(full_image_path):
                                    os.remove(full_image_path)
                    
                        flash(
                            "Project update deleted successfully.","success"
                        )
                    else:
                        flash(
                            "You are not authorised to delete this update.",
                            "danger"
                        )
                else:
                    flash(
                        "Invalid update information.", "danger"
                    )

        #Roll back the transaction so a failed operation does not leave
        #Partially saved database changes.
        except Exception:
            database.connection.rollback()
            current_app.logger.exception(
                "Management database operation failed"
            )
            flash(
                "An unexpected error occurres. Please try again.","danger"
            )

        return redirect(
            url_for(
                "management.management",project_id=project_id
            )
        )

    #Load visible supporter messages linked to donations for this campaign.
    supporter_messages = []

    if selected_campaign:
        message_query = """
            SELECT 
                m.messageId, m.postedDate, m.message, u.firstname, u.surname
            FROM supporterMessage AS m
            JOIN donation AS d
                ON m.donationId = d.donationId
            JOIN `user` AS u
               ON d.supporterId = u.userId
            WHERE d.projectId = %s
                AND m.visibility = 1
            ORDER BY m.postedDate DESC
        """  
        cursor.execute(
            message_query,(selected_campaign["projectId"],)
        )
        supporter_messages = cursor.fetchall()

    #Close the cursor after all database reads are complete.
    cursor.close()


    #Pass database results and calculated statistics to the template.
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
        supporter_messages=supporter_messages
    )