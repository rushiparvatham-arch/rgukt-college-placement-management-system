"""Pro-level portal features (second advanced layer).

Student : profile strength, schedule + .ics calendar export, skill-gap analysis,
          mock-interview practice with history.
Company : pipeline analytics, side-by-side candidate comparison, bulk status
          updates, candidate messaging (in-app + optional email).
CDPC    : at-risk student detection + nudges, package analytics, drive clash
          detection, e-mail broadcast.
"""
import json
import re
import statistics
import threading
from datetime import datetime, date, timedelta

from flask import Blueprint, jsonify, request, session, Response, current_app

from app.extensions import db
from app.models import (
    User, StudentProfile, CompanyProfile, Drive, Application, Interview, Result,
    Notification, Offer, AuditLog, MockInterview,
)
from app.utils.email_utils import send_email, smtp_configured

pro_bp = Blueprint("pro", __name__)

APP_STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]


# ------------------------------------------------------------------ helpers
def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def require_role(role):
    user = current_user()
    if not user or user.role != role:
        return None, (jsonify({"error": f"{role.title()} access required."}), 401)
    return user, None


def audit(actor, action, entity_type, entity_id=None, details=None):
    db.session.add(AuditLog(actor_id=actor.id if actor else None, action=action, entity_type=entity_type,
                            entity_id=str(entity_id) if entity_id is not None else None,
                            details=json.dumps(details or {})))


def tokens(text):
    return [x.strip() for x in re.split(r"[,;/\n]", text or "") if x.strip()]


