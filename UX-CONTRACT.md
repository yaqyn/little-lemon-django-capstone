# Little Lemon interface contract

Visual decisions and runtime token mapping are recorded in [DESIGN.md](DESIGN.md).

## Business-context sources

| Rule | Authoritative source | UI consequence |
| --- | --- | --- |
| Slots are 10–20, date must be current/future, one booking per slot | Task requirements sections 4, 6, 7; restaurant models and serializers implement them | Choose a date and an available native time option; server remains authoritative |
| Restricted mutations require authorization | Task requirements sections 5, 8; restaurant permission classes | Public website creates bookings; management uses staff-restricted APIs/admin |
| Customer record privacy | Project implementation permission policy agreed by coordinator | Public availability labels all booked times Reserved; no customer names in public pages |
| Fictional restaurant capstone | Task project scope | Shared footer states no real restaurant reservations are made |

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
| --- | --- | --- | --- | --- |
| Select/Listbox | Native HTML select in book.html | Task section 7 | Browser/OS popup | Open popup, keyboard selection; booking integration |
| Date | Native date input | Task section 7 | Browser/OS calendar | Date change loads availability; API date validation |
| Form | booking.js fieldError and submit handler | Server serializers; task section 7 | Public create | Blank fields, duplicate conflict, success, network recovery |
| Scrollbar | site.css :root and global selectors | DESIGN.md | Forced-colors system override | CSS inspection and narrow-page scroll |
| Toast | Inline form-message and availability-status | booking.js | Persistent status/field error, no transient toasts | Live regions, network and validation paths |
| CRUD | Booking form creates; DRF/admin manages | API permission classes | Pessimistic server-confirmed create | Unit/API CRUD tests plus browser booking |

## Flow ledger

Home/menu → book retains shared navigation. Booking chooses today's Chicago date initially, reads booked times, disables unavailable/past slots, submits CSRF-protected JSON, then announces server-confirmed success and refreshes availability. Inputs remain in place after errors. A database conflict refreshes the current list before retry. Page URLs record the selected date for share/reload. Native date and select popups deliberately use platform locale and geometry.

Reservations uses the same date-loading routine without a mutation form. Below that widget, a server-rendered, HTML-escaped JSON block shows all bookings across all dates; /reservations/?format=json returns the same array. Both representations share name redaction with /bookings?date=YYYY-MM-DD, which retains its date filter. Responses use Cache-Control: no-store. The booking page supplies the active inline Fetch transport for assignment source inspection; the shared script owns availability, submission, and recovery. Navigation is semantic links; the skip link reaches main content. Focus rings are visible and mobile reading order follows document order.

## Async and recovery

Each availability fetch aborts the previous one and verifies a request generation. A 12-second availability timeout produces a persistent retry action. Availability errors disable booking until revalidated. POST is pessimistic and blocks duplicate activation. An uncertain network response says the result is unconfirmed and reloads availability; it does not automatically repeat a mutation. Returning to the tab revalidates availability. No tokens or names are persisted in browser storage. Non-empty name input activates only the browser beforeunload navigation guard; there is no native alert, confirm, or prompt.

## Accessibility and locale

English app copy, US dollars, America/Chicago slots, browser-native calendar locale. Labels activate inputs; errors reference fields; first invalid field receives focus. Statuses are polite live regions and plain text expresses booked/error/success states. Native controls and links support keyboard interaction. Responsive one-column layouts avoid horizontal scrolling. Motion is absent and reduced-motion is respected.
