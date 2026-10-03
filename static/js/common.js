/* ============================================================
   Shared utilities used across landing, login, and all dashboards
   ============================================================ */

const API_BASE = "/api";

/* ---------- Self-contained line-icon system (no external assets) ---------- */
const ICON_PATHS = {
  home: '<path d="M4 11.5 12 4l8 7.5"/><path d="M6 10v9a1 1 0 0 0 1 1h3v-6h4v6h3a1 1 0 0 0 1-1v-9"/>',
  "building-2": '<rect x="5" y="3" width="9" height="18" rx="1"/><rect x="14" y="9" width="6" height="12" rx="1"/><line x1="8" y1="7" x2="8" y2="7"/><line x1="11" y1="7" x2="11" y2="7"/><line x1="8" y1="11" x2="8" y2="11"/><line x1="11" y1="11" x2="11" y2="11"/><line x1="8" y1="15" x2="8" y2="15"/><line x1="11" y1="15" x2="11" y2="15"/>',
  "clipboard-list": '<rect x="5" y="4" width="14" height="17" rx="2"/><rect x="9" y="2.3" width="6" height="3.4" rx="1"/><line x1="8.5" y1="10" x2="15.5" y2="10"/><line x1="8.5" y1="13.3" x2="15.5" y2="13.3"/><line x1="8.5" y1="16.6" x2="12.5" y2="16.6"/>',
  send: '<path d="M4 12 20 4l-6.5 16-3-6-6.5-2Z"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M6 11a6 6 0 0 0 12 0"/><line x1="12" y1="17" x2="12" y2="21"/><line x1="9" y1="21" x2="15" y2="21"/>',
  trophy: '<path d="M8 4h8v6a4 4 0 0 1-8 0Z"/><path d="M8 5H5a3 3 0 0 0 3 5"/><path d="M16 5h3a3 3 0 0 1-3 5"/><line x1="12" y1="14" x2="12" y2="18"/><path d="M8 21h8"/><path d="M9 21c0-2 1.3-2.5 3-3 1.7.5 3 1 3 3"/>',
  "file-text": '<path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z"/><path d="M14 3v4h4"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="15.5" x2="15" y2="15.5"/>',
  target: '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  brain: '<path d="M9 4.5a2.5 2.5 0 0 0-2.5 2.5v.3A3 3 0 0 0 5 10a3 3 0 0 0 1 5.6V17a3 3 0 0 0 3 3 2 2 0 0 0 2-2V6.5A2 2 0 0 0 9 4.5Z"/><path d="M15 4.5a2.5 2.5 0 0 1 2.5 2.5v.3A3 3 0 0 1 19 10a3 3 0 0 1-1 5.6V17a3 3 0 0 1-3 3 2 2 0 0 1-2-2V6.5A2 2 0 0 1 15 4.5Z"/>',
  bot: '<rect x="5" y="9" width="14" height="10" rx="2"/><line x1="12" y1="5" x2="12" y2="9"/><circle cx="12" cy="3.2" r="1.2"/><line x1="9" y1="14" x2="9" y2="14"/><line x1="15" y1="14" x2="15" y2="14"/><line x1="2.5" y1="13" x2="5" y2="13"/><line x1="19" y1="13" x2="21.5" y2="13"/>',
  "bar-chart": '<line x1="5" y1="21" x2="19" y2="21"/><rect x="6" y="12" width="3.4" height="9"/><rect x="10.3" y="7" width="3.4" height="14"/><rect x="14.6" y="3" width="3.4" height="18"/>',
  "help-circle": '<circle cx="12" cy="12" r="9"/><path d="M9.3 9.3a2.7 2.7 0 1 1 3.8 2.5c-.9.5-1.1 1-1.1 2"/><line x1="12" y1="17" x2="12" y2="17"/>',
  info: '<circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16.5"/><line x1="12" y1="7.5" x2="12" y2="7.5"/>',
  "log-out": '<path d="M9 4H6a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h3"/><line x1="21" y1="12" x2="10" y2="12"/><path d="M17 8l4 4-4 4"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><line x1="20" y1="20" x2="15.3" y2="15.3"/>',
  bell: '<path d="M6 10a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6Z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 13.5a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.9 2.9l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V20a2 2 0 1 1-4 0v-.2a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.9-2.9l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.6-1H4a2 2 0 1 1 0-4h.2a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.9-2.9l.1.1a1.7 1.7 0 0 0 1.9.3H10.5a1.7 1.7 0 0 0 1-1.6V4a2 2 0 1 1 4 0v.2a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.9 2.9l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1a1.7 1.7 0 0 0 1.6 1H20a2 2 0 1 1 0 4h-.2a1.7 1.7 0 0 0-1.6 1Z"/>',
  menu: '<line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/>',
  x: '<line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/>',
  "graduation-cap": '<path d="M2 9 12 4l10 5-10 5-10-5Z"/><path d="M6 11.5V17c0 1 2.7 3 6 3s6-2 6-3v-5.5"/><line x1="21" y1="9" x2="21" y2="15"/>',
  star: '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9-4.3-4.2 5.9-.8Z"/>',
  users: '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/><path d="M16 4.5a3 3 0 0 1 0 5.8"/><path d="M15 14c2.5.3 4.5 2.1 4.5 5"/>',
  "dollar-sign": '<line x1="12" y1="2.5" x2="12" y2="21.5"/><path d="M16.5 6.5c0-1.7-2-2.8-4.5-2.8s-4.5 1.1-4.5 2.8 2 2.5 4.5 3 4.5 1.3 4.5 3-2 2.8-4.5 2.8-4.5-1.1-4.5-2.8"/>',
  "map-pin": '<path d="M12 21s-7-6.3-7-11.5A7 7 0 0 1 19 9.5C19 14.7 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.4"/>',
  clock: '<circle cx="12" cy="12" r="9"/><line x1="12" y1="7.5" x2="12" y2="12.5"/><line x1="12" y1="12.5" x2="15.5" y2="14.3"/>',
  "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8 12.3l2.7 2.7L16.3 9"/>',
  "x-circle": '<circle cx="12" cy="12" r="9"/><line x1="9" y1="9" x2="15" y2="15"/><line x1="15" y1="9" x2="9" y2="15"/>',
  upload: '<line x1="12" y1="16" x2="12" y2="4.5"/><path d="M8 8.5 12 4.5 16 8.5"/><path d="M5 17.5v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1"/>',
  download: '<line x1="12" y1="4" x2="12" y2="15.5"/><path d="M8 11.5 12 15.5 16 11.5"/><path d="M5 17.5v1a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-1"/>',
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  award: '<circle cx="12" cy="8.5" r="5.5"/><path d="M8.5 13.2 7 21l5-2.6L17 21l-1.5-7.8"/>',
  briefcase: '<rect x="3.5" y="7.5" width="17" height="11.5" rx="2"/><path d="M8.5 7.5V6a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v1.5"/><line x1="3.5" y1="12.5" x2="20.5" y2="12.5"/>',
  "chevron-right": '<polyline points="9,5 16,12 9,19"/>',
  "chevron-down": '<polyline points="5,9 12,16 19,9"/>',
  mail: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M4 6.5 12 13l8-6.5"/>',
  "alert-triangle": '<path d="M12 4 21.5 20H2.5Z"/><line x1="12" y1="10" x2="12" y2="14.5"/><line x1="12" y1="17" x2="12" y2="17"/>',
  check: '<polyline points="4,12.5 9,17.5 20,6"/>',
  eye: '<path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  "eye-off": '<path d="M3 3l18 18"/><path d="M10.6 5.7A10.8 10.8 0 0 1 12 5.5c6.5 0 10 6.5 10 6.5a17.3 17.3 0 0 1-3.4 4.3M6.8 6.9C4 8.7 2 12 2 12s3.5 6.5 10 6.5c1.4 0 2.7-.3 3.8-.8"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/>',
};

