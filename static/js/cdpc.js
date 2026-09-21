let ALL_COMPANIES = [];
let ALL_DRIVES = [];
let ALL_APPLICATIONS = [];
let ALL_STUDENTS = [];

function navigateTo(viewName) {
  document.querySelectorAll(".view-section").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".sidebar-link").forEach((el) => el.classList.remove("active"));
  document.getElementById(`view-${viewName}`)?.classList.add("active");
  document.querySelector(`.sidebar-link[data-view="${viewName}"]`)?.classList.add("active");
  closeAllDropdowns();
  loadViewData(viewName);
}
window.navigateTo = navigateTo;

function initSidebarNav() {
  document.querySelectorAll(".sidebar-link[data-view]").forEach((link) => link.addEventListener("click", () => navigateTo(link.dataset.view)));
  document.querySelectorAll("[data-view-link]").forEach((el) => el.addEventListener("click", () => navigateTo(el.dataset.viewLink)));
}

function loadViewData(view) {
  const loaders = {
    overview: loadOverview, students: loadStudents, companies: loadCompanies,
    drives: loadDrives, applications: loadApplications, interviews: loadInterviews,
    results: loadResults, analytics: loadAnalytics, "send-notification": loadSendNotificationView,
  };
  if (loaders[view]) loaders[view]();
}

function statusBadge(status) {
  const cls = { Applied: "badge-blue", Shortlisted: "badge-yellow", Interview: "badge-purple", Selected: "badge-green", Rejected: "badge-red" }[status] || "badge-muted";
  return `<span class="badge ${cls}">${status}</span>`;
}

