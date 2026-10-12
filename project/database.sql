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
        paymentStatus varchar(20) NOT NULL default 'Pending', -- Pending, Received, Failed
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
        ('Queenie', 'Kwok', 'queenie.work@gmail.com' ,'scrypt:32768:8:1$s9hNSCfN6VfIv5b4$078546c973768f5f4366de35994ed0c532ebe82502806c44cffd747c8971e3941c4a255a972a4844391ddac82b4143b1d1a4345588267975f54819c1f9b7740e', 'Active'),
        ('Melanie', 'Brant', 'm.brant@gmail.com' ,'scrypt:32768:8:1$N3kKmV1pQoBEw3Pb$bd5d0d425d83e5f40f7f4c4dec553b9457520ae4a9cc50493e079e48ef79c3252f40b48cb4dd770ec03fb54d3b3100fde27d2e88ac0ec48bd7ab6bcb682803df', 'Active'),
        ('M.', 'Cheung', 'marcokhc22@gmail.com' ,'scrypt:32768:8:1$iGPZHCx6oI7rWykK$d24e2800d8f3c496d26f732b98a0d636d7b8617fbcae91df077e9698dac6b82b880ab1946cc11be767e55173a8802924367d2298ed40d97616c0d7e23588155d', 'Active'),
        ('Lily', 'Cronin', 'n12345678@qut.edu.au' ,'scrypt:32768:8:1$FuEboelfJxtqOxUn$13e475ac6f57c35ce29af4411d9f44776e8f245b6db0b928780dfbbfe1b17d6ba9e46396a6a8c088e39bb034ae07222b6e837c23ba73eb87bcd2ba792155ea5b', 'Suspended'),
        ('Kayshay', 'Smith', 'kayshay@gmail.com' ,'scrypt:32768:8:1$ti40HvI1hawZpmu4$8ce337e88c0653ef15defb80dcf3ccb355d55a2c9a4226f9f5a14757a93beab87bae04bf95cbb01db535ce5ec8b4699ee2f3b1ae4001ff7a6df82d1472ebe3a0', 'Active'),
        ('Tim', 'Lee', 'leetim@gmail.com' ,'scrypt:32768:8:1$MIrhekl5wvbG9Lmr$d89fa862a957a298fdca06ace8075396d3d1c10b2313cdf6dda0b47e3ac35c1c2adf48a48c7e82089a25ec10f0070132094f51527dc41992c45eb40b7047e7c4', 'Active'),
        ('Eloise', 'Bao', 'ebao@hotmail.com' ,'scrypt:32768:8:1$EEwwzeh9Nz0U5G0l$a0fa6cb00dd544c6e8e58de7202e0c4d402100738ee9ea8420692e086fc989deca75dac3902e838ea4fb61b8a7ab131a925a9461ce541e000d677da95b3dba76', 'Active'),
        ('Janet', 'White', 'fpwjanet@gmail.com' ,'scrypt:32768:8:1$pSMtn40qdpzFLtj5$819fd726a663abaf6a6c1346cf173457835159018936c3969369f9adab28524f21ce36003f7aa025026561219d069c3abb4c9360d8051d4781c585bcda87611d', 'Active'),
        ('Samantha', 'Robinson', 'admin2@makeartsfund.com' ,'scrypt:32768:8:1$mV21J0yAIS3bGqF0$8abba29b932cde2829e822a7030590823bafeec001e0ea7427402ff5f8abd19b5094d92cba700b368c7d12eb1bfa3a56e638578f8da1a83de5fdb6ed5e94ec5a', 'Active'),
        ('Casey', 'Bright', 'admin23@makeartsfund.com' ,'scrypt:32768:8:1$Mr8kkZh5YNvRDNDE$ea4d538435288a5f31d73935c562295f925ab9cf2977f8f9efb090c056b93cd81541c753cc91fc390131f3fbc98823dfef4edee74f21b12597cc96c7b05261e6', 'Active'),
        ('Johnathan', 'Jones', 'jjones@gmail.com' ,'scrypt:32768:8:1$IWpwzvluZ7V5cuYe$3f58971ee6791d40da20ef32f029818542948ddf8c0e637f0fd2da049d27906849c883c7ffc3fbeec9085128f8bc2235eb21dd724931e6020340bc25cfe779fd', 'Active'),
        ('Hannah', 'Brown', 'hannahbrown@gmail.com' ,'scrypt:32768:8:1$y7YkDrsNfmeAEnKZ$5750ad754a7b0fa625a1d5cdd8e3652018e998948336fa7ec8296ba4410cc882289e6b42394897dca5253ee5e005c2819465e27e2229f359f367dea1c241636f', 'Active'),
        ('Maria', 'Watts', 'admin13@makeartsfund.com' ,'scrypt:32768:8:1$2M4NRQ8xsX5OMS7n$9c61c2c6180f2096156a822450e7f96520648495bb8dd7de940f7b9e22470e8fdf46a0ace8f66b30555ecbab1de60eccf4dc7b66a7970f2d25f454a1b3a52dde', 'Active'),
        ('Jayden', 'Butler', 'admin14@makeartsfund.com' ,'scrypt:32768:8:1$HhrniNXNIxQgmGKR$20ce724ce71732287d413706a506db9009e8926734a90a427ee5627800747bf039ed043b9f99a47a128a57dfccc623c3bcca20a6b9e8c9f3ef6954f00766915a', 'Active'),
        ('Nina', 'Burcher', 'admin15@makeartsfund.com' ,'scrypt:32768:8:1$3TcUO7DZM5eXGzUj$7b464ed0dab5dfaaf32f94ac3ab62e6857bef48dce33954c008b9d2a3204e866bec34fc59ad03fe56ab48e22d6d813f3be95b094ed1ee2fe31a5d60c53914f66', 'Active'),
        ('John', 'Thompson', 'thomjohn@gmail.com' ,'scrypt:32768:8:1$QW5P5ulQPDy42uN1$1c3582e77aeb9c4e1120eb1e8454b64764386c2b2e6d6eda0926e56055a6202176383506de2d6d518ba1907df0d620fdfdc96d6629df81f223ebc8aef961446b', 'Active'),
        ('Karen', 'Hack', 'khacker@gmail.com' ,'scrypt:32768:8:1$HSMvlTkC0HzoDfLH$c23fa8b83e434ceeccc842612e4b8c4b1dbd3607291b3b4d893afafb748edb94a5f048d2866992d479cbd493b5ad8f512923cb25e3e5a8fe7245088f90d0a4e1', 'Active')
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
        (1, 2, 'janie._.bean', 'Brisbane', 'img/janie._.bead.png', '5000', '2026-10-23', 'Approved','Active', 'janie._.bean is a family-based handmade seed bead project run by Janet and Queenie.', 'For 12 years, I''ve been making seed beads with my mother, Janet, and now we''ve decided to take it a step further to janie._.bean.', TRUE, FALSE, 15, '2026-08-01'),
        (3, 3, 'MORY Model Diary', 'Perth', 'img/MORY-Model-Diary.png', '6000', '2026-11-18', 'Approved','Active', 'Original 3D printed models.', 'Makes original printed models for 3 years.', TRUE, FALSE, 13, '2026-08-12'),
        (5, 2, 'Croshay', 'Sydney', 'img/Croshay.png', '8000', '2026-11-11', 'Approved', 'Active', 'Handmade local crochet accessories.', 'Design crochet accessories for 8 years.', TRUE, FALSE, 14, '2026-09-01'),
        (6, 4, 'Positioning in Melbourne', 'Melbourne', 'img/Positioning-in-Melbourne.png', '4500', '2026-10-02', 'Suspended', 'Completed', 'A photo series retracing postcard images to identify and photograph their exact original locations in Melbourne.', 'Capture my hometown in Melbourne.', FALSE, TRUE, 10, '2026-07-15'),
        (8, 2, 'Get Thready', 'Brisbane', 'img/Get-Thready.png', '7000', '2026-10-12', 'Suspended', 'Completed', 'Delicate handmade flower accessories crocheted from single strands of embroidery thread.', 'Makes embroidered flower accessories for 12 years.', FALSE, TRUE, 9, '2026-07-01'),
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
        (3,7, 300, '2026-08-14', 'PayPal', 'Received'),
        (1,12, 120, '2026-08-14', 'Card', 'Received'),
        (3,16, 100, '2026-08-02', 'BankTransfer', 'Received'),
        (5,2, 500, '2026-08-02', 'Card', 'Received')
    ;





    INSERT INTO supporterMessage 
        (donationId, postedDate, message, visibility)
    VALUES
        (1, '2026-09-21 19:42:00', 'Can''t wait to see the new bead collection! Wishing Janet and Queenie all the best.', TRUE),
        (2, '2026-09-14 10:15:00', 'I bought one of your bracelets at a Brisbane market last year and still wear it every day. So happy to support you!', TRUE),
        (3, '2026-09-14 21:03:00', 'Good luck reaching your goal!', TRUE),
        (4, '2026-10-02 13:27:00', 'Click the link below and veiw more about caft activities: www.hellocraft.com !', FALSE),
        (5, '2026-10-02 08:50:00', 'Twelve years of flower craft deserves this next step. Proud to be one of your first supporters!', TRUE)
    ;