function icon(name, size = 18) {
  const path = ICON_PATHS[name];
  if (!path) return "";
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;
}

// Fills every static [data-icon="name"] placeholder in the current page.
// Call once on each page's boot — safe to call multiple times (idempotent).
function renderStaticIcons() {
  document.querySelectorAll("[data-icon]").forEach((el) => {
    const name = el.getAttribute("data-icon");
    const size = el.getAttribute("data-icon-size") || 18;
    el.innerHTML = icon(name, size);
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function apiRequest(path, { method = "GET", body = null } = {}, _isRetry = false) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  };
  if (body) opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(API_BASE + path, opts);
  } catch (networkErr) {
    // A genuine connection-level failure (server unreachable / mid-restart) —
    // not an application error. Retry once after a short delay before
    // surfacing anything to the user, since these are usually transient.
    if (!_isRetry) {
      await sleep(500);
      return apiRequest(path, { method, body }, true);
    }
    throw new Error("Can't reach the server. Please check your connection and try again.");
  }

  let data = {};
  try { data = await res.json(); } catch (e) { /* no json body */ }
  if (!res.ok) {
    throw new Error(data.error || "Something went wrong. Please try again.");
  }
  return data;
}

async function apiUpload(path, formData) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  let data = {};
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) throw new Error(data.error || "Upload failed.");
  return data;
}