/* ---------------- Overview ---------------- */
async function loadOverview() {
  try {
    const [statsData, appsData, interviewsData] = await Promise.all([
      apiRequest("/cdpc/dashboard-stats"), apiRequest("/cdpc/applications"), apiRequest("/cdpc/interviews"),
    ]);
    const s = statsData.stats;
    document.getElementById("cdpc-stats-grid").innerHTML = `
      ${statCard("graduation-cap", s.total_students, "Total Students", "blue")}
      ${statCard("trophy", `${s.placed_students} (${s.placement_percent}%)`, "Students Placed", "green")}
      ${statCard("building-2", s.total_companies, "Companies Onboarded", "purple")}
      ${statCard("clipboard-list", s.active_drives, "Active Drives", "orange")}
    `;
    const apps = appsData.applications.slice(0, 5);
    document.getElementById("overview-applications-list").innerHTML = apps.length ? apps.map((a) => `
      <div class="timeline-item"><div class="timeline-dot" style="background:var(--accent-blue)"></div>
      <div class="flex-col" style="flex:1;"><div class="flex justify-between"><b class="text-sm">${escapeHtml(a.student_name)}</b>${statusBadge(a.status)}</div>
      <span class="text-muted text-sm">${escapeHtml(a.role_title)} @ ${escapeHtml(a.company_name)}</span></div></div>`).join("")
      : `<div class="empty-state"><p>No applications yet.</p></div>`;

    const interviews = interviewsData.interviews.filter((i) => i.status === "Scheduled").slice(0, 5);
    document.getElementById("overview-interviews-list").innerHTML = interviews.length ? interviews.map((i) => `
      <div class="timeline-item"><div class="timeline-dot" style="background:var(--accent-purple)"></div>
      <div class="flex-col" style="flex:1;"><b class="text-sm">${escapeHtml(i.student_name)}</b>
      <span class="text-muted text-sm">${escapeHtml(i.round_name)} · ${escapeHtml(i.scheduled_at || "TBA")}</span></div></div>`).join("")
      : `<div class="empty-state"><p>No interviews scheduled.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

function statCard(iconName, value, label, color) {
  const map = { orange: ["var(--accent-orange-soft)", "var(--accent-orange)"], blue: ["var(--accent-blue-soft)", "var(--accent-blue)"], green: ["var(--accent-green-soft)", "var(--accent-green)"], purple: ["var(--accent-purple-soft)", "var(--accent-purple)"] };
  const [bg, fg] = map[color] || map.orange;
  return `<div class="card stat-card"><div class="stat-top"><div class="stat-icon" style="background:${bg}; color:${fg};">${icon(iconName)}</div></div><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`;
}

/* ---------------- Students ---------------- */
async function loadStudents() {
  try {
    const data = await apiRequest("/cdpc/students");
    ALL_STUDENTS = data.students;
    const branches = [...new Set(ALL_STUDENTS.map((s) => s.branch))];
    const branchSelect = document.getElementById("students-filter-branch");
    if (branchSelect.options.length <= 1) {
      branches.forEach((b) => branchSelect.insertAdjacentHTML("beforeend", `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`));
    }
    document.getElementById("students-filter-branch").onchange = renderStudents;
    document.getElementById("students-filter-placed").onchange = renderStudents;
    renderStudents();
  } catch (e) { showToast(e.message, "error"); }
}

function renderStudents() {
  const branchFilter = document.getElementById("students-filter-branch").value;
  const placedFilter = document.getElementById("students-filter-placed").value;
  let students = ALL_STUDENTS;
  if (branchFilter) students = students.filter((s) => s.branch === branchFilter);
  if (placedFilter) students = students.filter((s) => String(s.placed) === placedFilter);

  const tbody = document.getElementById("students-tbody");
  tbody.innerHTML = students.length ? students.map((s) => `
    <tr>
      <td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.roll_number || "-")}</td><td>${escapeHtml(s.branch)}</td>
      <td>${s.cgpa}</td><td>${s.backlogs}</td>
      <td>${s.placed ? '<span class="badge badge-green">Placed</span>' : '<span class="badge badge-muted">Not Placed</span>'}</td>
      <td>${s.resume_filename ? `<a href="/api/common/resume/${encodeURIComponent(s.resume_filename)}" target="_blank" class="badge badge-blue">View</a>` : '<span class="text-muted text-sm">None</span>'}</td>
      <td><button class="btn btn-outline btn-sm" onclick="togglePlaced(${s.id}, ${!s.placed})">${s.placed ? "Mark Unplaced" : "Mark Placed"}</button></td>
    </tr>`).join("") : `<tr><td colspan="8"><div class="empty-state"><p>No students match filters.</p></div></td></tr>`;
}

async function togglePlaced(studentId, newVal) {
  try {
    await apiRequest(`/cdpc/students/${studentId}`, { method: "PUT", body: { placed: newVal } });
    showToast("Student record updated.", "success");
    loadStudents();
  } catch (e) { showToast(e.message, "error"); }
}

function exportCSV(type) {
  if (type === "students") {
    const rows = [["Name", "Roll No", "Branch", "CGPA", "Backlogs", "Placed"]];
    ALL_STUDENTS.forEach((s) => rows.push([s.name, s.roll_number, s.branch, s.cgpa, s.backlogs, s.placed]));
    const csv = rows.map((r) => r.map((v) => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "students.csv"; a.click();
    URL.revokeObjectURL(url);
  }
}

/* ---------------- Companies ---------------- */
async function loadCompanies() {
  try {
    const data = await apiRequest("/cdpc/companies");
    ALL_COMPANIES = data.companies;
    const grid = document.getElementById("companies-grid");
    grid.innerHTML = ALL_COMPANIES.length ? ALL_COMPANIES.map((c) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(c.company_name)}</div><div class="ec-sub">${escapeHtml(c.industry || "")}</div></div>
        ${c.is_approved ? '<span class="badge badge-green">Approved</span>' : '<span class="badge badge-yellow">Pending</span>'}</div>
        <div class="ec-meta"><span>${icon("mail", 14)} ${escapeHtml(c.email)}</span><span>${icon("clipboard-list", 14)} ${c.drives_count} drives</span></div>
        <p class="text-sm text-secondary">${escapeHtml((c.about || "").slice(0, 100))}</p>
        ${!c.is_approved ? `<button class="btn btn-secondary btn-sm" onclick="approveCompany(${c.id})">Approve Company</button>` : ""}
      </div>`).join("") : `<div class="empty-state"><p>No companies yet.</p></div>`;
    populateCompanySelect();
  } catch (e) { showToast(e.message, "error"); }
}

async function approveCompany(id) {
  try {
    await apiRequest(`/cdpc/companies/${id}/approve`, { method: "PUT" });
    showToast("Company approved.", "success");
    loadCompanies();
  } catch (e) { showToast(e.message, "error"); }
}

function populateCompanySelect() {
  const sel = document.getElementById("cd-company");
  if (!sel) return;
  sel.innerHTML = ALL_COMPANIES.map((c) => `<option value="${c.id}">${escapeHtml(c.company_name)}</option>`).join("");
}

