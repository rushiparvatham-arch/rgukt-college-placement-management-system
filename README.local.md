# RGUKT Ongole — CDPC Placement Management System

A full-stack placement management system built for **RGUKT Ongole's Career Development
& Placement Cell (CDPC)**. It supports three distinct dashboards — **Student**,
**CDPC / Administrator**, and **Company** — behind a single shared login page, with a
persistent SQLite database, session-based auth, and a dark, responsive UI.

> Built as an academic project. Replace `static/images/rgukt-logo.svg` with the
> official RGUKT Ongole logo file (same filename) if you have the rights to use it —
> a neutral placeholder logo is included by default to avoid any copyright issues.

---

## ✨ Features

### Student Dashboard
- **Student section:** Companies, Placement Drives (with live eligibility checks),
  Applications tracker, Interviews, Results, Resume Creator (live preview + print/PDF),
  **Skill Assessment** (Python, SQL, Web Dev, DSA, Communication quizzes — auto-scored
  into Beginner / Intermediate / Advanced proficiency levels).
- **Resources section:** Aptitude Test (quant/logical/verbal sets with auto-grading),
  AI Resume Analyzer, ATS Scoring, Help, About, Logout (with confirmation dialog).
- Upload a resume (PDF) and get an instant **rule-based AI ATS score** (0–100), a
  section-completeness checklist, matched/missing keywords, and improvement tips —
  fully offline, no external API key required.

### CDPC / Administrator Dashboard
- Student Management (filter by branch/placement status, mark placed, CSV export).
- Company Management (approve companies, view onboarded recruiters).
- Drive Management (create/edit/delete drives with eligibility rules).
- Application tracking + status pipeline (Applied → Shortlisted → Interview → Selected/Rejected).
- Interview Management (schedule rounds, mark completed with feedback).
- Results publishing (Selected / Rejected / Waitlisted with package & remarks).
- **Send Notifications** — broadcast an announcement to all students, all companies, a
  specific branch, or everyone at once, with a "Recently Sent" audit log.
- Analytics & Reports: branch-wise placement %, application funnel, top recruiters,
  drive status distribution.

### Company Dashboard
- Post and manage placement drives.
- Review applicants per drive and update their status.
- **Browse Students** — search the entire eligible student pool by CGPA/branch to
  simplify shortlisting, view resumes directly.

### Authentication
- Email/password login and registration, shared across all three roles.
- **Email verification via OTP** — registering by email requires entering a 6-digit
  code sent to that address before the account is created. If SMTP isn't configured,
  the code is printed to the server console so registration still works for local
  testing/grading (see Setup below).
- **Continue with Google** — real OAuth 2.0 sign-in (via Authlib), not a fake button.
  Requires your own Google Cloud OAuth credentials (see Setup below) — Google email
  addresses are already verified, so accounts created this way skip the OTP step.
- Password visibility toggle, clear error states, demo-credential autofill.

### Shared across all dashboards
- Dark theme, fully responsive (desktop / tablet / mobile) sidebar + navbar layout.
- Working **search bar**, **notifications bell** (with unread badge), **settings**
  menu, and a clean, compact **profile dropdown** (avatar, name, email, role — all
  properly truncated so long names/emails never overflow) on every dashboard.
- **Edit Profile** modal — changes are persisted to the database and reload on next login.
- **Profile picture upload** — works identically for all three roles (Student, CDPC,
  Company) from the Edit Profile modal. Accepts JPG/PNG/WEBP up to 2 MB, shows live
  in the navbar avatar and the profile dropdown, and can be removed to fall back to
  initials. Old files are cleaned up automatically when a new picture is uploaded.
- Change password flow (Google-authenticated accounts are correctly blocked from this,
  since they have no password).
- RGUKT Ongole branding (sidebar, login, landing page).

---

## 🛠 Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-CORS, Authlib (Google OAuth)
- **Database:** SQLite (auto-created, auto-seeded with demo data on first run)
- **AI Resume Analyzer:** Custom rule-based NLP scoring engine (`app/utils/ai_resume_analyzer.py`)
  using `pdfplumber` for PDF text extraction — no external API keys needed.
- **Email OTP:** `smtplib` (Python standard library) with a console-log fallback for local dev.
- **Frontend:** HTML5, CSS3 (custom dark design system), Vanilla JavaScript (no build step)
- **Auth:** Server-side sessions (Flask `session`), password hashing via Werkzeug, OAuth 2.0 via Authlib

---

## 📁 Project Structure

