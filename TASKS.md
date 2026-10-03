# IFN582 Assignment 3 — Task Breakdown

**Project:** BUB (Brisbane University Bouldering Club) — Charity Event Fundraising Platform
**Due:** 23/10/2026 (Week 13) | **Demo:** Week 13 tutorial (4 min group demo + 5-6 min individual Q&A)
**Stack:** Flask + MySQL + Jinja2 + Bootstrap 5.3 only. No JavaScript, PHP, Flask-Admin, or other frameworks. No GenAI.

This builds on **BUB's A1 design + A2 database design** (charity event fundraising scenario). Roles: **Administrator / Fundraiser (event organiser) / Supporter (donor)**.

---

## How to use this file

- Each part below = one owner. Write your name next to "Owner:" when you claim a part.
- Check off each requirement as you complete it — these are taken directly from the Assessment 3 brief, not paraphrased loosely.
- Work on your own branch, open a PR into `IFN582_grp_assginment` when a part is ready, and tag someone for review before merging.
- If a requirement is unclear, ask in the group chat before guessing — markers check against the brief exactly.

---

## File Ownership Map

Some files belong to one part only. Others (`views.py`, `models.py`, `forms.py`) are shared — multiple parts add their own section to the same file, so **pull before you start, commit/push in small chunks, and mark your section with a comment header** (e.g. `# ---- Part 3: Home & Donation ----`) to avoid conflicts.

| Owner | File / Folder | What to do |
|---|---|---|
| Part 1 | `database.sql` | Write and own this file entirely — schema + constraints + sample data |
| Part 1 | `project/__init__.py` | Create the Flask app, configure DB connection, register blueprints |
| Part 1 | `run.py` | Entry point script that starts the app |
| Part 1 | `project/models.py` *(base)* | Create the file with base classes for each DB table (Campaign, User, Donation, Post, Report, etc.) |
| Part 2 | `project/models.py` *(add-on)* | Add/extend `User` role logic (admin/fundraiser/supporter checks) |
| Part 2 | `project/views.py` *(add-on)* | Add routes: register, login, logout, admin dashboard actions (approve/reject/suspend campaigns, manage users, manage reported content, manage featured) |
| Part 2 | `project/forms.py` *(add-on)* | Add `RegisterForm`, `LoginForm` |
| Part 2 | `project/templates/login.html` | Login page incl. the mandatory "Test Login Credentials For Assessment" block |
| Part 2 | `project/templates/register.html` | Registration page |
| Part 2 | `project/templates/admin_dashboard.html` | Administrator Dashboard page |
| Part 3 | `project/models.py` *(add-on)* | Add/extend `Campaign`, `Donation` classes |
| Part 3 | `project/views.py` *(add-on)* | Add routes: home (search/browse/featured), fundraiser details + donation submission |
| Part 3 | `project/forms.py` *(add-on)* | Add `DonationForm` |
| Part 3 | `project/templates/home.html` | Home page |
| Part 3 | `project/templates/donation.html` | Fundraiser Details and Donation page |
| Part 4 | `project/models.py` *(add-on)* | Add/extend `CampaignPost`/update-related classes |
| Part 4 | `project/views.py` *(add-on)* | Add routes: campaign management (create/edit/status/posts/stats) scoped to the logged-in fundraiser |
| Part 4 | `project/forms.py` *(add-on)* | Add `CampaignForm`, `CampaignPostForm` |
| Part 4 | `project/templates/campaign_management.html` | Campaign Management page |
| Part 5 | `project/views.py` *(add-on)* | Add Flask error handlers (404/500) |
| Part 5 | `project/templates/error.html` | Shared error page template |
| Part 5 | `project/static/css/` | Own the shared stylesheet/style guide (colours, fonts, spacing) used by all pages |
| Part 5 | `project/static/img/` | Shared/placeholder images not tied to one specific part |
| Part 5 | `README.txt` | Final setup/run instructions, written once the app is working |
| Part 5 | *(all templates)* | Final pass: navbar/footer consistency, responsive check across every page |

