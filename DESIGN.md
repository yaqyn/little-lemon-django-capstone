---
version: alpha
name: Little Lemon
description: A Mediterranean restaurant demonstration with a practical reservation form.
colors:
  primary: '#254d40'
  accent: '#f4ce36'
  background: '#ffffff'
  foreground: '#23352d'
  muted: '#52645b'
  surface: '#f2f6f2'
  border: '#d4dfd7'
  danger: '#a32b26'
  focus: '#865b00'
typography:
  display:
    fontFamily: 'Georgia, Times New Roman, serif'
  body:
    fontFamily: 'Trebuchet MS, Arial, sans-serif'
rounded:
  DEFAULT: '0.5rem'
  control: '0.3rem'
spacing:
  page-max: '72rem'
  field-gap: '1.25rem'
components:
  button:
    height: '48px'
  input:
    height: '48px'
---

# Little Lemon design system

## Overview

The creative reference is a neighborhood Mediterranean table: a generous illustrated salad, yellow lemons, and relaxed hospitality. Diners browse food and reserve an hour; capstone reviewers can inspect the corresponding APIs. This is a fictional restaurant demonstration, identified in the shared footer.

The site is a hybrid: expressive restaurant pages at home, about, and menu; a familiar, task-focused booking form and reservations view. English is the interface language. Prices use USD and reservation hours use America/Chicago. No Japan-market or Japanese-language behavior is in scope.

The memorable signature is the local SVG table illustration within an arched hero surface. Plain white backgrounds and quiet green navigation keep the rest restrained. Avoid the generic dashboard card grid, ornamental motion, and unavailable remote food photography.

Runtime tokens live in `static/css/site.css` `:root`. This document mirrors those values. The runtime mappings are primary → --green, accent → --yellow, background → --white, foreground → --ink, muted → --muted, surface → --surface, border → --line, danger → --danger, focus → --focus. Changes to either require updating the other. The shared template is `templates/base.html`; behavior ownership is in `UX-CONTRACT.md`.

## Colors

Dark green carries navigation and primary actions; lemon yellow is used for the logo and booking emphasis. White is the page background. Surface green separates illustration grounds and booked-time rows without shadows. Muted green is secondary text, never the only error indication. Danger text accompanies errors; the golden-brown focus outline is a visible three-pixel ring. The supported theme is light; forced-colors mode retains native system control boundaries.

## Typography

Georgia gives food headings the character of a neighborhood menu. Trebuchet MS with Arial fallback keeps controls and body text familiar and readable without downloaded fonts. Body type is 16px with 1.65 line height; paragraphs stay below 65 characters. Heading scale is responsive. Prices use tabular numerals. Navigation uses sentence case.

## Layout

Content is left-aligned within a 72rem maximum with 1.5rem side gutters on desktop and 1rem on phones. The hero pairs copy with table artwork. Menu lists use three columns, two below 850px, and one below 580px. Booking uses two columns on larger screens, then a single reading order on phones. Native controls have a 48px minimum height. Images reserve dimensions and consistent aspect ratios. Sections have a responsive 2.5–5rem rhythm.

## Elevation & Depth

Use flat surfaces, white space, and a single fine border around the booking form. There are no drop shadows, floating overlays, or sticky headers. Availability rows have a green left rule and a tinted ground to group information.

## Shapes

Shared buttons and image containers use 0.5rem corners; form fields use 0.3rem corners. The arched hero image is the single expressive exception. Illustrations use flat fills and rounded organic food shapes. No generic icon family is necessary: the only navigation emblem is a local lemon SVG with an empty decorative alt.

## Components

The shared base owns header, navigation, skip link, and footer. The menu-card include owns item preview composition. Buttons use green fill with white text; the highlighted navigation action uses yellow with dark text. Hover darkens green, focus exposes a ring, and disabled controls reduce opacity while preserving labels. A busy submit keeps its full width and says “Reserving…”.

Native date and select controls intentionally delegate calendar/popup geometry and locale to the browser/OS, as requested by the assignment. Their labels and field errors are app-owned. Errors are persistent text with aria-invalid and aria-describedby; invalid submission focuses the first failed field. The app never invokes native validation bubbles or native dialogs.

`static/js/booking.js` owns availability loading and mutation feedback. Loading, empty (“No Bookings”), error with retry, success, and duplicate-conflict paths use stable inline regions. Customer names remain private in public availability views. Request generations prevent old date results from replacing newer state. No animation is required; reduced-motion explicitly removes any transition or animation.

## Do's and Don'ts

- Do keep booking tasks legible and preserve values after server or connection failures.
- Do keep API implementation details out of diner-facing flows.
- Do reuse the shared template, field treatment, and availability behavior.
- Don't add external fonts, stock-image dependencies, ornamental movement, or invented restaurant credentials.
- Don't imply a real restaurant booking was made.