/* ---------------- Drives ---------------- */
async function loadDrives() {
  try {
    const data = await apiRequest("/cdpc/drives");
    ALL_DRIVES = data.drives;
    const grid = document.getElementById("drives-grid");
    grid.innerHTML = ALL_DRIVES.length ? ALL_DRIVES.map((d) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(d.role_title)}</div><div class="ec-sub">${escapeHtml(d.company_name || "")}</div></div>
        <span class="badge ${d.status === "Closed" ? "badge-red" : d.status === "Ongoing" ? "badge-green" : "badge-blue"}">${d.status}</span></div>
        <div class="ec-meta"><span>${icon("dollar-sign", 14)} ${escapeHtml(d.ctc || "N/A")}</span><span>${icon("map-pin", 14)} ${escapeHtml(d.location || "N/A")}</span><span>${icon("users", 14)} ${d.applicants_count} applied</span></div>
        <div class="ec-footer">
          <select onchange="quickUpdateDriveStatus(${d.id}, this.value)" style="background:var(--bg-2); border:1px solid var(--border); color:var(--text-primary); padding:6px 10px; border-radius:8px; font-size:0.78rem;">
            <option ${d.status === "Upcoming" ? "selected" : ""}>Upcoming</option>
            <option ${d.status === "Ongoing" ? "selected" : ""}>Ongoing</option>
            <option ${d.status === "Closed" ? "selected" : ""}>Closed</option>
          </select>
          <button class="btn btn-danger btn-sm" onclick="deleteDrive(${d.id})">Delete</button>
        </div>
      </div>`).join("") : `<div class="empty-state"><p>No drives created yet.</p></div>`;
    populateDriveSelectFilters();
  } catch (e) { showToast(e.message, "error"); }
}

function populateDriveSelectFilters() {
  const sel = document.getElementById("apps-filter-drive");
  if (sel) {
    sel.innerHTML = `<option value="">All Drives</option>` + ALL_DRIVES.map((d) => `<option value="${d.id}">${escapeHtml(d.role_title)} — ${escapeHtml(d.company_name || "")}</option>`).join("");
  }
}

async function quickUpdateDriveStatus(driveId, status) {
  try {
    await apiRequest(`/cdpc/drives/${driveId}`, { method: "PUT", body: { status } });
    showToast("Drive status updated.", "success");
    loadDrives();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteDrive(driveId) {
  if (!confirm("Delete this drive? This will remove all related applications.")) return;
  try {
    await apiRequest(`/cdpc/drives/${driveId}`, { method: "DELETE" });
    showToast("Drive deleted.", "success");
    loadDrives();
  } catch (e) { showToast(e.message, "error"); }
}

function openCreateDriveModal() {
  if (!ALL_COMPANIES.length) loadCompanies().then(() => openModal("create-drive-modal"));
  else { populateCompanySelect(); openModal("create-drive-modal"); }
}

async function submitCreateDrive() {
  const payload = {
    company_id: document.getElementById("cd-company").value,
    role_title: document.getElementById("cd-role").value,
    job_type: document.getElementById("cd-jobtype").value,
    description: document.getElementById("cd-description").value,
    ctc: document.getElementById("cd-ctc").value,
    location: document.getElementById("cd-location").value,
    min_cgpa: document.getElementById("cd-mincgpa").value,
    max_backlogs: document.getElementById("cd-maxbacklogs").value,
    eligible_branches: document.getElementById("cd-branches").value,
    drive_date: document.getElementById("cd-drivedate").value,
    application_deadline: document.getElementById("cd-deadline").value,
    status: document.getElementById("cd-status").value,
  };
  if (!payload.role_title || !payload.company_id) { showToast("Please select a company and enter a role title.", "error"); return; }
  try {
    await apiRequest("/cdpc/drives", { method: "POST", body: payload });
    showToast("Drive created successfully.", "success");
    closeModal("create-drive-modal");
    loadDrives();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Applications ---------------- */
async function loadApplications() {
  try {
    if (!ALL_DRIVES.length) await loadDrives();
    const data = await apiRequest("/cdpc/applications");
    ALL_APPLICATIONS = data.applications;
    document.getElementById("apps-filter-drive").onchange = renderApplications;
    renderApplications();
  } catch (e) { showToast(e.message, "error"); }
}

function renderApplications() {
  const driveFilter = document.getElementById("apps-filter-drive").value;
  let apps = ALL_APPLICATIONS;
  if (driveFilter) apps = apps.filter((a) => String(a.drive_id) === driveFilter);

  const tbody = document.getElementById("cdpc-applications-tbody");
  tbody.innerHTML = apps.length ? apps.map((a) => `
    <tr>
      <td>${escapeHtml(a.student_name)}</td><td>${escapeHtml(a.branch || "-")}</td><td>${a.cgpa ?? "-"}</td>
      <td>${escapeHtml(a.role_title)}</td><td>${escapeHtml(a.company_name)}</td><td>${statusBadge(a.status)}</td>
      <td>
        <select onchange="updateAppStatus(${a.id}, this.value)" style="background:var(--bg-2); border:1px solid var(--border); color:var(--text-primary); padding:5px 8px; border-radius:8px; font-size:0.76rem;">
          ${["Applied","Shortlisted","Interview","Selected","Rejected"].map((s) => `<option ${a.status===s?"selected":""}>${s}</option>`).join("")}
        </select>
      </td>
    </tr>`).join("") : `<tr><td colspan="7"><div class="empty-state"><p>No applications found.</p></div></td></tr>`;
}

async function updateAppStatus(appId, status) {
  try {
    await apiRequest(`/cdpc/applications/${appId}/status`, { method: "PUT", body: { status } });
    showToast("Application status updated.", "success");
    loadApplications();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Interviews ---------------- */
async function loadInterviews() {
  try {
    if (!ALL_APPLICATIONS.length) await loadApplications();
    const data = await apiRequest("/cdpc/interviews");
    const list = document.getElementById("interviews-list");
    list.innerHTML = data.interviews.length ? data.interviews.map((i) => `
      <div class="timeline-item">
        <div class="timeline-dot" style="background:${i.status === "Completed" ? "var(--accent-green)" : "var(--accent-blue)"}"></div>
        <div class="flex-col" style="flex:1;">
          <div class="flex justify-between"><b>${escapeHtml(i.student_name)} — ${escapeHtml(i.round_name)}</b><span class="badge ${i.status === "Completed" ? "badge-green" : "badge-blue"}">${i.status}</span></div>
          <span class="text-muted text-sm">${escapeHtml(i.role_title || "")} @ ${escapeHtml(i.company_name || "")}</span>
          <span class="text-muted text-sm">${icon("clock", 13)} ${escapeHtml(i.scheduled_at || "TBA")} · ${escapeHtml(i.mode)}</span>
          <div class="flex gap-8 mt-8">
            <button class="btn btn-outline btn-sm" onclick="markInterviewCompleted(${i.id})">Mark Completed</button>
          </div>
        </div>
      </div>`).join("") : `<div class="empty-state"><p>No interviews scheduled yet.</p></div>`;
    populateApplicationSelects();
  } catch (e) { showToast(e.message, "error"); }
}

async function markInterviewCompleted(id) {
  const feedback = prompt("Add feedback (optional):", "");
  try {
    await apiRequest(`/cdpc/interviews/${id}`, { method: "PUT", body: { status: "Completed", feedback: feedback || "" } });
    showToast("Interview marked completed.", "success");
    loadInterviews();
  } catch (e) { showToast(e.message, "error"); }
}

function populateApplicationSelects() {
  const opts = ALL_APPLICATIONS.map((a) => `<option value="${a.id}">${escapeHtml(a.student_name)} — ${escapeHtml(a.role_title)} @ ${escapeHtml(a.company_name)} (${a.status})</option>`).join("");
  const si = document.getElementById("si-application");
  const pr = document.getElementById("pr-application");
  if (si) si.innerHTML = opts;
  if (pr) pr.innerHTML = opts;
}

function openScheduleInterviewModal() {
  if (!ALL_APPLICATIONS.length) loadApplications().then(() => { populateApplicationSelects(); openModal("schedule-interview-modal"); });
  else { populateApplicationSelects(); openModal("schedule-interview-modal"); }
}

async function submitScheduleInterview() {
  const payload = {
    application_id: document.getElementById("si-application").value,
    round_name: document.getElementById("si-round").value || "Technical Round 1",
    scheduled_at: document.getElementById("si-datetime").value,
    mode: document.getElementById("si-mode").value,
    venue_or_link: document.getElementById("si-venue").value,
  };
  try {
    await apiRequest("/cdpc/interviews", { method: "POST", body: payload });
    showToast("Interview scheduled.", "success");
    closeModal("schedule-interview-modal");
    loadInterviews();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Results ---------------- */
async function loadResults() {
  try {
    if (!ALL_APPLICATIONS.length) await loadApplications();
    const data = await apiRequest("/cdpc/results");
    const grid = document.getElementById("results-grid");
    grid.innerHTML = data.results.length ? data.results.map((r) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(r.student_name)}</div><div class="ec-sub">${escapeHtml(r.role_title)} @ ${escapeHtml(r.company_name)}</div></div>
        <span class="badge ${r.outcome === "Selected" ? "badge-green" : r.outcome === "Waitlisted" ? "badge-yellow" : "badge-red"}">${r.outcome}</span></div>
        ${r.package_offered ? `<div class="text-sm">${icon("dollar-sign", 14)} ${escapeHtml(r.package_offered)}</div>` : ""}
        <div class="text-muted text-sm">Published: ${r.published_at}</div>
      </div>`).join("") : `<div class="empty-state"><p>No results published yet.</p></div>`;
    populateApplicationSelects();
  } catch (e) { showToast(e.message, "error"); }
}

