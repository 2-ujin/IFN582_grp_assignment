/*
Yujin Lee CREATEd this file
- schema: maf (MakeArtsFund)
- table related UMF File
*/


-- STEP 1. table creation

    DROP DATABASE IF EXISTS maf; -- to avoid code error

    CREATE DATABASE maf
    ;

    USE maf
    ;

-- User table
    -- link to Artist, Supporter and Administrator tables
    CREATE TABLE user (
        userId int AUTO_INCREMENT ,
        firstname varchar(50) NOT NULL,
        surname varchar(50) NOT NULL,
        email varchar(100) UNIQUE NOT NULL, -- email should not be null and UNIQUE
        password varchar(255) NOT NULL, -- for werkzeug 
        accountStatus varchar(20) NOT NULL default 'active', -- active, suspended, deactivated
        PRIMARY KEY (userId)
    )
    ;


-- Artist table
    -- this table is child table of user.
    -- make sure to inherit from user table. (add function related to inheritance)
    CREATE TABLE artist (
        userId int,
        PRIMARY KEY (userId),
        FOREIGN KEY (userId) REFERENCES user(userId)

    )
    ;


-- Supporter:
    -- this table is child table of user.
    -- make sure to inherit from user table. (add function related to inheritance)
    CREATE TABLE supporter (
        userId int,
        PRIMARY KEY (userId),
        FOREIGN KEY (userId) REFERENCES user(userId)
    )
    ;

-- Administrator:
    -- this table is child table of user.
    -- make sure to inherit from user table. (add function related to inheritance)
    CREATE TABLE administrator (
        userId int,
        PRIMARY KEY (userId),
        FOREIGN KEY (userId) REFERENCES user(userId)
    )
    ;


-- Category:
    CREATE TABLE category (
        categoryId int AUTO_INCREMENT ,
        categoryName varchar(50) UNIQUE NOT NULL, -- category name should not be null and UNIQUE
        PRIMARY KEY (categoryId)
    )
    ;


-- Project table
    -- FK from artist & category table
    CREATE TABLE project (
        projectId int AUTO_INCREMENT,
        creatorId int NOT NULL,
        categoryId int NOT NULL,
        projectName varchar(100) NOT NULL,
        location varchar(100),
        imagePath varchar(255),
        goal decimal(16,2),
        deadline date,
        /* changed the column status -> approvalStatus & projectStatus for requirement for A3*/
        approvalStatus varchar(20) NOT NULL default 'pending', -- pending, approved, rejected, suspended

        projectStatus varchar(20) NOT NULL default 'active', -- active, paused, closed
        projectDescription text,
        artistIntro text,
        featured boolean NOT NULL default false,
        successStoryFeatured boolean NOT NULL default false,
        reviewerId int,
        updateDt datetime NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
        PRIMARY KEY (projectId),
        FOREIGN KEY (creatorId) REFERENCES artist(userId),
        FOREIGN KEY (categoryId) REFERENCES category(categoryId),
        FOREIGN KEY (reviewerId) REFERENCES administrator(userId)
    )
    ;


-- donation table
    -- FK from project & supporter table

    CREATE TABLE donation (
        donationId int AUTO_INCREMENT ,
        projectId int NOT NULL,
        supporterId int NOT NULL,
        amount decimal(16,2) NOT NULL,
        donationDate datetime  NOT NULL default (now()),
        paymentMethod varchar(50)  NOT NULL,
        paymentStatus varchar(20) NOT NULL default 'pending', -- pending, completed, failed
        PRIMARY KEY (donationId),
        FOREIGN KEY (projectId) REFERENCES project(projectId),
        FOREIGN KEY (supporterId) REFERENCES supporter(userId)
    )
    ;


-- Supporter message table
    -- FK from donation

    CREATE TABLE supporterMessage (
        messageId int AUTO_INCREMENT,
        donationId int UNIQUE NOT NULL,
        postedDate datetime NOT NULL default (now()),
        message text NOT NULL,
        visibility boolean NOT NULL default true,
        PRIMARY KEY (messageId),
        FOREIGN KEY (donationId) REFERENCES donation(donationId)
    )
    ;

-- Project update table 
    -- FK from project table
    CREATE TABLE projectUpdate (
        updateId int AUTO_INCREMENT,
        projectId int NOT NULL,
        publishedDate datetime NOT NULL default (now()),
        title varchar(100) NOT NULL,
        description text,
        PRIMARY KEY (updateId),
        FOREIGN KEY (projectId) REFERENCES project(projectId)

    )
    ;


-- Report table 
    -- FK from project & user& message,  table

    CREATE TABLE report (
        reportId int AUTO_INCREMENT ,
        reporterId int NOT NULL,
        projectId int,
        messageId int,
        reportedContent text,
        reason varchar(255),
        reporterRole varchar(50),
        submittedDate datetime NOT NULL default (now()),
        status varchar(20) NOT NULL default 'pending',
        reviewerId int,
        PRIMARY KEY (reportId),
        FOREIGN KEY (reporterId) REFERENCES user(userId),
        FOREIGN KEY (projectId) REFERENCES project(projectId),
        FOREIGN KEY (messageId) REFERENCES supporterMessage(messageId),
        FOREIGN KEY (reviewerId) REFERENCES administrator(userId)
    )
    ;



-- image table 
    -- FK from projectUpdate table
    CREATE TABLE image (
        imageId int AUTO_INCREMENT,
        updateId int NOT NULL,
        imagePath varchar(255) NOT NULL,
        PRIMARY KEY (imageId),
        FOREIGN KEY (updateId) REFERENCES projectUpdate(updateId)
    )
    ;


-- STEP 2: DATA INSERT

