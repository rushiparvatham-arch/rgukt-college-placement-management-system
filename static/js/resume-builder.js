/* ---------------- Advanced Resume Creator ---------------- */
const RB_TEMPLATES = {
  classic: "Classic Professional",
  modern: "Modern Sidebar",
  minimal: "Minimal Clean",
  campus: "Campus Placement",
  executive: "Executive Split",
  compact: "Compact One-page",
};

const RB_PERSONAL_IDS = [
  "rb-name", "rb-headline", "rb-email", "rb-phone", "rb-location",
  "rb-website", "rb-linkedin", "rb-github", "rb-summary", "rb-interests",
  "rb-template", "rb-accent", "rb-font-scale",
];

let RB_STATE = null;
let RB_CONTROLS_BOUND = false;

function defaultResumeState() {
  const u = CURRENT_USER || {};
  const p = u.profile || {};
  return {
    version: 3,
    template: "classic",
    accent: "#7a1f2b",
    fontScale: "1",
    name: u.name || "",
    headline: "",
    email: u.email || "",
    phone: u.phone || "",
    location: p.address || "RGUKT Ongole",
    website: "",
    linkedin: p.linkedin || "",
    github: p.github || "",
    summary: "",
    interests: "",
    skillCategories: p.skills
      ? [{ category: "Technical Skills", items: p.skills }]
      : [{ category: "Technical Skills", items: "" }, { category: "Tools", items: "" }],
    education: [
      {
        school: "RGUKT Ongole",
        degree: p.branch ? `B.Tech — ${p.branch}` : "B.Tech",
        dates: p.batch_year || "2022 – 2026",
        details: [
          p.cgpa ? `CGPA: ${p.cgpa}` : "",
          p.tenth_percent ? `Class X: ${p.tenth_percent}%` : "",
          p.inter_percent ? `Intermediate: ${p.inter_percent}%` : "",
        ].filter(Boolean).join(" · "),
      },
    ],
    experience: [],
    projects: [],
    certifications: [],
    achievements: [],
    languages: [
      { language: "English", level: "Professional" },
      { language: "Telugu", level: "Native" },
    ],
    customSections: [],
  };
}

function migrateLegacyResume(rd) {
  if (!rd) return defaultResumeState();
  if (rd.version >= 2) {
    return { ...defaultResumeState(), ...rd, version: 3, customSections: rd.customSections || [], interests: rd.interests || "" };
  }
  const base = defaultResumeState();
  return {
    ...base,
    summary: rd.summary || "",
    linkedin: rd.linkedin || base.linkedin,
    github: rd.github || base.github,
    skillCategories: rd.skills
      ? [{ category: "Skills", items: rd.skills }]
      : base.skillCategories,
    education: rd.education
      ? String(rd.education).split("\n").filter(Boolean).map((line) => ({
          school: line, degree: "", dates: "", details: "",
        }))
      : base.education,
    experience: rd.experience
      ? String(rd.experience).split("\n").filter(Boolean).map((line) => ({
          company: line, role: "", dates: "", bullets: "",
        }))
      : [],
    projects: rd.projects
      ? String(rd.projects).split("\n").filter(Boolean).map((line) => ({
          name: line, tech: "", link: "", bullets: "",
        }))
      : [],
    certifications: rd.certifications
      ? String(rd.certifications).split("\n").filter(Boolean).map((line) => ({
          name: line, issuer: "", year: "",
        }))
      : [],
  };
}

async function loadResumeBuilder() {
  try {
    const data = await apiRequest("/student/resume-builder");
    RB_STATE = migrateLegacyResume(data.resume_data);
    bindResumeForm();
    renderResumeEntries();
    renderResumePreview();
    updateResumeCompleteness();
  } catch (e) { showToast(e.message, "error"); }
}

function bindResumeForm() {
  const s = RB_STATE;
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
  set("rb-name", s.name);
  set("rb-headline", s.headline);
  set("rb-email", s.email);
  set("rb-phone", s.phone);
  set("rb-location", s.location);
  set("rb-website", s.website);
  set("rb-linkedin", s.linkedin);
  set("rb-github", s.github);
  set("rb-summary", s.summary);
  set("rb-interests", s.interests);
  set("rb-template", s.template || "classic");
  set("rb-accent", s.accent || "#7a1f2b");
  set("rb-font-scale", s.fontScale || "1");
  const label = document.getElementById("rb-template-label");
  if (label) label.textContent = RB_TEMPLATES[s.template] || "Classic";
}

