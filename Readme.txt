Little Lemon Restaurant - Django REST API Capstone
=================================================

A fictional restaurant website and MySQL-backed menu/reservation API, built for
Meta's expert-guided Back-End Developer Capstone on Coursera, part of the Meta
Back-End Developer Professional Certificate. The course is taught by Meta Experts.
Course: https://www.coursera.org/learn/back-end-developer-capstone

Implementation and verification: Abdulrahman M. Yaqyn.
Technologies: Python 3.14, Django 5.2,
Django REST Framework, MySQL 8, mysqlclient, Djoser, DRF TokenAuthentication,
Pipenv, Django templates, HTML, CSS, vanilla JavaScript Fetch, Git and GitHub.

INSTALLATION
------------
1. Extract or clone this repository and enter its root directory.
2. Install Python 3.14, MySQL 8, Pipenv, compiler tools, pkg-config and MySQL client
   development headers. On Debian/Ubuntu: build-essential pkg-config python3-dev
   default-libmysqlclient-dev. Other systems need the equivalent packages.
3. python -m pip install --user pipenv
4. pipenv sync --dev
5. cp .env.example .env
6. Set a private DJANGO_SECRET_KEY and the DB_* values in .env. Generate a secret:
   python -c 'import secrets; print(secrets.token_urlsafe(64))'
   Keep DJANGO_DEBUG=True for local HTTP development; never commit .env.
7. Create the database and user in your local MySQL administrator client:
   CREATE DATABASE littlelemon CHARACTER SET utf8mb4;
   CREATE USER 'littlelemon'@'%' IDENTIFIED BY 'replace-with-your-local-password';
   GRANT ALL PRIVILEGES ON littlelemon.* TO 'littlelemon'@'%';
   Restrict the user host to the actual application host where possible.
8. Configure DB_NAME=littlelemon, DB_USER=littlelemon, your DB_PASSWORD,
   DB_HOST=127.0.0.1, DB_PORT=3306 in .env, matching your MySQL setup.
9. pipenv run python manage.py migrate
10. pipenv run python manage.py seed_menu
11. pipenv run python manage.py createsuperuser
12. pipenv run python manage.py runserver

Open http://127.0.0.1:8000/ . Stop the server with Ctrl+C.
Committed migrations are sufficient. After model changes, run:
  pipenv run python manage.py makemigrations restaurant
  pipenv run python manage.py migrate
Do not commit administrator credentials or authentication tokens.

DOCKER COMPOSE ALTERNATIVE
--------------------------
Requires Docker Engine and Compose. Configure .env, including a separate local
MYSQL_ROOT_PASSWORD. Skip manual SQL setup: Compose creates the database/user.
  docker compose up -d db
  docker compose run --rm web python manage.py migrate
  docker compose run --rm web python manage.py seed_menu
  docker compose run --rm web python manage.py createsuperuser
  docker compose up web
Stop with Ctrl+C then docker compose down. The MySQL volume retains data.
Only run docker compose down -v when you intend to delete that local database.

WEBSITE ROUTES
--------------
Route                      Methods    Description
/                          GET        Homepage and featured menu
/about/                    GET        Restaurant introduction
/menu/                     GET        MySQL-backed menu
/menu/{id}/                GET        Menu item details
/book/                     GET, POST  Booking page / CSRF-protected JSON creation
/reservations/             GET        Date-selected public reservation availability
/bookings?date=YYYY-MM-DD   GET        Public compatibility JSON (no slash required)
/bookings/?date=YYYY-MM-DD  GET        Same JSON, trailing slash accepted
/admin/                    GET, POST  Django administrator interface

API ENDPOINTS AND SUPPORTED METHODS
-----------------------------------
Route                      Methods                  Permissions
/api/menu-items/           GET, POST                 Public GET; staff POST
/api/menu-items/{id}/      GET, PUT, PATCH, DELETE    Public GET; staff writes
/api/categories/           GET, POST                 Public GET; staff POST
/api/categories/{id}/      GET, PUT, PATCH, DELETE    Public GET; staff writes
/api/bookings/             GET, POST                 Staff GET; public POST
/api/bookings/{id}/        GET, PUT, PATCH, DELETE    Staff only
/auth/users/               POST                      Public registration
/auth/users/me/            GET                       Authenticated user
/auth/token/login/         POST                      Public credentials exchange
/auth/token/logout/        POST                      Authenticated token revocation