```
rgukt-placement-system/
├── app/
│   ├── __init__.py            # App factory, blueprint registration, Google OAuth client, error handlers
│   ├── config.py               # Config (DB path, SMTP, Google OAuth, upload folder, secret key)
│   ├── extensions.py           # SQLAlchemy instance + Authlib OAuth instance
│   ├── models.py                # All DB models
│   ├── seed.py                  # Demo data seeding (runs once, on empty DB)
│   ├── routes/
│   │   ├── auth.py              # Register/OTP/login/logout/Google OAuth/profile
│   │   ├── student.py           # Student dashboard APIs
│   │   ├── cdpc.py              # CDPC/Admin dashboard APIs (incl. Send Notifications)
│   │   ├── company.py           # Company dashboard APIs
│   │   ├── common.py            # Notifications, search, resume file serving
│   │   └── pages.py             # HTML page routes
│   └── utils/
│       ├── ai_resume_analyzer.py  # Rule-based AI ATS scoring engine
│       └── email_utils.py         # OTP generation + SMTP sending (with console fallback)
├── templates/
│   ├── landing.html             # Role-selection landing page (Log In / Sign Up)
│   ├── login.html               # Shared login/register page (Google + OTP flow)
│   ├── student_dashboard.html
│   ├── cdpc_dashboard.html
│   ├── company_dashboard.html
│   └── partials/                # Shared Jinja includes (DRY, used by all 3 dashboards)
│       ├── head_common.html         # Shared <head> tags (fonts, css, favicon)
│       ├── notification_dropdown.html
│       └── change_password_modal.html
├── static/
│   ├── css/ (main.css, dashboard.css, landing.css)
│   ├── js/  (common.js, landing.js, login.js, student.js, cdpc.js, company.js)
│   └── images/rgukt-logo.svg
├── uploads/
│   ├── resumes/                  # Uploaded resume PDFs stored here
│   └── profile_pictures/         # Uploaded profile pictures stored here
├── instance/                     # SQLite DB file created here at runtime
├── requirements.txt
├── run.py                        # Entry point
└── README.md
```

---

## 🚀 Setup & Run

> ### ⚠️ Upgrading from an earlier version? Delete your old database first.
> This version adds new columns to the `users` table (for Google Sign-In, email
> verification, and profile pictures) and new tables (for email OTPs and CDPC
> notification broadcasts). SQLite does **not** automatically add columns to an
> existing database file. If you run this version against an `instance/placement.db`
> created by an older version of this project, **it will crash with a `no such
> column` error.**
>
> Fix: delete the old database file (or extract this zip into a brand-new folder)
> before running it — it will be recreated automatically with the correct schema
> and reseeded with demo data:
> ```bash
> rm instance/placement.db
> python run.py
> ```

```bash
# 1. Clone your repo / unzip the project, then cd into it
cd rgukt-placement-system

# 2. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python run.py
```

The app starts at **http://localhost:5000**. On first run, it automatically creates
the SQLite database and seeds it with demo companies, students, drives, and aptitude
tests — no manual DB setup needed.

### Setting up Email OTP verification (optional but recommended)