function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity .3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3800);
}

function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(" ");
  return (parts[0][0] + (parts[1] ? parts[1][0] : "")).toUpperCase();
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function closeAllDropdowns(exceptId = null) {
  document.querySelectorAll(".dropdown-panel.open").forEach((el) => {
    if (el.id !== exceptId) el.classList.remove("open");
  });
}

document.addEventListener("click", (e) => {
  if (!e.target.closest(".dropdown-wrap")) closeAllDropdowns();
  if (!e.target.closest(".navbar-search")) {
    const sr = document.getElementById("search-results");
    if (sr) sr.classList.remove("open");
  }
});

/* ============================================================
   Navbar bootstrapping — call initNavbar(currentUser) from each
   dashboard page after fetching /api/auth/me
   ============================================================ */

let CURRENT_USER = null;

async function loadCurrentUser() {
  try {
    const data = await apiRequest("/auth/me");
    CURRENT_USER = data.user;
    return data.user;
  } catch (e) {
    window.location.href = "/login";
    return null;
  }
}

function renderAvatarInto(el, user) {
  if (user.profile_picture) {
    el.style.background = "transparent";
    el.innerHTML = `<img src="/api/common/profile-picture/${encodeURIComponent(user.profile_picture)}" alt="${escapeHtml(user.name)}" />`;
  } else {
    el.style.background = user.avatar_color || "#f97316";
    el.textContent = initials(user.name);
  }
}

function renderNavbarProfile(user) {
  const avatarEls = document.querySelectorAll(".js-avatar");
  avatarEls.forEach((el) => renderAvatarInto(el, user));
  const nameEls = document.querySelectorAll(".js-user-name");
  nameEls.forEach((el) => (el.textContent = user.name));
  const roleEls = document.querySelectorAll(".js-user-role");
  const roleLabel = { student: "Student", cdpc: "CDPC / Admin", company: "Company" }[user.role] || user.role;
  roleEls.forEach((el) => (el.textContent = roleLabel));
  renderProfileDetailCard(user);
}

// Builds the "who am I" card shown at the top of the account dropdown —
// real profile details rather than just a menu of actions.
function renderProfileDetailCard(user) {
  const mount = document.getElementById("profile-detail-card-mount");
  if (!mount) return;
  const p = user.profile || {};
  const roleLabel = { student: "Student", cdpc: "CDPC / Admin", company: "Company" }[user.role] || user.role;

  let meta = roleLabel;
  if (user.role === "student") {
    meta = `${escapeHtml(p.roll_number || "No roll no.")} \u00b7 CGPA ${escapeHtml(String(p.cgpa ?? "—"))}`;
  } else if (user.role === "cdpc") {
    meta = escapeHtml(p.designation || "Placement Officer");
  } else if (user.role === "company") {
    meta = escapeHtml(p.company_name || "Company");
  }

  const avatarInner = user.profile_picture
    ? `<img src="/api/common/profile-picture/${encodeURIComponent(user.profile_picture)}" alt="${escapeHtml(user.name)}" />`
    : initials(user.name);
  const avatarBg = user.profile_picture ? "transparent" : (user.avatar_color || "#f97316");

  mount.innerHTML = `
    <div class="pdc-avatar" style="background:${avatarBg};">${avatarInner}</div>
    <div class="pdc-name" title="${escapeHtml(user.name)}">${escapeHtml(user.name)}</div>
    <div class="pdc-email" title="${escapeHtml(user.email)}">${escapeHtml(user.email)}</div>
    <div class="pdc-meta">${meta}</div>
  `;
}

function toggleDropdown(id) {
  const el = document.getElementById(id);
  const isOpen = el.classList.contains("open");
  closeAllDropdowns();
  if (!isOpen) {
    el.classList.add("open");
    if (id === "notif-panel") loadNotifications();
  }
}

