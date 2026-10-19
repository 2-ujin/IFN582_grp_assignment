IFN582 Assignment 3 - MakeArtsFund(MAF)
 

Project Info

1. About the Project
MakeArtsFund is a crowdfunding web application designed to support creative arts projects in Australia. The platform connects local artists with supporters who wish to contribute to original artistic work. It is intended to assist artists in raising funds for projects in various categories such as Visual Arts, Handicrafts, 3D Printing, Photography, Music, and Film & Performance. Users can browse campaigns by category and location, helping them discover creative projects in their local communities.

2. GroupID: Mostafa - Gr 3
3. Team Member:
    - Hao-Chun Chang (n12554839)
    - Hiu Lam Queenie Kwok (n12876615)
    - Lim Li San (n12768065)
    - Woolim Han (n12873217)
    - Yujin Lee (n12537675)



Setup Instructions
---------------------

1. System Requirements
    - Python 3.13 (Tested)
    - MySQL Server 8.0+ (running on localhost)
    - MySQL user: root, password: 123456
    (If your MySQL credentials differ, Change the password to match your MySQL server from project/__init__.py line:)
    
    > MYSQL_PASSWORD=os.environ.get("MYSQL_PASSWORD", "123456")


2. Install dependencies
   Open terminal in this folder and run:

   > pip3 install -r requirements.txt

3. Database Setup
    Run project/database.sql in MySQL once from terminal before starting the app.

    >  mysql -u root -p < project/database.sql

4. Run the application

    > python3 run.py

    After run the code, open http://127.0.0.1:8888 in your web browser.



5. Test Accounts
    ----------------------------------------------------------
    | Role          | Email                     | Password   |
    |---------------|---------------------------|------------|
    | Fundraiser    | queenie.work@gmail.com    | Password1  |
    | Fundraiser    | marcokhc22@gmail.com      | Password3  |
    | Supporter     | m.brant@gmail.com         | Password2  |
    | Supporter     | ebao@hotmail.com          | Password7  |
    | Administrator | admin2@makeartsfund.com   | Password9  |
    | Administrator | admin23@makeartsfund.com  | Password10 |
    ----------------------------------------------------------

6. Key Features to Test

1) Without Login
    - View Featured projects and Success Stories.
    - Register a new account and log in / log out.

2) Fundraiser Accounts
    - Open Campaign Management to create a new project (name, category, location, goal, deadline, description).
    - Edit a project, change its status, and post / edit / delete project updates.

3) Supporter Accounts
    - Open a project detail page and make a donation (amount, message, payment method).

4) Administrator Accounts
    - Open Admin Dashboard(/admin) to approve, reject, suspend, restore or delete projects.
    - Suspend, reactivate, edit or delete users.
    - Dismiss or resolve reports; add / remove Featured projects and Success Stories.

5) Error cases
    - Wrong email or password, or a suspended account, cannot log in.
    - Donation amount of 0 or invalid is rejected; donating while logged out or as a Fundraiser is blocked.
    - A Supporter opening /admin or /management is denied.
    - 404 error case: http://127.0.0.1:8888/error-404
    - 500 error template link: http://127.0.0.1:8888/error-eg-500
