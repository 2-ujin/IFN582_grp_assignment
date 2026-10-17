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
    def is_active(self):
        """Return the boolean Flask-Login uses before allowing a session."""
        return self.accountStatus is AccountStatus.ACTIVE
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


# ----- Part 5. Admin Dashboard -----

def get_campaign_stats():
    # Display the total number of campaigns including active and pending
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
    # Display the total number of active creators
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
    # Display the total number of active supporters
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
    # Display the total number of reports including pending
    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  COUNT(*) AS totalReports,
                SUM(report.status = 'Pending') AS pendingReports
        FROM report
    """)
    report_stats = cursor.fetchone()
    cursor.close()
    return report_stats

def get_pending_projects():
    # Projects waiting for admin to approve or reject

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
    # Admin reviews a pending project and approves or rejects it
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
    # Projects that have already been reviewed (not Pending or Removed)
    
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
    # Update project approval status (approved -> suspended or suspended -> approved)
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET approvalStatus = %s,
            featured = FALSE  # Remove suspended projects from featured projects 
        WHERE projectId = %s
          AND approvalStatus = %s
    """, (new_status, project_id, current_status)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def soft_delete_project(project_id):
    # Hide reviewed projects by setting their approval status to 'Deleted'
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

def get_users():
    # Display all accounts for the user management table
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
    # Get a specific account to fill in the edit user form
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
    # Check if another account already uses this email address
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
    # Save the changes for an artist/supporter account
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
    cursor.close    

def change_user_status(user_id, current_status, new_status):
    # Suspend or reactivate an artist/supporter account
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
    # Hide an artist/supporter account and keep the record in database
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE user
        SET approvalStatus = 'Deleted'   
        WHERE userId = %s
          AND accountStatus IN ('Active', 'Suspended')
          AND userId NOT IN (SELECT administrator.userId FROM administrator)
    """, (user_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows    

def get_reports():
    # Display all reports for the reported content table
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
    # Admin reviews a pending report and resolves or dismisses it
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

def get_featured_projects():
    # Projects currently shown in featured section
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
    # Get projects that can be added to featured section
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
    # Show a project in featured section
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET featured = TRUE   
        WHERE projectId = %s
          And approvalStatus = 'Approved'
          And projectStatus = 'Active'
          AND featured = FALSE
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def remove_from_featured(project_id):
    # Take a project out from featured section
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

def get_success_stories():
    # Projects currently shown in success stories section
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
    # Get projects that can be added to success stories section
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
    # Show a project in success stories section
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET successStoryFeatured = TRUE   
        WHERE projectId = %s
          And approvalStatus = 'Approved'
          And projectStatus = 'Completed'
          AND successStoryFeatured = FALSE
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def remove_from_success_stories(project_id):
    # Take a project out from success stories section
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