async function loadNotifications() {
  const list = document.getElementById("notif-list");
  if (!list) return;
  list.innerHTML = `<div class="loading-row"><div class="spinner"></div></div>`;
  try {
    const data = await apiRequest("/common/notifications");
    updateNotifDot(data.unread_count);
    if (data.notifications.length === 0) {
      list.innerHTML = `<div class="empty-state"><div class="icon">${icon("bell", 32)}</div><p>No notifications yet.</p></div>`;
      return;
    }
    list.innerHTML = data.notifications
      .map(
        (n) => `
      <div class="notif-item ${n.is_read ? "" : "unread"}" data-id="${n.id}" onclick="markNotifRead(${n.id})">
        <div class="msg">${escapeHtml(n.message)}</div>
        <div class="time">${n.created_at}</div>
      </div>`
      )
      .join("");
  } catch (e) {
    list.innerHTML = `<div class="empty-state"><p>Couldn't load notifications.</p></div>`;
  }
}

async function markNotifRead(id) {
  try {
    await apiRequest(`/common/notifications/${id}/read`, { method: "PUT" });
    loadNotifications();
  } catch (e) {}
}

async function markAllNotifsRead() {
  try {
    await apiRequest("/common/notifications/read-all", { method: "PUT" });
    loadNotifications();
  } catch (e) {}
}

function updateNotifDot(count) {
  const dot = document.getElementById("notif-dot");
  if (dot) dot.classList.toggle("show", count > 0);
  const countEl = document.getElementById("notif-count-label");
  if (countEl) countEl.textContent = count > 0 ? `${count} new` : "All caught up";
}

async function refreshNotifCount() {
  try {
    const data = await apiRequest("/common/notifications");
    updateNotifDot(data.unread_count);
  } catch (e) {}
}

/* ---------- Global search ---------- */
let searchDebounce = null;
function initGlobalSearch() {
  const input = document.getElementById("navbar-search-input");
  if (!input) return;
  input.addEventListener("input", () => {
    clearTimeout(searchDebounce);
    const q = input.value.trim();
    const resultsEl = document.getElementById("search-results");
    if (q.length < 1) {
      resultsEl.classList.remove("open");
      return;
    }
    searchDebounce = setTimeout(async () => {
      try {
        const data = await apiRequest(`/common/search?q=${encodeURIComponent(q)}`);
        renderSearchResults(data.results);
      } catch (e) {}
    }, 280);
  });
}

function renderSearchResults(results) {
  const resultsEl = document.getElementById("search-results");
  if (!resultsEl) return;
  if (!results.length) {
    resultsEl.innerHTML = `<div class="search-result-item"><span class="srt-sub">No matches found.</span></div>`;
  } else {
    resultsEl.innerHTML = results
      .map(
        (r) => `
      <div class="search-result-item" onclick="handleSearchResultClick('${r.link}')">
        <div>
          <div class="srt-label">${escapeHtml(r.label)}</div>
          <div class="srt-sub">${escapeHtml(r.sub || "")}</div>
        </div>
        <span class="badge badge-blue">${r.type}</span>
      </div>`
      )
      .join("");
  }
  resultsEl.classList.add("open");
}

function handleSearchResultClick(link) {
  document.getElementById("search-results").classList.remove("open");
  document.getElementById("navbar-search-input").value = "";
  if (link && link.startsWith("#")) {
    const navFn = window.navigateTo;
    if (navFn) navFn(link.replace("#", ""));
  }
}

/* ---------- Profile edit modal (shared across dashboards) ---------- */
function openModal(id) {
  document.getElementById(id).classList.add("open");
}
function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

async function handleLogout() {
  try {
    await apiRequest("/auth/logout", { method: "POST" });
  } catch (e) {}
  window.location.href = "/";
}