function readResumePersonalFields() {
  if (!RB_STATE) return;
  const get = (id) => (document.getElementById(id)?.value || "").trim();
  RB_STATE.name = get("rb-name");
  RB_STATE.headline = get("rb-headline");
  RB_STATE.email = get("rb-email");
  RB_STATE.phone = get("rb-phone");
  RB_STATE.location = get("rb-location");
  RB_STATE.website = get("rb-website");
  RB_STATE.linkedin = get("rb-linkedin");
  RB_STATE.github = get("rb-github");
  RB_STATE.summary = get("rb-summary");
  RB_STATE.interests = get("rb-interests");
  RB_STATE.template = get("rb-template") || "classic";
  RB_STATE.accent = get("rb-accent") || "#7a1f2b";
  RB_STATE.fontScale = get("rb-font-scale") || "1";
}

function entryToolbar(kind, i, len) {
  return `<div class="rb-entry-tools">
    <button type="button" class="btn btn-ghost btn-sm rb-move" data-kind="${kind}" data-i="${i}" data-dir="-1" ${i === 0 ? "disabled" : ""}>Up</button>
    <button type="button" class="btn btn-ghost btn-sm rb-move" data-kind="${kind}" data-i="${i}" data-dir="1" ${i === len - 1 ? "disabled" : ""}>Down</button>
    <button type="button" class="btn btn-ghost btn-sm rb-remove" data-kind="${kind}" data-i="${i}">Remove</button>
  </div>`;
}

