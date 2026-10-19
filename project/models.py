from dataclasses import dataclass, field
from datetime import datetime, date
from typing import ClassVar, Optional
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import generate_password_hash

from . import database

# Part 2- account status value 


class AccountStatus(Enum):
    ACTIVE = 'Active'
    SUSPENDED = 'Suspended'
    DEACTIVATED = 'Deactivated'
    DELETED = 'Deleted'  # Part 5 soft-deletion value; never permits login.
# Part 2- authentication model classes    
@dataclass
class User(UserMixin):
    id: int
    firstname: str
    surname: str
    email: str
    password: str = field (repr=False)
    accountStatus: AccountStatus = AccountStatus.ACTIVE
    role: ClassVar[str] = "User"
#Part 2- Flask Login active account check
    @property
    def status_value(self):
        """Support loaded enum values and raw database status strings."""
        return getattr(self.accountStatus, 'value', self.accountStatus)

    @property
    def is_active(self):
        """Return the boolean Flask-Login uses before allowing a session."""
        return self.status_value == AccountStatus.ACTIVE.value
    @property
    def is_suspended(self):
        """Return True when the account is suspended."""
        return self.status_value == AccountStatus.SUSPENDED.value

    @property
    def is_deactivated(self):
        """Return True when the account is deactivated."""
        return self.status_value in (AccountStatus.DEACTIVATED.value, AccountStatus.DELETED.value)

    
#Part 2- pw hashing
    def set_password(self, raw_password: str):
        """Store a Werkzeug password hash rather than a plain-text password."""
        self.password = generate_password_hash(raw_password)
#Part 2- lookup by email/ userID
    @classmethod
    def get_by_id(cls, user_id):
        """Reload the account and role for Flask-Login's signed session ID."""
        return cls._load("WHERE u.userId = %s", (user_id,))

    @classmethod
    def get_by_email(cls, email):
        """Find a login account without treating email letter case as significant."""
        return cls._load("WHERE LOWER(u.email) = LOWER(%s)", (email.strip(),))
#Part 2- database query join users to role table + identify account role
    @classmethod
    def _load(cls, condition, values):
        # Stores common account data in `user` and role membership in
        # one of three child tables. LEFT JOIN lets this query discover that role.
        # The CASE expression returns a role only if exactly one child row exists.
        query = (
            "SELECT u.userId, u.firstname, u.surname, u.email, u.password, "
            "u.accountStatus, "
            "CASE "
            "WHEN ((a.userId IS NOT NULL) + (s.userId IS NOT NULL) + "
            "(ad.userId IS NOT NULL)) = 1 THEN "
            "CASE "
            "WHEN a.userId IS NOT NULL THEN 'Fundraiser' "
            "WHEN s.userId IS NOT NULL THEN 'Supporter' "
            "WHEN ad.userId IS NOT NULL THEN 'Administrator' "
            "END "
            "ELSE NULL END AS role "
            "FROM user AS u "
            "LEFT JOIN artist AS a ON a.userId = u.userId "
            "LEFT JOIN supporter AS s ON s.userId = u.userId "
            "LEFT JOIN administrator AS ad ON ad.userId = u.userId "
            f"{condition} LIMIT 1"
        )
        cursor = database.connection.cursor()
        try:
            # The condition is selected only by the fixed helper methods above
            # actual email/ID values passed separately as parameters
            cursor.execute(query, values)
            row = cursor.fetchone()
        finally:
            cursor.close()

        if not row or not row.get("role"):
            # Missing accounts and accounts with zero/multiple role rows cannot
            # authenticate because their role is ambiguous/invalid
            return None

        role_classes = {
            "Fundraiser": Artist,
            "Supporter": Supporter,
            "Administrator": Administrator,
        }
        user_class = role_classes.get(row["role"])
        if user_class is None:
            return None

        try:
            status = AccountStatus(row["accountStatus"])
        except ValueError:
            # Treat an unexpected database value as blocked instead of granting access.
            status = AccountStatus.DEACTIVATED

        return user_class(
            id=row["userId"],
            firstname=row["firstname"],
            surname=row["surname"],
            email=row["email"],
            password=row["password"],
            accountStatus=status,
        )


