// Campus Tech Help Desk - browser interface. Talks only to the JSON API in web.py.
// Builds every element with textContent (never innerHTML) so typed text can't inject markup.
"use strict";

const state = { users: [], meta: null, user: null, tab: null, selected: null, results: null };

const TABS = {
  Requester: ["Submit a request", "My requests"],
  Coordinator: ["All requests", "Search", "Summary"],
  Technician: ["My assignments"],
};

// ---------- small helpers ----------
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined) el.append(kid);
  return el;
}
const $ = (id) => document.getElementById(id);
const when = (iso) => (iso || "").replace("T", " ").slice(0, 16);
const short = (iso) => when(iso).slice(5);  // "11-16 09:00" for tables
const pill = (status) => h("span", { class: `pill s-${status.replace(/ /g, "-")}` }, status);
const options = (list, chosen, blank) => [
  blank !== undefined ? h("option", { value: "" }, blank) : null,
  ...list.map((o) => {
    const [value, text] = typeof o === "string" ? [o, o] : o;
    return h("option", { value, selected: value === chosen }, text);
  }),
];
const userName = (id) => (state.users.find((u) => u.user_id === id) || {}).name || id;

async function api(path, body) {
  const res = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" },
                                         body: JSON.stringify({ user: state.user.user_id, ...body }) } : {});
  const data = await res.json();
  if (!res.ok) { const e = new Error(data.error); e.code = res.status; throw e; }
  return data;
}
const get = (path, params = {}) =>
  api(`${path}?${new URLSearchParams({ user: state.user ? state.user.user_id : "", ...params })}`);

function showError(err) {
  const b = $("banner");
  b.replaceChildren(h("span", {}, err.message), h("button", { type: "button", "aria-label": "Dismiss", onclick: () => (b.hidden = true) }, "×"));
  b.className = "banner " + (err.code === 501 ? "todo" : "error");
  b.hidden = false;
}
function toast(msg) {
  const t = $("toast"); t.textContent = msg; t.hidden = false;
  clearTimeout(toast.timer); toast.timer = setTimeout(() => (t.hidden = true), 2200);
}
async function act(fn, done) {
  $("banner").hidden = true;
  try { await fn(); toast(done); await render(); } catch (e) { showError(e); }
}

// ---------- login ----------
function renderLogin(role) {
  $("roles").replaceChildren(...[
    ["Requester", "Report a technology problem and track it."],
    ["Coordinator", "Review, prioritize and assign requests."],
    ["Technician", "Work on assigned requests and resolve them."],
  ].map(([r, text]) => h("button", { type: "button", class: "role-card", "aria-pressed": String(r === role),
      onclick: () => renderLogin(r) }, h("strong", {}, r), h("span", { class: "muted" }, text))));
  const people = $("people");
  people.hidden = !role;
  if (role) people.replaceChildren(h("h2", {}, "Choose a sample user"),
    ...state.users.filter((u) => u.role === role).map((u) =>
      h("button", { type: "button", class: "person", onclick: () => signIn(u) }, h("span", {}, u.name), h("code", {}, u.user_id))));
}
function signIn(user) {
  $("banner").hidden = true; $("toast").hidden = true;
  state.user = user; state.tab = TABS[user.role][0]; state.selected = null; state.results = null;
  $("login").hidden = true; $("app").hidden = false; $("who").hidden = false;
  $("who-name").textContent = user.name; $("who-role").textContent = user.role;
  render();
}
$("switch").addEventListener("click", () => {
  state.user = null; $("app").hidden = true; $("who").hidden = true; $("login").hidden = false; renderLogin(null);
});

// ---------- main ----------
async function render() {
  $("tabs").replaceChildren(...TABS[state.user.role].map((t) =>
    h("button", { type: "button", class: "tab", "aria-current": t === state.tab ? "page" : null,
      onclick: () => { state.tab = t; state.selected = null; $("banner").hidden = true; render(); } }, t)));
  const view = $("view");
  try {
    if (state.tab === "Submit a request") view.replaceChildren(submitForm());
    else if (state.tab === "Search") view.replaceChildren(await searchView());
    else if (state.tab === "Summary") view.replaceChildren(await summaryView());
    else view.replaceChildren(await listView(state.tab, await get("/api/requests")));
  } catch (e) {
    view.replaceChildren(h("div", { class: "card" }, h("h2", {}, state.tab), h("p", { class: "muted" }, "This screen can't load yet.")));
    showError(e);
  }
}

