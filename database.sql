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
        accountStatus varchar(20) NOT NULL default 'Active', -- Active, Suspended, Deactivated
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
        approvalStatus varchar(20) NOT NULL default 'Pending', -- Pending, Approved, Rejected, Suspended

        projectStatus varchar(20) NOT NULL default 'Active', -- Active, Paused, Completed
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
        paymentStatus varchar(20) NOT NULL default 'Pending', -- pending, completed, failed
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
        status varchar(20) NOT NULL default 'Pending',
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

-- USER
    INSERT INTO user
        (       firstname,
                surname,
                email, -- email should not be null and UNIQUE
                password, -- for werkzeug 
                accountStatus -- active, suspended, deactivated
        )
    VALUES 
        ('Queenie', 'Kwok', 'queenie.work@gmail.com' ,'0b14d501a594442a01c6859541bcb3e8164d183d32937b851835442f69d5c94e', 'Active'),
        ('Melanie', 'Brant', 'm.brant@gmail.com' ,'6cf615d5bcaac778352a8f1f3360d23f02f34ec182e259897fd6ce485d7870d4', 'Active'),
        ('M.', 'Cheung', 'marcokhc22@gmail.com' ,'5906ac361a137e2d286465cd6588ebb5ac3f5ae955001100bc41577c3d751764', 'Active'),
        ('Lily ', 'Cronin', 'n12345678@qut.edu.au' ,'b97873a40f73abedd8d685a7cd5e5f85e4a9cfb83eac26886640a0813850122b', 'Suspended'),
        ('Kayshay', 'Smith', 'kayshay@gmail.com' ,'8b2c86ea9cf2ea4eb517fd1e06b74f399e7fec0fef92e3b482a6cf2e2b092023', 'Active'),
        ('Tim', 'Lee', 'leetim@gmail.com' ,'598a1a400c1dfdf36974e69d7e1bc98593f2e15015eed8e9b7e47a83b31693d5', 'Active'),
        ('Eloise', 'Bao', 'ebao@hotmail.com' ,'5860836e8f13fc9837539a597d4086bfc0299e54ad92148d54538b5c3feefb7c', 'Active'),
        ('Janet', 'White', 'fpwjanet@gmail.com' ,'57f3ebab63f156fd8f776ba645a55d96360a15eeffc8b0e4afe4c05fa88219aa', 'Active'),
        ('Samantha', 'Robinson', 'admin2@makeartsfund.com ' ,'9323dd6786ebcbf3ac87357cc78ba1abfda6cf5e55cd01097b90d4a286cac90e', 'Active'),
        ('Casey', 'Bright', 'admin23@makeartsfund.com ' ,'aa4a9ea03fcac15b5fc63c949ac34e7b0fd17906716ac3b8e58c599cdc5a52f0', 'Active'),
        ('Johnathan', 'Jones', 'jjones@gmail.com' ,'53d453b0c08b6b38ae91515dc88d25fbecdd1d6001f022419629df844f8ba433', 'Active'),
        ('Hannah ', 'Brown', 'hannahbrown@gmail.com' ,'b3d17ebbe4f2b75d27b6309cfaae1487b667301a73951e7d523a039cd2dfe110', 'Active'),
        ('Maria', 'Watts', 'admin13@makeartsfund.com ' ,'48caafb68583936afd0d78a7bfd7046d2492fad94f3c485915f74bb60128620d', 'Active'),
        ('Jayden', 'Butler', 'admin14@makeartsfund.com ' ,'c6863e1db9b396ed31a36988639513a1c73a065fab83681f4b77adb648fac3d6', 'Active'),
        ('Nina', 'Burcher', 'admin15@makeartsfund.com ' ,'c63c2d34ebe84032ad47b87af194fedd17dacf8222b2ea7f4ebfee3dd6db2dfb', 'Active'),
        ('John ', 'Thompson', 'thomjohn@gmail.com' ,'17a3379984b560dc311bb921b7a46b28aa5cb495667382f887a44a7fdbca7a7a', 'Active'),
        ('Karen ', 'Hack', 'khacker@gmail.com' ,'69bfb918de05145fba9dcee9688dfb23f6115845885e48fa39945eebb99d8527', 'Active')
    ;

-- ARTIST
    INSERT INTO artist (userId)
    VALUES 
     (1),(3),(5),(6),(8)
    ;

 -- SUPPORTER
    INSERT INTO supporter (userId)
    VALUES 
     (2),(4),(7), (11), (12), (16), (17)
    ;

-- ADMINISTRATOR
    INSERT INTO administrator (userId)
    VALUES 
        (9),(10),(13), (14), (15)
    ;