---

## Part 1 — Database & Project Foundation

**Owner:** _______________
**Priority:** Do this first — every other part depends on it.

### Requirements
- [ ] `database.sql` — hand-written (NOT an exported dump) SQL script that:
  - [ ] Creates all tables derived from the A2 data model (3NF)
  - [ ] Defines primary keys, foreign keys, and other constraints
  - [ ] Inserts all sample data, including the test login accounts (see Part 2)
- [ ] Sample data must meet these minimums:
  - [ ] ≥ 15 campaigns/events, across ≥ 2 categories
  - [ ] ≥ 6 users: ≥ 2 administrators, ≥ 2 fundraisers, ≥ 2 supporters
  - [ ] ≥ 5 donation/support records, across different fundraisers
  - [ ] ≥ 3 campaign posts/updates, across different fundraisers
  - [ ] ≥ 2 campaigns with status "pending approval"
  - [ ] ≥ 2 campaigns marked as featured
  - [ ] ≥ 2 reported-content records, attached to different campaigns/posts
- [ ] `models.py` — Python classes representing each DB table (one class per entity), following the Week 6 pattern (constructor + `get_*_details()` method)
- [ ] Flask project skeleton set up and running locally, matching the required submission structure:
  ```
  run.py
  project/
      __init__.py
      models.py
      views.py
      forms.py
      static/css/
      static/img/
      templates/
  ```
- [ ] Flask app successfully connects to MySQL and can run one test query end-to-end
- [ ] Share DB setup instructions (how to create the local MySQL database and import `database.sql`) with the team

---

## Part 2 — Authentication & Administrator Dashboard

**Owner:** _______________
**Depends on:** Part 1 (users table + models.py)

### Authentication requirements
- [ ] Registration, Login, Logout — fully working
- [ ] Hashed passwords (no plaintext storage)
- [ ] Session-based authentication
- [ ] Registered Supporters and Fundraisers can use their role's functionality immediately — **no admin approval needed for new accounts**
- [ ] New campaigns still require admin approval before going public (handled in Campaign Management + Admin Dashboard, but auth must support the role check)
- [ ] **Mandatory:** directly below the username/password fields on the login page, a clearly labelled **"Test Login Credentials For Assessment"** section showing role + username + password for working sample accounts — **two accounts per role** (admin, fundraiser, supporter)
- [ ] Access control implemented via custom decorators (e.g. `@admin_required`) or Flask-Login session-based role checks — **Flask-Admin is prohibited**
- [ ] Role restrictions enforced:
  - [ ] Admins → admin/moderation functionality only
  - [ ] Fundraisers → only their own campaigns and content
  - [ ] Supporters → browse + submit contributions when logged in
  - [ ] Guests → browse and view details only, no contributions

### Administrator Dashboard Page requirements
- [ ] Accessible **only** to Administrator users
- [ ] Review and manage campaigns
- [ ] Approve or reject new campaigns before they become publicly available
- [ ] Update campaign status, suspend campaigns, remove campaigns
- [ ] Manage user accounts — edit account details, suspend or remove accounts
- [ ] Review and manage content reported as inappropriate or misleading (reported-content records can come from sample data — a user-facing reporting form is not required, but if one is built it must be restricted to authenticated users)
- [ ] Select/remove campaigns in the Featured section of the Home Page

---

## Part 3 — Home Page + Fundraiser Details and Donation Page

**Owner:** _______________
**Depends on:** Part 1 (data), Part 2 (login check for donation form)

### Home Page requirements
- [ ] Display fundraisers/campaigns **dynamically from the database** (not hard-coded)
- [ ] Search functionality relevant to the scenario
- [ ] A Featured selection — each featured item links to its Fundraiser Details and Donation Page
- [ ] Categories/browsing options relevant to the scenario
- [ ] Brief description of how the platform works
- [ ] Responsive design; functional navbar/header and footer