# fundraisers =Artist

class Artist(User):
    role: ClassVar[str] = "Fundraiser"

class Supporter(User):
    role: ClassVar[str] = "Supporter"

class Administrator(User):
    role: ClassVar[str] = "Administrator"


class ApprovalStatus(Enum):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    SUSPENDED = 'Suspended'

class ProjectStatus(Enum):
    ACTIVE = 'Active'
    PAUSED = 'Paused'
    COMPLETED = 'Completed'


# dataclasses describe database concepts used by later project pages
# Part 2- names for the project schema, while Part 3-5 add their workflows

# Category
@dataclass
class Category:
    categoryId: int
    categoryName: str


# A fundraising project belongs to an artist and one category.
@dataclass
class Project:
    projectId: int
    creator: Artist
    category: Category
    projectName: str
    location: Optional[str]     # this field can be NULL
    imagePath: Optional[str]    # this field can be NULL
    goal: Optional[float]       # this field can be NULL
    deadline: Optional[date]    # this field can be NULL
    projectDescription: str
    artistIntro: str
    reviewerId: Optional[int] = None    # this field can be NULL
    approvalStatus: ApprovalStatus = ApprovalStatus.PENDING
    projectStatus: ProjectStatus = ProjectStatus.ACTIVE
    featured: bool = False
    successStoryFeatured: bool = False
    updateDt: datetime = field(default_factory=lambda: datetime.now())





# A donation links a supporter to the project they choose to fund.

class PaymentStatus(Enum):
    PENDING = 'Pending'
    RECEIVED = 'Received'
    FAILED = 'Failed'


@dataclass
class Donation:
    donationId: int
    project: Project
    supporter: Supporter
    amount: float
    paymentMethod: str
    donationDate: datetime = field(default_factory=lambda: datetime.now())
    paymentStatus: PaymentStatus = PaymentStatus.PENDING


# Supporter messages are associated with donations and can be hidden via visibility.

@dataclass
class SupporterMessage:
    messageId: int
    donation: Donation
    message: str
    postedDate: datetime = field(default_factory=lambda: datetime.now())
    visibility: bool = True


# Project updates store progress posts made by the fundraiser.

@dataclass
class ProjectUpdate:
    updateId: int
    project: Project
    title: str
    description: Optional[str]
    publishedDate: datetime = field(default_factory=lambda: datetime.now())

# Reports record content that a user asks an administrator to review.

class ReportStatus(Enum):
    PENDING = 'Pending'
    RESOLVED = 'Resolved'


@dataclass
class Report:
    reportId: int
    reporter: User
    projectId: Optional[int]    # this field can be NULL
    messageId: Optional[int]    # this field can be NULL
    reportedContent: Optional[str]   # this field can be NULL
    reason: Optional[str]      # this field can be NULL
    submittedDate: datetime = field(default_factory=lambda: datetime.now())
    status: ReportStatus = ReportStatus.PENDING
    reviewerId: Optional[int] = None    # this field can be NULL


# Images are attached to project updates, rather than directly to user accounts.

@dataclass
class Image:
    imageId: int
    update: ProjectUpdate
    imagePath: str

# ----- Part 4. Campaign Management -----
def get_fundraiser_campaigns(creator_id):
    """Return every campaign owned by the logged-in fundraiser."""

    cursor = database.connection.cursor()
    cursor.execute(
        """
        SELECT
            p.projectId,
            p.creatorId,
            p.categoryId,
            p.projectName,
            p.approvalStatus,
            p.projectStatus,
            p.location,
            p.imagePath,
            p.goal,
            p.deadline,
            p.projectDescription,
            p.artistIntro,
            p.updateDt,
            c.categoryName
        FROM project AS p
        JOIN category AS c
            ON p.categoryId = c.categoryId
        WHERE p.creatorId = %s
        ORDER BY p.updateDt DESC, p.projectId DESC
        """,
        (creator_id,),
    )

    campaigns = cursor.fetchall()
    cursor.close()
    return campaigns