function openPublishResultModal() {
  if (!ALL_APPLICATIONS.length) loadApplications().then(() => { populateApplicationSelects(); openModal("publish-result-modal"); });
  else { populateApplicationSelects(); openModal("publish-result-modal"); }
}

async function submitPublishResult() {
  const payload = {
    application_id: document.getElementById("pr-application").value,
    outcome: document.getElementById("pr-outcome").value,
    package_offered: document.getElementById("pr-package").value,
    remarks: document.getElementById("pr-remarks").value,
  };
  try {
    await apiRequest("/cdpc/results", { method: "POST", body: payload });
    showToast("Result published.", "success");
    closeModal("publish-result-modal");
    loadResults();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Analytics ---------------- */
async function loadAnalytics() {
  try {
    const data = await apiRequest("/cdpc/analytics");
    const branchEl = document.getElementById("branch-analytics");
    branchEl.innerHTML = Object.entries(data.branch_stats).map(([branch, s]) => {
      const pct = s.total ? Math.round((s.placed / s.total) * 100) : 0;
      return `<div class="mb-16"><div class="flex justify-between text-sm mb-8"><span>${escapeHtml(branch)}</span><span class="text-muted">${s.placed}/${s.total} (${pct}%)</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%;"></div></div></div>`;
    }).join("") || `<p class="text-muted text-sm">No data yet.</p>`;

    const funnelEl = document.getElementById("funnel-analytics");
    const maxVal = Math.max(...Object.values(data.application_funnel), 1);
    funnelEl.innerHTML = Object.entries(data.application_funnel).map(([stage, count]) => `
      <div class="mb-16"><div class="flex justify-between text-sm mb-8"><span>${stage}</span><span class="text-muted">${count}</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${(count/maxVal)*100}%;"></div></div></div>`).join("");

    const topCoEl = document.getElementById("top-companies-analytics");
    topCoEl.innerHTML = data.top_companies.length ? data.top_companies.map((c) => `
      <div class="flex justify-between items-center mb-12"><span class="text-sm">${escapeHtml(c.name)}</span><span class="badge badge-green">${c.offers} offers</span></div>`).join("")
      : `<p class="text-muted text-sm">No offers recorded yet.</p>`;

    const driveStatusEl = document.getElementById("drive-status-analytics");
    driveStatusEl.innerHTML = Object.entries(data.drive_status).map(([status, count]) => `
      <div class="flex justify-between items-center mb-12"><span class="text-sm">${status}</span>${statusBadge(status === "Upcoming" ? "Applied" : status === "Ongoing" ? "Interview" : "Rejected")} <b class="text-sm">${count}</b></div>`).join("");
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Send Notifications ---------------- */
let NOTIF_BRANCHES_LOADED = false;

async function loadSendNotificationView() {
  if (!NOTIF_BRANCHES_LOADED) {
    try {
      const data = await apiRequest("/cdpc/notifications/branches");
      const sel = document.getElementById("notif-branch");
      sel.innerHTML = data.branches.map((b) => `<option value="${escapeHtml(b)}">${escapeHtml(b)}</option>`).join("");
      NOTIF_BRANCHES_LOADED = true;
    } catch (e) { showToast(e.message, "error"); }
  }
  loadSentNotifications();
}

function initNotificationForm() {
  const audienceSelect = document.getElementById("notif-audience");
  const branchField = document.getElementById("notif-branch-field");
  audienceSelect.addEventListener("change", () => {
    branchField.style.display = audienceSelect.value === "branch" ? "block" : "none";
  });

  const messageInput = document.getElementById("notif-message");
  const charCount = document.getElementById("notif-char-count");
  messageInput.addEventListener("input", () => {
    charCount.textContent = messageInput.value.length;
  });

  document.getElementById("send-notification-btn").addEventListener("click", submitSendNotification);
}

async function submitSendNotification() {
  const audience = document.getElementById("notif-audience").value;
  const branch = document.getElementById("notif-branch").value;
  const message = document.getElementById("notif-message").value.trim();

  if (!message) {
    showToast("Please write a message to send.", "error");
    return;
  }

  const btn = document.getElementById("send-notification-btn");
  btn.disabled = true;
  btn.textContent = "Sending...";
  try {
    const res = await apiRequest("/cdpc/notifications/send", {
      method: "POST",
      body: { audience, branch, message },
    });
    showToast(res.message, "success");
    document.getElementById("notif-message").value = "";
    document.getElementById("notif-char-count").textContent = "0";
    loadSentNotifications();
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Send Notification";
  }
}

async function loadSentNotifications() {
  try {
    const data = await apiRequest("/cdpc/notifications/sent");
    const list = document.getElementById("sent-notifications-list");
    list.innerHTML = data.broadcasts.length ? data.broadcasts.map((b) => `
      <div class="timeline-item">
        <div class="timeline-dot" style="background:var(--accent-blue)"></div>
        <div class="flex-col" style="flex:1;">
          <div class="flex justify-between"><span class="badge badge-blue">${escapeHtml(b.audience_label)}</span><span class="text-muted text-sm">${b.recipient_count} recipient(s)</span></div>
          <span class="text-sm mt-8">${escapeHtml(b.message)}</span>
          <span class="text-muted text-sm">${b.created_at} &middot; by ${escapeHtml(b.sender_name || "CDPC")}</span>
        </div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("bell", 32)}</div><p>No notifications sent yet.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Profile ---------------- */
function populateEditProfileForm() {
  const u = CURRENT_USER;
  const p = u.profile || {};
  renderProfilePicturePreview(u);
  document.getElementById("ep-name").value = u.name || "";
  document.getElementById("ep-phone").value = u.phone || "";
  document.getElementById("ep-designation").value = p.designation || "";
  document.getElementById("ep-department").value = p.department || "";
}

async function saveProfile() {
  const payload = {
    name: document.getElementById("ep-name").value.trim(),
    phone: document.getElementById("ep-phone").value.trim(),
    designation: document.getElementById("ep-designation").value.trim(),
    department: document.getElementById("ep-department").value.trim(),
  };
  try {
    const data = await apiRequest("/auth/update-profile", { method: "PUT", body: payload });
    CURRENT_USER = data.user;
    renderNavbarProfile(CURRENT_USER);
    document.getElementById("welcome-heading").textContent = `Welcome back, ${CURRENT_USER.name.split(" ")[0]}!`;
    showToast("Profile updated successfully.", "success");
    closeModal("edit-profile-modal");
  } catch (e) { showToast(e.message, "error"); }
}

async function savePassword() {
  const old_password = document.getElementById("cp-old").value;
  const new_password = document.getElementById("cp-new").value;
  try {
    await apiRequest("/auth/change-password", { method: "PUT", body: { old_password, new_password } });
    showToast("Password updated.", "success");
    closeModal("change-password-modal");
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Boot ---------------- */
document.addEventListener("DOMContentLoaded", async () => {
  renderStaticIcons();
  initSidebarNav();
  initGlobalSearch();
  initMobileSidebar();
  initProfilePictureUpload();
  const user = await loadCurrentUser();
  if (!user) return;
  renderNavbarProfile(user);
  document.getElementById("welcome-heading").textContent = `Welcome back, ${user.name.split(" ")[0]}!`;
  refreshNotifCount();
  loadOverview();

  document.getElementById("save-profile-btn").addEventListener("click", saveProfile);
  document.getElementById("save-password-btn").addEventListener("click", savePassword);
  document.getElementById("submit-drive-btn").addEventListener("click", submitCreateDrive);
  document.getElementById("submit-interview-btn").addEventListener("click", submitScheduleInterview);
  initNotificationForm();
  document.getElementById("submit-result-btn").addEventListener("click", submitPublishResult);

  document.querySelectorAll('button[onclick*="edit-profile-modal"]').forEach((btn) => btn.addEventListener("click", populateEditProfileForm));
});