function renderResumeEntries() {
  if (!RB_STATE) return;

  const skills = RB_STATE.skillCategories || [];
  const skillsHost = document.getElementById("rb-skills-list");
  skillsHost.innerHTML = skills.map((sc, i) => `
    <div class="rb-entry" data-kind="skill" data-i="${i}">
      <div class="field-row">
        <div class="field"><label>Category</label><input data-f="category" value="${escapeHtml(sc.category || "")}" placeholder="e.g. Languages" /></div>
        <div class="field"><label>Skills (comma separated)</label><input data-f="items" value="${escapeHtml(sc.items || "")}" placeholder="Python, Java, C++" /></div>
      </div>
      ${entryToolbar("skill", i, skills.length)}
    </div>`).join("") || `<p class="text-muted text-sm">No skill categories yet.</p>`;

  const edu = RB_STATE.education || [];
  document.getElementById("rb-education-list").innerHTML = edu.map((ed, i) => `
    <div class="rb-entry">
      <div class="field-row">
        <div class="field"><label>Institution</label><input data-kind="education" data-i="${i}" data-f="school" value="${escapeHtml(ed.school || "")}" /></div>
        <div class="field"><label>Degree / Program</label><input data-kind="education" data-i="${i}" data-f="degree" value="${escapeHtml(ed.degree || "")}" /></div>
      </div>
      <div class="field-row">
        <div class="field"><label>Dates</label><input data-kind="education" data-i="${i}" data-f="dates" value="${escapeHtml(ed.dates || "")}" placeholder="2022 – 2026" /></div>
        <div class="field"><label>Details (CGPA, coursework)</label><input data-kind="education" data-i="${i}" data-f="details" value="${escapeHtml(ed.details || "")}" /></div>
      </div>
      ${entryToolbar("education", i, edu.length)}
    </div>`).join("") || emptyEntryHint("education");

  const exp = RB_STATE.experience || [];
  document.getElementById("rb-experience-list").innerHTML = exp.map((ex, i) => `
    <div class="rb-entry">
      <div class="field-row">
        <div class="field"><label>Company / Org</label><input data-kind="experience" data-i="${i}" data-f="company" value="${escapeHtml(ex.company || "")}" /></div>
        <div class="field"><label>Role</label><input data-kind="experience" data-i="${i}" data-f="role" value="${escapeHtml(ex.role || "")}" /></div>
      </div>
      <div class="field"><label>Dates</label><input data-kind="experience" data-i="${i}" data-f="dates" value="${escapeHtml(ex.dates || "")}" placeholder="Jun 2025 – Aug 2025" /></div>
      <div class="field"><label>Highlights (one per line, start with action verbs)</label><textarea data-kind="experience" data-i="${i}" data-f="bullets" rows="3">${escapeHtml(ex.bullets || "")}</textarea></div>
      ${entryToolbar("experience", i, exp.length)}
    </div>`).join("") || emptyEntryHint("experience");

  const proj = RB_STATE.projects || [];
  document.getElementById("rb-projects-list").innerHTML = proj.map((pr, i) => `
    <div class="rb-entry">
      <div class="field-row">
        <div class="field"><label>Project Name</label><input data-kind="projects" data-i="${i}" data-f="name" value="${escapeHtml(pr.name || "")}" /></div>
        <div class="field"><label>Tech Stack</label><input data-kind="projects" data-i="${i}" data-f="tech" value="${escapeHtml(pr.tech || "")}" placeholder="React, Flask, MySQL" /></div>
      </div>
      <div class="field"><label>Link</label><input data-kind="projects" data-i="${i}" data-f="link" value="${escapeHtml(pr.link || "")}" placeholder="github.com/..." /></div>
      <div class="field"><label>Description / bullets (one per line)</label><textarea data-kind="projects" data-i="${i}" data-f="bullets" rows="3">${escapeHtml(pr.bullets || "")}</textarea></div>
      ${entryToolbar("projects", i, proj.length)}
    </div>`).join("") || emptyEntryHint("projects");

  const certs = RB_STATE.certifications || [];
  document.getElementById("rb-certifications-list").innerHTML = certs.map((c, i) => `
    <div class="rb-entry">
      <div class="field-row">
        <div class="field"><label>Certification</label><input data-kind="certifications" data-i="${i}" data-f="name" value="${escapeHtml(c.name || "")}" /></div>
        <div class="field"><label>Issuer</label><input data-kind="certifications" data-i="${i}" data-f="issuer" value="${escapeHtml(c.issuer || "")}" /></div>
      </div>
      <div class="field"><label>Year</label><input data-kind="certifications" data-i="${i}" data-f="year" value="${escapeHtml(c.year || "")}" /></div>
      ${entryToolbar("certifications", i, certs.length)}
    </div>`).join("") || emptyEntryHint("certifications");

  const ach = RB_STATE.achievements || [];
  document.getElementById("rb-achievements-list").innerHTML = ach.map((a, i) => `
    <div class="rb-entry">
      <div class="field"><label>Achievement</label><input data-kind="achievements" data-i="${i}" data-f="text" value="${escapeHtml(a.text || "")}" placeholder="Hackathon winner, Rank in GATE, ..." /></div>
      ${entryToolbar("achievements", i, ach.length)}
    </div>`).join("") || emptyEntryHint("achievements");

  const langs = RB_STATE.languages || [];
  document.getElementById("rb-languages-list").innerHTML = langs.map((l, i) => `
    <div class="rb-entry">
      <div class="field-row">
        <div class="field"><label>Language</label><input data-kind="languages" data-i="${i}" data-f="language" value="${escapeHtml(l.language || "")}" /></div>
        <div class="field"><label>Proficiency</label><input data-kind="languages" data-i="${i}" data-f="level" value="${escapeHtml(l.level || "")}" placeholder="Native / Fluent / Intermediate" /></div>
      </div>
      ${entryToolbar("languages", i, langs.length)}
    </div>`).join("") || emptyEntryHint("languages");

  const custom = RB_STATE.customSections || [];
  const customHost = document.getElementById("rb-custom-list");
  if (customHost) {
    customHost.innerHTML = custom.map((c, i) => `
      <div class="rb-entry">
        <div class="field"><label>Section title</label><input data-kind="customSections" data-i="${i}" data-f="title" value="${escapeHtml(c.title || "")}" placeholder="Positions of Responsibility" /></div>
        <div class="field"><label>Content (one bullet per line)</label><textarea data-kind="customSections" data-i="${i}" data-f="body" rows="3">${escapeHtml(c.body || "")}</textarea></div>
        ${entryToolbar("customSections", i, custom.length)}
      </div>`).join("") || emptyEntryHint("custom sections");
  }

  skillsHost.querySelectorAll(".rb-entry[data-kind='skill']").forEach((row) => {
    const i = Number(row.dataset.i);
    row.querySelectorAll("input[data-f]").forEach((inp) => {
      inp.addEventListener("input", () => {
        RB_STATE.skillCategories[i][inp.dataset.f] = inp.value;
        renderResumePreview();
        updateResumeCompleteness();
      });
    });
  });

  document.querySelectorAll("#view-resume-creator .rb-remove").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kind = btn.dataset.kind;
      const i = Number(btn.dataset.i);
      if (kind === "skill") RB_STATE.skillCategories.splice(i, 1);
      else RB_STATE[kind].splice(i, 1);
      renderResumeEntries();
      renderResumePreview();
      updateResumeCompleteness();
    });
  });

  document.querySelectorAll("#view-resume-creator .rb-move").forEach((btn) => {
    btn.addEventListener("click", () => {
      const kind = btn.dataset.kind;
      const i = Number(btn.dataset.i);
      const dir = Number(btn.dataset.dir);
      const arr = kind === "skill" ? RB_STATE.skillCategories : RB_STATE[kind];
      const j = i + dir;
      if (!arr || j < 0 || j >= arr.length) return;
      [arr[i], arr[j]] = [arr[j], arr[i]];
      renderResumeEntries();
      renderResumePreview();
    });
  });

  document.querySelectorAll("#view-resume-creator [data-kind][data-f]").forEach((inp) => {
    if (inp.closest("#rb-skills-list")) return;
    inp.addEventListener("input", () => {
      const kind = inp.dataset.kind;
      const i = Number(inp.dataset.i);
      const f = inp.dataset.f;
      if (RB_STATE[kind] && RB_STATE[kind][i]) {
        RB_STATE[kind][i][f] = inp.value;
        renderResumePreview();
        updateResumeCompleteness();
      }
    });
  });
}