def get_campaign_categories():
    """Return all categories for campaign create and edit forms."""

    cursor = database.connection.cursor()
    cursor.execute(
        """
        SELECT categoryId, categoryName
        FROM category
        ORDER BY categoryName
        """
    )

    categories = cursor.fetchall()
    cursor.close()
    return categories


def get_campaign_donation_statistics(project_id, creator_id):
    """Calculate donation statistics for a campaign owned by the fundraiser."""

    cursor = database.connection.cursor()
    cursor.execute(
        """
        SELECT
            COALESCE(SUM(d.amount), 0) AS fundRaised,
            COUNT(DISTINCT d.supporterId) AS supporterCount,
            COUNT(d.donationId) AS donationCount,
            COALESCE(AVG(d.amount), 0) AS averageDonation
        FROM project AS p
        LEFT JOIN donation AS d
            ON p.projectId = d.projectId
            AND d.paymentStatus = 'Received'
        WHERE p.projectId = %s
            AND p.creatorId = %s
        GROUP BY p.projectId
        """,
        (project_id, creator_id),
    )

    statistics = cursor.fetchone()
    cursor.close()

    if statistics is None:
        return {
            "fundRaised": 0,
            "supporterCount": 0,
            "donationCount": 0,
            "averageDonation": 0,
        }

    return statistics


def get_recent_campaign_donations(project_id, creator_id):
    """Return the five most recent donations for an owned campaign."""

    cursor = database.connection.cursor()
    cursor.execute(
        """
        SELECT
            d.donationId,
            d.amount,
            d.donationDate,
            d.paymentMethod,
            d.paymentStatus,
            u.firstname,
            u.surname
        FROM donation AS d
        JOIN project AS p
            ON d.projectId = p.projectId
        JOIN `user` AS u
            ON d.supporterId = u.userId
        WHERE d.projectId = %s
            AND p.creatorId = %s
        ORDER BY d.donationDate DESC
        LIMIT 5
        """,
        (project_id, creator_id),
    )

    donations = cursor.fetchall()
    cursor.close()
    return donations


def get_campaign_updates(project_id, creator_id):
    """Return project updates and their first associated image."""

    cursor = database.connection.cursor()
    cursor.execute(
        """
        SELECT
            pu.updateId,
            pu.projectId,
            pu.publishedDate,
            pu.title,
            pu.description,
            (
                SELECT MIN(i.imagePath)
                FROM image AS i
                WHERE i.updateId = pu.updateId
            ) AS imagePath
        FROM projectUpdate AS pu
        JOIN project AS p
            ON pu.projectId = p.projectId
        WHERE pu.projectId = %s
            AND p.creatorId = %s
        ORDER BY pu.publishedDate DESC
        """,
        (project_id, creator_id),
    )

    updates = cursor.fetchall()
    cursor.close()
    return updates


def get_campaign_supporter_messages(project_id, creator_id):
    """Return visible supporter messages for an owned campaign."""

    cursor = database.connection.cursor()
    cursor.execute(
        """
        SELECT
            sm.messageId,
            sm.postedDate,
            sm.message,
            u.firstname,
            u.surname
        FROM supporterMessage AS sm
        JOIN donation AS d
            ON sm.donationId = d.donationId
        JOIN project AS p
            ON d.projectId = p.projectId
        JOIN `user` AS u
            ON d.supporterId = u.userId
        WHERE d.projectId = %s
            AND p.creatorId = %s
            AND sm.visibility = TRUE
        ORDER BY sm.postedDate DESC
        """,
        (project_id, creator_id),
    )

    messages = cursor.fetchall()
    cursor.close()
    return messages

