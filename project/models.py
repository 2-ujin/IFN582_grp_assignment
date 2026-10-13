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