function emptyEntryHint(kind) {
  return `<p class="text-muted text-sm">No ${kind} added yet. Click + Add to create an entry.</p>`;
}

function addResumeEntry(kind) {
  if (!RB_STATE) RB_STATE = defaultResumeState();
  const blanks = {
    education: { school: "", degree: "", dates: "", details: "" },
    experience: { company: "", role: "", dates: "", bullets: "" },
    projects: { name: "", tech: "", link: "", bullets: "" },
    certifications: { name: "", issuer: "", year: "" },
    achievements: { text: "" },
    languages: { language: "", level: "" },
    customSections: { title: "", body: "" },
  };
  if (kind === "skill") {
    RB_STATE.skillCategories.push({ category: "", items: "" });
  } else {
    RB_STATE[kind] = RB_STATE[kind] || [];
    RB_STATE[kind].push(blanks[kind]);
  }
  renderResumeEntries();
  updateResumeCompleteness();
}

function importResumeFromProfile() {
  if (!CURRENT_USER) return;
  const merged = defaultResumeState();
  if (RB_STATE) {
    merged.summary = RB_STATE.summary || merged.summary;
    merged.template = RB_STATE.template || merged.template;
    merged.accent = RB_STATE.accent || merged.accent;
    merged.fontScale = RB_STATE.fontScale || merged.fontScale;
    merged.headline = RB_STATE.headline || merged.headline;
    merged.website = RB_STATE.website || merged.website;
    merged.interests = RB_STATE.interests || merged.interests;
    merged.projects = RB_STATE.projects?.length ? RB_STATE.projects : merged.projects;
    merged.experience = RB_STATE.experience?.length ? RB_STATE.experience : merged.experience;
    merged.certifications = RB_STATE.certifications?.length ? RB_STATE.certifications : merged.certifications;
    merged.achievements = RB_STATE.achievements?.length ? RB_STATE.achievements : merged.achievements;
    merged.customSections = RB_STATE.customSections?.length ? RB_STATE.customSections : merged.customSections;
  }
  RB_STATE = merged;
  bindResumeForm();
  renderResumeEntries();
  renderResumePreview();
  updateResumeCompleteness();
  showToast("Profile details imported into the resume.", "success");
}

