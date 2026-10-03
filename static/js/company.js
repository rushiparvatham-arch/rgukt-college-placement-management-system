let MY_DRIVES = [];
let MY_APPLICANTS = [];

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
  const loaders = { overview: loadOverview, drives: loadMyDrives, applicants: loadApplicants, students: loadBrowseStudents };
  if (loaders[view]) loaders[view]();
}

function statusBadge(status) {
  const cls = { Applied: "badge-blue", Shortlisted: "badge-yellow", Interview: "badge-purple", Selected: "badge-green", Rejected: "badge-red" }[status] || "badge-muted";
  return `<span class="badge ${cls}">${status}</span>`;
}

function statCard(iconName, value, label, color) {
  const map = { orange: ["var(--accent-orange-soft)", "var(--accent-orange)"], blue: ["var(--accent-blue-soft)", "var(--accent-blue)"], green: ["var(--accent-green-soft)", "var(--accent-green)"], purple: ["var(--accent-purple-soft)", "var(--accent-purple)"] };
  const [bg, fg] = map[color] || map.orange;
  return `<div class="card stat-card"><div class="stat-top"><div class="stat-icon" style="background:${bg}; color:${fg};">${icon(iconName)}</div></div><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`;
}

/* ---------------- Overview ---------------- */
async function loadOverview() {
  try {
    const [statsData, appsData] = await Promise.all([apiRequest("/company/dashboard-stats"), apiRequest("/company/applications")]);
    const s = statsData.stats;
    document.getElementById("company-stats-grid").innerHTML = `
      ${statCard("clipboard-list", s.active_drives, "Active Drives", "orange")}
      ${statCard("send", s.total_applicants, "Total Applicants", "blue")}
      ${statCard("star", s.shortlisted, "Shortlisted", "purple")}
      ${statCard("trophy", s.selected, "Selected", "green")}
    `;
    const apps = appsData.applications.slice(0, 6);
    document.getElementById("overview-applicants-list").innerHTML = apps.length ? apps.map((a) => `
      <div class="timeline-item"><div class="timeline-dot" style="background:var(--accent-blue)"></div>
      <div class="flex-col" style="flex:1;"><div class="flex justify-between"><b class="text-sm">${escapeHtml(a.student_name)}</b>${statusBadge(a.status)}</div>
      <span class="text-muted text-sm">${escapeHtml(a.role_title)} · ${escapeHtml(a.branch || "")} · CGPA ${a.cgpa ?? "-"}</span></div></div>`).join("")
      : `<div class="empty-state"><p>No applicants yet.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- My Drives ---------------- */
async function loadMyDrives() {
  try {
    const data = await apiRequest("/company/drives");
    MY_DRIVES = data.drives;
    const grid = document.getElementById("my-drives-grid");
    grid.innerHTML = MY_DRIVES.length ? MY_DRIVES.map((d) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(d.role_title)}</div><div class="ec-sub">${escapeHtml(d.job_type)}</div></div>
        <span class="badge ${d.status === "Closed" ? "badge-red" : d.status === "Ongoing" ? "badge-green" : "badge-blue"}">${d.status}</span></div>
        <div class="ec-meta"><span>${icon("dollar-sign", 14)} ${escapeHtml(d.ctc || "N/A")}</span><span>${icon("map-pin", 14)} ${escapeHtml(d.location || "N/A")}</span><span>${icon("users", 14)} ${d.applicants_count} applied</span></div>
        <div class="ec-footer">
          <span class="text-muted text-sm">Deadline: ${escapeHtml(d.application_deadline || "N/A")}</span>
          <select onchange="quickUpdateDriveStatus(${d.id}, this.value)" style="background:var(--bg-2); border:1px solid var(--border); color:var(--text-primary); padding:6px 10px; border-radius:8px; font-size:0.78rem;">
            <option ${d.status === "Upcoming" ? "selected" : ""}>Upcoming</option>
            <option ${d.status === "Ongoing" ? "selected" : ""}>Ongoing</option>
            <option ${d.status === "Closed" ? "selected" : ""}>Closed</option>
          </select>
        </div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("clipboard-list", 32)}</div><p>You haven't posted any drives yet.</p></div>`;
    populateDriveFilter();
  } catch (e) { showToast(e.message, "error"); }
}

function populateDriveFilter() {
  const sel = document.getElementById("applicants-filter-drive");
  if (sel) sel.innerHTML = `<option value="">All Drives</option>` + MY_DRIVES.map((d) => `<option value="${d.id}">${escapeHtml(d.role_title)}</option>`).join("");
}

async function quickUpdateDriveStatus(driveId, status) {
  try {
    await apiRequest(`/company/drives/${driveId}`, { method: "PUT", body: { status } });
    showToast("Drive status updated.", "success");
    loadMyDrives();
  } catch (e) { showToast(e.message, "error"); }
}

function openPostDriveModal() { openModal("post-drive-modal"); }