### Fundraiser Details and Donation Page requirements
- [ ] Display: fundraiser/campaign name, image/banner, description of the organiser, description of fundraising purpose and goals
- [ ] Fundraising goal and amount raised to date
- [ ] Donor/support tiers (if relevant to design)
- [ ] Brief display of donation/support history — donor info, contribution amounts, messages left
- [ ] Posts, images, or updates from the fundraiser
- [ ] Guests may browse and view details
- [ ] To submit a donation, the user must be registered and logged in as a Supporter — if a guest tries, prompt them to log in/register
- [ ] Each contribution stored against **both** the campaign **and** the authenticated Supporter account
- [ ] Donation form captures: donor name, contact details, donation amount, payment/support method, plus anything else from the A1 design
- [ ] Form validation with clear feedback for invalid inputs

---

## Part 4 — Campaign Management Page

**Owner:** _______________
**Depends on:** Part 1 (data), Part 2 (role check — fundraiser only)

### Requirements
- [ ] Accessible **only** to an authenticated Fundraiser
- [ ] Access control must prevent a fundraiser from managing another fundraiser's campaigns
- [ ] View the campaign(s) the logged-in fundraiser is authorised to manage
- [ ] View key campaign info: title, description, donation/support history, fundraising goal, amount raised
- [ ] Create campaign information where the design requires it
- [ ] Edit key campaign information
- [ ] Update operational status (active/paused/closed) — **must not override** administrator approval, rejection, or suspension decisions
- [ ] Create and manage campaign posts/images/updates
- [ ] View relevant donation/support history
- [ ] View dynamically generated campaign statistics
- [ ] All data dynamically integrated with the database; validation, error handling, responsive design, access control all required

---

## Part 5 — UI Consistency, Error Handling, Testing & Submission Packaging

**Owner:** _______________
**Note:** light workload early on (help Parts 1-2, or set up the shared Bootstrap style guide so Parts 3-4 can reuse it), heavy workload near the deadline.

### Error Handling requirements
- [ ] Custom error pages for at least 404 Not Found and 500 Internal Server Error
- [ ] Single `error.html` template used for both
- [ ] Flask application-level error handlers that render `error.html` and return the correct HTTP status code

### Professional UI requirements
- [ ] Responsive across screen sizes (desktop/tablet/mobile)
- [ ] Consistent colour scheme, fonts, layout across every page
- [ ] No overlapping or broken elements
- [ ] Every page has a navbar/header and footer
- [ ] All forms/buttons error-free, clear spacing and alignment
- [ ] All form inputs validated, with clear feedback for invalid data

### Testing & demo prep
- [ ] End-to-end test of each role's flow (guest browse → supporter donation → fundraiser campaign management → admin approval)
- [ ] Confirm `app.debug = False` before submission
- [ ] Rehearse the 4-minute group demo covering: Home, Fundraiser Details and Donation, Campaign Management, Administrator Dashboard, Login/Register, at least 2 core features connecting front end + back end + database, dynamic data loading, partial auth/access-control demo
- [ ] Every team member should be able to answer questions about the whole app (front and back end), not just their own part

### Submission packaging
- [ ] `README.txt` at project root — brief setup instructions (how to run the project)
- [ ] Final ZIP named `[groupID]_582_A3.zip`, structured exactly per the brief (excludes virtual environments/dependencies)
- [ ] Declaration Form (PDF) — all member names/IDs + each member's role and contribution, named `[groupID]_A3.pdf`
- [ ] Confirm the login page's test accounts actually work against the final `database.sql`

---

## Cross-cutting rules (apply to everyone, every part)

- Front end: HTML + CSS + Bootstrap 5.3 only — no JavaScript, no PHP
- Back end: Flask, Flask-Login, Jinja2, Flask-WTF, WTForms, Flask-MySQLdb/MySQLClient, bootstrap-flask, Python standard library only — no Flask-Admin, no Django
- No GenAI (ChatGPT, DeepSeek, etc.) — write your own code
- No Wix/Squarespace/Bootswatch templates — original design only
- Markers run the app locally in Google Chrome — test that your part works with no unexpected dependencies