function branchSamplePack() {
  const branch = CURRENT_USER?.profile?.branch || "";
  const packs = {
    "Computer Science & Engineering": {
      headline: "Aspiring Software Engineer | Full-Stack & DSA",
      skills: [
        { category: "Languages", items: "Python, Java, C, JavaScript, SQL" },
        { category: "Frameworks", items: "React, Flask, Node.js, REST APIs" },
        { category: "Tools", items: "Git, GitHub, MySQL, Linux, Postman" },
      ],
      projects: [{
        name: "Campus Placement Portal",
        tech: "Flask, SQLite, HTML/CSS, JavaScript",
        link: "",
        bullets: "Built student, CDPC and company dashboards for campus drives.\nImplemented eligibility checks, applications and interview tracking.",
      }],
    },
    "Electronics & Communication Engineering": {
      headline: "ECE Undergraduate | Embedded Systems & VLSI",
      skills: [
        { category: "Core", items: "Digital Electronics, Signals & Systems, Analog Circuits" },
        { category: "Tools", items: "MATLAB, Verilog, Multisim, Embedded C, Arduino" },
        { category: "Hardware", items: "Microcontrollers, Sensors, PCB basics" },
      ],
      projects: [{
        name: "IoT Health Monitoring Node",
        tech: "Arduino, Sensors, Embedded C",
        link: "",
        bullets: "Designed a wearable prototype to stream temperature and pulse data.\nCalibrated sensors and documented power-budget trade-offs.",
      }],
    },
    "Electrical & Electronics Engineering": {
      headline: "EEE Undergraduate | Power Systems & Control",
      skills: [
        { category: "Core", items: "Electrical Machines, Power Systems, Control Systems" },
        { category: "Tools", items: "MATLAB/Simulink, AutoCAD Electrical, PLC basics" },
      ],
      projects: [{
        name: "Load Flow Study of a Sample Grid",
        tech: "MATLAB, PowerWorld (optional)",
        link: "",
        bullets: "Modelled a small network and analysed voltage profile under load variations.\nSummarised protection and power-factor improvement recommendations.",
      }],
    },
    "Mechanical Engineering": {
      headline: "Mechanical Undergraduate | Design & Manufacturing",
      skills: [
        { category: "Core", items: "SOM, Thermodynamics, Fluid Mechanics, Machine Design" },
        { category: "Tools", items: "SolidWorks, AutoCAD, ANSYS, CNC basics" },
      ],
      projects: [{
        name: "Solar-Assisted Dryer Prototype",
        tech: "CAD, Heat Transfer",
        link: "",
        bullets: "Designed a low-cost dryer geometry and estimated drying time from energy balance.\nFabricated a lab-scale model and compared predicted vs measured temperatures.",
      }],
    },
    "Civil Engineering": {
      headline: "Civil Undergraduate | Structures & Site Works",
      skills: [
        { category: "Core", items: "Structural Analysis, RCC, Surveying, Geotech, Transportation" },
        { category: "Tools", items: "AutoCAD, STAAD.Pro, MS Excel, Total Station basics" },
      ],
      projects: [{
        name: "G+2 Residential Building Analysis",
        tech: "STAAD.Pro, AutoCAD",
        link: "",
        bullets: "Modelled gravity and lateral loads for a small residential frame.\nPrepared bar-bending and quantity take-off summaries.",
      }],
    },
  };
  return packs[branch] || {
    headline: "B.Tech Undergraduate | RGUKT Ongole",
    skills: [{ category: "Technical Skills", items: CURRENT_USER?.profile?.skills || "" }],
    projects: [],
  };
}

function applyBranchSample() {
  if (!RB_STATE) RB_STATE = defaultResumeState();
  const sample = branchSamplePack();
  RB_STATE.headline = RB_STATE.headline || sample.headline;
  if (!(RB_STATE.skillCategories || []).some((s) => s.items?.trim())) {
    RB_STATE.skillCategories = sample.skills;
  }
  if (!(RB_STATE.projects || []).some((p) => p.name?.trim()) && sample.projects.length) {
    RB_STATE.projects = sample.projects;
  }
  if (!RB_STATE.summary) RB_STATE.summary = generatedSummary();
  if (!(RB_STATE.customSections || []).length) {
    RB_STATE.customSections = [{
      title: "Positions of Responsibility",
      body: "Class representative / club volunteer — coordinated peer study sessions and campus events.",
    }];
  }
  bindResumeForm();
  renderResumeEntries();
  renderResumePreview();
  updateResumeCompleteness();
  showToast("Branch sample content filled. Edit it to match your real work.", "success");
}

function generatedSummary() {
  const u = CURRENT_USER || {};
  const p = u.profile || {};
  const name = (document.getElementById("rb-name")?.value || u.name || "I").split(" ")[0];
  const branch = p.branch || "engineering";
  const cgpa = p.cgpa ? ` with a CGPA of ${p.cgpa}` : "";
  const skills = (p.skills || "").split(",").map((s) => s.trim()).filter(Boolean).slice(0, 4);
  const skillBit = skills.length ? ` Skilled in ${skills.join(", ")}.` : "";
  return `${name} is a B.Tech student in ${branch} at RGUKT Ongole${cgpa}. Seeking campus placement opportunities to apply classroom fundamentals on real products.${skillBit} Comfortable collaborating in teams, documenting work, and learning new tools quickly.`;
}

function generateResumeSummary() {
  if (!RB_STATE) RB_STATE = defaultResumeState();
  const summary = generatedSummary();
  RB_STATE.summary = summary;
  const el = document.getElementById("rb-summary");
  if (el) el.value = summary;
  renderResumePreview();
  updateResumeCompleteness();
  showToast("Summary drafted from your profile. Personalise it before exporting.", "success");
}

function bulletsHtml(text) {
  return escapeHtml(text || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => `<li>${l}</li>`)
    .join("");
}

