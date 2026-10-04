# IFN582 Assignment 3 — Task Breakdown

**Project:** TBD — scenario to be decided by the team (see "Decisions to make first")
**Due:** _verify exact date on the syllabus page_ (48-hour late period and extensions are available) | **Demo:** Week 13 tutorial (4 min group demo + 5-6 min individual Q&A per person)
**Stack:** Flask + MySQL + Jinja2 + Bootstrap 5.3 only. No Flask-Admin, Django, PHP or other frameworks. No GenAI.

This builds on **one team member's A1 design + the corresponding A2 database design**. Roles: **Administrator / Fundraiser / Supporter** (names may be adapted to the chosen scenario, as long as the responsibilities and access restrictions are clear).

---

## Decisions to make first

- [ ] **Scenario** (pick one): Charity event fundraising / Crowdfunding for creative projects / Subscription-based funding
- [ ] **Whose A1 design + A2 database** is the team's base
- [ ] **Role names** for the chosen scenario (e.g. Administrator / Fundraiser / Supporter)
- [ ] **Categories** used for browsing (e.g. location, creator type, content type) — at least 2
- [ ] **Account deletion policy** — soft delete (status flag) or cascade? What happens to donations/posts of a removed user?
- [ ] **Suspended users** — blocked from logging in? (recommended: yes)
- [ ] **Password hashing approach** — the login page must show plaintext test passwords, but the DB must store hashes. Agree how hashes are generated and pasted into `database.sql` (Part 1 + Part 2)
- [ ] **Package owner** — one person responsible for final packaging (see Shared Tasks)
- [ ] Confirm with tutor: is the **Bootstrap 5.3 JS bundle** (navbar collapse, dropdowns) allowed? The brief says "HTML and CSS, including Bootstrap 5.3". Do not write custom JavaScript.

---

## How to use this file

- Each part below = one owner. Write your name next to "Owner:" when you claim a part.
- Check off each requirement as you complete it — these come from the Assessment 3 brief.
- Work on your own branch, open a PR into `IFN582_grp_assginment` _(verify the branch name — possible typo)_ when a part is ready, and tag someone for review before merging.
- If a requirement is unclear, ask in the group chat before guessing — markers check against the brief exactly.
- **Each owner checks their own pages at mobile and tablet widths before opening a PR.**
- **Ethics / cultural sensitivity (ULO3):** sample data, images and wording must be appropriate and respectful.

---

## Workload overview (estimate)

| Part | Scope | Approx. share |
|---|---|---|
| Part 1 | Database, project skeleton, base models | 20% |
| Part 2 | Authentication, `base.html`, decorators, error pages, shared CSS | 20% |
| Part 3 | Home page, Fundraiser Details + Donation page | 22% |
| Part 4 | Campaign Management page | 20% |
| Part 5 | Administrator Dashboard | 18% |
| Shared | Testing, demo prep, packaging, peer evaluation (everyone) | — |

**Dependency order:** Part 1 → Part 2 (`base.html` + decorators first) → Parts 3, 4, 5 in parallel.
Part 2 should post `base.html` and the decorators early and notify the team — Parts 3, 4 and 5 are blocked until then.

---

## File Ownership Map

Some files belong to one part only. Others (`views.py`, `models.py`, `forms.py`) are shared — multiple parts add their own section to the same file, so **pull before you start, commit/push in small chunks, and mark your section with a comment header** (e.g. `# ---- Part 3: Home & Donation ----`) to avoid conflicts.

