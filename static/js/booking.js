(() => {
  "use strict";
  const app = document.querySelector("[data-booking-app]");
  if (!app) return;
  const date = document.getElementById("reservation_date");
  const slot = document.getElementById("reservation_slot");
  const form = document.getElementById("booking-form");
  const submit = form?.querySelector("button[type=submit]");
  const status = document.getElementById("availability-status");
  const list = document.getElementById("reservation-list");
  const retry = document.getElementById("retry-availability");
  const message = document.getElementById("form-message");
  let controller;
  let generation = 0;
  let availabilityReady = false;
  let submitting = false;
  const chicagoNow = () => {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/Chicago",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date());
    const get = (type) => parts.find((part) => part.type === type).value;
    return {
      date: `${get("year")}-${get("month")}-${get("day")}`,
      hour: Number(get("hour")),
    };
  };
  const timeLabel = (hour) => `${hour % 12 || 12} ${hour < 12 ? "AM" : "PM"}`;
  function fieldError(name, text = "") {
    const field = document.getElementById(name);
    const error = document.getElementById(`${name}-error`);
    if (!field || !error) return;
    field.setAttribute("aria-invalid", text ? "true" : "false");
    error.textContent = text;
  }
  function notice(text, tone = "") {
    if (!message) return;
    message.textContent = text;
    message.dataset.tone = tone;
  }
  function updateSubmit() {
    if (submit) submit.disabled = submitting || !availabilityReady;
  }
  async function loadAvailability() {
    const version = ++generation;
    controller?.abort();
    controller = new AbortController();
    const requestController = controller;
    availabilityReady = false;
    updateSubmit();
    if (slot) slot.disabled = true;
    retry.hidden = true;
    retry.disabled = true;
    list.replaceChildren();
    fieldError("reservation_date");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date.value)) {
      status.textContent = "Choose a valid date to view reservations.";
      fieldError("reservation_date", "Choose a date using the date picker.");
      app.setAttribute("aria-busy", "false");
      return;
    }
    document.getElementById("selected-date").textContent =
      new Intl.DateTimeFormat("en-US", {
        dateStyle: "long",
        timeZone: "UTC",
      }).format(new Date(`${date.value}T12:00:00Z`));
    const url = new URL(window.location.href);
    url.searchParams.set("date", date.value);
    window.history.replaceState(null, "", url);
    status.textContent = "Loading reservations…";
    app.setAttribute("aria-busy", "true");
    const timeout = setTimeout(() => requestController.abort(), 12000);
    try {
      const response = await fetch(
        `/bookings?date=${encodeURIComponent(date.value)}`,
        {
          signal: requestController.signal,
          headers: { Accept: "application/json" },
        },
      );
      if (!response.ok) throw new Error("availability");
      const bookings = await response.json();
      if (version !== generation) return;
      if (!Array.isArray(bookings)) throw new Error("format");
      const booked = new Set(
        bookings.map((booking) => Number(booking.reservation_slot)),
      );
      for (const booking of bookings) {
        const li = document.createElement("li");
        li.textContent = `${timeLabel(Number(booking.reservation_slot))} — Reserved`;
        list.append(li);
      }
      status.textContent = bookings.length
        ? `${bookings.length} reserved time${bookings.length === 1 ? "" : "s"}.`
        : "No Bookings";
      if (slot) {
        const previous = slot.value;
        slot.replaceChildren(new Option("Choose a time", ""));
        const now = chicagoNow();
        for (let hour = 10; hour <= 20; hour++) {
          const past =
            date.value < now.date ||
            (date.value === now.date && hour <= now.hour);
          const unavailable = booked.has(hour) || past;
          const option = new Option(
            `${timeLabel(hour)}${booked.has(hour) ? " — Booked" : past ? " — Unavailable" : ""}`,
            String(hour),
          );
          option.disabled = unavailable;
          slot.add(option);
        }
        if (
          [...slot.options].some(
            (option) => option.value === previous && !option.disabled,
          )
        )
          slot.value = previous;
        slot.disabled = submitting;
      }
      availabilityReady = true;
    } catch (error) {
      if (version !== generation) return;
      status.textContent =
        "Availability could not be loaded. Check your connection and retry.";
      retry.hidden = false;
      retry.disabled = false;
    } finally {
      clearTimeout(timeout);
      if (version === generation) {
        app.setAttribute("aria-busy", "false");
        updateSubmit();
      }
    }
  }
  const initial = new URLSearchParams(window.location.search).get("date");
  date.value =
    initial && /^\d{4}-\d{2}-\d{2}$/.test(initial)
      ? initial
      : chicagoNow().date;
  if (!date.value) date.value = chicagoNow().date;
  if (form) date.min = chicagoNow().date;
  date.addEventListener("change", () => {
    notice("");
    fieldError("reservation_slot");
    loadAvailability();
  });
  retry.addEventListener("click", loadAvailability);
  form?.addEventListener("input", (event) => fieldError(event.target.id));
  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitting || !availabilityReady) return;
    notice("");
    for (const name of ["first_name", "reservation_date", "reservation_slot"])
      fieldError(name);
    const name = document.getElementById("first_name");
    if (!name.value.trim())
      fieldError("first_name", "Enter the name for your reservation.");
    if (!date.value || date.value < chicagoNow().date)
      fieldError("reservation_date", "Choose today or a future date.");
    if (!slot.value || slot.selectedOptions[0]?.disabled)
      fieldError("reservation_slot", "Choose an available time.");
    const invalid = form.querySelector('[aria-invalid="true"]');
    if (invalid) {
      invalid.focus();
      return;
    }
    submitting = true;
    const submittedDate = date.value;
    const submittedSlot = Number(slot.value);
    const submittedName = name.value.trim();
    for (const field of [name, date, slot]) field.disabled = true;
    const postController = new AbortController();
    const postTimeout = setTimeout(() => postController.abort(), 15000);
    updateSubmit();
    submit.textContent = "Reserving…";
    try {
      const response = await fetch("/book/", {
        method: "POST",
        signal: postController.signal,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]')
            .value,
          Accept: "application/json",
        },
        body: JSON.stringify({
          first_name: submittedName,
          reservation_date: submittedDate,
          reservation_slot: submittedSlot,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        for (const key of [
          "first_name",
          "reservation_date",
          "reservation_slot",
        ]) {
          if (data[key])
            fieldError(
              key,
              Array.isArray(data[key])
                ? data[key].join(" ")
                : String(data[key]),
            );
        }
        notice(
          data.non_field_errors?.join(" ") ||
            data.detail ||
            "Your reservation was not saved. Check the fields and choose an available time.",
          "error",
        );
        await loadAvailability();
        return;
      }
      notice(
        `Table reserved for ${data.first_name} on ${data.reservation_date} at ${timeLabel(Number(data.reservation_slot))}, Chicago time.`,
        "success",
      );
      name.value = "";
      slot.value = "";
      await loadAvailability();
    } catch (error) {
      notice(
        "We could not confirm the result. Refresh availability before trying again; the reservation may have been saved.",
        "error",
      );
      await loadAvailability();
    } finally {
      clearTimeout(postTimeout);
      submitting = false;
      name.disabled = false;
      date.disabled = false;
      slot.disabled = !availabilityReady;
      submit.textContent = "Reserve a table";
      updateSubmit();
      form.querySelector('[aria-invalid="true"]')?.focus();
    }
  });
  window.addEventListener("beforeunload", (event) => {
    if (form && document.getElementById("first_name").value.trim()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !submitting) loadAvailability();
  });
  loadAvailability();
})();