function requestTable(rows) {
  if (!rows.length) return h("p", { class: "empty" }, "No requests found.");
  return h("div", { class: "table-wrap" }, h("table", {},
    h("thead", {}, h("tr", {}, ["ID", "Title", "Status", "Priority", "Category", "Updated"].map((c) => h("th", {}, c)))),
    h("tbody", {}, rows.map((r) => h("tr", { tabindex: "0", "aria-selected": String(r.request_id === state.selected),
        onclick: () => select(r.request_id), onkeydown: (e) => e.key === "Enter" && select(r.request_id) },
      h("td", { class: "id" }, r.request_id), h("td", {}, r.title), h("td", {}, pill(r.status)),
      h("td", { class: `pri-${r.priority}` }, r.priority), h("td", {}, r.category), h("td", { class: "muted nowrap" }, short(r.updated_at)))))));
}
function select(id) { state.selected = id; render(); }

async function listView(title, rows) {
  const list = h("div", { class: "card" }, h("div", { class: "card-head" }, h("h2", {}, title),
    h("span", { class: "muted" }, `${rows.length} request${rows.length === 1 ? "" : "s"}`)), requestTable(rows));
  return h("div", { class: "split" }, list, await detailPanel());
}

async function detailPanel() {
  if (!state.selected) return h("div", { class: "card" }, h("p", { class: "muted" }, "Select a request to see its details."));
  const d = await get("/api/request", { id: state.selected });
  const r = d.request, role = state.user.role;
  const card = h("div", { class: "card" },
    h("div", { class: "card-head" }, h("h2", {}, `${r.request_id} · ${r.title}`), pill(r.status)),
    h("dl", { class: "fields" },
      h("dt", {}, "Location"), h("dd", {}, r.location),
      h("dt", {}, "Category"), h("dd", {}, r.category),
      h("dt", {}, "Priority"), h("dd", { class: `pri-${r.priority}` }, `${r.priority} (requested: ${r.requested_urgency})`),
      h("dt", {}, "Requester"), h("dd", {}, userName(r.requester_id)),
      h("dt", {}, "Technician"), h("dd", {}, r.assignment ? userName(r.assignment.technician_id) : "Not assigned"),
      h("dt", {}, "Description"), h("dd", {}, r.description)),
    h("h3", {}, "History"),
    h("ul", { class: "history" }, r.history.map((c) => h("li", {}, h("time", {}, when(c.changed_at)),
      `${c.from_status ? c.from_status + " → " : ""}${c.to_status} by ${userName(c.changed_by)}`))),
    h("h3", {}, "Notes"),
    d.notes_message ? h("p", { class: "muted" }, d.notes_message)
      : d.notes.length ? d.notes.map((n) => h("div", { class: `note t-${n.type}` },
          h("div", { class: "by" }, `${n.type} note · ${userName(n.author_id)} · ${when(n.created_at)}`), n.text))
      : h("p", { class: "muted" }, "No notes."));

  // Actions: only what this role may do next (the server still checks everything).
  const next = d.allowed_next;
  if (role === "Coordinator" && r.status === "Submitted") card.append(reviewForm(r));
  if (role === "Coordinator" && r.status === "Reviewed") card.append(assignForm(r));
  const simple = next.filter((s) => !(s === "Reviewed" && r.status === "Submitted") && s !== "Assigned" && s !== "Resolved");
  if (simple.length) card.append(h("div", { class: "action" }, h("h3", {}, "Change status"), h("div", { class: "row" },
    simple.map((s) => h("button", { type: "button", class: "btn ghost small",
      onclick: () => act(() => api("/api/status", { id: r.request_id, status: s }), `Moved to ${s}.`) },
      s === "Cancelled" ? "Cancel request" : s === "Reviewed" ? "Unassign" : s === "Closed" ? "Close request" : r.status === "Resolved" ? "Reopen" : `Move to ${s}`)))));
  if (next.includes("Resolved")) card.append(resolveForm(r));
  if ((role === "Technician" || role === "Coordinator") && !["Closed", "Cancelled"].includes(r.status)) card.append(noteForm(r, role));
  return card;
}

function reviewForm(r) {
  const cat = h("select", { id: "rv-cat" }, options(state.meta.categories, r.category));
  const pri = h("select", { id: "rv-pri" }, options(state.meta.priorities, r.priority));
  return h("div", { class: "action" }, h("h3", {}, "Review"), h("div", { class: "row" },
    h("label", {}, "Category", cat), h("label", {}, "Priority", pri),
    h("button", { type: "button", class: "btn small", onclick: () => act(() => api("/api/review",
      { id: r.request_id, category: cat.value, priority: pri.value }), "Marked as reviewed.") }, "Mark reviewed")));
}
function assignForm(r) {
  const tech = h("select", { id: "as-tech" }, options(state.meta.technicians.map((t) => [t.user_id, t.name])));
  return h("div", { class: "action" }, h("h3", {}, "Assign"), h("div", { class: "row" },
    h("label", {}, "Technician", tech),
    h("button", { type: "button", class: "btn small", onclick: () => act(() => api("/api/assign",
      { id: r.request_id, technician_id: tech.value }), "Assigned.") }, "Assign")));
}
function resolveForm(r) {
  const text = h("textarea", { id: "rs-note", placeholder: "What was the problem and how was it fixed?" });
  return h("div", { class: "action" }, h("h3", {}, "Resolve"), h("label", {}, "Resolution note (the requester sees this)", text),
    h("div", {}, h("button", { type: "button", class: "btn small", onclick: () => act(() => api("/api/status",
      { id: r.request_id, status: "Resolved", resolution_note: text.value }), "Resolved.") }, "Mark resolved")));
}
function noteForm(r, role) {
  const text = h("textarea", { id: "nt-text", placeholder: role === "Technician" ? "What did you do?" : "Internal note for the help desk" });
  return h("div", { class: "action" }, h("h3", {}, role === "Technician" ? "Add work note" : "Add admin note"),
    h("label", {}, "Note (not shown to the requester)", text),
    h("div", {}, h("button", { type: "button", class: "btn ghost small",
      onclick: () => act(() => api("/api/note", { id: r.request_id, text: text.value }), "Note added.") }, "Add note")));
}