/* ---------- Generic confirm dialog (built once, reused everywhere) ---------- */
function showConfirmDialog({ title, message, confirmText = "Confirm", danger = true, onConfirm }) {
  let overlay = document.getElementById("generic-confirm-modal");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "generic-confirm-modal";
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal-box" style="max-width:380px;">
        <div class="modal-body" style="text-align:center; padding-top:34px;">
          <div class="confirm-icon" id="confirm-modal-icon"></div>
          <h3 id="confirm-modal-title" class="mb-8"></h3>
          <p class="text-muted text-sm" id="confirm-modal-message"></p>
        </div>
        <div class="modal-footer" style="justify-content:center;">
          <button class="btn btn-outline" id="confirm-modal-cancel">Cancel</button>
          <button class="btn btn-danger" id="confirm-modal-confirm"></button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("open");
    });
  }
  overlay.querySelector("#confirm-modal-title").textContent = title;
  overlay.querySelector("#confirm-modal-message").textContent = message;
  overlay.querySelector("#confirm-modal-icon").innerHTML = icon(danger ? "log-out" : "help-circle", 32);
  const confirmBtn = overlay.querySelector("#confirm-modal-confirm");
  confirmBtn.textContent = confirmText;
  confirmBtn.className = danger ? "btn btn-danger" : "btn btn-primary";
  // Replace node to clear any previously-bound click listeners
  const freshBtn = confirmBtn.cloneNode(true);
  confirmBtn.parentNode.replaceChild(freshBtn, confirmBtn);
  freshBtn.addEventListener("click", () => {
    overlay.classList.remove("open");
    onConfirm();
  });
  overlay.querySelector("#confirm-modal-cancel").onclick = () => overlay.classList.remove("open");
  overlay.classList.add("open");
}

/* ---------- Profile picture upload (shared by all 3 dashboards' Edit Profile modal) ---------- */

// Renders the current picture (or initials) into the #ppu-preview element
// inside the Edit Profile modal. Call this each time the modal is opened.
function renderProfilePicturePreview(user) {
  const preview = document.getElementById("ppu-preview");
  const removeBtn = document.getElementById("ppu-remove-btn");
  if (!preview) return;
  renderAvatarInto(preview, user);
  if (removeBtn) removeBtn.style.display = user.profile_picture ? "inline-flex" : "none";
}

// Wires up the file input + remove button. Call once per dashboard boot.
function initProfilePictureUpload() {
  const fileInput = document.getElementById("ppu-file-input");
  const removeBtn = document.getElementById("ppu-remove-btn");
  if (!fileInput) return;

  fileInput.addEventListener("change", async () => {
    if (!fileInput.files.length) return;
    const file = fileInput.files[0];
    const validTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type)) {
      showToast("Please choose a JPG, PNG, or WEBP image.", "error");
      fileInput.value = "";
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      showToast("Image is too large. Please choose one under 2 MB.", "error");
      fileInput.value = "";
      return;
    }
    const formData = new FormData();
    formData.append("picture", file);
    try {
      const data = await apiUpload("/auth/profile-picture", formData);
      CURRENT_USER.profile_picture = data.profile_picture;
      renderNavbarProfile(CURRENT_USER);
      renderProfilePicturePreview(CURRENT_USER);
      showToast("Profile picture updated.", "success");
    } catch (e) {
      showToast(e.message, "error");
    } finally {
      fileInput.value = "";
    }
  });

  if (removeBtn) {
    removeBtn.addEventListener("click", async () => {
      try {
        await apiRequest("/auth/profile-picture", { method: "DELETE" });
        CURRENT_USER.profile_picture = null;
        renderNavbarProfile(CURRENT_USER);
        renderProfilePicturePreview(CURRENT_USER);
        showToast("Profile picture removed.", "success");
      } catch (e) {
        showToast(e.message, "error");
      }
    });
  }
}

function confirmLogout() {
  closeAllDropdowns();
  showConfirmDialog({
    title: "Log out?",
    message: "Are you sure you want to log out of your RGUKT Ongole Placement Portal account?",
    confirmText: "Log Out",
    danger: true,
    onConfirm: handleLogout,
  });
}

// Alias kept for pages/buttons that call openLogoutConfirm() — same dialog.
function openLogoutConfirm() {
  confirmLogout();
}

/* ---------- Mobile sidebar ---------- */
function initMobileSidebar() {
  const toggleBtn = document.getElementById("sidebar-toggle-btn");
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  if (!toggleBtn || !sidebar) return;
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.add("open");
    overlay.classList.add("open");
  });
  overlay?.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("open");
  });
  document.querySelectorAll(".sidebar-link").forEach((link) => {
    link.addEventListener("click", () => {
      sidebar.classList.remove("open");
      overlay?.classList.remove("open");
    });
  });
}

function fmtDate(dstr) {
  if (!dstr) return "-";
  return dstr;
}
