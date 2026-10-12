IFN582 Assessment 3 - MakeArtsFund

LOCAL SETUP

1. Install Python 3.13 and MySQL Server. This version is recommended because
   requirements.txt pins mysqlclient 2.2.7.
2. From this folder, create and activate a virtual environment:
   python3.13 -m venv .venv
   source .venv/bin/activate
3. On macOS, install mysqlclient's build tools if they are not already present:
   brew install pkg-config mysql-client
   export PKG_CONFIG_PATH="$(brew --prefix)/opt/mysql-client/lib/pkgconfig"
   On other platforms, install the MySQL client development libraries required
   by mysqlclient before continuing.
4. Install the permitted packages:
   python -m pip install -r requirements.txt
5. Configure the local MySQL connection. In a macOS or Linux terminal, set:
   export MYSQL_HOST=localhost
   export MYSQL_USER=root
   export MYSQL_PASSWORD='your-local-mysql-password'
   export MYSQL_DB=maf
   export FLASK_SECRET_KEY='use-a-long-random-value-for-this-local-run'
6. Import the hand-written schema and sample data:
   mysql -u "$MYSQL_USER" -p < project/database.sql
   The SQL script drops and recreates the maf database. Back up any existing maf data first.
7. Start the application:
   python run.py
8. Open http://127.0.0.1:8888/login in a browser to view the styled login page.

The account passwords are stored as Werkzeug hashes in database.sql. The login
page displays the matching assessment test credentials for the three roles.
For a fresh installation, import database.sql before starting the application.

PART 2 INTEGRATION NOTES

- Login uses an email address and password.
- Fundraiser accounts are represented by rows in the artist table.
- New public registrations can create Supporter or Fundraiser accounts only.
- Only Active accounts can sign in. Suspended and Deactivated accounts receive
  a status-specific message.
- Role decorators are available in project.views:
  admin_required, fundraiser_required, and supporter_required.
- Other page owners should extend project/templates/base.html and use the
  shared classes in project/static/css/styles.css.
- Shared colours, typography, spacing, and navigation guidance are in
  project/STYLE_GUIDE.md.
- Login, registration, and error pages keep the MakeArtsFund logo and English
  language selector in the header, and use the Assessment 1 footer links.
- Registration accepts 10-255 ASCII letters and digits for a password.

WHERE TO FOLLOW THE PART 2 CODE

1. run.py calls create_app() in project/__init__.py. The factory loads settings,
   starts the shared database/login/CSRF extensions, registers views.py, and adds
   the common error pages.
2. login.html and register.html render the forms from forms.py. Flask-WTF checks
   submitted values on the server and includes a CSRF token in each POST form.
3. views.py handles the submitted forms. Login looks up the email, checks its
   password hash, rejects non-Active accounts, and starts a Flask-Login session.
4. models.py reads account fields and joins the user row to the role table. The
   artist table is displayed in the app as the Fundraiser role.
5. On later requests, Flask-Login reloads the account. The inactive-account hook
   ends sessions for Suspended or Deactivated accounts; role decorators protect
   routes that Part 3-5 add.
6. base.html is the shared page shell. It shows navigation, flash messages, and
   the footer; login.html, register.html, and error.html fill its content block.
7. styles.css contains shared colours, layout, focus, form, error, and responsive
   rules. STYLE_GUIDE.md explains how teammates should extend the same design.

For a quick code reading order, start with project/__init__.py, then
project/forms.py, project/models.py, project/views.py, and the three templates.
The SQL file creates the tables first, inserts sample users and their role rows,
then sets hashes for the six assessment test accounts.