Regular registered users cannot change menus or access complete bookings.
A superuser created with createsuperuser has staff access. Authorized admins may
assign staff status using Django Admin. Registration never grants staff status.

Menu filtering: ?category=mains (or category ID), ?featured=true (also false/1/0),
?search=lemon, ?ordering=price, ?ordering=-price, ?ordering=title, ?page=2,
?page_size=6 (maximum 100). Queries can be combined with &.
Staff booking filtering: /api/bookings/?date=YYYY-MM-DD.
API lists return {"count":...,"next":...,"previous":...,"results":[...]}.
The compatibility /bookings endpoint requires a date and returns a bare array.

AUTHENTICATION EXAMPLES
-----------------------
Set your own passwords locally. These request/response shapes are illustrative;
IDs and authentication tokens are assigned by the running application.

Register:
POST /auth/users/
Content-Type: application/json
{"username":"diner_example","password":"choose-a-long-unique-password"}
Success: 201 Created. Passwords use Django hashing and are never returned.

Login:
POST /auth/token/login/
Content-Type: application/json
{"username":"diner_example","password":"your-password"}
Success: 200 OK
{"auth_token":"<token-returned-by-your-server>"}
Invalid credentials: 400 Bad Request.

Use the returned token:
GET /auth/users/me/
Authorization: Token <authentication-token>
Success: 200 OK with your user data. No valid token: 401 Unauthorized.

Logout:
POST /auth/token/logout/
Authorization: Token <authentication-token>
Success: 204 No Content; the token is revoked.

MENU EXAMPLES
-------------
GET /api/menu-items/?search=lemon&ordering=price
Success: 200 OK, paginated menu list.

POST /api/menu-items/
Authorization: Token <staff-authentication-token>
Content-Type: application/json
{"title":"Greek salad","price":"12.50","featured":true,"category":1,
 "description":"Tomatoes, cucumber and olives","image":"images/salad.svg"}
Success: 201 Created with the saved object and its ID.
Use an existing category ID; browse GET /api/categories/ first.
Image is an optional local static asset path, not an uploaded file or remote URL.

PUT /api/menu-items/1/
Authorization: Token <staff-authentication-token>
Content-Type: application/json
{"title":"Greek salad","price":"13.00","featured":true,"category":1,
 "description":"Tomatoes, cucumber and olives","image":"images/salad.svg"}
Success: 200 OK. PUT supplies a complete replacement of required fields.

PATCH /api/menu-items/1/
Authorization: Token <staff-authentication-token>
Content-Type: application/json
{"price":"13.50"}
Success: 200 OK. PATCH changes selected fields.

DELETE /api/menu-items/1/
Authorization: Token <staff-authentication-token>
Success: 204 No Content.

BOOKING EXAMPLES
----------------
Choose a future date before running these examples. Slots are integers 10 through
20: 10 = 10 AM, 11 = 11 AM, 12 = 12 PM, 13 = 1 PM, ... 20 = 8 PM.
Dates and hours use the restaurant timezone America/Chicago. Past dates and
already-started hours today are rejected.

POST /api/bookings/
Content-Type: application/json
{"first_name":"Jordan","reservation_date":"2027-06-15","reservation_slot":18}
Success: 201 Created with the booking ID, name, date and slot.
This endpoint permits anonymous creation; listing and changing records need staff.

GET /bookings?date=2027-06-15
Success: 200 OK
[{"id":1,"first_name":"Reserved","reservation_date":"2027-06-15",
  "reservation_slot":18}]
Empty date: [] (the website shows "No Bookings").
Public responses redact names. A staff session signed in through Django Admin
can see names in this compatibility endpoint. Token clients should use the
staff-only /api/bookings/ endpoint to inspect full booking details.

GET /api/bookings/?date=2027-06-15
Authorization: Token <staff-authentication-token>
Success: 200 OK, paginated records for that date.

GET /api/bookings/1/
Authorization: Token <staff-authentication-token>
Success: 200 OK, the complete booking.

PUT /api/bookings/1/
Authorization: Token <staff-authentication-token>
Content-Type: application/json
{"first_name":"Jordan","reservation_date":"2027-06-16","reservation_slot":17}
Success: 200 OK.