def create_campaign(
    creator_id,
    category_id,
    project_name,
    location,
    goal,
    deadline,
    project_description,
    artist_intro,
    image_path=None,
):
    """Create a new campaign with pending administrator approval."""

    cursor = database.connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO project (
                creatorId,
                categoryId,
                projectName,
                location,
                imagePath,
                goal,
                deadline,
                approvalStatus,
                projectStatus,
                projectDescription,
                artistIntro,
                updateDt
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                'Pending', 'Active', %s, %s, CURRENT_TIMESTAMP
            )
            """,
            (
                creator_id,
                category_id,
                project_name,
                location,
                image_path,
                goal,
                deadline,
                project_description,
                artist_intro,
            ),
        )

        new_project_id = cursor.lastrowid
        database.connection.commit()
        return new_project_id

    except Exception:
        database.connection.rollback()
        raise

    finally:
        cursor.close()


def update_owned_campaign(
    project_id,
    creator_id,
    category_id,
    project_name,
    location,
    goal,
    deadline,
    project_description,
    artist_intro,
):
    """Update campaign information only when it belongs to the fundraiser."""

    cursor = database.connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE project
            SET
                categoryId = %s,
                projectName = %s,
                location = %s,
                goal = %s,
                deadline = %s,
                projectDescription = %s,
                artistIntro = %s,
                updateDt = CURRENT_TIMESTAMP
            WHERE projectId = %s
                AND creatorId = %s
            """,
            (
                category_id,
                project_name,
                location,
                goal,
                deadline,
                project_description,
                artist_intro,
                project_id,
                creator_id,
            ),
        )

        affected_rows = cursor.rowcount
        database.connection.commit()
        return affected_rows

    except Exception:
        database.connection.rollback()
        raise

    finally:
        cursor.close()


def update_owned_campaign_status(
    project_id,
    creator_id,
    new_status,
):
    """Change operational status without overriding administrator decisions."""

    allowed_statuses = ("Active", "Paused", "Closed")

    if new_status not in allowed_statuses:
        return 0

    cursor = database.connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE project
            SET
                projectStatus = %s,
                updateDt = CURRENT_TIMESTAMP
            WHERE projectId = %s
                AND creatorId = %s
                AND approvalStatus = 'Approved'
            """,
            (
                new_status,
                project_id,
                creator_id,
            ),
        )

        affected_rows = cursor.rowcount
        database.connection.commit()
        return affected_rows

    except Exception:
        database.connection.rollback()
        raise

    finally:
        cursor.close()

def create_owned_project_update(
    project_id,
    creator_id,
    update_title,
    update_description,
    image_path=None,
):
    """Create a project update only for a campaign owned by the fundraiser."""

    cursor = database.connection.cursor()

    try:
        # Confirm that the campaign belongs to the logged-in fundraiser.
        cursor.execute(
            """
            SELECT projectId
            FROM project
            WHERE projectId = %s
                AND creatorId = %s
            """,
            (project_id, creator_id),
        )

        owned_project = cursor.fetchone()

        if owned_project is None:
            database.connection.rollback()
            return None

        cursor.execute(
            """
            INSERT INTO projectUpdate (
                projectId,
                publishedDate,
                title,
                description
            )
            VALUES (%s, NOW(), %s, %s)
            """,
            (
                project_id,
                update_title,
                update_description,
            ),
        )

        new_update_id = cursor.lastrowid

        # Only create an image record when the user uploaded an image.
        if image_path:
            cursor.execute(
                """
                INSERT INTO image (
                    updateId,
                    imagePath
                )
                VALUES (%s, %s)
                """,
                (
                    new_update_id,
                    image_path,
                ),
            )

        database.connection.commit()
        return new_update_id

    except Exception:
        database.connection.rollback()
        raise

    finally:
        cursor.close()


def edit_owned_project_update(
    update_id,
    project_id,
    creator_id,
    edited_title,
    edited_description,
):
    """Edit an update only when its campaign belongs to the fundraiser."""

    cursor = database.connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE projectUpdate AS pu
            JOIN project AS p
                ON pu.projectId = p.projectId
            SET
                pu.title = %s,
                pu.description = %s,
                pu.publishedDate = NOW()
            WHERE pu.updateId = %s
                AND pu.projectId = %s
                AND p.creatorId = %s
            """,
            (
                edited_title,
                edited_description,
                update_id,
                project_id,
                creator_id,
            ),
        )

        affected_rows = cursor.rowcount
        database.connection.commit()
        return affected_rows

    except Exception:
        database.connection.rollback()
        raise

    finally:
        cursor.close()


