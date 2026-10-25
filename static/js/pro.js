/* Pro feature hubs: Career Toolkit (student), Hiring Studio (company), Insights Hub (CDPC). */
(function () {
  const esc = (v) => (window.escapeHtml ? escapeHtml(v) : String(v ?? ""));
  const api = (p, o) => window.apiRequest(p, o);
  const toast = (m, t = "success") => window.showToast && showToast(m, t);
  const spin = '<div class="loading-row"><div class="spinner"></div></div>';
  const $ = (id) => document.getElementById(id);

  function addNav(label, view, icon) {
    const sections = document.querySelectorAll(".sidebar-section");
    const section = sections[0];
    if (!section || document.querySelector(`.sidebar-link[data-view="${view}"]`)) return;
    const b = document.createElement("button");
    b.className = "sidebar-link"; b.dataset.view = view;
    b.innerHTML = `<span class="ic" data-icon="${icon}"></span> ${label}`;
    b.addEventListener("click", () => window.navigateTo && window.navigateTo(view));
    section.appendChild(b);
    window.renderStaticIcons && renderStaticIcons();
  }
  function addSection(id, html) {
    if ($(`view-${id}`)) return $(`view-${id}`);
    const main = document.querySelector("main.main-content"); if (!main) return null;
    const s = document.createElement("section"); s.className = "view-section"; s.id = `view-${id}`; s.innerHTML = html; main.appendChild(s); return s;
  }
  function tabs(root, defs, onOpen) {
    const bar = root.querySelector(".pro-tabs");
    bar.innerHTML = defs.map((d, i) => `<button class="pro-tab${i ? "" : " active"}" data-tab="${d[0]}" data-no-loader>${d[1]}</button>`).join("");
    const open = (key) => {
      bar.querySelectorAll(".pro-tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === key));
      root.querySelectorAll(".pro-pane").forEach((p) => p.classList.toggle("active", p.dataset.pane === key));
      onOpen[key] && onOpen[key]();
    };
    bar.addEventListener("click", (e) => { const b = e.target.closest(".pro-tab"); if (b) open(b.dataset.tab); });
    open(defs[0][0]);
  }
  const bar = (pct) => `<div class="pro-meter"><span style="width:${Math.max(0, Math.min(100, pct))}%"></span></div>`;
  const fail = (e) => toast(e.message || "Something went wrong", "error");

  /* ============================== STUDENT ============================== */
  function student() {
    addNav("Career Toolkit", "toolkit", "briefcase");
    const root = addSection("toolkit", `
      <div class="page-header"><div><h1>Career Toolkit</h1><p>Profile strength, calendar, skill-gap analysis and mock interviews in one place.</p></div></div>
      <div class="pro-tabs"></div>
      <div class="pro-pane" data-pane="strength"><div class="card card-pad" id="tk-strength">${spin}</div></div>
      <div class="pro-pane" data-pane="schedule"><div class="card card-pad"><div class="flex justify-between items-center mb-16"><h3>Upcoming schedule</h3><a class="btn btn-outline btn-sm" href="/api/pro/student/schedule.ics" download>Add to calendar (.ics)</a></div><div id="tk-schedule">${spin}</div></div></div>
      <div class="pro-pane" data-pane="gap"><div class="grid-2"><div class="card card-pad"><h3 class="mb-16">Drive match &amp; missing skills</h3><div id="tk-gap">${spin}</div></div><div class="card card-pad"><h3 class="mb-16">Your learning plan</h3><div id="tk-plan"></div></div></div></div>
      <div class="pro-pane" data-pane="mock"><div class="grid-2"><div class="card card-pad"><div class="pro-toolbar"><select id="mk-track"></select><button class="btn btn-primary btn-sm" id="mk-start">Start session</button></div><div id="mk-stage"><div class="empty-state">Pick a track and start a 6-question practice round. Answer out loud, then rate yourself honestly.</div></div></div><div class="card card-pad"><h3 class="mb-16">History</h3><div id="mk-history"></div></div></div></div>`);
    if (!root) return;
    let mockTracks = false;

    async function strength() {
      const d = await api("/pro/student/profile-strength");
      $("tk-strength").innerHTML = `<div class="flex gap-20 items-center" style="flex-wrap:wrap"><div class="pro-ring" style="--p:${d.score}"><b>${d.score}%</b></div><div style="flex:1;min-width:220px"><h3>Profile strength</h3><p class="text-muted text-sm mb-8">Recruiters shortlist complete profiles first. Finish the items below.</p>${bar(d.score)}</div></div><div class="mt-16">${d.items.map((i) => `<div class="pro-check"><span class="pro-dot ${i.done ? "ok" : ""}">${i.done ? "✓" : ""}</span><div style="flex:1">${esc(i.label)}${i.done ? "" : `<small>${esc(i.tip)}</small>`}</div><span class="badge ${i.done ? "badge-green" : "badge-muted"}">+${i.weight}</span></div>`).join("")}</div>`;
    }
    async function schedule() {
      const d = await api("/pro/student/schedule");
      $("tk-schedule").innerHTML = d.events.length ? `<div class="pro-timeline">${d.events.map((e) => `<div class="pro-ev ${e.type} ${e.past ? "past" : ""}"><b>${esc(e.title)}</b><div class="when">${esc(e.when)} · ${esc(e.where || "")}</div><span class="badge ${e.type === "deadline" ? "badge-red" : e.type === "interview" ? "badge-orange" : "badge-blue"}">${esc(e.type)}</span></div>`).join("")}</div>` : `<div class="empty-state">Nothing scheduled yet. Apply to drives to see interviews and deadlines here.</div>`;
    }
    async function gap() {
      const d = await api("/pro/student/skill-gap");
      $("tk-gap").innerHTML = d.drives.length ? d.drives.slice(0, 8).map((x) => `<div class="advanced-row" style="align-items:flex-start"><div><b>${esc(x.drive.role_title)}</b> <span class="text-muted text-sm">${esc(x.drive.company_name || "")}</span>${bar(x.match_pct)}<div class="mt-8">${x.have.map((s) => `<span class="pro-chip have">${esc(s)}</span>`).join("")}${x.missing.map((s) => `<span class="pro-chip miss">${esc(s)}</span>`).join("")}${x.required.length ? "" : '<span class="text-muted text-sm">No specific skills listed</span>'}</div></div><div class="match-score">${x.match_pct}%<small>skills</small></div></div>`).join("") : `<div class="empty-state">No open drives right now.</div>`;
      $("tk-plan").innerHTML = d.learning_plan.length ? d.learning_plan.map((p) => `<div class="advanced-row"><div><b style="text-transform:capitalize">${esc(p.skill)}</b><div class="text-sm text-muted">${esc(p.action)}</div></div><span class="badge badge-orange">${p.demand} drive${p.demand > 1 ? "s" : ""}</span></div>`).join("") : `<div class="empty-state">You already cover the skills requested by open drives. 🎉</div>`;
    }
    async function history() {
      const d = await api("/pro/student/mock/sessions");
      $("mk-history").innerHTML = d.sessions.length ? d.sessions.map((s) => `<div class="advanced-row"><div><b>${esc(s.track)}</b><div class="text-sm text-muted">${esc(s.created_at)} · ${s.questions} questions${s.weak_topics ? " · weak: " + esc(s.weak_topics) : ""}</div></div><span class="badge ${s.avg_rating >= 4 ? "badge-green" : s.avg_rating >= 3 ? "badge-orange" : "badge-red"}">${s.avg_rating}/5</span></div>`).join("") : `<div class="empty-state">No sessions yet.</div>`;
    }
    async function mockInit() {
      if (!mockTracks) {
        const d = await api("/pro/student/mock/questions?track=HR");
        $("mk-track").innerHTML = d.tracks.map((t) => `<option>${esc(t)}</option>`).join(""); mockTracks = true;
      }
      history().catch(fail);
    }
    $("mk-start").onclick = async () => {
      const d = await api(`/pro/student/mock/questions?track=${encodeURIComponent($("mk-track").value)}`);
      let i = 0; const answers = []; const t0 = Date.now();
      const render = () => {
        if (i >= d.questions.length) {
          const dur = Math.round((Date.now() - t0) / 1000);
          $("mk-stage").innerHTML = spin;
          api("/pro/student/mock/sessions", { method: "POST", body: { track: d.track, answers, duration_sec: dur } }).then((r) => {
            $("mk-stage").innerHTML = `<div class="empty-state"><h3>Session complete 🎯</h3><p>Average self-rating <b>${r.session.avg_rating}/5</b>${r.session.weak_topics ? `<br>Revise: ${esc(r.session.weak_topics)}` : ""}</p></div>`;
            history(); toast("Mock interview saved.");
          }).catch(fail);
          return;
        }
        const q = d.questions[i];
        $("mk-stage").innerHTML = `<div class="pro-qa"><span class="badge badge-blue">${esc(q.topic)}</span> <span class="text-muted text-sm">Question ${i + 1} of ${d.questions.length}</span><h3>${esc(q.q)}</h3><p class="text-muted text-sm">Answer out loud (aim for 60-90s), then rate how well you answered:</p><div class="pro-stars">${[1, 2, 3, 4, 5].map((n) => `<button class="btn btn-outline btn-sm" data-r="${n}" data-no-loader>${n}</button>`).join("")}</div><div class="text-sm text-muted">1 = blank · 3 = okay · 5 = confident &amp; complete</div></div>`;
        $("mk-stage").querySelectorAll("[data-r]").forEach((b) => (b.onclick = () => { answers.push({ rating: +b.dataset.r, topic: q.topic }); i++; render(); }));
      };
      render();
    };
    tabs(root, [["strength", "Profile Strength"], ["schedule", "Schedule"], ["gap", "Skill Gap"], ["mock", "Mock Interview"]],
      { strength: () => strength().catch(fail), schedule: () => schedule().catch(fail), gap: () => gap().catch(fail), mock: () => mockInit().catch(fail) });
  }

  /* ============================== COMPANY ============================== */
  function company() {
    addNav("Hiring Studio", "studio", "bar-chart");
    const root = addSection("studio", `
      <div class="page-header"><div><h1>Hiring Studio</h1><p>Pipeline analytics, bulk actions, candidate comparison and messaging.</p></div></div>
      <div class="pro-tabs"></div>
      <div class="pro-pane" data-pane="pipeline"><div id="hs-pipeline">${spin}</div></div>
      <div class="pro-pane" data-pane="bulk"><div class="card card-pad">
        <div class="pro-toolbar"><select id="hs-drive"><option value="">All drives</option></select>
          <select id="hs-status"><option>Shortlisted</option><option>Interview</option><option>Selected</option><option>Rejected</option><option>Applied</option></select>
          <button class="btn btn-primary btn-sm" id="hs-apply">Apply to selected</button>
          <button class="btn btn-outline btn-sm" id="hs-compare">Compare selected</button>
          <button class="btn btn-outline btn-sm" id="hs-msg">Message selected</button></div>
        <div class="table-wrap"><table class="data-table"><thead><tr><th><input type="checkbox" class="pro-row-check" id="hs-all"></th><th>Student</th><th>Branch</th><th>CGPA</th><th>Role</th><th>Status</th></tr></thead><tbody id="hs-tbody"></tbody></table></div>
        <div class="pro-note">Tick applicants, then move them to a new stage in one click. Students are notified automatically.</div>
        <div id="hs-compare-out" class="pro-compare mt-16"></div>
        <div id="hs-msg-box" style="display:none" class="mt-16"><div class="field"><label>Message</label><textarea id="hs-msg-text" rows="3" placeholder="Hi! We'd like to invite you for…"></textarea></div><label class="text-sm"><input type="checkbox" id="hs-msg-mail"> Also send by email</label><div class="mt-8"><button class="btn btn-primary btn-sm" id="hs-msg-send">Send</button></div></div>
      </div></div>`);
    if (!root) return;
    let apps = [];
    async function pipeline() {
      const d = await api("/pro/company/pipeline");
      const max = Math.max(1, ...Object.values(d.totals));
      $("hs-pipeline").innerHTML = `<div class="card card-pad mb-16"><h3 class="mb-16">All drives funnel</h3>${Object.entries(d.totals).map(([k, v]) => `<div class="pro-funnel-row"><span>${k}</span><div class="pro-funnel-bar"><span class="${k}" style="width:${(v / max) * 100}%"></span></div><b>${v}</b></div>`).join("")}</div>` +
        (d.drives.length ? `<div class="grid-2" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">${d.drives.map((x) => `<div class="card card-pad"><div class="flex justify-between"><b>${esc(x.role_title)}</b><span class="badge badge-blue">${esc(x.status)}</span></div><div class="text-sm text-muted mb-8">${x.total} applicants · ${x.conversion}% selected</div>${Object.entries(x.counts).map(([k, v]) => `<div class="pro-funnel-row"><span>${k}</span><div class="pro-funnel-bar"><span class="${k}" style="width:${x.total ? (v / x.total) * 100 : 0}%"></span></div><b>${v}</b></div>`).join("")}</div>`).join("")}</div>` : `<div class="empty-state">Post a drive to see analytics.</div>`);
    }
    async function loadApps() {
      const [a, d] = await Promise.all([api("/company/applications" + ($("hs-drive").value ? `?drive_id=${$("hs-drive").value}` : "")), api("/company/drives")]);
      apps = a.applications;
      if ($("hs-drive").options.length === 1) $("hs-drive").insertAdjacentHTML("beforeend", d.drives.map((x) => `<option value="${x.id}">${esc(x.role_title)}</option>`).join(""));
      $("hs-tbody").innerHTML = apps.map((x) => `<tr><td><input type="checkbox" class="pro-row-check hs-row" value="${x.id}" data-student="${x.student_id}"></td><td><b>${esc(x.student_name)}</b><div class="text-sm text-muted">${esc(x.roll_number || "")}</div></td><td>${esc(x.branch || "")}</td><td>${x.cgpa ?? "-"}</td><td>${esc(x.role_title)}</td><td><span class="badge badge-blue">${esc(x.status)}</span></td></tr>`).join("") || `<tr><td colspan="6" class="empty-state">No applicants yet.</td></tr>`;
    }
    const picked = () => [...document.querySelectorAll(".hs-row:checked")];
    $("hs-all").onchange = (e) => document.querySelectorAll(".hs-row").forEach((c) => (c.checked = e.target.checked));
    $("hs-drive").onchange = () => loadApps().catch(fail);
    $("hs-apply").onclick = async () => {
      const ids = picked().map((c) => +c.value); if (!ids.length) return toast("Select applicants first.", "error");
      try { const r = await api("/pro/company/applications/bulk", { method: "POST", body: { application_ids: ids, status: $("hs-status").value } }); toast(r.message); await loadApps(); pipeline(); } catch (e) { fail(e); }
    };
    $("hs-compare").onclick = async () => {
      const ids = [...new Set(picked().map((c) => c.dataset.student))];
      if (ids.length < 2) return toast("Select 2-4 applicants to compare.", "error");
      try {
        const d = await api(`/pro/company/compare?ids=${ids.slice(0, 4).join(",")}`);
        const row = (label, fn, best) => `<tr><th>${label}</th>${d.candidates.map((c) => `<td class="${best && c[best] ? "best" : ""}">${fn(c)}</td>`).join("")}</tr>`;
        $("hs-compare-out").innerHTML = `<table><thead><tr><th></th>${d.candidates.map((c) => `<th>${esc(c.name)}</th>`).join("")}</tr></thead><tbody>${row("Branch", (c) => esc(c.branch))}${row("CGPA", (c) => c.cgpa, "best_cgpa")}${row("Backlogs", (c) => c.backlogs)}${row("10th / Inter %", (c) => `${c.tenth} / ${c.inter}`)}${row("ATS score", (c) => c.ats_score, "best_ats_score")}${row("Mock interview avg", (c) => (c.mock_avg ? c.mock_avg + "/5" : "-"))}${row("Skills", (c) => c.skills.map((s) => `<span class="pro-chip">${esc(s)}</span>`).join(""))}</tbody></table>`;
      } catch (e) { fail(e); }
    };
    $("hs-msg").onclick = () => ($("hs-msg-box").style.display = "block");
    $("hs-msg-send").onclick = async () => {
      const ids = [...new Set(picked().map((c) => +c.dataset.student))];
      try { const r = await api("/pro/company/message", { method: "POST", body: { student_ids: ids, message: $("hs-msg-text").value, send_email: $("hs-msg-mail").checked } }); toast(r.message); $("hs-msg-text").value = ""; $("hs-msg-box").style.display = "none"; } catch (e) { fail(e); }
    };
    tabs(root, [["pipeline", "Pipeline"], ["bulk", "Applicants & Actions"]], { pipeline: () => pipeline().catch(fail), bulk: () => loadApps().catch(fail) });
  }

  /* ============================== CDPC ============================== */
  function cdpc() {
    addNav("Insights Hub", "insights", "alert-triangle");
    const root = addSection("insights", `
      <div class="page-header"><div><h1>Insights Hub</h1><p>Find students who need help, understand packages, avoid drive clashes and broadcast by email.</p></div></div>
      <div class="pro-tabs"></div>
      <div class="pro-pane" data-pane="risk"><div class="card card-pad">
        <div class="pro-toolbar"><button class="btn btn-primary btn-sm" id="ih-nudge">Nudge selected</button><label class="text-sm"><input type="checkbox" id="ih-nudge-mail"> Also email them</label><span class="text-muted text-sm" id="ih-risk-count"></span></div>
        <div class="table-wrap"><table class="data-table"><thead><tr><th><input type="checkbox" class="pro-row-check" id="ih-all"></th><th>Student</th><th>Branch</th><th>CGPA</th><th>ATS</th><th>Risk</th><th>Why</th></tr></thead><tbody id="ih-risk">${`<tr><td colspan="7">${spin}</td></tr>`}</tbody></table></div></div></div>
      <div class="pro-pane" data-pane="pkg"><div id="ih-pkg">${spin}</div></div>
      <div class="pro-pane" data-pane="clash"><div class="card card-pad" id="ih-clash">${spin}</div></div>
      <div class="pro-pane" data-pane="mail"><div class="card card-pad" style="max-width:640px"><h3 class="mb-16">Email broadcast</h3>
        <div class="field-row"><div class="field"><label>Audience</label><select id="eb-aud"><option value="students">All students</option><option value="companies">All companies</option><option value="all">Everyone</option></select></div><div class="field"><label>Branch (students)</label><input id="eb-branch" placeholder="All"/></div></div>
        <div class="field"><label>Subject</label><input id="eb-sub" placeholder="Campus drive on 15 Oct"/></div>
        <div class="field"><label>Message</label><textarea id="eb-msg" rows="5"></textarea></div>
        <button class="btn btn-primary" id="eb-send">Send email</button><div class="pro-note">Also appears in each recipient's notification bell. Requires SMTP settings in <code>.env</code>.</div></div></div>`);
    if (!root) return;
    async function risk() {
      const d = await api("/pro/cdpc/at-risk");
      $("ih-risk-count").textContent = `${d.total} student(s) need attention`;
      $("ih-risk").innerHTML = d.students.map((s) => `<tr><td><input type="checkbox" class="pro-row-check ih-row" value="${s.id}"></td><td><b>${esc(s.name)}</b><div class="text-sm text-muted">${esc(s.roll_number || "")}</div></td><td>${esc(s.branch)}</td><td>${s.cgpa}</td><td>${s.ats_score}</td><td><span class="badge ${s.level === "High" ? "badge-red" : "badge-orange"}">${s.level}</span></td><td>${s.reasons.map((r) => `<span class="pro-chip miss">${esc(r)}</span>`).join("")}</td></tr>`).join("") || `<tr><td colspan="7" class="empty-state">Nobody is at risk. Great work!</td></tr>`;
    }
    $("ih-all").onchange = (e) => document.querySelectorAll(".ih-row").forEach((c) => (c.checked = e.target.checked));
    $("ih-nudge").onclick = async () => {
      const ids = [...document.querySelectorAll(".ih-row:checked")].map((c) => +c.value); if (!ids.length) return toast("Select students first.", "error");
      try { const r = await api("/pro/cdpc/nudge", { method: "POST", body: { student_ids: ids, send_email: $("ih-nudge-mail").checked } }); toast(r.message); } catch (e) { fail(e); }
    };
    async function pkg() {
      const d = await api("/pro/cdpc/package-analytics");
      const max = Math.max(1, ...Object.values(d.buckets));
      const tbl = (rows) => rows.length ? `<table class="data-table"><thead><tr><th>Name</th><th>Placed</th><th>Avg LPA</th><th>Max LPA</th></tr></thead><tbody>${rows.map((r) => `<tr><td>${esc(r.name)}</td><td>${r.count}</td><td>${r.avg}</td><td>${r.max}</td></tr>`).join("")}</tbody></table>` : `<div class="empty-state">No data yet.</div>`;
      $("ih-pkg").innerHTML = `<div class="stats-grid">${[["Highest", d.highest + " LPA"], ["Average", d.average + " LPA"], ["Median", d.median + " LPA"], ["Offers counted", d.count]].map((x) => `<div class="stat-card"><div class="stat-label">${x[0]}</div><div class="stat-value">${x[1]}</div></div>`).join("")}</div>
        <div class="grid-2"><div class="card card-pad"><h3>Package distribution (LPA)</h3><div class="pro-bars">${Object.entries(d.buckets).map(([k, v]) => `<div><span>${v}</span><i style="height:${(v / max) * 100}%"></i><span>${k}</span></div>`).join("")}</div></div><div class="card card-pad"><h3 class="mb-8">By branch</h3>${tbl(d.by_branch)}</div></div><div class="card card-pad mt-16"><h3 class="mb-8">Top recruiters by average package</h3>${tbl(d.by_company)}</div>`;
    }
    async function clash() {
      const d = await api("/pro/cdpc/drive-clashes");
      $("ih-clash").innerHTML = d.clashes.length ? d.clashes.map((c) => `<div class="advanced-row" style="align-items:flex-start"><div><b>${esc(c.date)}</b><div class="mt-8">${c.drives.map((x) => `<span class="pro-chip miss">${esc(x.company)} - ${esc(x.role_title)}</span>`).join("")}</div></div><span class="badge badge-red">${c.students_affected} student(s) double-booked</span></div>`).join("") : `<div class="empty-state">No two upcoming drives share a date. 👍</div>`;
    }
    $("eb-send").onclick = async () => {
      try { const r = await api("/pro/cdpc/email-broadcast", { method: "POST", body: { audience: $("eb-aud").value, branch: $("eb-branch").value.trim() || "All", subject: $("eb-sub").value, message: $("eb-msg").value } }); toast(r.message); $("eb-sub").value = ""; $("eb-msg").value = ""; } catch (e) { fail(e); }
    };
    tabs(root, [["risk", "At-risk Students"], ["pkg", "Package Analytics"], ["clash", "Drive Clashes"], ["mail", "Email Broadcast"]],
      { risk: () => risk().catch(fail), pkg: () => pkg().catch(fail), clash: () => clash().catch(fail), mail: () => {} });
  }

  async function boot() {
    let u = window.CURRENT_USER;
    if (!u && window.loadCurrentUser) { try { u = await loadCurrentUser(); } catch (e) { return; } }
    if (!u) return;
    ({ student, company, cdpc })[u.role]?.();
  }
  document.addEventListener("DOMContentLoaded", () => setTimeout(boot, 450));
})();