def parse_dt(text):
    """Parse '28 Aug 2026, 10:00 AM' / '15 Sep 2026' / '2026-09-15' -> datetime | None."""
    if not text:
        return None
    for fmt in ("%d %b %Y, %I:%M %p", "%d %b %Y %I:%M %p", "%d %b %Y", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d", "%d %B %Y"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_lpa(text):
    """'₹8 LPA' / '6.5 LPA' / '12' -> 8.0 (lakhs per annum) or None."""
    if not text:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", str(text).replace(",", ""))
    if not m:
        return None
    val = float(m.group(1))
    if val > 1000:          # looks like an absolute yearly amount
        val = val / 100000.0
    return val


def notify(user_id, message, link=None):
    db.session.add(Notification(user_id=user_id, message=message[:255], link=link))


def _email_async(app, jobs):
    """jobs: [(to, subject, text)]. Runs in a thread so the request returns fast."""
    def run():
        with app.app_context():
            for to, subject, text in jobs:
                ok, err = send_email(to, subject, text)
                if not ok:
                    app.logger.warning("Email to %s failed: %s", to, err)
    threading.Thread(target=run, daemon=True).start()


KNOWN_SKILLS = {
    "python": "Practise on HackerRank/LeetCode Easy-Medium; build one automation script.",
    "java": "Revisit OOP, collections and streams; solve 20 problems in Java.",
    "javascript": "Learn ES6+, async/await and DOM; build a small interactive app.",
    "react": "Build a CRUD app with hooks, routing and API calls.",
    "node": "Create a REST API with Express and connect it to a database.",
    "flask": "Build a REST API with auth and SQLAlchemy.",
    "django": "Complete the official polls tutorial, then add auth.",
    "sql": "Master JOINs, GROUP BY, subqueries and window functions.",
    "mysql": "Practise schema design, indexes and transactions.",
    "mongodb": "Model documents and use the aggregation pipeline.",
    "html": "Build a responsive, accessible landing page.",
    "css": "Practise Flexbox/Grid and responsive layouts.",
    "git": "Use branches, pull requests and resolve merge conflicts.",
    "aws": "Deploy a small app using EC2/S3; earn the Cloud Practitioner badge.",
    "docker": "Containerise one of your projects with a Dockerfile + compose.",
    "kubernetes": "Learn pods/deployments/services using minikube.",
    "c++": "Practise STL and pointers; solve DSA problems in C++.",
    "c": "Revisit pointers, memory management and structs.",
    "machine learning": "Complete an end-to-end scikit-learn project on a Kaggle dataset.",
    "data structures": "Solve arrays, linked lists, trees and graphs problems daily.",
    "algorithms": "Practise sorting, DP, greedy and graph traversal.",
    "excel": "Learn pivot tables, lookups and charts.",
    "power bi": "Build a dashboard from a public dataset.",
    "communication": "Do weekly mock HR rounds; record and review yourself.",
    "aptitude": "Practise 20 quant/logical questions daily.",
}
SKILL_ALIASES = {"cpp": "c++", "js": "javascript", "reactjs": "react", "node.js": "node", "nodejs": "node",
                 "ml": "machine learning", "dsa": "data structures", "postgres": "sql", "postgresql": "sql"}


def norm_skill(s):
    s = s.strip().lower()
    return SKILL_ALIASES.get(s, s)


def drive_required_skills(drive):
    text = f" {drive.role_title} {drive.description or ''} ".lower()
    found = []
    for sk in KNOWN_SKILLS:
        if re.search(r"(?<![a-z0-9+])" + re.escape(sk) + r"(?![a-z0-9+])", text):
            found.append(sk)
    for alias, canon in SKILL_ALIASES.items():
        if re.search(r"(?<![a-z0-9+])" + re.escape(alias) + r"(?![a-z0-9+])", text) and canon not in found:
            found.append(canon)
    return found


# ------------------------------------------------------------------ STUDENT
@pro_bp.route("/student/profile-strength", methods=["GET"])
def profile_strength():
    user, err = require_role("student")
    if err: return err
    p = user.student_profile
    checks = [
        ("Phone number added", bool(user.phone), 5, "Add your phone in Edit Profile."),
        ("Profile picture uploaded", bool(user.profile_picture), 5, "Upload a professional photo."),
        ("CGPA entered", bool(p and p.cgpa), 10, "Enter your latest CGPA."),
        ("10th & Intermediate marks", bool(p and p.tenth_percent and p.inter_percent), 10, "Fill in your 10th and Inter percentages."),
        ("At least 5 skills listed", bool(p and len(tokens(p.skills)) >= 5), 15, "List 5+ skills, comma separated."),
        ("Resume uploaded", bool(p and p.resume_filename), 15, "Upload your resume (PDF)."),
        ("ATS score 70+", bool(p and (p.ats_score or 0) >= 70), 15, "Use the AI Resume Analyzer tips to reach 70+."),
        ("LinkedIn added", bool(p and p.linkedin), 5, "Add your LinkedIn URL."),
        ("GitHub added", bool(p and p.github), 5, "Add your GitHub URL."),
        ("Applied to a drive", Application.query.filter_by(student_id=user.id).count() > 0, 10, "Apply to at least one drive."),
        ("Practised a mock interview", MockInterview.query.filter_by(student_id=user.id).count() > 0, 5, "Complete one mock interview."),
    ]
    total = sum(w for _, ok, w, _ in checks if ok)
    return jsonify({"score": total, "items": [{"label": l, "done": ok, "weight": w, "tip": t} for l, ok, w, t in checks]})


def _student_events(user):
    events = []
    apps = Application.query.filter_by(student_id=user.id).all()
    for a in apps:
        for iv in a.interviews:
            if iv.status == "Cancelled":
                continue
            dt = parse_dt(iv.scheduled_at)
            events.append({"type": "interview", "title": f"{iv.round_name} - {a.drive.company.company_profile.company_name if a.drive.company.company_profile else ''}",
                           "role": a.drive.role_title, "when": iv.scheduled_at, "ts": dt.isoformat() if dt else None,
                           "where": iv.venue_or_link or iv.mode, "status": iv.status, "has_time": bool(dt and (dt.hour or dt.minute))})
        d = a.drive
        dd = parse_dt(d.drive_date)
        if dd:
            events.append({"type": "drive", "title": f"Drive: {d.role_title}", "role": d.role_title, "when": d.drive_date,
                           "ts": dd.isoformat(), "where": d.location, "status": a.status, "has_time": False})
    applied = {a.drive_id for a in apps}
    for d in Drive.query.filter(Drive.status.in_(["Upcoming", "Ongoing"])).all():
        dl = parse_dt(d.application_deadline)
        if dl and d.id not in applied:
            events.append({"type": "deadline", "title": f"Apply by: {d.role_title}", "role": d.role_title, "when": d.application_deadline,
                           "ts": dl.isoformat(), "where": d.location, "status": "Open", "has_time": False})
    events.sort(key=lambda e: e["ts"] or "9999")
    return events


@pro_bp.route("/student/schedule", methods=["GET"])
def student_schedule():
    user, err = require_role("student")
    if err: return err
    events = _student_events(user)
    now = datetime.now().isoformat()
    for e in events:
        e["past"] = bool(e["ts"] and e["ts"] < now[:10])
    return jsonify({"events": events})


@pro_bp.route("/student/schedule.ics", methods=["GET"])
def student_schedule_ics():
    user, err = require_role("student")
    if err: return err

    def esc(t):
        t = (t or "").replace(chr(92), chr(92) * 2)
        for ch in (";", ","):
            t = t.replace(ch, chr(92) + ch)
        return t.replace("\n", chr(92) + "n")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//RGUKT Ongole CDPC//Placement Portal//EN", "CALSCALE:GREGORIAN"]
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for i, e in enumerate(_student_events(user)):
        if not e["ts"]:
            continue
        dt = datetime.fromisoformat(e["ts"])
        lines += ["BEGIN:VEVENT", f"UID:rgukt-{user.id}-{i}-{dt:%Y%m%d%H%M}@placement", f"DTSTAMP:{stamp}"]
        if e["has_time"]:
            lines += [f"DTSTART:{dt:%Y%m%dT%H%M%S}", f"DTEND:{dt + timedelta(hours=1):%Y%m%dT%H%M%S}"]
        else:
            lines += [f"DTSTART;VALUE=DATE:{dt:%Y%m%d}", f"DTEND;VALUE=DATE:{dt + timedelta(days=1):%Y%m%d}"]
        lines += [f"SUMMARY:{esc(e['title'])}", f"LOCATION:{esc(e['where'])}", f"DESCRIPTION:{esc(e['role'])}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(lines) + "\r\n", mimetype="text/calendar",
                    headers={"Content-Disposition": "attachment; filename=placement-schedule.ics"})


@pro_bp.route("/student/skill-gap", methods=["GET"])
def skill_gap():
    user, err = require_role("student")
    if err: return err
    p = user.student_profile
    mine = {norm_skill(s) for s in tokens(p.skills if p else "")}
    drive_id = request.args.get("drive_id", type=int)
    drives = [Drive.query.get(drive_id)] if drive_id else Drive.query.filter(Drive.status.in_(["Upcoming", "Ongoing"])).all()
    drives = [d for d in drives if d]
    out, missing_count = [], {}
    for d in drives:
        req = drive_required_skills(d)
        have = [s for s in req if s in mine]
        miss = [s for s in req if s not in mine]
        for s in miss:
            missing_count[s] = missing_count.get(s, 0) + 1
        pct = round(len(have) / len(req) * 100) if req else 100
        out.append({"drive": d.to_dict(), "required": req, "have": have, "missing": miss, "match_pct": pct})
    out.sort(key=lambda x: -x["match_pct"])
    top = sorted(missing_count.items(), key=lambda kv: -kv[1])[:6]
    plan = [{"skill": s, "demand": c, "action": KNOWN_SKILLS.get(s, "Search for a beginner course and build a mini project.")} for s, c in top]
    return jsonify({"my_skills": sorted(mine), "drives": out[:20], "learning_plan": plan})


MOCK_BANK = {
    "HR": [
        ("Tell me about yourself.", "Introduction"), ("Why do you want to work for our company?", "Motivation"),
        ("What are your strengths and weaknesses?", "Self-awareness"), ("Describe a time you worked in a team and faced a conflict.", "Teamwork"),
        ("Where do you see yourself in five years?", "Goals"), ("Tell me about a failure and what you learned.", "Resilience"),
        ("Are you willing to relocate or work in shifts?", "Flexibility"), ("Why should we hire you?", "Pitch"),
    ],
    "Python": [
        ("Difference between list, tuple, set and dict?", "Data types"), ("What are decorators and generators?", "Advanced Python"),
        ("Explain the GIL.", "Concurrency"), ("What is the difference between deep and shallow copy?", "Memory"),
        ("How does exception handling work (try/except/finally)?", "Errors"), ("Explain list comprehension with an example.", "Syntax"),
        ("What are *args and **kwargs?", "Functions"), ("How is memory managed in Python?", "Internals"),
    ],
    "SQL": [
        ("Explain INNER, LEFT and FULL joins.", "Joins"), ("What is normalisation? Explain 1NF-3NF.", "Design"),
        ("Difference between WHERE and HAVING?", "Aggregation"), ("What are indexes and when do they hurt?", "Performance"),
        ("Find the second highest salary.", "Queries"), ("Explain ACID properties.", "Transactions"),
        ("What is a window function? Give an example.", "Advanced SQL"), ("Primary key vs unique key vs foreign key?", "Keys"),
    ],
    "Web Development": [
        ("Explain the CSS box model.", "CSS"), ("var vs let vs const in JavaScript?", "JavaScript"),
        ("What is the event loop?", "JavaScript"), ("Explain REST and common HTTP status codes.", "APIs"),
        ("What is CORS and why is it needed?", "Security"), ("How do cookies, sessions and JWT differ?", "Auth"),
        ("What is the virtual DOM?", "React"), ("How do you make a page responsive and accessible?", "UX"),
    ],
    "DSA": [
        ("Array vs linked list - trade-offs?", "Basics"), ("Explain Big-O with examples.", "Complexity"),
        ("How would you detect a cycle in a linked list?", "Linked lists"), ("BFS vs DFS - when to use which?", "Graphs"),
        ("Explain how a hash map works internally.", "Hashing"), ("Reverse a string / check palindrome - approach?", "Strings"),
        ("What is dynamic programming? Example.", "DP"), ("Explain quicksort and its worst case.", "Sorting"),
    ],
}


@pro_bp.route("/student/mock/questions", methods=["GET"])
def mock_questions():
    user, err = require_role("student")
    if err: return err
    track = request.args.get("track", "HR")
    if track not in MOCK_BANK:
        return jsonify({"error": "Unknown track."}), 400
    import random
    qs = MOCK_BANK[track][:]
    random.shuffle(qs)
    return jsonify({"track": track, "tracks": list(MOCK_BANK), "questions": [{"q": q, "topic": t} for q, t in qs[:6]]})


@pro_bp.route("/student/mock/sessions", methods=["GET", "POST"])
def mock_sessions():
    user, err = require_role("student")
    if err: return err
    if request.method == "POST":
        data = request.get_json(force=True)
        track = data.get("track")
        answers = data.get("answers") or []
        if track not in MOCK_BANK or not answers:
            return jsonify({"error": "Invalid session."}), 400
        ratings = [min(5, max(1, int(a.get("rating", 3)))) for a in answers]
        weak = sorted({a.get("topic", "") for a, r in zip(answers, ratings) if r <= 2 and a.get("topic")})
        row = MockInterview(student_id=user.id, track=track, questions=len(ratings),
                            avg_rating=sum(ratings) / len(ratings), duration_sec=int(data.get("duration_sec") or 0),
                            weak_topics=", ".join(weak)[:255])
        db.session.add(row)
        db.session.commit()
        return jsonify({"session": row.to_dict()}), 201
    rows = MockInterview.query.filter_by(student_id=user.id).order_by(MockInterview.created_at.desc()).limit(30).all()
    return jsonify({"sessions": [r.to_dict() for r in rows]})


# ------------------------------------------------------------------ COMPANY
@pro_bp.route("/company/pipeline", methods=["GET"])
def company_pipeline():
    user, err = require_role("company")
    if err: return err
    drives = Drive.query.filter_by(company_id=user.id).all()
    out, totals = [], {s: 0 for s in APP_STATUSES}
    for d in drives:
        counts = {s: 0 for s in APP_STATUSES}
        for a in d.applications:
            counts[a.status] = counts.get(a.status, 0) + 1
            totals[a.status] = totals.get(a.status, 0) + 1
        total = len(d.applications)
        out.append({"drive_id": d.id, "role_title": d.role_title, "status": d.status, "total": total, "counts": counts,
                    "conversion": round(counts["Selected"] / total * 100, 1) if total else 0})
    return jsonify({"drives": out, "totals": totals})


@pro_bp.route("/company/compare", methods=["GET"])
def company_compare():
    user, err = require_role("company")
    if err: return err
    ids = [int(x) for x in (request.args.get("ids") or "").split(",") if x.strip().isdigit()][:4]
    if len(ids) < 2:
        return jsonify({"error": "Select at least two candidates to compare."}), 400
    rows = []
    for sid in ids:
        u = User.query.get(sid)
        if not u or u.role != "student" or not u.student_profile:
            continue
        p = u.student_profile
        rows.append({"id": u.id, "name": u.name, "roll_number": p.roll_number, "branch": p.branch, "cgpa": p.cgpa,
                     "backlogs": p.backlogs, "ats_score": p.ats_score, "skills": tokens(p.skills),
                     "tenth": p.tenth_percent, "inter": p.inter_percent, "github": p.github, "linkedin": p.linkedin,
                     "mock_avg": round(sum(m.avg_rating for m in MockInterview.query.filter_by(student_id=u.id)) /
                                       max(1, MockInterview.query.filter_by(student_id=u.id).count()), 2)})
    for key in ("cgpa", "ats_score"):
        best = max((r[key] or 0) for r in rows) if rows else 0
        for r in rows:
            r[f"best_{key}"] = bool(rows) and (r[key] or 0) == best and best > 0
    return jsonify({"candidates": rows})


@pro_bp.route("/company/applications/bulk", methods=["POST"])
def bulk_status():
    user, err = require_role("company")
    if err: return err
    data = request.get_json(force=True)
    status = data.get("status")
    ids = data.get("application_ids") or []
    if status not in APP_STATUSES or not ids:
        return jsonify({"error": "Choose applications and a valid status."}), 400
    updated = 0
    for app_row in Application.query.filter(Application.id.in_(ids)).all():
        if app_row.drive.company_id != user.id:
            continue  # never touch another company's applicants
        app_row.status = status
        notify(app_row.student_id, f"Your application for {app_row.drive.role_title} is now '{status}'.")
        updated += 1
    audit(user, "bulk_status_update", "application", None, {"status": status, "count": updated})
    db.session.commit()
    return jsonify({"updated": updated, "message": f"{updated} application(s) moved to {status}."})


@pro_bp.route("/company/message", methods=["POST"])
def company_message():
    user, err = require_role("company")
    if err: return err
    data = request.get_json(force=True)
    msg = (data.get("message") or "").strip()
    ids = data.get("student_ids") or []
    if not msg or not ids:
        return jsonify({"error": "Write a message and choose at least one candidate."}), 400
    name = user.company_profile.company_name if user.company_profile else user.name
    # Only message students who have a relationship with this company (applicant or shortlisted)
    from app.models import CompanyShortlist
    allowed = {a.student_id for d in Drive.query.filter_by(company_id=user.id) for a in d.applications}
    allowed |= {s.student_id for s in CompanyShortlist.query.filter_by(company_id=user.id)}
    jobs, sent = [], 0
    for sid in ids:
        if sid not in allowed:
            continue
        stu = User.query.get(sid)
        if not stu:
            continue
        notify(sid, f"Message from {name}: {msg}")
        sent += 1
        if data.get("send_email") and smtp_configured():
            jobs.append((stu.email, f"Message from {name} (RGUKT Placement Portal)", f"Hello {stu.name},\n\n{msg}\n\n- {name}"))
    audit(user, "message_candidates", "student", None, {"count": sent})
    db.session.commit()
    if jobs:
        _email_async(current_app._get_current_object(), jobs)
    return jsonify({"sent": sent, "emailed": len(jobs), "message": f"Message delivered to {sent} candidate(s)."})


# ------------------------------------------------------------------ CDPC
def _risk(p):
    reasons = []
    apps = Application.query.filter_by(student_id=p.user_id).count()
    if p.placed:
        return 0, []
    if apps == 0: reasons.append("No applications yet")
    if not p.resume_filename: reasons.append("No resume uploaded")
    if (p.ats_score or 0) < 50: reasons.append("Low ATS score")
    if len(tokens(p.skills)) < 3: reasons.append("Few skills listed")
    if (p.backlogs or 0) > 0: reasons.append("Active backlogs")
    if (p.cgpa or 0) and p.cgpa < 6.5: reasons.append("CGPA below 6.5")
    if apps >= 3 and Result.query.join(Application).filter(Application.student_id == p.user_id, Result.outcome == "Rejected").count() >= 3:
        reasons.append("Multiple rejections")
    return len(reasons), reasons


@pro_bp.route("/cdpc/at-risk", methods=["GET"])
def at_risk():
    user, err = require_role("cdpc")
    if err: return err
    out = []
    for p in StudentProfile.query.all():
        score, reasons = _risk(p)
        if score >= 2:
            out.append({"id": p.user_id, "name": p.user.name, "email": p.user.email, "roll_number": p.roll_number,
                        "branch": p.branch, "cgpa": p.cgpa, "ats_score": p.ats_score, "risk": score,
                        "level": "High" if score >= 4 else "Medium", "reasons": reasons})
    out.sort(key=lambda x: -x["risk"])
    return jsonify({"students": out[:200], "total": len(out)})


@pro_bp.route("/cdpc/nudge", methods=["POST"])
def nudge():
    user, err = require_role("cdpc")
    if err: return err
    data = request.get_json(force=True)
    ids = data.get("student_ids") or []
    msg = (data.get("message") or "").strip() or "Your placement profile needs attention. Please complete your profile, upload your resume and apply to open drives."
    jobs, n = [], 0
    for sid in ids:
        u = User.query.get(sid)
        if not u or u.role != "student":
            continue
        notify(sid, msg)
        n += 1
        if data.get("send_email") and smtp_configured():
            jobs.append((u.email, "Action needed: your placement profile", f"Hello {u.name},\n\n{msg}\n\n- RGUKT Ongole CDPC"))
    audit(user, "nudge_students", "student", None, {"count": n})
    db.session.commit()
    if jobs:
        _email_async(current_app._get_current_object(), jobs)
    return jsonify({"sent": n, "emailed": len(jobs), "message": f"Nudge sent to {n} student(s)."})


@pro_bp.route("/cdpc/package-analytics", methods=["GET"])
def package_analytics():
    user, err = require_role("cdpc")
    if err: return err
    pkgs, by_branch, by_company = [], {}, {}
    rows = Result.query.filter_by(outcome="Selected").all()
    for r in rows:
        v = parse_lpa(r.package_offered)
        if v is None:
            continue
        a = r.application
        branch = a.student.student_profile.branch if a.student and a.student.student_profile else "Unknown"
        comp = a.drive.company.company_profile.company_name if a.drive.company.company_profile else "Unknown"
        pkgs.append(v)
        by_branch.setdefault(branch, []).append(v)
        by_company.setdefault(comp, []).append(v)
    for o in Offer.query.filter_by(status="Accepted").all():
        v = parse_lpa(o.package_offered)
        if v is None:
            continue
        sp = o.student.student_profile if o.student else None
        pkgs.append(v)
        by_branch.setdefault(sp.branch if sp else "Unknown", []).append(v)
        by_company.setdefault(o.company.company_profile.company_name if o.company.company_profile else "Unknown", []).append(v)

    def summ(d):
        return sorted([{"name": k, "count": len(v), "avg": round(sum(v) / len(v), 2), "max": max(v)} for k, v in d.items()], key=lambda x: -x["avg"])
    buckets = {"< 4": 0, "4-6": 0, "6-10": 0, "10-20": 0, "20+": 0}
    for v in pkgs:
        buckets["< 4" if v < 4 else "4-6" if v < 6 else "6-10" if v < 10 else "10-20" if v < 20 else "20+"] += 1
    return jsonify({
        "count": len(pkgs),
        "highest": max(pkgs) if pkgs else 0, "average": round(sum(pkgs) / len(pkgs), 2) if pkgs else 0,
        "median": round(statistics.median(pkgs), 2) if pkgs else 0, "lowest": min(pkgs) if pkgs else 0,
        "buckets": buckets, "by_branch": summ(by_branch), "by_company": summ(by_company)[:10],
    })


@pro_bp.route("/cdpc/drive-clashes", methods=["GET"])
def drive_clashes():
    user, err = require_role("cdpc")
    if err: return err
    by_date = {}
    for d in Drive.query.filter(Drive.status.in_(["Upcoming", "Ongoing"])).all():
        dt = parse_dt(d.drive_date)
        if dt:
            by_date.setdefault(dt.date().isoformat(), []).append(d)
    clashes = [{"date": k, "drives": [{"id": d.id, "role_title": d.role_title, "company": d.company.company_profile.company_name if d.company.company_profile else ""} for d in v]}
               for k, v in sorted(by_date.items()) if len(v) > 1]
    # students eligible & applied to >1 drive on the same day
    conflicts = []
    for c in clashes:
        ids = [x["id"] for x in c["drives"]]
        counts = {}
        for a in Application.query.filter(Application.drive_id.in_(ids)).all():
            counts.setdefault(a.student_id, []).append(a.drive_id)
        both = [sid for sid, lst in counts.items() if len(lst) > 1]
        conflicts.append({**c, "students_affected": len(both)})
    return jsonify({"clashes": conflicts})


@pro_bp.route("/cdpc/email-broadcast", methods=["POST"])
def email_broadcast():
    user, err = require_role("cdpc")
    if err: return err
    if not smtp_configured():
        return jsonify({"error": "Email is not configured on the server. Set SMTP_USER and SMTP_PASSWORD in .env first."}), 400
    data = request.get_json(force=True)
    subject = (data.get("subject") or "").strip()
    body = (data.get("message") or "").strip()
    audience = data.get("audience", "students")
    branch = data.get("branch")
    if not subject or not body:
        return jsonify({"error": "Subject and message are required."}), 400
    q = User.query.filter(User.is_active == True)  # noqa: E712
    if audience == "students":
        q = q.filter_by(role="student")
    elif audience == "companies":
        q = q.filter_by(role="company")
    users = q.all()
    if audience == "students" and branch and branch != "All":
        users = [u for u in users if u.student_profile and u.student_profile.branch == branch]
    users = users[:500]
    jobs = [(u.email, subject, f"Hello {u.name},\n\n{body}\n\n- RGUKT Ongole CDPC") for u in users]
    for u in users:
        notify(u.id, f"{subject}: {body}")
    audit(user, "email_broadcast", "broadcast", None, {"audience": audience, "branch": branch, "count": len(users)})
    db.session.commit()
    _email_async(current_app._get_current_object(), jobs)
    return jsonify({"queued": len(jobs), "message": f"Email queued for {len(jobs)} recipient(s)."})