def delete_owned_project_update(
    update_id,
    project_id,
    creator_id,
):
    """Delete an owned project update and return its stored image paths."""

    cursor = database.connection.cursor()

    try:
        # Retrieve image paths before deleting their database records.
        cursor.execute(
            """
            SELECT i.imagePath
            FROM projectUpdate AS pu
            JOIN project AS p
                ON pu.projectId = p.projectId
            LEFT JOIN image AS i
                ON pu.updateId = i.updateId
            WHERE pu.updateId = %s
                AND pu.projectId = %s
                AND p.creatorId = %s
            """,
            (
                update_id,
                project_id,
                creator_id,
            ),
        )

        records = cursor.fetchall()

        # No records means that the update does not exist or is not owned
        # by the logged-in fundraiser.
        if not records:
            database.connection.rollback()
            return None

        image_paths = [
            record["imagePath"]
            for record in records
            if record["imagePath"]
        ]

        cursor.execute(
            """
            DELETE i
            FROM image AS i
            JOIN projectUpdate AS pu
                ON i.updateId = pu.updateId
            JOIN project AS p
                ON pu.projectId = p.projectId
            WHERE pu.updateId = %s
                AND pu.projectId = %s
                AND p.creatorId = %s
            """,
            (
                update_id,
                project_id,
                creator_id,
            ),
        )

        cursor.execute(
            """
            DELETE pu
            FROM projectUpdate AS pu
            JOIN project AS p
                ON pu.projectId = p.projectId
            WHERE pu.updateId = %s
                AND pu.projectId = %s
                AND p.creatorId = %s
            """,
            (
                update_id,
                project_id,
                creator_id,
            ),
        )

        deleted_rows = cursor.rowcount
        database.connection.commit()

        return {
            "deleted": deleted_rows == 1,
            "image_paths": image_paths,
        }

    except Exception:
        database.connection.rollback()
        raise

    finally:
        cursor.close()


# ----- Part 5. Admin Dashboard -----
"""All function below follow the same pattern:
1. cursor = database.connection.cursor() open a cursor to send SQL to MySQL
2. cursor.execute() run the SQL (%s placeholders prevent SQL injection)
3. SELECT: fetchone() returns one row, fetchall() returns a list of rows
4. cursor.close() and return the result to views.py

UPDATE functions return rowcount (1 = success, 0 = nothing changed), so the view can show a success or error message.
Extra WHERE conditions make sure an action only runs on rows in the right state. 
"""

# ----- Administration Overview -----

def get_campaign_stats():
    """Count campaigns for the overview cards: total, active, and pending.
    SUM(condition) adds 1 for each row where the condition is true, so it counts matching rows.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  COUNT(*) AS totalCampaigns,
                SUM(project.approvalStatus = 'Approved' AND project.projectStatus = 'Active') AS activeCampaigns,
                SUM(project.approvalStatus = 'Pending') AS pendingCampaigns
        FROM project
        WHERE project.approvalStatus <> 'Deleted'
    """)
    campaign_stats = cursor.fetchone()
    cursor.close()
    return campaign_stats

def get_creator_count():
    """Count active creators (artists) for the overview card.
    JOIN with user to check the account status, which is stored in the user table.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  COUNT(*) AS activeCreators
        FROM artist
        JOIN user ON user.userId = artist.userId
        WHERE user.accountStatus = 'Active'
    """)
    creator_count = cursor.fetchone()
    cursor.close()
    return creator_count