-- REPORT
    INSERT INTO report 
        (
        reporterId,
        projectId,
        messageId,
        reportedContent,
        reason,
        submittedDate,
        status,
        reviewerId)
    VALUES
        (1, 2, NULL, 'Project image', 'Copyright of image posted', '2026-08-19', 'Pending', NULL),
        (5, NULL, 4, 'Supporter messages', 'Inappropriate language.', '2026-08-06', 'Resolved', 13),
        (17, 3, NULL, 'Project description', 'Misleading information', '2026-08-05', 'Resolved', 14),
        (12, 4, NULL, 'Content under Project Updates', 'Disclosure of sensitive personal info', '2026-07-20', 'Resolved', 10),
        (2, 4, NULL, 'Project image', 'Copyright of image posted', '2026-07-21', 'Resolved', 9)
    ;


-- PROJECT UPDATE

    INSERT INTO projectUpdate 
        (projectId, publishedDate, title, description)
    VALUES
        (1, '2026-10-14', 'Pop-Up Store in October', 'We''re excited to announce that janie._.bean is preparing for a pop-up store at Wintergarden, Queen Street Mall, starting from 1 September 2026 for a month.'),
        (1, '2026-10-02', 'See you at the West End Market this Saturday!', 'We''re excited to share that we will have a sales booth at the West End Market on 8 August, from 9:00 am to 2:00 pm.'),
        (2, '2026-10-11', 'Our First Product is Out!', 'The first printed model is on sale now.'),
        (3, '2026-10-07', 'Halloween crochet series', 'No tricks but just treats: up to 20% off for the Halloween Series'),
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