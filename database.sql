/*
Yujin Lee created this file
- schema: maf (MakeArtsFund)
- table related UMF File
*/


-- STEP 1. table creation

    DROP DATABASE IF EXISTS maf; -- to avoid code error

    create database maf
    ;

    use maf
    ;

-- User table
    -- link to Artist, Supporter and Administrator tables
    create table user (
        userId int AUTO_INCREMENT ,
        firstname varchar(50) not null,
        surname varchar(50) not null,
        email varchar(100) unique not null, -- email should not be null and unique
        password varchar(255) not null, -- for werkzeug 
        accountStatus varchar(20) not null default 'active', -- active, suspended, deactivated
        primary key (userId)
    )
    ;


-- Artist table
    -- this table is child table of user.
    -- make sure to inherit from user table. (add function related to inheritance)
    create table artist (
        userId int,
        primary key (userId),
        foreign key (userId) references user(userId)

    )
    ;


-- Supporter:
    -- this table is child table of user.
    -- make sure to inherit from user table. (add function related to inheritance)
    create table supporter (
        userId int,
        primary key (userId),
        foreign key (userId) references user(userId)
    )
    ;

-- Administrator:
    -- this table is child table of user.
    -- make sure to inherit from user table. (add function related to inheritance)
    create table administrator (
        userId int,
        primary key (userId),
        foreign key (userId) references user(userId)
    )
    ;


-- Category:
    create table category (
        categoryId int AUTO_INCREMENT ,
        categoryName varchar(50) unique not null, -- category name should not be null and unique
        primary key (categoryId)
    )
    ;


-- Project table
    -- FK from artist & category table
    create table project (
        projectId int AUTO_INCREMENT,
        creatorId int not null,
        categoryId int not null,
        projectName varchar(100) not null,
        location varchar(100),
        imagePath varchar(255),
        goal decimal(16,2),
        deadline date,
        /* changed the column status -> approvalStatus & projectStatus for requirement for A3*/
        approvalStatus varchar(20) not null default 'pending', -- pending, approved, rejected, suspended

        projectStatus varchar(20) not null default 'active', -- active, paused, closed
        projectDescription text,
        artistIntro text,
        featured boolean not null default false,
        successStoryFeatured boolean not null default false,
        reviewerId int,
        updateDt datetime not null default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
        primary key (projectId),
        foreign key (creatorId) references artist(userId),
        foreign key (categoryId) references category(categoryId),
        foreign key (reviewerId) references administrator(userId)
    )
    ;


-- donation table
    -- FK from project & supporter table

    create table donation (
        donationId int AUTO_INCREMENT ,
        projectId int not null,
        supporterId int not null,
        amount decimal(16,2) not null,
        donationDate datetime  not null default (now()),
        paymentMethod varchar(50)  not null,
        paymentStatus varchar(20) not null default 'pending', -- pending, completed, failed
        primary key (donationId),
        foreign key (projectId) references project(projectId),
        foreign key (supporterId) references supporter(userId)
    )
    ;


-- Supporter message table
    -- FK from donation

    create table supporterMessage (
        messageId int AUTO_INCREMENT,
        donationId int unique not null,
        postedDate datetime not null default (now()),
        message text not null,
        visibility boolean not null default true,
        primary key (messageId),
        foreign key (donationId) references donation(donationId)
    )
    ;

-- Project update table 
    -- FK from project table
    create table projectUpdate (
        updateId int AUTO_INCREMENT,
        projectId int not null,
        publishedDate datetime not null default (now()),
        title varchar(100) not null,
        description text,
        primary key (updateId),
        foreign key (projectId) references project(projectId)

    )
    ;


-- Report table 
    -- FK from project & user& message,  table

    create table report (
        reportId int AUTO_INCREMENT ,
        reporterId int not null,
        projectId int,
        messageId int,
        reportedContent text,
        reason varchar(255),
        reporterRole varchar(50),
        submittedDate datetime not null default (now()),
        status varchar(20) not null default 'pending',
        reviewerId int,
        primary key (reportId),
        foreign key (reporterId) references user(userId),
        foreign key (projectId) references project(projectId),
        foreign key (messageId) references supporterMessage(messageId),
        foreign key (reviewerId) references administrator(userId)
    )
    ;



-- image table 
    -- FK from projectUpdate table
    create table image (
        imageId int AUTO_INCREMENT,
        updateId int not null,
        imagePath varchar(255) not null,
        primary key (imageId),
        foreign key (updateId) references projectUpdate(updateId)
    )
    ;


-- STEP 2: DATA INSERT