PATCH /api/bookings/1/
Authorization: Token <staff-authentication-token>
Content-Type: application/json
{"reservation_slot":19}
Success: 200 OK.

DELETE /api/bookings/1/
Authorization: Token <staff-authentication-token>
Success: 204 No Content.

VALIDATION AND HTTP STATUS CODES
-------------------------------
200 successful read/update; 201 created; 204 deleted/logout (empty body).
400 invalid/missing fields, bad date/slot/price, or duplicate booking.
401 missing/invalid authentication on restricted API operations.
403 authenticated non-staff user attempts a staff operation; CSRF failure on
website POST /book/ also returns 403.
404 unknown record ID; 405 unsupported method; 415 unsupported content type.
429 API rate limit exceeded (120 anonymous or 300 authenticated requests/minute).
Serializer errors are JSON keyed by a field or non_field_errors. A uniqueness
constraint also rejects conflicting date/slot rows at the database layer.

JAVASCRIPT BOOKING REVIEW
-------------------------
The booking JavaScript is in static/js/. It selects today's restaurant-local date,
loads availability through Fetch, refreshes on date changes, disables reserved and
past slots, and submits JSON to /book/ with the Django CSRF cookie/header. It
shows loading, empty, success and error feedback, preserving entered values on
failure. POST /book/ is an actual CSRF-protected Django endpoint; do not use it as
an authentication-free cross-origin API. Insomnia should use /api/bookings/.

INSOMNIA / POSTMAN TESTING
--------------------------
1. Run Django, open Insomnia and import docs/insomnia.json (Insomnia export v4).
2. Select the Little Lemon environment. Set base_url=http://127.0.0.1:8000.
3. Set reservation_date to a future YYYY-MM-DD, initially set category_id from
   GET categories, then register and log in with your own local credentials.
4. Copy auth_token from login into the environment's token field. For staff
   requests, log in with the createsuperuser account; regular tokens lack staff.
5. Send list/create menu requests; set menu_item_id to the returned ID. Test GET,
   PUT, PATCH and DELETE with the supplied requests.
6. Create a booking; set booking_id to its ID. Repeat the create request to check
   duplicate rejection. Fetch date availability and staff booking list, then test
   GET, PUT, PATCH and DELETE. Change date/slot when needed to keep them valid.
7. Log out and verify that protected requests reject the revoked token.
The collection has empty credential/token placeholders; no real secrets are saved.
Postman can issue the same URLs, JSON bodies and Authorization header directly.

UNIT TESTS AND CHECKS
---------------------
pipenv run python manage.py check
pipenv run python manage.py makemigrations --check --dry-run
pipenv run python manage.py test

The MySQL test runner creates test_littlelemon. A development test account needs
CREATE/DROP permissions for that test database, separate from production rights.
Run locally as MySQL root (user host must match your configured account):
  GRANT ALL PRIVILEGES ON test_littlelemon.* TO 'littlelemon'@'%';
When MySQL is unavailable, run the explicit SQLite-only test configuration:
  pipenv run python manage.py test --settings=littlelemon.test_settings
SQLite testing does not verify MySQL connectivity. Execution evidence is recorded
in docs/verification.md; do not infer a passing result merely from these commands.

ADMINISTRATION AND LIMITATIONS
-------------------------------
Use /admin/ with your locally created superuser to manage users, categories,
menu items and bookings. There are no committed administrator credentials.
The capstone models one booking per hour, without party size, payment or email.
Local illustrations and seed data are sample content, not a real trading business.
Production hosting requires HTTPS, private environment configuration, static-file
serving, monitoring and backups. Django runserver is for development only.

TECHNICAL REFERENCES
--------------------
Django MySQL notes: https://docs.djangoproject.com/en/5.2/ref/databases/#mysql-notes
Djoser tokens: https://djoser.readthedocs.io/en/latest/token_endpoints.html
DRF tokens: https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication

JAVASCRIPT AND LIVE HTTP CHECKS
------------------------------
Node.js 18+ (optional verification tool, not a runtime dependency):
  node --test scripts/booking.test.cjs
These tests run the actual booking script with simulated DOM/Fetch fixtures.
They do not verify browser rendering. With the local server already running:
  pipenv run python scripts/smoke_http.py
The HTTP checks use the configured development database, create temporary records,
then remove them. Never run against a production database.