function resumeTipList() {
  readResumePersonalFields();
  const s = RB_STATE;
  const tips = [];
  const add = (ok, label) => tips.push({ ok, label });
  add(!!s.name && !!s.email && !!s.phone, "Contact block: name, email, phone");
  add(!!(s.linkedin || s.github || s.website), "At least one professional link (LinkedIn / GitHub / portfolio)");
  add((s.headline || "").length >= 12, "Headline targeting a role (not just 'student')");
  add((s.summary || "").split(" ").filter(Boolean).length >= 30, "Summary of 30+ words with branch + goal");
  add((s.skillCategories || []).some((x) => (x.items || "").split(",").filter((i) => i.trim()).length >= 6), "6+ skills grouped by category");
  add((s.education || []).some((e) => e.school && e.details), "Education with CGPA / board scores");
  add((s.projects || []).some((p) => p.name && ((p.bullets || "").includes("\n") || (p.bullets || "").length > 40)), "Projects with quantified bullets");
  add((s.experience || []).some((e) => e.company) || (s.achievements || []).some((a) => a.text), "Internship, POR, or achievement");
  add(!(s.summary || "").toLowerCase().includes("hardworking team player seeking challenging"), "Avoid generic clichés in the summary");
  add((s.projects || []).every((p) => !p.bullets || !/responsible for|various|etc\.?/i.test(p.bullets)), "Prefer action verbs over 'responsible for'");
  return tips;
}

function updateResumeCompleteness() {
  if (!RB_STATE) return;
  const tips = resumeTipList();
  const pct = Math.round((tips.filter((t) => t.ok).length / tips.length) * 100);
  const bar = document.getElementById("rb-completeness-bar");
  const label = document.getElementById("rb-completeness-label");
  if (bar) bar.style.width = `${pct}%`;
  if (label) label.textContent = `${pct}%`;
  const host = document.getElementById("rb-ats-tips");
  if (host) {
    host.innerHTML = tips.map((t) => `
      <div class="rb-tip ${t.ok ? "is-ok" : "is-miss"}">
        <span>${t.ok ? "✓" : "○"}</span>
        <span>${escapeHtml(t.label)}</span>
      </div>`).join("");
  }
}