| Owner | File / Folder | What to do |
|---|---|---|
| Part 1 | `database.sql` | Write and own this file entirely — `CREATE DATABASE`, tables, constraints, sample data |
| Part 1 | `project/__init__.py` | Create the Flask app, configure DB connection, register blueprints |
| Part 1 | `run.py` | Entry point script that starts the app |
| Part 1 | `requirements.txt` | Permitted packages only (from Canvas) |
| Part 1 | `project/models.py` *(base)* | Base classes for each DB table (Campaign, User, Category, Donation, Post, Report, etc.) |
| Part 2 | `project/templates/base.html` | Shared layout: navbar, footer, flash messages area, Bootstrap includes |
| Part 2 | `project/models.py` *(add-on)* | `User` role logic (admin/fundraiser/supporter checks), suspended-account check |
| Part 2 | `project/views.py` *(add-on)* | Routes: register, login, logout; `user_loader`; `@admin_required`, `@fundraiser_required`, `@supporter_required`; 404/500 error handlers |
| Part 2 | `project/forms.py` *(add-on)* | `RegisterForm`, `LoginForm` |
| Part 2 | `project/templates/login.html` | Login page incl. the mandatory "Test Login Credentials For Assessment" block |
| Part 2 | `project/templates/register.html` | Registration page |
| Part 2 | `project/templates/error.html` | Shared error page template (404 and 500) |
| Part 2 | `project/static/css/` | Shared stylesheet/style guide (colours, fonts, spacing) used by all pages |
| Part 2 | `project/static/img/` | Shared/placeholder images not tied to one specific part |
| Part 3 | `project/models.py` *(add-on)* | Extend `Campaign`, `Donation`, `Category` (search, browse, featured queries) |
| Part 3 | `project/views.py` *(add-on)* | Routes: home (search/browse/featured), fundraiser details + donation submission |
| Part 3 | `project/forms.py` *(add-on)* | `DonationForm` |
| Part 3 | `project/templates/home.html` | Home page |
| Part 3 | `project/templates/donation.html` | Fundraiser Details and Donation page |
| Part 4 | `project/models.py` *(add-on)* | Extend `CampaignPost`/update-related classes, campaign statistics queries |
| Part 4 | `project/views.py` *(add-on)* | Routes: campaign management (create/edit/status/posts/stats) scoped to the logged-in fundraiser |
| Part 4 | `project/forms.py` *(add-on)* | `CampaignForm`, `CampaignPostForm` |
| Part 4 | `project/templates/campaign_management.html` | Campaign Management page |
| Part 5 | `project/models.py` *(add-on)* | Admin model methods (approve/reject/suspend/remove, user management, reports, featured) |
| Part 5 | `project/views.py` *(add-on)* | Administrator Dashboard routes and actions |
| Part 5 | `project/forms.py` *(add-on)* | Admin forms (e.g. edit user details) if needed |
| Part 5 | `project/templates/admin_dashboard.html` | Administrator Dashboard page |
| Package owner | `README.txt` | Setup/run instructions, written once the app is working |

---

## Part 1 — Database & Project Foundation

**Owner:** Yujin
**Priority:** Do this first — every other part depends on it.

### Requirements
- [ ] `database.sql` — hand-written (NOT an exported dump) SQL script that:
  - [ ] Creates the database (`CREATE DATABASE`) and all tables derived from the A2 data model (3NF)
  - [ ] Defines primary keys, foreign keys, and other constraints
  - [ ] Inserts all sample data, including the test login accounts (stored as **hashed** passwords — see Part 2)
- [ ] Schema supports: user status (e.g. active/suspended), campaign approval status (pending/approved/rejected/suspended) separate from operational status (active/paused/closed), featured flag, categories, reported-content records
- [ ] Sample data must meet these minimums:
  - [ ] ≥ 15 campaigns/events, across ≥ 2 categories
  - [ ] ≥ 6 users: ≥ 2 administrators, ≥ 2 fundraisers, ≥ 2 supporters
  - [ ] ≥ 5 donation/support records, across different fundraisers
  - [ ] ≥ 3 campaign posts/updates, across different fundraisers
  - [ ] ≥ 2 campaigns with status "pending approval"
  - [ ] ≥ 2 campaigns marked as featured
  - [ ] ≥ 2 reported-content records, attached to different campaigns/posts
  - [ ] Data shows different roles, multiple interaction types, and realistic relationships
  - [ ] Content is realistic, respectful and culturally appropriate