-- CATEGORY

    INSERT INTO category (categoryName)
    VALUES 
        ('Visual Arts'),
        ('Handicrafts'),
        ('3D Printing'),
        ('Photography'),
        ('Music'),
        ('Film & Performance')
    ;




-- PROJECT
    INSERT INTO project 
    (
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
        featured,
        successStoryFeatured,
        reviewerId,
        updateDt

    )
    VALUES 
        (1, 2, 'janie._.bean', 'Brisbane', 'img/janie._.bead.png', '5000', '2026-09-23', 'Approved','Active', 'janie._.bean is a family-based handmade seed bead project run by Janet and Queenie.', 'For 12 years, I''ve been making seed beads with my mother, Janet, and now we''ve decided to take it a step further to janie._.bean.', TRUE, FALSE, 15, '2026-08-01'),
        (3, 3, 'MORY Model Diary', 'Perth', 'img/MORY-Model-Diary.png', '6000', '2026-09-18', 'Approved','Active', 'Original 3D printed models.', 'Makes original printed models for 3 years.', TRUE, FALSE, 13, '2026-08-12'),
        (5, 2, 'Croshay', 'Sydney', 'img/Croshay.png', '8000', '2026-09-11', 'Approved', 'Active', 'Handmade local crochet accessories.', 'Design crochet accessories for 8 years.', TRUE, FALSE, 14, '2026-09-01'),
        (6, 4, 'Positioning in Melbourne', 'Melbourne', 'img/Positioning-in-Melbourne.png', '4500', '2026-08-02', 'Suspended', 'Completed', 'A photo series retracing postcard images to identify and photograph their exact original locations in Melbourne.', 'Capture my hometown in Melbourne.', FALSE, TRUE, 10, '2026-07-15'),
        (8, 2, 'Get Thready', 'Brisbane', 'img/Get-Thready.png', '7000', '2026-08-12', 'Suspended', 'Completed', 'Delicate handmade flower accessories crocheted from single strands of embroidery thread.', 'Makes embroidered flower accessories for 12 years.', FALSE, TRUE, 9, '2026-07-01'),
        (5, 2, 'Doll Craft', 'Gold Coast', 'img/Doll_Craft.jpg', '5500', '2026-12-15', 'Pending', 'Active', 'Handmade fabric dolls with hand-stitched outfits and tiny accessories.', 'Sewing and designing one-of-a-kind dolls for 6 years.', FALSE, FALSE, 13, '2026-10-02'),
        (3, 4, 'Brisbane After Dark', 'Brisbane', 'img/Brisbane-After-Dark.png', '4000', '2026-12-20', 'Pending', 'Active', 'A night photography series capturing Brisbane''s laneways, bridges and riverfront after sunset.', 'Shooting long-exposure city photography for 5 years.', FALSE, FALSE, 10, '2026-10-06'),
        (8, 1, 'Inkwell Botanica', 'Hobart', 'img/Inkwell-Botanica.png', '3500', '2026-11-30', 'Approved', 'Active', 'Botanical ink and watercolour illustrations of native Tasmanian plants.', 'Illustrating native flora for 7 years.', FALSE, FALSE, 15, '2026-09-20'),
        (6, 5, 'Botanic Garden Jazz Concert', 'Brisbane', 'img/Botanic-Garden-Jazz-Concert.png', '9000', '2026-12-05', 'Approved', 'Active', 'A free outdoor jazz concert series held at Brisbane''s City Botanic Gardens on summer evenings.', 'Performing and organising live jazz gigs for 10 years.', TRUE, FALSE, 14, '2026-09-25'),
        (8, 6, 'Small Stage Stories', 'Adelaide', 'img/Small-Stage-Stories.png', '12000', '2026-12-18', 'Approved', 'Active', 'A short documentary following three independent theatre troupes through one festival season.', 'Directing short films about local performers for 4 years.', FALSE, FALSE, 13, '2026-10-01'),
        (1, 6, 'Puppet Theatre on Wheels', 'Canberra', 'img/Puppet-Theatre-on-Wheels.png', '7500', '2026-11-20', 'Approved', 'Active', 'A travelling puppet show bringing free performances to regional schools.', 'Building puppets and performing for children for 11 years.', TRUE, FALSE, 9, '2026-09-15'),
        (3, 1, 'Street Canvas Project', 'Melbourne', 'img/Street-Canvas-Project.png', '6500', '2026-08-20', 'Approved', 'Completed', 'Community murals painted with local residents on blank laneway walls.', 'Painting public murals for 9 years.', FALSE, TRUE, 9, '2026-06-15'),
        (5, 5, 'Choir of the Coast', 'Gold Coast', 'img/Choir-of-the-Coast.png', '5000', '2026-07-30', 'Approved', 'Completed', 'A community choir recording its first album of coastal folk songs.', 'Leading a community choir for 15 years.', FALSE, TRUE, 15, '2026-05-20'),
        (3, 3, 'Tiny Terrain', 'Darwin', 'img/Tiny-Terrain.png', '4800', '2027-01-10', 'Pending', 'Active', '3D printed miniature dioramas of Top End landscapes.', 'Designing printable terrain models for 2 years.', FALSE, FALSE, 14, '2026-10-08'),
        (1, 5, 'Lo-fi Bedroom Beats', 'Sydney', 'img/Lo-fi-Bedroom-Beats.png', '3000', '2027-01-15', 'Suspended', 'Active', 'A lo-fi instrumental album produced entirely in a home studio.', 'Producing chill beats for 3 years.', FALSE, FALSE, 10, '2026-09-12')
