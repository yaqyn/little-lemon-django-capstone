const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync(
  new URL("../static/js/booking.js", `file://${__filename}`),
  "utf8",
);
const tick = () => new Promise((resolve) => setImmediate(resolve));

function fixture(fetch) {
  class Element {
    constructor(id) {
      this.id = id;
      this.value = "";
      this.textContent = "";
      this.disabled = false;
      this.hidden = false;
      this.dataset = {};
      this.attributes = {};
      this.listeners = {};
      this.options = [];
      this.children = [];
    }
    addEventListener(type, handler) {
      (this.listeners[type] ||= []).push(handler);
    }
    async emit(type) {
      for (const handler of this.listeners[type] || [])
        await handler({ target: this, preventDefault() {} });
    }
    setAttribute(name, value) {
      this.attributes[name] = value;
    }
    replaceChildren(...children) {
      this.children = children;
      this.options = children;
      this.value = "";
    }
    append(child) {
      this.children.push(child);
    }
    add(option) {
      this.options.push(option);
    }
    get selectedOptions() {
      return this.options.filter((option) => option.value === this.value);
    }
    focus() {
      this.focused = true;
    }
  }
  const ids = [
    "reservation_date",
    "reservation_slot",
    "booking-form",
    "availability-status",
    "reservation-list",
    "retry-availability",
    "form-message",
    "first_name",
    "selected-date",
    "first_name-error",
    "reservation_date-error",
    "reservation_slot-error",
  ];
  const nodes = Object.fromEntries(ids.map((id) => [id, new Element(id)]));
  const app = new Element("app");
  const submit = new Element("submit");
  nodes["booking-form"].querySelector = (selector) => {
    if (selector === "button[type=submit]") return submit;
    if (selector === '[name="csrfmiddlewaretoken"]')
      return { value: "fixture-csrf" };
    if (selector === '[aria-invalid="true"]')
      return Object.values(nodes).find(
        (node) => node.attributes["aria-invalid"] === "true",
      );
  };
  const doc = {
    querySelector: () => app,
    getElementById: (id) => nodes[id],
    createElement: (tag) => new Element(tag),
    addEventListener() {},
    hidden: false,
  };
  const timers = new Set();
  const context = {
    document: doc,
    window: {
      location: {
        href: "http://localhost/book/?date=2099-04-07",
        search: "?date=2099-04-07",
      },
      history: { replaceState() {} },
      addEventListener() {},
    },
    fetch,
    URL,
    URLSearchParams,
    Intl,
    Date,
    AbortController,
    Option: function (text, value) {
      this.textContent = text;
      this.value = value;
      this.disabled = false;
    },
    setTimeout(fn, ms) {
      const timer = setTimeout(fn, ms);
      timer.unref();
      timers.add(timer);
      return timer;
    },
    clearTimeout(timer) {
      clearTimeout(timer);
      timers.delete(timer);
    },
  };
  vm.runInNewContext(source, context, { filename: "booking.js" });
  return {
    nodes,
    submit,
    app,
    cleanup() {
      for (const timer of timers) clearTimeout(timer);
    },
  };
}
const response = (body, ok = true) => ({
  ok,
  async json() {
    return body;
  },
});

test("availability marks booked hours unavailable and empty dates show No Bookings", async (t) => {
  let bookings = [{ reservation_slot: 12 }];
  const ui = fixture(async () => response(bookings));
  t.after(ui.cleanup);
  await tick();
  assert.equal(
    ui.nodes.reservation_slot.options.find((option) => option.value === "12")
      .disabled,
    true,
  );
  assert.equal(
    ui.nodes.reservation_slot.options.find((option) => option.value === "13")
      .disabled,
    false,
  );
  assert.equal(
    ui.nodes["reservation-list"].children[0].textContent,
    "12 PM — Reserved",
  );
  bookings = [];
  ui.nodes.reservation_date.value = "2099-04-08";
  await ui.nodes.reservation_date.emit("change");
  await tick();
  assert.equal(ui.nodes["availability-status"].textContent, "No Bookings");
  assert.equal(ui.submit.disabled, false);
});

