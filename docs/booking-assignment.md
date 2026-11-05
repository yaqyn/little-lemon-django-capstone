# Little Lemon Table Reservation System: assignment audit

This is the existing Little Lemon Django capstone in
https://github.com/yaqyn/little-lemon-django-capstone . The same application,
models, MySQL database, authentication, management APIs, and project structure
serve both the reservation assignment and the capstone.

## Requirement results

Checked on 5 November 2026. “Pass” identifies executed automated or HTTP checks,
not an unperformed browser test.

| # | Requirement | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Restaurant app installed | Pass | `restaurant` in `INSTALLED_APPS`; Django system checks pass |
| 2 | MySQL configured | Pass | Live default database connection reports MySQL 8.4.13; full Django suite executed against it |
| 3 | Booking migrations created and applied | Pass | Committed `0001_initial`; `showmigrations restaurant` reports `[X]`; `migrate` reports no outstanding migrations |
| 4 | Name, date and time fields | Pass | `/book/` renders `first_name`, native `reservation_date`, and `reservation_slot`; website POST tests save reservations |
| 5 | Native date picker works | Not fully verified | `input[type=date]` and date values are verified in rendered HTML; opening and operating the platform calendar could not be tested because browser control fails |
| 6 | Reservations page displays all bookings as JSON | Pass; fixed | `/reservations/` contains a formatted, escaped JSON array across all dates; `?format=json` returns it directly; tested with 15 bookings to exclude accidental pagination |
| 7 | Duplicate bookings prevented | Pass | Website/API rejection plus MySQL date/slot uniqueness tests |
| 8 | Date changes refresh bookings | Pass, automated JS | Tests change the date, assert the exact filtered request URL and updated list, and reject stale responses |
| 9 | Already-booked slots disabled | Pass, automated JS | Tests assert disabled booked options and replacement of the previous date's options |
| 10 | `/bookings?date=YYYY-MM-DD` filters correctly | Pass | Django and real HTTP checks verify date filtering and public redaction |
| 11 | No Bookings message | Pass, automated JS | Empty availability response produces exactly `No Bookings` |
| 12 | Booking HTML source contains `fetch()` | Pass; fixed | Executable inline Fetch adapter in `/book/` is consumed by the shared booking script; rendered-HTML and actual-script tests cover the adapter |
| 13 | Today selected automatically | Pass, automated | Rendered date `value`/`min` use the restaurant date; JS tests verify Chicago's date even across UTC midnight |

Summary: 12 passed by automated checks, 0 known failures, 1 browser-dependent
requirement not fully verified. Browser interaction for requirements 8, 9, 11,
and 13 also remains unverified; those passes refer to JavaScript execution with
DOM/Fetch fixtures, not a native browser session.

## What changed

The two implementation gaps were requirements 6 and 12. The reservations page
now preserves its selected-date widget and adds every booking as a server-rendered
JSON block. `/reservations/?format=json` exposes the same array without HTML.
The shared serialization helper preserves public name redaction; staff signed
into Django Admin receive actual names. HTML remains escaped and these HTML and JSON
responses use `Cache-Control: no-store`.

The booking template now supplies the actual inline Fetch transport used by
`static/js/booking.js`. Availability, slot disabling, submission, timeouts,
validation, and duplicate prevention remain in the existing shared implementation.
The server also initializes the date field to today's Chicago date before JS runs.

No model changes or new migrations were necessary. API routes and token/staff
permissions remain intact. Public availability still labels names `Reserved`;
reviewers can create a local administrator with `createsuperuser` and sign in at
`/admin/` to inspect full reservation names.

## Executed checks

- MySQL 8.4.13: 46 Django tests passed, 0 failed, including all original 37 tests.
- Explicit SQLite fallback: 46 passed, 0 failed.
- Node booking behavior suite: 9 passed, 0 failed, including the original 5.
- Running MySQL-backed server: 43 real HTTP checks passed, with temporary data removed.
- Django checks, production-mode checks, migration drift check, Python/JS syntax,
  static collection, and strict frontend static audit passed.

Commands from the existing project root after the installation in `Readme.txt`:

```bash
pipenv run python manage.py check
pipenv run python manage.py migrate
pipenv run python manage.py showmigrations restaurant
pipenv run python manage.py makemigrations --check --dry-run
pipenv run python manage.py test
pipenv run python manage.py test --settings=littlelemon.test_settings
node --test scripts/booking.test.cjs
```

With the local development server already running against the same configured DB:

```bash
pipenv run python scripts/smoke_http.py
```

The in-app browser inventory was empty. Chromium was launched and appeared in the
connected inventory. Tab navigation then failed in the browser-control tool with
`Cannot read properties of undefined (reading 'timeoutMs')`. No successful native
calendar, desktop/mobile, or real-browser booking interaction is claimed.

## Submission package

The updated release ZIP contains the complete existing project, including
`Readme.txt`, this audit, the Meta-branded README and cover, committed migrations,
Pipenv lockfile, source code, static assets, and tests. It excludes `.env`, actual
credentials, virtual environments, caches, database volumes, and generated static
output. Configure your own `.env`, run migrations, and create a local administrator
as documented; no users or private reservations are shipped in the archive.