;

-- DONATION


    INSERT INTO donation 
        (projectId, supporterId, amount, donationDate, paymentMethod, paymentStatus)
    VALUES
        (1,11, 200, '2026-08-21', 'Card', 'Pending'),
        (1,7, 300, '2026-08-14', 'PayPal', 'Received'),
        (1,12, 120, '2026-08-14', 'Card', 'Received'),
        (1,16, 100, '2026-08-02', 'BankTransfer', 'Received'),
        (1,2, 500, '2026-08-02', 'Card', 'Received')
    ;





    INSERT INTO supporterMessage 
        (donationId, postedDate, message, visibility)
    VALUES
        (1, '2026-08-21 19:42:00', 'Can''t wait to see the new bead collection! Wishing Janet and Queenie all the best.', TRUE),
        (2, '2026-08-14 10:15:00', 'I bought one of your bracelets at a Brisbane market last year and still wear it every day. So happy to support you!', TRUE),
        (3, '2026-08-14 21:03:00', 'Love that this is a mother and daughter project. Good luck reaching your goal!', TRUE),
        (4, '2026-08-02 13:27:00', 'Click the link below and veiw more about caft activities: www.hellocraft.com !', FALSE),
        (5, '2026-08-02 08:50:00', 'Twelve years of craft deserves this next step. Proud to be one of your first supporters!', TRUE)
    ;

-- REPORT
    INSERT INTO report 
        (
        reporterId,
        projectId,
        messageId,
        reportedContent,
        reason,
        reporterRole,
        submittedDate,
        status,
        reviewerId)
    VALUES
        (1, 2, NULL, 'Project image', 'Copyright of image posted', 'Artist', '2026-08-19', 'Pending', NULL),
        (5, NULL, 4, 'Supporter messages', 'Inappropriate language.', 'Artist', '2026-08-06', 'Resolved', 13),
        (17, 3, NULL, 'Project description', 'Misleading information', 'Supporter', '2026-08-05', 'Resolved', 14),
        (12, 4, NULL, 'Content under Project Updates', 'Disclosure of sensitive personal info', 'Supporter', '2026-07-20', 'Resolved', 10),
        (2, 4, NULL, 'Project image', 'Copyright of image posted', 'Supporter', '2026-07-21', 'Resolved', 9)
    ;


-- PROJECT UPDATE

    INSERT INTO projectUpdate 
        (projectId, publishedDate, title, description)
    VALUES
        (1, '2026-08-14', 'Pop-Up Store in September', 'We''re excited to announce that janie._.bean is preparing for a pop-up store at Wintergarden, Queen Street Mall, starting from 1 September 2026 for a month.'),
        (1, '2026-08-02', 'See you at the West End Market this Saturday!', 'We''re excited to share that we will have a sales booth at the West End Market on 8 August, from 9:00 am to 2:00 pm.'),
        (2, '2026-08-11', 'Our First Product is Out!', 'The first printed model is on sale now.'),
        (3, '2026-09-07', 'Halloween crochet series', 'No tricks but just treats: up to 20% off for the Halloween Series'),
        (4, '2026-07-20', 'Upcoming exhibit', 'The final photo album is ready to exhibit on 30 July')
    ;


-- IMAGE

    INSERT INTO image 
        (updateId, imagePath)
    VALUES
        (1, 'updates/store.jpg'),
        (1, 'updates/storecollection.jpg'),
        (2, 'updates/market.jpg'),
        (3, 'updates/model.jpg'),
        (4, 'updates/crochet.jpg'),
        (5, 'updates/photos.jpg')
    ;