async function submitPostDrive() {
  const payload = {
    role_title: document.getElementById("pd-role").value,
    job_type: document.getElementById("pd-jobtype").value,
    description: document.getElementById("pd-description").value,
    ctc: document.getElementById("pd-ctc").value,
    location: document.getElementById("pd-location").value,
    min_cgpa: document.getElementById("pd-mincgpa").value,
    max_backlogs: document.getElementById("pd-maxbacklogs").value,
    eligible_branches: document.getElementById("pd-branches").value,
    drive_date: document.getElementById("pd-drivedate").value,
    application_deadline: document.getElementById("pd-deadline").value,
  };
  if (!payload.role_title) { showToast("Please enter a role title.", "error"); return; }
  try {
    await apiRequest("/company/drives", { method: "POST", body: payload });
    showToast("Drive posted successfully.", "success");
    closeModal("post-drive-modal");
    loadMyDrives();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Applicants ---------------- */
async function loadApplicants() {
  try {
    if (!MY_DRIVES.length) await loadMyDrives();
    const data = await apiRequest("/company/applications");
    MY_APPLICANTS = data.applications;
    document.getElementById("applicants-filter-drive").onchange = renderApplicants;
    renderApplicants();
  } catch (e) { showToast(e.message, "error"); }
}

function renderApplicants() {
  const driveFilter = document.getElementById("applicants-filter-drive").value;
  let apps = MY_APPLICANTS;
  if (driveFilter) apps = apps.filter((a) => String(a.drive_id) === driveFilter);
  const tbody = document.getElementById("applicants-tbody");
  tbody.innerHTML = apps.length ? apps.map((a) => `
    <tr>
      <td>${escapeHtml(a.student_name)}</td><td>${escapeHtml(a.branch || "-")}</td><td>${a.cgpa ?? "-"}</td>
      <td>${escapeHtml(a.role_title)}</td><td>${statusBadge(a.status)}</td>
      <td>
        <select onchange="updateApplicantStatus(${a.id}, this.value)" style="background:var(--bg-2); border:1px solid var(--border); color:var(--text-primary); padding:5px 8px; border-radius:8px; font-size:0.76rem;">
          ${["Applied","Shortlisted","Interview","Selected","Rejected"].map((s) => `<option ${a.status===s?"selected":""}>${s}</option>`).join("")}
        </select>
      </td>
    </tr>`).join("") : `<tr><td colspan="6"><div class="empty-state"><p>No applicants found.</p></div></td></tr>`;
}

async function updateApplicantStatus(appId, status) {
  try {
    await apiRequest(`/company/applications/${appId}/status`, { method: "PUT", body: { status } });
    showToast("Applicant status updated.", "success");
    loadApplicants();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Browse Students ---------------- */
async function loadBrowseStudents() {
  try {
    const minCgpa = document.getElementById("students-min-cgpa").value;
    const branch = document.getElementById("students-branch-filter").value;
    let url = "/company/students?";
    if (minCgpa) url += `min_cgpa=${minCgpa}&`;
    if (branch) url += `branch=${encodeURIComponent(branch)}&`;
    const data = await apiRequest(url);
    const grid = document.getElementById("browse-students-grid");
    grid.innerHTML = data.students.length ? data.students.map((s) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(s.name)}</div><div class="ec-sub">${escapeHtml(s.branch)}</div></div>
        ${s.placed ? '<span class="badge badge-green">Placed</span>' : '<span class="badge badge-blue">Available</span>'}</div>
        <div class="ec-meta"><span>${icon("graduation-cap", 14)} CGPA ${s.cgpa}</span><span>${icon("alert-triangle", 14)} ${s.backlogs} backlogs</span></div>
        <p class="text-sm text-secondary">${escapeHtml(s.skills || "No skills listed")}</p>
        ${s.resume_filename ? `<a href="/api/common/resume/${encodeURIComponent(s.resume_filename)}" target="_blank" class="btn btn-outline btn-sm btn-block">View Resume</a>` : `<span class="text-muted text-sm">No resume uploaded</span>`}
      </div>`).join("") : `<div class="empty-state"><p>No students match these filters.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Profile ---------------- */
function populateEditProfileForm() {
  const u = CURRENT_USER;
  const p = u.profile || {};
  renderProfilePicturePreview(u);
  document.getElementById("ep-name").value = u.name || "";
  document.getElementById("ep-phone").value = u.phone || "";
  document.getElementById("ep-company-name").value = p.company_name || "";
  document.getElementById("ep-industry").value = p.industry || "";
  document.getElementById("ep-designation").value = p.hr_designation || "";
  document.getElementById("ep-website").value = p.website || "";
  document.getElementById("ep-address").value = p.address || "";
  document.getElementById("ep-about").value = p.about || "";
}

async function saveProfile() {
  const payload = {
    name: document.getElementById("ep-name").value.trim(),
    phone: document.getElementById("ep-phone").value.trim(),
    company_name: document.getElementById("ep-company-name").value.trim(),
    industry: document.getElementById("ep-industry").value.trim(),
    hr_designation: document.getElementById("ep-designation").value.trim(),
    website: document.getElementById("ep-website").value.trim(),
    address: document.getElementById("ep-address").value.trim(),
    about: document.getElementById("ep-about").value.trim(),
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
  document.getElementById("submit-post-drive-btn").addEventListener("click", submitPostDrive);

  document.querySelectorAll('button[onclick*="edit-profile-modal"]').forEach((btn) => btn.addEventListener("click", populateEditProfileForm));
});