test("late results for an earlier date cannot replace current availability", async (t) => {
  const pending = [];
  const ui = fixture(() => new Promise((resolve) => pending.push(resolve)));
  t.after(ui.cleanup);
  ui.nodes.reservation_date.value = "2099-04-09";
  await ui.nodes.reservation_date.emit("change");
  pending[1](response([{ reservation_slot: 15 }]));
  await tick();
  pending[0](response([{ reservation_slot: 12 }]));
  await tick();
  assert.equal(ui.nodes["reservation-list"].children.length, 1);
  assert.equal(
    ui.nodes["reservation-list"].children[0].textContent,
    "3 PM — Reserved",
  );
  assert.equal(
    ui.nodes.reservation_slot.options.find((option) => option.value === "12")
      .disabled,
    false,
  );
});

test("availability failures disable submission and expose working retry", async (t) => {
  let failing = true;
  const ui = fixture(async () => {
    if (failing) throw new Error("offline");
    return response([]);
  });
  t.after(ui.cleanup);
  await tick();
  assert.equal(ui.submit.disabled, true);
  assert.equal(ui.nodes.reservation_slot.disabled, true);
  assert.equal(ui.nodes["retry-availability"].hidden, false);
  assert.match(
    ui.nodes["availability-status"].textContent,
    /could not be loaded/,
  );
  failing = false;
  await ui.nodes["retry-availability"].emit("click");
  assert.equal(ui.submit.disabled, false);
  assert.equal(ui.nodes["retry-availability"].hidden, true);
});

test("reservation submits integer hour and CSRF then refreshes booked times", async (t) => {
  const calls = [];
  let saved;
  const ui = fixture(async (url, options = {}) => {
    calls.push({ url, options });
    if (options.method === "POST") {
      saved = JSON.parse(options.body);
      return response(saved);
    }
    return response(saved ? [saved] : []);
  });
  t.after(ui.cleanup);
  await tick();
  ui.nodes.first_name.value = "  Sam  ";
  ui.nodes.reservation_slot.value = "14";
  await ui.nodes["booking-form"].emit("submit");
  const post = calls.find((call) => call.options.method === "POST");
  assert.equal(post.url, "/book/");
  assert.equal(post.options.headers["X-CSRFToken"], "fixture-csrf");
  assert.deepEqual(JSON.parse(post.options.body), {
    first_name: "Sam",
    reservation_date: "2099-04-07",
    reservation_slot: 14,
  });
  assert.equal(ui.nodes.first_name.value, "");
  assert.match(ui.nodes["form-message"].textContent, /Table reserved for Sam/);
  assert.equal(
    ui.nodes.reservation_slot.options.find((option) => option.value === "14")
      .disabled,
    true,
  );
  assert.equal(ui.nodes.first_name.disabled, false);
  assert.equal(calls.length, 3);
});

test("rejected reservation preserves customer input and reports correction", async (t) => {
  const ui = fixture(async (url, options = {}) =>
    options.method === "POST"
      ? response(
          { reservation_slot: ["This hour is already reserved."] },
          false,
        )
      : response([]),
  );
  t.after(ui.cleanup);
  await tick();
  ui.nodes.first_name.value = "Sam";
  ui.nodes.reservation_slot.value = "14";
  await ui.nodes["booking-form"].emit("submit");
  assert.equal(ui.nodes.first_name.value, "Sam");
  assert.equal(ui.nodes["form-message"].dataset.tone, "error");
  assert.match(
    ui.nodes["reservation_slot-error"].textContent,
    /already reserved/,
  );
  assert.equal(ui.nodes.reservation_slot.attributes["aria-invalid"], "true");
  assert.equal(ui.nodes.reservation_slot.focused, true);
  assert.equal(ui.nodes.first_name.disabled, false);
});
