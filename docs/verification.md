# Verification record

Executed on 5 November 2026 against the application source in this repository.

| Check | Observed result |
| --- | --- |
| GitHub Actions MySQL workflow | Passed on published application commit; workflow repeats migration, Django, static collection, and JavaScript checks |
| Pipenv lock verification and `pipenv sync --dev` | Lock current; installation succeeded |
| Dependency vulnerability audit (`pip-audit` against installed packages) | No known vulnerabilities found after locking DRF 3.18.3 |
| Dependency compatibility (`uv pip check --python .venv/bin/python`) | 23 compatible packages |
| Docker image build and Compose container checks | Build succeeded; Django check clean and 37 MySQL tests passed inside the container |
| MySQL connection | MySQL 8.4.13 in the local Compose database service |
| `python manage.py migrate --noinput` | All migrations applied to MySQL |
| `python manage.py makemigrations --check --dry-run` | No model drift |
| `python manage.py seed_menu` | Five sample menu items created |
| `python manage.py test` with default MySQL settings | 37 passed, 0 failed |
| `python manage.py test --settings=littlelemon.test_settings` | 37 passed, 0 failed; separate SQLite fallback |
| `node --test scripts/booking.test.cjs` | 5 passed, 0 failed |
| `python scripts/smoke_http.py` against a running MySQL-backed development server | 40 live HTTP checks passed; temporary users, bookings, categories, and dishes removed |
| Django default system checks | No issues |
| `DJANGO_DEBUG=False python manage.py check --deploy` | No issues |
| `python manage.py collectstatic --noinput` | 173 static files collected |
| Python syntax, JavaScript syntax, SVG XML, Insomnia JSON | Passed |
| Frontend premium static audit | Zero errors or warnings |

The Django suite covers website responses and database-driven menu rendering,
menu and booking CRUD, regular/staff/anonymous access, token login and revocation,
password hashing and weak-password rejection, missing/invalid fields, bad IDs,
price validation, category/featured filtering, pagination, searching, ordering,
reservation dates and slots, duplicate conflicts, database uniqueness, public
name redaction, and CSRF-protected website creation.

The five JavaScript tests execute the real booking script in a simulated DOM
with controlled Fetch responses. They check booked and empty dates, stale-date
responses, retry after availability failure, CSRF/integer-slot submission,
refresh after success, and input preservation and field feedback after rejection.
They do not establish browser rendering or native-picker behavior.

The live HTTP checks cover registration, token authentication, role rejection,
staff menu/category writes, booking CRUD, duplicate prevention, redacted
availability, all six HTML views, and their referenced static assets.

## Verification limits

The in-app browser inventory was empty. Chromium was launched and its connection
appeared in the browser inventory, but the browser-control tool failed on tab
navigation/reload with `Cannot read properties of undefined (reading 'timeoutMs')`.
Consequently desktop/mobile appearance, keyboard traversal, native date/select
popups, and browser accessibility behavior were not visually verified. The
responsive CSS, template semantics, static audit, simulated JavaScript tests,
and live HTTP checks provide narrower evidence only.

The Insomnia collection was validated as JSON and its request routes are covered
by the API/HTTP tests; no interactive Insomnia session was available. This project
is a local capstone application, not a verified public production deployment.
Production static hosting, HTTPS infrastructure, backups, and operational controls
remain deployment responsibilities. Local DEBUG-mode deployment checks correctly
warn about development HTTP; the production-mode check above was clean.

## Booking assignment compatibility update

The later update in [booking-assignment.md](booking-assignment.md) records the
13-requirement audit and supersedes the initial test counts above: 46 MySQL Django
tests, 46 SQLite fallback tests, 9 JavaScript behavior tests, and 43 live HTTP
checks passed. The native browser calendar remains unverified because connected
browser navigation failed. Requirements 6 and 12 were fixed without replacing
the capstone, changing its models, or relaxing staff permissions.