Without any setup, registering by email still works — the 6-digit verification code
is printed to the terminal running `run.py` (clearly labelled `[DEV MODE]`) so you can
copy it into the OTP field yourself. To have it actually emailed, set these environment
variables before running the app (example uses Gmail with an
[App Password](https://myaccount.google.com/apppasswords), not your normal password):

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=youraddress@gmail.com
export SMTP_PASSWORD=your16digitapppassword
export SMTP_FROM=youraddress@gmail.com
```

(On Windows, use `set VAR=value` instead of `export VAR=value`, or add these to a
`.env` file — `python-dotenv` is already included in requirements.txt.)

### Setting up "Continue with Google" (optional)

Google Sign-In requires OAuth credentials that **only you can create** — no one else
can generate these for your app, this is fundamental to how OAuth works. Without
them, the Google button shows a clear "not configured" message instead of pretending
to work.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a project (or use an existing one) → **Create Credentials → OAuth client ID**.
3. Application type: **Web application**.
4. Under **Authorized redirect URIs**, add exactly:
   `http://localhost:5000/api/auth/google/callback`
   (update the host/port if you deploy elsewhere).
5. Copy the generated **Client ID** and **Client Secret**, then set:
   ```bash
   export GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   export GOOGLE_CLIENT_SECRET=your-client-secret
   ```
6. Restart `python run.py`. The "Continue with Google" button on `/login` will now work.

If a user's email is already registered under a different role (e.g. as a Student)
and they try Google Sign-In while the "Company" role pill is selected, they'll get a
clear error rather than a silently-wrong login — pick the correct role and try again.

### If you see `ModuleNotFoundError: No module named 'authlib'`

This means `pip install -r requirements.txt` was run before Authlib was added to
that file, or hasn't been re-run since. Fix: `pip install -r requirements.txt`
(or `pip install Authlib`) and restart. Separately from that immediate fix, the
app itself no longer crashes if Authlib is missing — `app/extensions.py` imports
it defensively and disables Google Sign-In gracefully (showing "not configured"
instead of erroring) if it isn't installed, so a missing *optional* dependency
can never take down the whole app again.

### If you see repeated "Failed to fetch" errors

This was a real bug in an earlier version, now fixed. Cause: the dashboards fire
several API calls in parallel on every page load (profile, notifications, stats,
lists), but Flask's default dev server only handles **one request at a time**.
Enough simultaneous requests would cause the OS to refuse new connections outright —
which browsers report as `Failed to fetch`. Fixed by:
- `run.py` now runs with `threaded=True`.
- `app/config.py` adds `check_same_thread: False` for SQLite (required once the
  server is threaded).
- `static/js/common.js`'s `apiRequest()` now retries once automatically on a
  genuine network-level failure before showing an error.
- A global Flask error handler now returns clean JSON for any unexpected server
  error on `/api/*` routes instead of leaking a raw Python traceback.

If you still see this after pulling the latest version, make sure you're running
`python run.py` (not an old cached process) and that port 5000 isn't already in
use by another instance.

---

## 🔑 Demo Login Credentials

| Role | Email | Password |
|---|---|---|
| Student | `n200001@rguktong.ac.in` | `student123` |
| Student | `n200002@rguktong.ac.in` | `student123` |
| CDPC / Admin | `cdpc@rguktong.ac.in` | `cdpc12345` |
| Company | `technovasolutions@company.example.com` | `company123` |

The login page also has an **"Autofill demo credentials"** button per role, and you
can register brand-new accounts from the same page (Register tab).

---

## 📝 Notes for Submission / Viva

- All data (users, drives, applications, interviews, results, resumes, notifications)
  is persisted in **SQLite** (`instance/placement.db`) — nothing is hardcoded in the
  frontend; every dashboard view is populated live via REST API calls (`/api/...`).
- The **AI Resume Analyzer / ATS Scoring** feature is a genuine rule-based NLP engine
  (structural section detection + keyword density + action-verb analysis + length
  heuristics) — it runs fully offline so the project works without any internet
  connection or API key, which is ideal for demos and grading.
- Profile edits made by any user role are written back to the database immediately,
  so updated details persist across logins/sessions.
- To reset all demo data, simply delete `instance/placement.db` and restart the app —
  it will reseed automatically.
- The current logo (`static/images/rgukt-logo.svg`) is an original crest-style placeholder
  built for this project — it avoids reproducing any trademarked institutional asset. To
  use the real RGUKT Ongole logo instead: download it from
  `https://rguktong.ac.in/img/rguktlogo.png`, save it as `static/images/rgukt-logo.png`,
  then do a find-and-replace of `rgukt-logo.svg` → `rgukt-logo.png` across the five HTML
  templates (`landing.html`, `login.html`, and the three dashboards).
- A `DESIGN.md` supplied for this project was actually a *meta-prompt* (instructions for
  an AI assistant) rather than a concrete visual spec — it contains no color values,
  font names, or spacing scale. Its qualitative rules were still applied: avoid excessive
  gradients/glassmorphism/animation, prioritize clarity and functionality, keep a
  consistent icon system, non-color-only status indicators, and role-appropriate
  (not identical) dashboard layouts.
- Per DESIGN.md's request for a clean file structure, the CSS is already split by
  concern (`main.css` for shared tokens/components, `dashboard.css` for the app
  shell, `landing.css` for the public pages), and the three dashboard templates now
  share three Jinja partials (`templates/partials/`) instead of duplicating that
  markup: the `<head>` tags, the notification dropdown, and the change-password
  modal. These were chosen specifically because they were verified **byte-for-byte
  identical** (or identical once whitespace-only formatting was normalized) across
  all three dashboards before extraction — the sidebar and edit-profile modal were
  deliberately left inline per-page since their content genuinely differs by role,
  and forcing them into a shared partial would add conditional complexity without
  removing real duplication. Since this environment can't run the live Flask
  server, the refactor was verified by literally substituting each `{% include %}`
  with its target file's content and re-running the full check (HTML tag balance,
  every `id` reference, every `onclick` handler, duplicate-ID detection) against
  that simulated output — all clean.
- **CDPC → Send Notifications** creates one real `Notification` row per matching
  recipient (same mechanism already used when a drive is created) plus one
  `NotificationBroadcast` audit row for the "Recently Sent" log — it does not use
  placeholder/static data.
- **Google Sign-In** and **Email OTP verification** are both real, complete
  implementations, not mockups — see the Setup section above for the credentials
  each one needs from you to actually activate. Until configured: OTP falls back to
  a console-printed code (fully functional for local testing), and the Google
  button shows an honest "not configured" message rather than pretending to work.

---

## 📄 License

Academic project — free to use, modify, and submit for coursework.