function submitForm() {
  const f = {
    title: h("input", { id: "sb-title", maxlength: "100", placeholder: "e.g. Projector won't turn on" }),
    description: h("textarea", { id: "sb-desc", maxlength: "1000", placeholder: "What is happening? When did it start?" }),
    location: h("input", { id: "sb-loc", placeholder: "Building, room, and PC number if relevant" }),
    category: h("select", { id: "sb-cat" }, options(state.meta.categories)),
    urgency: h("select", { id: "sb-urg" }, options(state.meta.priorities, "Medium")),
  };
  return h("div", { class: "card" }, h("h2", {}, "Submit a request"),
    h("form", { class: "form", onsubmit: (e) => { e.preventDefault();
        act(async () => { const r = await api("/api/submit", Object.fromEntries(Object.entries(f).map(([k, el]) => [k, el.value])));
          state.tab = "My requests"; state.selected = r.request_id; }, "Request submitted."); } },
      h("label", {}, "Title", f.title), h("label", {}, "Description", f.description), h("label", {}, "Location", f.location),
      h("div", { class: "grid2" }, h("label", {}, "Category", f.category), h("label", {}, "Urgency", f.urgency)),
      h("div", {}, h("button", { type: "submit", class: "btn" }, "Submit request"))));
}

async function searchView() {
  const people = (role) => state.users.filter((u) => u.role === role).map((u) => [u.user_id, u.name]);
  const f = {
    status: h("select", { id: "sf-status" }, options(state.meta.statuses, null, "Any status")),
    category: h("select", { id: "sf-cat" }, options(state.meta.categories, null, "Any category")),
    priority: h("select", { id: "sf-pri" }, options(state.meta.priorities, null, "Any priority")),
    requester_id: h("select", { id: "sf-req" }, options(people("Requester"), null, "Any requester")),
    technician_id: h("select", { id: "sf-tech" }, options(people("Technician"), null, "Any technician")),
  };
  if (state.filters) for (const [k, v] of Object.entries(state.filters)) f[k].value = v;
  const run = () => act(async () => {
    state.filters = Object.fromEntries(Object.entries(f).map(([k, el]) => [k, el.value]));
    state.results = await get("/api/search", state.filters); }, "Search done.");
  const form = h("div", { class: "card" }, h("h2", {}, "Search and filter"),
    h("div", { class: "grid2" }, h("label", {}, "Status", f.status), h("label", {}, "Category", f.category),
      h("label", {}, "Priority", f.priority), h("label", {}, "Requester", f.requester_id), h("label", {}, "Technician", f.technician_id)),
    h("div", {}, h("button", { type: "button", class: "btn", onclick: run }, "Search")));
  if (!state.results) return form;
  return h("div", { class: "stack" }, form, await listView("Results", state.results));
}

async function summaryView() {
  const s = await get("/api/summary");
  const block = (title, counts) => {
    const max = Math.max(1, ...Object.values(counts));
    return h("div", { class: "card" }, h("h2", {}, title), ...Object.entries(counts).map(([k, v]) =>
      h("div", { class: "bar" }, h("span", {}, k), h("div", { class: "track" }, h("div", { class: "fill", style: `width:${(v / max) * 100}%` })), h("span", {}, String(v)))));
  };
  return h("div", { class: "stats" }, block("Open vs. closed", s.open_closed), block("By category", s.by_category),
    block("By priority", s.by_priority), block("Open by technician", Object.fromEntries(Object.entries(s.by_technician).map(([k, v]) => [userName(k), v]))));
}

// ---------- start ----------
(async () => {
  try {
    [state.users, state.meta] = await Promise.all([get("/api/users"), get("/api/meta")]);
    renderLogin(null);
  } catch (e) { document.body.append(h("p", { class: "banner error" }, "The help desk server isn't responding. Is python -m helpdesk still running?")); }
})();
