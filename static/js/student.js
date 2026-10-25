let DRIVES_CACHE = [];
let LATEST_ANALYSIS = null;

function navigateTo(viewName) {
  document.querySelectorAll(".view-section").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".sidebar-link").forEach((el) => el.classList.remove("active"));
  const view = document.getElementById(`view-${viewName}`);
  if (view) view.classList.add("active");
  const link = document.querySelector(`.sidebar-link[data-view="${viewName}"]`);
  if (link) link.classList.add("active");
  closeAllDropdowns();
  loadViewData(viewName);
}
window.navigateTo = navigateTo;

function initSidebarNav() {
  document.querySelectorAll(".sidebar-link[data-view]").forEach((link) => {
    link.addEventListener("click", () => navigateTo(link.dataset.view));
  });
  document.querySelectorAll("[data-view-link]").forEach((el) => {
    el.addEventListener("click", () => navigateTo(el.dataset.viewLink));
  });
}

function loadViewData(view) {
  const loaders = {
    overview: loadOverview,
    companies: loadCompanies,
    drives: loadDrives,
    applications: loadApplications,
    interviews: loadInterviews,
    results: loadResults,
    "resume-creator": loadResumeBuilder,
    aptitude: loadAptitudeTests,
    "skill-assessment": loadSkillAssessments,
    "cdpc-assessments": loadCDPCAssessments,
    "ai-analyzer": loadAnalyzerView,
    "ats-score": loadAtsView,
  };
  if (loaders[view]) loaders[view]();
}

/* ---------------- Overview ---------------- */
async function loadOverview() {
  try {
    const [statsData, appsData, interviewsData] = await Promise.all([
      apiRequest("/student/dashboard-stats"),
      apiRequest("/student/applications"),
      apiRequest("/student/interviews"),
    ]);
    const s = statsData.stats;
    document.getElementById("student-stats-grid").innerHTML = `
      ${statCard("send", s.applications_count, "Applications Sent", "orange")}
      ${statCard("mic", s.interviews_scheduled, "Interviews Scheduled", "blue")}
      ${statCard("trophy", s.offers_received, "Offers Received", "green")}
      ${statCard("clipboard-list", s.open_drives, "Open Drives", "purple")}
    `;

    const apps = appsData.applications.slice(0, 5);
    document.getElementById("overview-applications-list").innerHTML = apps.length
      ? apps.map((a) => `
        <div class="timeline-item">
          <div class="timeline-dot" style="background:${statusColor(a.status)}"></div>
          <div class="flex-col" style="flex:1;">
            <div class="flex justify-between"><b class="text-sm">${escapeHtml(a.role_title)}</b>${statusBadge(a.status)}</div>
            <span class="text-muted text-sm">${escapeHtml(a.company_name)} · ${a.applied_at}</span>
          </div>
        </div>`).join("")
      : `<div class="empty-state"><div class="icon">${icon("send", 32)}</div><p>No applications yet. Browse drives to get started.</p></div>`;

    const interviews = interviewsData.interviews.filter((i) => i.status === "Scheduled").slice(0, 5);
    document.getElementById("overview-interviews-list").innerHTML = interviews.length
      ? interviews.map((i) => `
        <div class="timeline-item">
          <div class="timeline-dot" style="background:var(--accent-blue)"></div>
          <div class="flex-col" style="flex:1;">
            <b class="text-sm">${escapeHtml(i.round_name)}</b>
            <span class="text-muted text-sm">${escapeHtml(i.company_name || "")} · ${escapeHtml(i.scheduled_at || "TBA")} · ${escapeHtml(i.mode)}</span>
          </div>
        </div>`).join("")
      : `<div class="empty-state"><div class="icon">${icon("mic", 32)}</div><p>No interviews scheduled yet.</p></div>`;
  } catch (e) {
    showToast(e.message, "error");
  }
}

function statCard(iconName, value, label, color) {
  const map = { orange: ["var(--accent-orange-soft)", "var(--accent-orange)"], blue: ["var(--accent-blue-soft)", "var(--accent-blue)"], green: ["var(--accent-green-soft)", "var(--accent-green)"], purple: ["var(--accent-purple-soft)", "var(--accent-purple)"] };
  const [bg, fg] = map[color] || map.orange;
  return `<div class="card stat-card"><div class="stat-top"><div class="stat-icon" style="background:${bg}; color:${fg};">${icon(iconName)}</div></div><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div>`;
}