function renderResumePreview() {
  if (!RB_STATE) return;
  readResumePersonalFields();
  const s = RB_STATE;
  const accent = s.accent || "#7a1f2b";
  const scale = Number(s.fontScale || 1);
  const contact = [s.email, s.phone, s.location, s.linkedin, s.github, s.website].filter(Boolean).map(escapeHtml).join(" · ");

  const skillsBlock = (s.skillCategories || [])
    .filter((sc) => sc.items?.trim())
    .map((sc) => `<div class="rb-skill-row"><b>${escapeHtml(sc.category || "Skills")}:</b> ${escapeHtml(sc.items)}</div>`)
    .join("");

  const eduBlock = (s.education || [])
    .filter((e) => e.school || e.degree)
    .map((e) => `
      <div class="rb-item">
        <div class="rb-item-top"><b>${escapeHtml(e.degree || e.school)}</b><span>${escapeHtml(e.dates || "")}</span></div>
        <div class="rb-item-sub">${escapeHtml(e.school || "")}</div>
        ${e.details ? `<div class="rb-item-detail">${escapeHtml(e.details)}</div>` : ""}
      </div>`).join("");

  const expBlock = (s.experience || [])
    .filter((e) => e.company || e.role)
    .map((e) => `
      <div class="rb-item">
        <div class="rb-item-top"><b>${escapeHtml(e.role || "Role")}</b><span>${escapeHtml(e.dates || "")}</span></div>
        <div class="rb-item-sub">${escapeHtml(e.company || "")}</div>
        ${e.bullets ? `<ul class="rb-bullets">${bulletsHtml(e.bullets)}</ul>` : ""}
      </div>`).join("");

  const projBlock = (s.projects || [])
    .filter((p) => p.name)
    .map((p) => `
      <div class="rb-item">
        <div class="rb-item-top"><b>${escapeHtml(p.name)}</b><span>${escapeHtml(p.link || "")}</span></div>
        ${p.tech ? `<div class="rb-item-sub">${escapeHtml(p.tech)}</div>` : ""}
        ${p.bullets ? `<ul class="rb-bullets">${bulletsHtml(p.bullets)}</ul>` : ""}
      </div>`).join("");

  const certBlock = (s.certifications || [])
    .filter((c) => c.name)
    .map((c) => `<div class="rb-item"><b>${escapeHtml(c.name)}</b> — ${escapeHtml([c.issuer, c.year].filter(Boolean).join(", "))}</div>`)
    .join("");

  const achBlock = (s.achievements || [])
    .filter((a) => a.text)
    .map((a) => `<li>${escapeHtml(a.text)}</li>`)
    .join("");

  const langBlock = (s.languages || [])
    .filter((l) => l.language)
    .map((l) => `${escapeHtml(l.language)}${l.level ? ` (${escapeHtml(l.level)})` : ""}`)
    .join(" · ");

  const customBlocks = (s.customSections || [])
    .filter((c) => c.title && c.body)
    .map((c) => `<section class="rb-sec"><h4>${escapeHtml(c.title)}</h4><ul class="rb-bullets">${bulletsHtml(c.body)}</ul></section>`)
    .join("");

  const section = (title, body) => body ? `<section class="rb-sec"><h4>${title}</h4>${body}</section>` : "";
  const bodySections = `
    ${section("Professional Summary", s.summary ? `<p>${escapeHtml(s.summary)}</p>` : "")}
    ${section("Skills", skillsBlock)}
    ${section("Education", eduBlock)}
    ${section("Experience", expBlock)}
    ${section("Projects", projBlock)}
    ${section("Certifications", certBlock)}
    ${section("Achievements", achBlock ? `<ul class="rb-bullets">${achBlock}</ul>` : "")}
    ${customBlocks}
    ${section("Languages", langBlock ? `<p>${langBlock}</p>` : "")}
    ${section("Interests", s.interests ? `<p>${escapeHtml(s.interests)}</p>` : "")}
  `;

  const preview = document.getElementById("resume-preview");
  preview.className = `rb-preview tpl-${s.template || "classic"}`;
  preview.style.setProperty("--rb-accent", accent);
  preview.style.setProperty("--rb-scale", String(scale));
  const label = document.getElementById("rb-template-label");
  if (label) label.textContent = RB_TEMPLATES[s.template] || "Classic";

  if (s.template === "modern") {
    preview.innerHTML = `
      <div class="rb-modern">
        <aside class="rb-modern-side">
          <h2>${escapeHtml(s.name || "Your Name")}</h2>
          ${s.headline ? `<p class="rb-headline">${escapeHtml(s.headline)}</p>` : ""}
          <div class="rb-side-block"><h5>Contact</h5><p>${contact || "—"}</p></div>
          ${skillsBlock ? `<div class="rb-side-block"><h5>Skills</h5>${skillsBlock}</div>` : ""}
          ${langBlock ? `<div class="rb-side-block"><h5>Languages</h5><p>${langBlock}</p></div>` : ""}
        </aside>
        <div class="rb-modern-main">
          ${section("Summary", s.summary ? `<p>${escapeHtml(s.summary)}</p>` : "")}
          ${section("Education", eduBlock)}
          ${section("Experience", expBlock)}
          ${section("Projects", projBlock)}
          ${section("Certifications", certBlock)}
          ${section("Achievements", achBlock ? `<ul class="rb-bullets">${achBlock}</ul>` : "")}
          ${customBlocks}
          ${section("Interests", s.interests ? `<p>${escapeHtml(s.interests)}</p>` : "")}
        </div>
      </div>`;
  } else if (s.template === "executive") {
    preview.innerHTML = `
      <header class="rb-exec-header">
        <div>
          <h2>${escapeHtml(s.name || "Your Name")}</h2>
          ${s.headline ? `<p class="rb-headline">${escapeHtml(s.headline)}</p>` : ""}
        </div>
        <p class="rb-contact rb-exec-contact">${contact.split(" · ").join("<br>")}</p>
      </header>
      ${bodySections}`;
  } else {
    preview.innerHTML = `
      <header class="rb-header">
        <h2>${escapeHtml(s.name || "Your Name")}</h2>
        ${s.headline ? `<p class="rb-headline">${escapeHtml(s.headline)}</p>` : ""}
        <p class="rb-contact">${contact}</p>
      </header>
      ${bodySections}`;
  }
  updateResumeCompleteness();
}

async function saveResumeBuilder() {
  if (!RB_STATE) RB_STATE = defaultResumeState();
  readResumePersonalFields();
  RB_STATE.version = 3;
  try {
    await apiRequest("/student/resume-builder", { method: "POST", body: RB_STATE });
    showToast("Resume saved!", "success");
    renderResumePreview();
  } catch (err) { showToast(err.message, "error"); }
}

