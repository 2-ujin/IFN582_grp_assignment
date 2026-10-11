from dataclasses import dataclass, field
from datetime import datetime,date
from typing import Optional
from enum import Enum


# user

class AccountStatus(Enum):
    ACTIVE = 'Active'
    SUSPENDED = 'Suspended'
    DEACTIVATED = 'Deactivated'
    
@dataclass
class User:
    id: int
    firstname: str
    surname: str
    email: str
    password: str = field (repr=False)
    accountStatus: AccountStatus = AccountStatus.ACTIVE


# define class attribute for artist supporter administrator
class Artist(User):
    role = 'Artist'

class Supporter(User):
    role = 'Supporter'

class Administrator(User):
    role = 'Administrator'


class ApprovalStatus(Enum):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    SUSPENDED = 'Suspended'

class ProjectStatus(Enum):
    ACTIVE = 'Active'
    PAUSED = 'Paused'
    COMPLETED = 'Completed'


# Category 
@dataclass
class Category:
    categoryId: int
    categoryName: str


# Project
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





# donation

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


# supporterMessage

@dataclass
class SupporterMessage:
    messageId: int
    donation: Donation
    message: str
    postedDate: datetime = field(default_factory=lambda: datetime.now())
    visibility: bool = True


# projectUpdate

@dataclass
class ProjectUpdate:
    updateId: int
    project: Project
    title: str
    description: Optional[str]
    publishedDate: datetime = field(default_factory=lambda: datetime.now())

# Report

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


# Image

@dataclass
class Image:
    imageId: int
    update: ProjectUpdate
    imagePath: str


# ----- Part 5. Admin Dashboard -----
from . import database

def get_pending_projects():
    # Projects waiting for admin to approve or reject

    cursor = database.connection.cursor()
    cursor.execute("""
        SELECT  project.projectId,
                project.projectName,
                CONCAT(user.firstname, ' ', user.surname) AS creatorName,
                category.categoryName,
                project.location,
                project.updateDt AS submittedDate  -- submitted date 추가할 수 있는지 Part 1과 확인 필요
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
          And approvalStatus = 'Pending'
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
          And approvalStatus = %s
    """, (new_status, project_id, current_status)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows

def soft_delete_project(project_id):
    # Hide reviewed projects by setting their approval status to 'Removed'
    cursor = database.connection.cursor()
    cursor.execute("""
        UPDATE project
        SET approvalStatus = 'Removed',
            featured = FALSE   
        WHERE projectId = %s
          And approvalStatus IN ('Approved', 'Suspended', 'Rejected')
    """, (project_id,)) 
    database.connection.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    return updated_rows