def get_supporter_count():
    """Count active supporters for the overview card (same approach as get_creator_count)."""
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  COUNT(*) AS activeSupporters
        FROM supporter
        JOIN user ON user.userId = supporter.userId
        WHERE user.accountStatus = 'Active'
    """)
    supporter_count = cursor.fetchone()
    cursor.close()
    return supporter_count

def get_report_stats():
    """Count all reports and pending reports.""" 
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  COUNT(*) AS totalReports,
                SUM(report.status = 'Pending') AS pendingReports
        FROM report
    """)
    report_stats = cursor.fetchone()
    cursor.close()
    return report_stats


# ----- Pending Project Approvals -----

def get_pending_projects():
    """Get projects waiting for an admin to approve or reject them.
    JOIN user (on creatorId) to get the creator's name, and JOIN category to get the category name. 
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName,
                CONCAT(user.firstname, ' ', user.surname) AS creatorName,
                category.categoryName,
                project.location,
                project.updateDt AS submittedDate
        FROM project
        JOIN user ON user.userId = project.creatorId
        JOIN category ON category.categoryId = project.categoryId
        WHERE project.approvalStatus = 'Pending'
        ORDER BY project.updateDt ASC
    """)

    pending_projects = cursor.fetchall()
    cursor.close()
    return pending_projects

def review_project_approval(project_id, new_status):
    """Approve or reject a pending project. The update only runs if the project is still 'Pending',
    so a project that was already reviewed is not changed again. 
    Return rowcount(1 = updated, 0 = not updated)
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET approvalStatus = %s
        WHERE projectId = %s
          AND approvalStatus = 'Pending'
    """, (new_status, project_id)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def get_reviewed_projects():
    """Get projects that have already been reviewed for the project management table.
    Includes approved, suspended and rejected projects.
    Pending projects are in the approval table, and deleted projects are hidden but remain in the database.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName,
                CONCAT(user.firstname, ' ', user.surname) AS creatorName,
                category.categoryName,
                project.location,
                project.projectStatus,
                project.approvalStatus
        FROM project
        JOIN user ON user.userId = project.creatorId
        JOIN category ON category.categoryId = project.categoryId
        WHERE project.approvalStatus IN ('Approved', 'Suspended', 'Rejected')
        ORDER BY project.projectName ASC
    """)

    reviewed_projects = cursor.fetchall()
    cursor.close()
    return reviewed_projects