function exportResumeJson() {
  if (!RB_STATE) RB_STATE = defaultResumeState();
  readResumePersonalFields();
  const blob = new Blob([JSON.stringify(RB_STATE, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${(RB_STATE.name || "resume").replace(/\s+/g, "_")}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function importResumeJson(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const parsed = JSON.parse(reader.result);
      RB_STATE = migrateLegacyResume(parsed);
      bindResumeForm();
      renderResumeEntries();
      renderResumePreview();
      updateResumeCompleteness();
      showToast("Resume JSON imported.", "success");
    } catch (e) {
      showToast("Could not parse that JSON file.", "error");
    }
  };
  reader.readAsText(file);
}

function printResume() {
  renderResumePreview();
  const content = document.getElementById("resume-preview").innerHTML;
  const accent = RB_STATE?.accent || "#7a1f2b";
  const tpl = RB_STATE?.template || "classic";
  const scale = RB_STATE?.fontScale || "1";
  const win = window.open("", "_blank");
  if (!win) {
    showToast("Allow pop-ups to export the PDF.", "error");
    return;
  }
  win.document.write(`<!DOCTYPE html><html><head><title>${escapeHtml(RB_STATE?.name || "Resume")}</title>
    <style>
      body{font-family:Georgia,'Times New Roman',serif;color:#111;margin:0;padding:24px;background:#fff;}
      .rb-preview{font-size:calc(11.5pt * ${scale});line-height:1.45;max-width:800px;margin:0 auto;--rb-accent:${accent};}
      .rb-header{text-align:center;border-bottom:2px solid ${accent};padding-bottom:10px;margin-bottom:14px;}
      .tpl-minimal .rb-header{border-bottom:1px solid #ccc;text-align:left;}
      .tpl-campus .rb-header{border-bottom:3px double ${accent};}
      .tpl-compact .rb-sec{margin:8px 0;}
      .rb-exec-header{display:flex;justify-content:space-between;gap:16px;border-bottom:2px solid ${accent};padding-bottom:10px;margin-bottom:14px;}
      .rb-exec-contact{text-align:right;font-size:9.5pt;}
      h2{margin:0;font-size:22pt;color:${accent};}
      .rb-headline{margin:4px 0;font-style:italic;color:#444;}
      .rb-contact{margin:6px 0 0;font-size:9.5pt;color:#444;}
      .rb-sec{margin:14px 0;}
      .rb-sec h4{margin:0 0 6px;font-size:11pt;text-transform:uppercase;letter-spacing:.06em;color:${accent};border-bottom:1px solid #ddd;padding-bottom:3px;}
      .rb-item{margin-bottom:8px;}
      .rb-item-top{display:flex;justify-content:space-between;gap:12px;}
      .rb-item-sub{color:#444;font-size:10pt;}
      .rb-item-detail{font-size:10pt;}
      .rb-bullets{margin:4px 0 0 18px;padding:0;}
      .rb-bullets li{margin:2px 0;}
      .rb-skill-row{margin:3px 0;font-size:10.5pt;}
      .rb-modern{display:grid;grid-template-columns:32% 1fr;min-height:900px;}
      .rb-modern-side{background:${accent};color:#fff;padding:22px 16px;}
      .rb-modern-side h2{color:#fff;font-size:18pt;}
      .rb-modern-side .rb-headline,.rb-modern-side p,.rb-modern-side .rb-skill-row{color:rgba(255,255,255,.92);}
      .rb-modern-side h5{margin:14px 0 6px;text-transform:uppercase;letter-spacing:.08em;font-size:9pt;opacity:.85;}
      .rb-modern-main{padding:22px 18px;}
      .rb-modern-main .rb-sec h4{color:${accent};}
      @media print{body{padding:0;} .rb-modern{min-height:auto;}}
    </style></head><body><div class="rb-preview tpl-${tpl}">${content}</div>
    <script>window.onload=function(){window.print();}<\/script>
    </body></html>`);
  win.document.close();
}
window.printResume = printResume;

function initResumeBuilder() {
  if (RB_CONTROLS_BOUND) return;
  RB_CONTROLS_BOUND = true;
  document.getElementById("rb-save-btn")?.addEventListener("click", saveResumeBuilder);
  document.getElementById("rb-import-profile")?.addEventListener("click", importResumeFromProfile);
  document.getElementById("rb-sample-btn")?.addEventListener("click", applyBranchSample);
  document.getElementById("rb-gen-summary")?.addEventListener("click", generateResumeSummary);
  document.getElementById("rb-export-pdf")?.addEventListener("click", printResume);
  document.getElementById("rb-export-json")?.addEventListener("click", exportResumeJson);
  document.getElementById("rb-import-json")?.addEventListener("change", (e) => {
    importResumeJson(e.target.files[0]);
    e.target.value = "";
  });
  document.querySelectorAll("[data-rb-add]").forEach((btn) => {
    btn.addEventListener("click", () => addResumeEntry(btn.dataset.rbAdd));
  });
  document.getElementById("rb-add-skill-cat")?.addEventListener("click", () => addResumeEntry("skill"));
  RB_PERSONAL_IDS.forEach((id) => {
    document.getElementById(id)?.addEventListener("input", () => {
      renderResumePreview();
      updateResumeCompleteness();
    });
  });
}