function statusColor(status) {
  return { Applied: "var(--accent-blue)", Shortlisted: "var(--accent-yellow)", Interview: "var(--accent-purple)", Selected: "var(--accent-green)", Rejected: "var(--accent-red)" }[status] || "var(--text-muted)";
}
function statusBadge(status) {
  const cls = { Applied: "badge-blue", Shortlisted: "badge-yellow", Interview: "badge-purple", Selected: "badge-green", Rejected: "badge-red" }[status] || "badge-muted";
  return `<span class="badge ${cls}">${status}</span>`;
}

/* ---------------- Companies ---------------- */
async function loadCompanies() {
  try {
    const data = await apiRequest("/student/companies");
    const grid = document.getElementById("companies-grid");
    grid.innerHTML = data.companies.length ? data.companies.map((c) => `
      <div class="card entity-card">
        <div class="ec-top">
          <div><div class="ec-title">${escapeHtml(c.company_name)}</div><div class="ec-sub">${escapeHtml(c.industry || "")}</div></div>
          <span class="badge badge-green">${c.active_drives} open</span>
        </div>
        <p class="text-sm text-secondary">${escapeHtml((c.about || "No description provided.").slice(0, 120))}</p>
        <div class="ec-footer"><span class="text-muted text-sm">${c.website ? escapeHtml(c.website) : ""}</span></div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("building-2", 32)}</div><p>No companies onboarded yet.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Drives ---------------- */
async function loadDrives() {
  try {
    const data = await apiRequest("/student/drives");
    DRIVES_CACHE = data.drives;
    renderDrives();
    document.getElementById("drives-filter-status").onchange = renderDrives;
    document.getElementById("drives-filter-eligible").onchange = renderDrives;
  } catch (e) { showToast(e.message, "error"); }
}

function renderDrives() {
  const statusFilter = document.getElementById("drives-filter-status").value;
  const eligibleFilter = document.getElementById("drives-filter-eligible").value;
  let drives = DRIVES_CACHE;
  if (statusFilter) drives = drives.filter((d) => d.status === statusFilter);
  if (eligibleFilter === "true") drives = drives.filter((d) => d.eligible);

  const grid = document.getElementById("drives-grid");
  grid.innerHTML = drives.length ? drives.map((d) => `
    <div class="card entity-card">
      <div class="ec-top">
        <div><div class="ec-title">${escapeHtml(d.role_title)}</div><div class="ec-sub">${escapeHtml(d.company_name)}</div></div>
        <span class="badge ${d.status === "Closed" ? "badge-red" : d.status === "Ongoing" ? "badge-green" : "badge-blue"}">${d.status}</span>
      </div>
      <div class="ec-meta">
        <span>${icon("dollar-sign", 14)} ${escapeHtml(d.ctc || "Not disclosed")}</span>
        <span>${icon("map-pin", 14)} ${escapeHtml(d.location || "N/A")}</span>
        <span>${icon("graduation-cap", 14)} Min CGPA ${d.min_cgpa}</span>
      </div>
      <div class="ec-meta">${d.eligible ? `<span class="badge badge-green">${icon("check", 12)} Eligible</span>` : `<span class="badge badge-red">${icon("x", 12)} Not Eligible</span>`} ${d.already_applied ? '<span class="badge badge-purple">Applied</span>' : ""}</div>
      <div class="ec-footer">
        <span class="text-muted text-sm">Deadline: ${escapeHtml(d.application_deadline || "N/A")}</span>
        <button class="btn btn-secondary btn-sm" onclick="openDriveDetail(${d.id})">View Details</button>
      </div>
    </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("clipboard-list", 32)}</div><p>No drives match your filters.</p></div>`;
}

function openDriveDetail(driveId) {
  const d = DRIVES_CACHE.find((x) => x.id === driveId);
  if (!d) return;
  document.getElementById("dd-title").textContent = d.role_title;
  document.getElementById("dd-body").innerHTML = `
    <div class="flex gap-8 mb-16" style="flex-wrap:wrap;">
      <span class="badge badge-blue">${escapeHtml(d.company_name)}</span>
      <span class="badge ${d.status === "Closed" ? "badge-red" : "badge-green"}">${d.status}</span>
      <span class="badge badge-purple">${escapeHtml(d.job_type)}</span>
    </div>
    <p class="text-secondary text-sm mb-16">${escapeHtml(d.description || "No description provided.")}</p>
    <div class="grid-3 mb-16">
      <div><div class="text-muted text-sm">CTC</div><b>${escapeHtml(d.ctc || "N/A")}</b></div>
      <div><div class="text-muted text-sm">Location</div><b>${escapeHtml(d.location || "N/A")}</b></div>
      <div><div class="text-muted text-sm">Drive Date</div><b>${escapeHtml(d.drive_date || "TBA")}</b></div>
    </div>
    <div class="grid-3 mb-16">
      <div><div class="text-muted text-sm">Min CGPA</div><b>${d.min_cgpa}</b></div>
      <div><div class="text-muted text-sm">Max Backlogs</div><b>${d.max_backlogs}</b></div>
      <div><div class="text-muted text-sm">Eligible Branches</div><b>${escapeHtml(d.eligible_branches)}</b></div>
    </div>
    ${d.eligible ? "" : `<div class="badge badge-red">You do not meet the eligibility criteria for this drive.</div>`}
  `;
  const applyBtn = document.getElementById("dd-apply-btn");
  applyBtn.disabled = !d.eligible || d.already_applied || d.status === "Closed";
  applyBtn.textContent = d.already_applied ? "Already Applied" : "Apply Now";
  applyBtn.onclick = () => submitApplication(d.id);
  openModal("drive-detail-modal");
}

async function submitApplication(driveId) {
  try {
    await apiRequest(`/student/apply/${driveId}`, { method: "POST" });
    showToast("Application submitted successfully!", "success");
    closeModal("drive-detail-modal");
    loadDrives();
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Applications ---------------- */
async function loadApplications() {
  try {
    const data = await apiRequest("/student/applications");
    const tbody = document.getElementById("applications-tbody");
    tbody.innerHTML = data.applications.length ? data.applications.map((a) => `
      <tr><td>${escapeHtml(a.role_title)}</td><td>${escapeHtml(a.company_name)}</td><td>${a.applied_at}</td><td>${statusBadge(a.status)}</td></tr>
    `).join("") : `<tr><td colspan="4"><div class="empty-state"><div class="icon">${icon("send", 32)}</div><p>No applications yet.</p></div></td></tr>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Interviews ---------------- */
async function loadInterviews() {
  try {
    const data = await apiRequest("/student/interviews");
    const list = document.getElementById("interviews-list");
    list.innerHTML = data.interviews.length ? data.interviews.map((i) => `
      <div class="timeline-item">
        <div class="timeline-dot" style="background:${i.status === "Completed" ? "var(--accent-green)" : "var(--accent-blue)"}"></div>
        <div class="flex-col" style="flex:1;">
          <div class="flex justify-between"><b>${escapeHtml(i.round_name)}</b><span class="badge ${i.status === "Completed" ? "badge-green" : "badge-blue"}">${i.status}</span></div>
          <span class="text-muted text-sm">${escapeHtml(i.company_name || "")} · ${escapeHtml(i.role_title || "")}</span>
          <span class="text-muted text-sm">${icon("clock", 13)} ${escapeHtml(i.scheduled_at || "TBA")} · ${escapeHtml(i.mode)} ${i.venue_or_link ? "· " + escapeHtml(i.venue_or_link) : ""}</span>
          ${i.feedback ? `<span class="text-sm mt-8">Feedback: ${escapeHtml(i.feedback)}</span>` : ""}
        </div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("mic", 32)}</div><p>No interviews scheduled yet.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Results ---------------- */
async function loadResults() {
  try {
    const data = await apiRequest("/student/results");
    const grid = document.getElementById("results-grid");
    grid.innerHTML = data.results.length ? data.results.map((r) => `
      <div class="card entity-card">
        <div class="ec-top">
          <div><div class="ec-title">${escapeHtml(r.role_title)}</div><div class="ec-sub">${escapeHtml(r.company_name)}</div></div>
          <span class="badge ${r.outcome === "Selected" ? "badge-green" : r.outcome === "Waitlisted" ? "badge-yellow" : "badge-red"}">${r.outcome}</span>
        </div>
        ${r.package_offered ? `<div class="text-sm">${icon("dollar-sign", 14)} Package: <b>${escapeHtml(r.package_offered)}</b></div>` : ""}
        ${r.remarks ? `<p class="text-sm text-secondary">${escapeHtml(r.remarks)}</p>` : ""}
        <div class="text-muted text-sm">Published: ${r.published_at}</div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("trophy", 32)}</div><p>No results published yet.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- Aptitude Tests ---------------- */
async function loadAptitudeTests() {
  try {
    const [testsData, historyData] = await Promise.all([
      apiRequest("/student/aptitude-tests?type=aptitude"),
      apiRequest("/student/aptitude-results?type=aptitude"),
    ]);
    const grid = document.getElementById("aptitude-grid");
    grid.innerHTML = testsData.tests.map((t) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(t.title)}</div><div class="ec-sub">${escapeHtml(t.category)}</div></div><span class="badge badge-blue">${t.total_questions} Qs</span></div>
        <div class="ec-meta"><span>${icon("clock", 14)} ${t.duration_minutes} min</span>${t.last_score !== undefined ? `<span>${icon("check-circle", 14)} Last: ${t.last_score}/${t.last_total}</span>` : ""}</div>
        <div class="flex gap-8">
          <button class="btn btn-primary btn-block" onclick="startAptitudeTest(${t.id}, 'aptitude')">Start Test</button>
          ${t.last_has_review ? `<button class="btn btn-outline btn-sm" onclick="openAssessmentReview(${t.last_result_id})">Review</button>` : ""}
        </div>
      </div>`).join("");

    const historyTbody = document.getElementById("aptitude-history-tbody");
    historyTbody.innerHTML = historyData.results.length
      ? historyData.results.map((r) => `<tr>
          <td>${escapeHtml(r.test_title)}</td>
          <td>${r.score}/${r.total}</td>
          <td>${r.taken_at}</td>
          <td>${r.has_review ? `<button class="btn btn-outline btn-sm" onclick="openAssessmentReview(${r.id})">Review</button>` : "—"}</td>
        </tr>`).join("")
      : `<tr><td colspan="4" class="text-muted" style="padding:16px;">No attempts yet.</td></tr>`;
  } catch (e) { showToast(e.message, "error"); }
}

const SKILL_LEVEL_BADGE = { Beginner: "badge-muted", Intermediate: "badge-blue", Advanced: "badge-green" };
let ACTIVE_TEST = null;
let ACTIVE_TEST_KIND = "aptitude";
let APT_TIMER = null;
let APT_SUBMITTING = false;

function stopAptTimer() {
  if (APT_TIMER) {
    clearInterval(APT_TIMER);
    APT_TIMER = null;
  }
}

function startAptTimer(minutes, testId) {
  stopAptTimer();
  let remaining = Math.max(1, (minutes || 10) * 60);
  const el = document.getElementById("apt-timer");
  const tick = () => {
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    if (el) {
      el.textContent = `${m}:${String(s).padStart(2, "0")}`;
      el.classList.toggle("badge-red", remaining <= 30);
    }
    if (remaining <= 0) {
      stopAptTimer();
      submitAptitudeTest(testId, { auto: true });
      return;
    }
    remaining -= 1;
  };
  tick();
  APT_TIMER = setInterval(tick, 1000);
}

async function startAptitudeTest(testId, kind = "aptitude") {
  ACTIVE_TEST_KIND = kind;
  try {
    const data = await apiRequest(`/student/aptitude-tests/${testId}`);
    ACTIVE_TEST = data.test;
    document.getElementById("apt-title").textContent = ACTIVE_TEST.title;
    document.getElementById("apt-body").innerHTML = ACTIVE_TEST.questions.map((q, idx) => `
      <div class="mb-16 apt-question">
        <b class="text-sm">${idx + 1}. ${escapeHtml(q.question)}</b>
        <div class="mt-8 flex-col gap-8">
          ${q.options.map((opt, oi) => `
            <label class="flex items-center gap-8 text-sm apt-option" style="cursor:pointer;">
              <input type="radio" name="apt-q-${idx}" value="${oi}" /> ${escapeHtml(opt)}
            </label>`).join("")}
        </div>
      </div>`).join("");
    document.getElementById("apt-footer").innerHTML = `
      <button class="btn btn-outline" onclick="stopAptTimer(); closeModal('aptitude-test-modal')">Cancel</button>
      <button class="btn btn-primary" id="apt-submit-btn">Submit Test</button>`;
    document.getElementById("apt-submit-btn").onclick = () => submitAptitudeTest(testId);
    startAptTimer(ACTIVE_TEST.duration_minutes, testId);
    openModal("aptitude-test-modal");
  } catch (e) { showToast(e.message, "error"); }
}

async function submitAptitudeTest(testId, opts = {}) {
  if (APT_SUBMITTING) return;
  const answers = {};
  let unanswered = 0;
  ACTIVE_TEST.questions.forEach((q, idx) => {
    const selected = document.querySelector(`input[name="apt-q-${idx}"]:checked`);
    if (selected) answers[idx] = selected.value;
    else unanswered += 1;
  });
  if (!opts.auto && unanswered > 0) {
    const ok = window.confirm(`You left ${unanswered} question(s) unanswered. Submit anyway?`);
    if (!ok) return;
  }
  APT_SUBMITTING = true;
  stopAptTimer();
  try {
    const res = await apiRequest(`/student/aptitude-tests/${testId}/submit`, { method: "POST", body: { answers } });
    closeModal("aptitude-test-modal");
    const levelMsg = res.level ? ` — Level: ${res.level}` : "";
    showToast(`${opts.auto ? "Time up. " : ""}Submitted! Score: ${res.score}/${res.total}${levelMsg}`, "success");
    showAssessmentReview({
      test_title: res.test_title || ACTIVE_TEST.title,
      score: res.score,
      total: res.total,
      percent: res.percent,
      level: res.level,
      review: res.review,
    });
    if (ACTIVE_TEST_KIND === "skill") loadSkillAssessments();
    else if (ACTIVE_TEST_KIND === "cdpc") loadCDPCAssessments();
    else loadAptitudeTests();
  } catch (e) { showToast(e.message, "error"); }
  finally { APT_SUBMITTING = false; }
}

function showAssessmentReview(payload) {
  document.getElementById("review-title").textContent = `Review — ${payload.test_title || "Assessment"}`;
  const pct = payload.percent ?? (payload.total ? Math.round((payload.score / payload.total) * 100) : 0);
  document.getElementById("review-summary").innerHTML = `
    <div class="flex items-center gap-12" style="flex-wrap:wrap;">
      <span class="badge badge-orange" style="font-size:0.95rem;padding:8px 14px;">Score: ${payload.score}/${payload.total} (${pct}%)</span>
      ${payload.level ? `<span class="badge ${SKILL_LEVEL_BADGE[payload.level] || "badge-muted"}">${escapeHtml(payload.level)}</span>` : ""}
      <span class="text-muted text-sm">${(payload.review || []).filter((r) => r.is_correct).length} correct · ${(payload.review || []).filter((r) => !r.is_correct).length} incorrect / skipped</span>
    </div>`;

  document.getElementById("review-body").innerHTML = (payload.review || []).map((r, idx) => {
    const statusClass = r.is_correct ? "review-correct" : "review-wrong";
    const statusLabel = r.is_correct ? "Correct" : (r.selected_index == null ? "Not answered" : "Incorrect");
    const optionsHtml = (r.options || []).map((opt, oi) => {
      let cls = "review-opt";
      if (oi === r.correct_index) cls += " is-correct";
      if (r.selected_index != null && oi === r.selected_index && oi !== r.correct_index) cls += " is-selected-wrong";
      if (r.selected_index != null && oi === r.selected_index && oi === r.correct_index) cls += " is-selected-correct";
      return `<div class="${cls}">${escapeHtml(opt)}</div>`;
    }).join("");
    return `
      <div class="review-q ${statusClass}">
        <div class="flex justify-between gap-12 mb-8">
          <b class="text-sm">${idx + 1}. ${escapeHtml(r.question)}</b>
          <span class="badge ${r.is_correct ? "badge-green" : "badge-red"}">${statusLabel}</span>
        </div>
        <div class="review-opts">${optionsHtml}</div>
        ${r.explanation ? `<p class="review-explain text-sm mt-8">${escapeHtml(r.explanation)}</p>` : ""}
        ${r.selected_option ? `<p class="text-sm mt-8 text-secondary">Your answer: <b>${escapeHtml(r.selected_option)}</b></p>` : `<p class="text-sm mt-8 text-secondary">You did not select an option.</p>`}
        ${!r.is_correct && r.correct_option ? `<p class="text-sm mt-8 text-secondary">Correct answer: <b>${escapeHtml(r.correct_option)}</b></p>` : ""}
      </div>`;
  }).join("") || `<p class="text-muted">No review data available.</p>`;

  openModal("assessment-review-modal");
}

async function openAssessmentReview(resultId) {
  try {
    const data = await apiRequest(`/student/aptitude-results/${resultId}/review`);
    showAssessmentReview({
      test_title: data.test_title,
      score: data.result.score,
      total: data.result.total,
      percent: data.result.percent,
      level: data.result.level,
      review: data.review,
    });
  } catch (e) { showToast(e.message, "error"); }
}
window.startAptitudeTest = startAptitudeTest;
window.stopAptTimer = stopAptTimer;

/* ---------------- Skill Assessment ---------------- */

async function loadSkillAssessments() {
  try {
    const [testsData, historyData] = await Promise.all([
      apiRequest("/student/aptitude-tests?type=skill"),
      apiRequest("/student/aptitude-results?type=skill"),
    ]);
    const branch = testsData.student_branch || CURRENT_USER?.profile?.branch || "your branch";
    const badge = document.getElementById("skill-branch-badge");
    const lead = document.getElementById("skill-branch-lead");
    if (badge) badge.textContent = branch;
    if (lead) lead.textContent = `Technical assessments curated for ${branch}. Soft-skill modules are available to every branch.`;

    const grid = document.getElementById("skill-grid");
    grid.innerHTML = testsData.tests.length ? testsData.tests.map((t) => `
      <div class="card entity-card">
        <div class="ec-top">
          <div>
            <div class="ec-title">${escapeHtml(t.title)}</div>
            <div class="ec-sub">${escapeHtml(t.category)}${t.branches && t.branches !== "All Branches" ? " · Branch-specific" : " · All branches"}</div>
          </div>
          <span class="badge badge-purple">${t.total_questions} Qs</span>
        </div>
        <div class="ec-meta"><span>${icon("clock", 14)} ${t.duration_minutes} min</span></div>
        ${t.last_score !== undefined ? `<div class="ec-meta"><span class="badge ${SKILL_LEVEL_BADGE[t.last_level] || "badge-muted"}">Latest: ${t.last_score}/${t.last_total} · ${t.last_level || "—"}</span></div>` : ""}
        <div class="flex gap-8">
          <button class="btn btn-primary btn-block" onclick="startAptitudeTest(${t.id}, 'skill')">Start Assessment</button>
          ${t.last_has_review ? `<button class="btn btn-outline btn-sm" onclick="openAssessmentReview(${t.last_result_id})">Review</button>` : ""}
        </div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("target", 32)}</div><p>No skill assessments available for your branch yet.</p></div>`;

    const historyTbody = document.getElementById("skill-history-tbody");
    historyTbody.innerHTML = historyData.results.length
      ? historyData.results.map((r) => `<tr>
          <td>${escapeHtml(r.test_title)}</td>
          <td>${r.score}/${r.total}</td>
          <td><span class="badge ${SKILL_LEVEL_BADGE[r.level] || "badge-muted"}">${r.level || "—"}</span></td>
          <td>${r.taken_at}</td>
          <td>${r.has_review ? `<button class="btn btn-outline btn-sm" onclick="openAssessmentReview(${r.id})">Review</button>` : "—"}</td>
        </tr>`).join("")
      : `<tr><td colspan="5" class="text-muted" style="padding:16px;">No attempts yet.</td></tr>`;
  } catch (e) { showToast(e.message, "error"); }
}


async function loadCDPCAssessments() {
  try {
    const data = await apiRequest("/student/aptitude-tests?type=cdpc");
    const grid = document.getElementById("cdpc-assessment-grid");
    grid.innerHTML = data.tests.length ? data.tests.map((t) => `
      <div class="card entity-card">
        <div class="ec-top"><div><div class="ec-title">${escapeHtml(t.title)}</div><div class="ec-sub">${escapeHtml(t.category || "General")}</div></div><span class="badge badge-blue">${t.total_questions} Qs</span></div>
        <div class="ec-meta"><span>${icon("clock", 14)} ${t.duration_minutes} min</span>${t.last_score !== undefined ? `<span>${icon("check-circle", 14)} Latest: ${t.last_score}/${t.last_total}</span>` : ""}</div>
        <div class="flex gap-8"><button class="btn btn-primary btn-block" onclick="startAptitudeTest(${t.id}, 'cdpc')">${t.last_score !== undefined ? "Retake Assessment" : "Start Assessment"}</button>
        ${t.last_has_review ? `<button class="btn btn-outline btn-sm" onclick="openAssessmentReview(${t.last_result_id})">Review</button>` : ""}</div>
      </div>`).join("") : `<div class="empty-state"><div class="icon">${icon("clipboard-check", 32)}</div><p>No CDPC assessments have been assigned to you yet.</p></div>`;
  } catch (e) { showToast(e.message, "error"); }
}

/* ---------------- AI Resume Analyzer + ATS ---------------- */
function loadAnalyzerView() {
  const profile = CURRENT_USER?.profile;
  document.getElementById("current-resume-label").textContent = profile?.resume_filename
    ? `Current resume: ${profile.resume_filename}`
    : "No resume uploaded yet.";
  if (LATEST_ANALYSIS) renderAnalysis(LATEST_ANALYSIS);
}

function loadAtsView() {
  if (LATEST_ANALYSIS) {
    renderAtsScore(LATEST_ANALYSIS);
  } else if (CURRENT_USER?.profile?.ats_score) {
    animateAtsRing(CURRENT_USER.profile.ats_score);
  }
}

async function handleResumeUpload() {
  const fileInput = document.getElementById("resume-upload-input");
  if (!fileInput.files.length) {
    showToast("Please choose a PDF file first.", "error");
    return;
  }
  const formData = new FormData();
  formData.append("resume", fileInput.files[0]);
  const btn = document.getElementById("upload-resume-btn");
  btn.disabled = true;
  btn.textContent = "Analyzing...";
  try {
    const data = await apiUpload("/student/resume/upload", formData);
    LATEST_ANALYSIS = data.analysis;
    document.getElementById("current-resume-label").textContent = `Current resume: ${data.filename}`;
    renderAnalysis(data.analysis);
    renderAtsScore(data.analysis);
    showToast("Resume analyzed successfully!", "success");
  } catch (e) {
    showToast(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Upload & Analyze";
  }
}

async function handleReanalyze() {
  const jd = document.getElementById("jd-input").value.trim();
  try {
    const data = await apiRequest("/student/resume/analyze", { method: "POST", body: { job_description: jd } });
    LATEST_ANALYSIS = data.analysis;
    renderAnalysis(data.analysis);
    renderAtsScore(data.analysis);
    showToast("Re-analysis complete.", "success");
  } catch (e) { showToast(e.message, "error"); }
}

function renderAnalysis(analysis) {
  const list = document.getElementById("ai-suggestions-list");
  list.innerHTML = `
    <div class="flex items-center gap-12 mb-16">
      <div class="badge badge-orange" style="font-size:0.9rem; padding:8px 14px;">Score: ${analysis.ats_score}/100</div>
      <span class="text-muted text-sm">${analysis.word_count} words analyzed</span>
    </div>
    ${analysis.suggestions.map((s) => `
      <div class="timeline-item">
        <div class="timeline-dot" style="background:var(--accent-orange)"></div>
        <span class="text-sm">${escapeHtml(s)}</span>
      </div>`).join("")}
  `;
}

function renderAtsScore(analysis) {
  animateAtsRing(analysis.ats_score);
  const checklist = document.getElementById("ats-checklist");
  const sectionLabels = { contact: "Contact Info", education: "Education", skills: "Skills", experience: "Experience", projects: "Projects", achievements: "Achievements" };
  checklist.innerHTML = Object.entries(analysis.sections_found).map(([key, found]) => `
    <div class="flex items-center gap-12 mb-8">
      <span style="color:${found ? "var(--accent-green)" : "var(--accent-red)"};">${found ? icon("check", 16) : icon("x", 16)}</span>
      <span class="text-sm">${sectionLabels[key] || key}</span>
    </div>`).join("");
  const keywords = document.getElementById("ats-keywords");
  keywords.innerHTML = analysis.matched_keywords.length
    ? analysis.matched_keywords.map((k) => `<span class="badge badge-green">${escapeHtml(k)}</span>`).join("")
    : `<span class="text-muted text-sm">No matched keywords yet.</span>`;
}

function animateAtsRing(score) {
  const circle = document.getElementById("ats-ring");
  const circumference = 352;
  const offset = circumference - (score / 100) * circumference;
  circle.style.strokeDashoffset = offset;
  document.getElementById("ats-score-num").textContent = score;
}

/* ---------------- Profile edit ---------------- */
function populateEditProfileForm() {
  const u = CURRENT_USER;
  const p = u.profile || {};
  renderProfilePicturePreview(u);
  document.getElementById("ep-name").value = u.name || "";
  document.getElementById("ep-phone").value = u.phone || "";
  document.getElementById("ep-branch").value = p.branch || "Computer Science & Engineering";
  document.getElementById("ep-year").value = p.current_year || "";
  document.getElementById("ep-cgpa").value = p.cgpa || "";
  document.getElementById("ep-backlogs").value = p.backlogs || 0;
  document.getElementById("ep-tenth").value = p.tenth_percent || "";
  document.getElementById("ep-inter").value = p.inter_percent || "";
  document.getElementById("ep-address").value = p.address || "";
  document.getElementById("ep-gender").value = p.gender || "Male";
  document.getElementById("ep-dob").value = p.dob || "";
  document.getElementById("ep-skills").value = p.skills || "";
  document.getElementById("ep-linkedin").value = p.linkedin || "";
  document.getElementById("ep-github").value = p.github || "";
}

async function saveProfile() {
  const payload = {
    name: document.getElementById("ep-name").value.trim(),
    phone: document.getElementById("ep-phone").value.trim(),
    branch: document.getElementById("ep-branch").value,
    current_year: document.getElementById("ep-year").value,
    cgpa: document.getElementById("ep-cgpa").value,
    backlogs: document.getElementById("ep-backlogs").value,
    tenth_percent: document.getElementById("ep-tenth").value,
    inter_percent: document.getElementById("ep-inter").value,
    address: document.getElementById("ep-address").value,
    gender: document.getElementById("ep-gender").value,
    dob: document.getElementById("ep-dob").value,
    skills: document.getElementById("ep-skills").value,
    linkedin: document.getElementById("ep-linkedin").value,
    github: document.getElementById("ep-github").value,
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
    document.getElementById("cp-old").value = "";
    document.getElementById("cp-new").value = "";
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
  initResumeBuilder();

  document.getElementById("upload-resume-btn").addEventListener("click", handleResumeUpload);
  document.getElementById("reanalyze-btn").addEventListener("click", handleReanalyze);
  document.getElementById("save-profile-btn").addEventListener("click", saveProfile);
  document.getElementById("save-password-btn").addEventListener("click", savePassword);

  document.querySelector('[onclick="openModal(\'edit-profile-modal\')"]');
  document.querySelectorAll('button[onclick*="edit-profile-modal"]').forEach((btn) => {
    btn.addEventListener("click", populateEditProfileForm);
  });
});