- [ ] `models.py` — Python classes representing each DB table (one class per entity), following the pattern taught in class (constructor + `get_*_details()` method)
- [ ] `requirements.txt` containing only permitted packages
- [ ] Flask project skeleton set up and running locally, matching the required submission structure:
  ```
  run.py
  README.txt
  requirements.txt
  database.sql
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

## Part 2 — Authentication, Base Layout, Error Pages & Shared Style

**Owner:** Queenie
**Depends on:** Part 1 (users table + models.py)

### Do first (unblocks Parts 3, 4, 5)
- [ ] `base.html` — navbar/header, footer, flash messages, Bootstrap 5.3; all other templates extend it
- [ ] Flask-Login setup and `user_loader`
- [ ] Custom decorators: `@admin_required`, `@fundraiser_required`, `@supporter_required` (Flask-Admin is prohibited)
- [ ] Notify the team when these are merged

### Authentication requirements
- [ ] Registration, Login, Logout — fully working
- [ ] Hashed passwords (no plaintext storage)
- [ ] Session-based authentication
- [ ] Suspended accounts cannot log in
- [ ] Registered Supporters and Fundraisers can use their role's functionality immediately — **no admin approval needed for new accounts**
- [ ] New campaigns still require admin approval before going public (handled in Part 4 + Part 5, but auth must support the role check)
- [ ] **Mandatory:** directly below the username/password fields on the login page, a clearly labelled **"Test Login Credentials For Assessment"** section showing role + username + password for working sample accounts — **two accounts per role** (admin, fundraiser, supporter)
- [ ] Confirm the displayed credentials actually work against the final `database.sql`
- [ ] Role restrictions enforced:
  - [ ] Administrator-only pages are accessible only to admins
  - [ ] Fundraisers → manage only their own campaigns and content
  - [ ] Supporters → browse + submit contributions when logged in
  - [ ] Guests → browse and view details only, no contributions
- [ ] Registration and login forms validated with clear feedback messages

### Error handling requirements
- [ ] Custom error pages for at least 404 Not Found and 500 Internal Server Error
- [ ] Single `error.html` template used for both
- [ ] Flask application-level error handlers that render `error.html` and return the correct HTTP status code

### Shared style
- [ ] Shared stylesheet in `static/css/`: consistent colour scheme, fonts, spacing, layout
- [ ] Placeholder/shared images in `static/img/`
- [ ] Short style guide for the team (colours, fonts, button styles) so Parts 3, 4, 5 match

---

## Part 3 — Home Page + Fundraiser Details and Donation Page

**Owner:** Sky
**Depends on:** Part 1 (data), Part 2 (`base.html`, login check for donation form)

### Home Page requirements
- [ ] Display fundraisers/campaigns **dynamically from the database** (not hard-coded)
- [ ] Only publicly available campaigns shown (approved, not suspended/removed)
- [ ] Search functionality relevant to the scenario
- [ ] A Featured selection — each featured item links to its Fundraiser Details and Donation Page
- [ ] Categories/browsing options relevant to the scenario
- [ ] Brief description of how the platform works
- [ ] Responsive design; uses the shared navbar and footer

### Fundraiser Details and Donation Page requirements
- [ ] Display: fundraiser/campaign name, image/banner, description of the organiser, description of fundraising purpose and goals
- [ ] Fundraising goal and amount raised to date (updated after each donation)
- [ ] Donor/support tiers (if relevant to design)
- [ ] Brief display of donation/support history — donor info, contribution amounts, messages left
- [ ] Posts, images, or updates from the fundraiser
- [ ] Guests may browse and view details
- [ ] To submit a donation, the user must be registered and logged in as a Supporter — if a guest tries, prompt them to log in/register
- [ ] Each contribution stored against **both** the campaign **and** the authenticated Supporter account
- [ ] Donation form captures: donor name, contact details, donation amount, payment/support method, plus anything else from the A1 design
- [ ] Payment is **simulated** — validate and store the data, no real payment gateway
- [ ] Form validation with clear feedback for invalid inputs

---

## Part 4 — Campaign Management Page

**Owner:** Lisan
**Depends on:** Part 1 (data), Part 2 (`base.html`, `@fundraiser_required`)

### Requirements
- [ ] Accessible **only** to an authenticated Fundraiser (not Supporters)
- [ ] Access control prevents a fundraiser from managing another fundraiser's campaigns (check ownership on every view/edit/status/post route, not just in the UI)
- [ ] View the campaign(s) the logged-in fundraiser is authorised to manage
- [ ] View key campaign info: title, description, donation/support history, fundraising goal, amount raised
- [ ] Create campaign information where the design requires it — new campaigns start as **pending approval**
- [ ] Edit key campaign information
- [ ] Update operational status (active/paused/closed) — **must not override** administrator approval, rejection, or suspension decisions
- [ ] Create and manage campaign posts/images/updates
- [ ] View relevant donation/support history
- [ ] View dynamically generated campaign statistics (e.g. total raised, number of donors, average donation)
- [ ] All data dynamically integrated with the database; validation, error handling, responsive design, access control all required

---

## Part 5 — Administrator Dashboard

**Owner:** Rachel
**Depends on:** Part 1 (data), Part 2 (`base.html`, `@admin_required`)
**Note:** This is a required demo page — start as soon as Part 2's decorators are merged, don't leave it to the end.

### Requirements
- [ ] Accessible **only** to Administrator users
- [ ] Review and manage campaigns
- [ ] Approve or reject new campaigns before they become publicly available
- [ ] Update campaign status, suspend campaigns, remove campaigns
- [ ] Manage user accounts — edit account details, suspend or remove accounts (new registrations do not need approval)
- [ ] Review and manage content reported as inappropriate or misleading (reported-content records come from sample data — a user-facing reporting form is not required, but if one is built it must be restricted to authenticated users)
- [ ] Select/remove campaigns in the Featured section of the Home Page
- [ ] Admin decisions are respected by the rest of the app (e.g. suspended campaigns hidden from public, fundraisers cannot override)
- [ ] Validation, error handling, responsive design

---

## Shared Tasks (everyone)

Submission preparation is shared. Each item has one **responsible person** so nothing is missed.

| Task | Responsible | Everyone's part |
|---|---|---|
| Final packaging (ZIP, structure check) | _______ | Review contents before submitting |
| `README.txt` | _______ | Test setup on a clean machine/environment |
| Declaration Form (PDF) | _______ | Check own name, ID, role and contribution |
| Cross-testing | _______ | Test another member's part for each role |
| Demo rehearsal | _______ | Attend and present your part |
| Pre-submission checklist | _______ | Tick off together |

### Cross-testing
- [ ] Each member tests **another member's** pages as guest, supporter, fundraiser and admin, and reports bugs as issues
- [ ] Mid-point check: one week before the demo
- [ ] Final check: 3 days before submission
- [ ] End-to-end flow: guest browse → supporter donation → fundraiser campaign management → admin approval

### Responsive & UI check
- [ ] Every page has navbar/header and footer
- [ ] Responsive on desktop, tablet and mobile — no overlapping or broken elements
- [ ] Consistent colours, fonts and layout across all pages
- [ ] All forms/buttons error-free, with clear spacing and alignment
- [ ] All form inputs validated, with clear feedback for invalid data

### Demo preparation (Week 13, tutorial session)
- [ ] 4-minute group demo; each person then answers questions for 5-6 minutes (individual mark)
- [ ] Demo is with the tutor only, in group number order
- [ ] Bring your own laptop; the app must already be running before your turn (no setup time)
- [ ] Demo must include: navigation across Home, Fundraiser Details and Donation, Campaign Management, Administrator Dashboard, Login/Register
- [ ] At least 2 core features connecting front end + back end + database (e.g. donation, creating/updating a campaign, admin approval, registration/login)
- [ ] Dynamic data loading from the database (no hard-coded data)
- [ ] Partial auth/access-control demo (login/logout and a role-restricted page)
- [ ] Every member can answer questions about the **whole** app (front and back end), not just their own part
- [ ] The app does not need to be finished for the demo; it can still be improved before the final deadline

### Pre-submission checklist
- [ ] `app.debug = False`
- [ ] Only permitted packages used; `requirements.txt` is correct; no unexpected imports
- [ ] App runs locally from a fresh setup using `README.txt` and `database.sql`
- [ ] Test accounts shown on the login page work (2 per role)
- [ ] `database.sql` runs cleanly and meets all sample-data minimums
- [ ] No Flask-Admin, custom JavaScript, or external templates (Wix, Squarespace, Bootswatch)
- [ ] ZIP excludes virtual environments/dependencies and follows the required structure
- [ ] ZIP named `[groupID]_582_A3.zip` and declaration form named `[groupID]_A3.pdf` _(verify naming rules on Canvas)_
- [ ] Declaration Form (PDF): all member names/IDs + each member's role and contribution

### Peer evaluation (individual, FeedbackFruits)
- [ ] Each member submits their own peer review (worth 10% of the final unit grade)
- [ ] Self-reflection on own contributions + reflection on teammates
- [ ] Assess teamwork, participation and communication
- [ ] **A comment is required for every criterion** — a score without a comment may receive zero for that criterion

---

## Cross-cutting rules (apply to everyone, every part)

- Front end: HTML + CSS + Bootstrap 5.3 only — no custom JavaScript, no PHP
- Back end: Flask, Flask-Login, Jinja2, Flask-WTF, WTForms, Flask-MySQLdb/MySQLClient, bootstrap-flask, Python standard library only — no Flask-Admin, no Django
- No GenAI (ChatGPT, DeepSeek, etc.) — write your own code; keep good records (commits, notes) in case authorship is questioned
- No collusion with other groups
- No Wix/Squarespace/Bootswatch templates — original design only (small snippets from w3schools are allowed)
- Markers run the app locally in Google Chrome — test that your part works with no unexpected dependencies
- Payment is simulated: validate and store contribution data and update the app's data, no real transactions