def change_project_status(project_id, current_status, new_status):
    """Suspend or restore a project (approved -> suspended or suspended -> approved).
       The update only runs if the project currently has current_status.
       It also sets featured = False, so a suspended project is removed from the featured section.
       If it is restored, an admin can feature it again.     
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET approvalStatus = %s,
            featured = FALSE 
        WHERE projectId = %s
          AND approvalStatus = %s
    """, (new_status, project_id, current_status)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def soft_delete_project(project_id):
    """Soft delete a reviewed project by setting its approval status to 'Deleted'.
    The data stays in the database, so related donations and reports are kept, 
    but the project is hidden from the table.
    It is also removed from featured project.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET approvalStatus = 'Deleted',
            featured = FALSE   
        WHERE projectId = %s
          AND approvalStatus IN ('Approved', 'Suspended', 'Rejected')
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows


# ----- User Management -----

def get_users():
    """Get all accounts (except deleted ones) for the user management table.
    The role is stored in separate tables (administrator, artist, supporter).
    LEFT JOIN keeps every user even if they have no row in a role table,
    and CASE picks the role from whichever table has a matching row.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  user.userId,
                CONCAT(user.firstname, ' ', user.surname) AS fullName,
                user.email,
                CASE
                    WHEN administrator.userId IS NOT NULL THEN 'Administrator'
                    WHEN artist.userId IS NOT NULL THEN 'Artist'
                    WHEN supporter.userId IS NOT NULL THEN 'Supporter'
                    ELSE 'Unknown'
                END AS role,
                user.accountStatus
        FROM user
        LEFT JOIN administrator ON administrator.userId = user.userId
        LEFT JOIN artist ON artist.userId = user.userId
        LEFT JOIN supporter ON supporter.userId = user.userId
        WHERE user.accountStatus <> 'Deleted'
        ORDER BY user.firstname ASC        
    """)
    users = cursor.fetchall()
    cursor.close()
    return users

def get_user(user_id):
    """Get one artist/supporter account to fill in the edit user form.
    Returns None if the account does not exist, is deleted, or is an administrator.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  user.userId,
                user.firstname,
                user.surname,
                user.email,
                user.accountStatus,
                CASE
                    WHEN artist.userId IS NOT NULL THEN 'Artist'
                    WHEN supporter.userId IS NOT NULL THEN 'Supporter'
                    ELSE 'Unknown'
                END AS role
        FROM user
        LEFT JOIN artist ON artist.userId = user.userId
        LEFT JOIN supporter ON supporter.userId = user.userId
        WHERE user.userId = %s
          AND user.accountStatus <> 'Deleted'
          AND user.userId NOT IN (SELECT administrator.userId FROM administrator)
    """, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user

def email_in_use(email, user_id):
    """Check if another account already uses this email address.
    userId <> %s skips the account being edited, so keeping the same email is allowed.
    Returns True if another account was found, otherwise False.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  user.userId
        FROM user                 
        WHERE user.email = %s
          AND user.userId <> %s
    """, (email, user_id))
    existing_user = cursor.fetchone()
    cursor.close()
    return existing_user is not None

def update_user_details(user_id, firstname, surname, email):
    """Save the edited names and email for an artist/supporter account.
    Admin and deleted accounts are protected by the WHERE conditions.
    No rowcount is returned, because saving without any changes also gives 0 rows.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE user
        SET firstname = %s,
            surname = %s,
            email = %s
        WHERE userId = %s
          AND accountStatus <> 'Deleted'
          AND userId NOT IN (SELECT administrator.userId FROM administrator)
    """, (firstname, surname, email, user_id))
    database.connection.commit()
    cursor.close()    

def change_user_status(user_id, current_status, new_status):
    """Suspend or reactivate an artist/supporter account (Active <-> Suspended).
    The update only runs if the account currently has current_status, and administrator accounts cannot be changed.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE user
        SET accountStatus = %s
        WHERE userId = %s
          AND accountStatus = %s
          AND userId NOT IN (SELECT administrator.userId FROM administrator)
    """, (new_status, user_id, current_status))
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def soft_delete_user(user_id):
    """Soft delete an artist/supporter account by setting its status to 'Deleted'. (Admins cannot be deleted)
    The data stays in the database, so the user's projects, donations and reports are kept, 
    but the account is hidden from the table.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE user
        SET accountStatus = 'Deleted'   
        WHERE userId = %s
          AND accountStatus IN ('Active', 'Suspended')
          AND userId NOT IN (SELECT administrator.userId FROM administrator)
    """, (user_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows    


# ----- Reported Content -----

def get_reports():
    """Get all reports for the reported content table, newest first.
    JOIN user gives the reporter's name. 
    LEFT JOIN + CASE finds the reporter's role, the same way as get_users().
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  report.reportId,
                report.reportedContent,
                report.reason,
                CONCAT(user.firstname, ' ', user.surname) AS reporterName,
                CASE
                    WHEN administrator.userId IS NOT NULL THEN 'Administrator'
                    WHEN artist.userId IS NOT NULL THEN 'Artist'
                    WHEN supporter.userId IS NOT NULL THEN 'Supporter'
                    ELSE 'Unknown'
                END AS reporterRole,
                report.submittedDate,
                report.status
        FROM report
        JOIN user ON user.userId = report.reporterId
        LEFT JOIN administrator ON administrator.userId = report.reporterId
        LEFT JOIN artist ON artist.userId = report.reporterId
        LEFT JOIN supporter ON supporter.userId = report.reporterId
        ORDER BY report.submittedDate DESC
    """)
    reports = cursor.fetchall()
    cursor.close()
    return reports

def review_report(report_id, new_status):
    """Resolve or dismiss a pending report.
    Only pending reports can be reviewed, so a report isn't reviewed twice. (new_status = 'Resolved' or 'Dismissed')
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE report
        SET status = %s
        WHERE reportId = %s
          AND status = 'Pending'
    """, (new_status, report_id)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows


# ----- Featured Projects -----

def get_featured_projects():
    """Get all projects currently marked as featured for the featured panel.
    The featured column (TRUE/FALSE) decides if a project is featured.
    The home page reads the same column and shows up to 3 projects, but admin can monitor all featured projects in the dashboard.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName,
                CONCAT(user.firstname, ' ', user.surname) AS creatorName,
                category.categoryName,
                project.location
        FROM project
        JOIN user ON user.userId = project.creatorId
        JOIN category ON category.categoryId = project.categoryId
        WHERE project.featured = TRUE
        ORDER BY project.projectName ASC
    """)

    featured_projects = cursor.fetchall()
    cursor.close()
    return featured_projects

def get_feature_candidates():
    """Get projects that can be added to featured section (fills the dropdown).
    Only applicable for approved, active projects that aren't featured yet.
    Completed projects belong in success stories instead.
    """    
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName
        FROM project
        WHERE project.approvalStatus = 'Approved'
        AND project.projectStatus = 'Active'
        AND project.featured = FALSE
        ORDER BY project.projectName ASC
    """)

    feature_candidates = cursor.fetchall()
    cursor.close()
    return feature_candidates

def add_to_featured(project_id):
    """Mark a project as featured.
    The same conditions as get_feature_candidates are checked again here.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET featured = TRUE   
        WHERE projectId = %s
          AND approvalStatus = 'Approved'
          AND projectStatus = 'Active'
          AND featured = FALSE
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def remove_from_featured(project_id):
    """Take a project out from featured section (featured = FALSE)."""
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET featured = FALSE   
        WHERE projectId = %s
          AND featured = TRUE
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows


# ----- Success Stories -----

def get_success_stories():
    """Get all projects currently shown as success stories.
    The successStoryFeatured column (TRUE/FALSE) decides if a project is success story.
    The home page reads the same column and shows up to 2 projects, but admin can monitor all of them in the dashboard.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName,
                CONCAT(user.firstname, ' ', user.surname) AS creatorName,
                category.categoryName,
                project.location
        FROM project
        JOIN user ON user.userId = project.creatorId
        JOIN category ON category.categoryId = project.categoryId
        WHERE project.successStoryFeatured = TRUE
        ORDER BY project.projectName ASC
    """)

    success_stories = cursor.fetchall()
    cursor.close()
    return success_stories

def get_success_story_candidates():
    """Get projects that can be added to success stories section (fills the dropdown).
    Only applicable for approved, completed projects that aren't success stories yet.
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName
        FROM project
        WHERE project.approvalStatus = 'Approved'
        AND project.projectStatus = 'Completed'
        AND project.successStoryFeatured = FALSE
        ORDER BY project.projectName ASC
    """)

    success_story_candidates = cursor.fetchall()
    cursor.close()
    return success_story_candidates

def add_to_success_stories(project_id):
    """Show a project in success stories.
    Conditions are checked again, like add_to_featured.    
    """
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET successStoryFeatured = TRUE   
        WHERE projectId = %s
          AND approvalStatus = 'Approved'
          AND projectStatus = 'Completed'
          AND successStoryFeatured = FALSE
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def remove_from_success_stories(project_id):
    """Take a project out of success stories (successStoryFeatured = FALSE)."""
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET successStoryFeatured = FALSE   
        WHERE projectId = %s
          AND successStoryFeatured = TRUE
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

