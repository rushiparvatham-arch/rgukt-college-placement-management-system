import os
import json
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import (
    User, StudentProfile, Drive, Application, Interview, Result,
    Notification, AptitudeTest, AptitudeResult, CompanyProfile, compute_skill_level,
)
from app.utils.ai_resume_analyzer import extract_text_from_pdf, analyze_resume, extract_skills

student_bp = Blueprint("student", __name__)


def require_student():
    uid = session.get("user_id")
    if not uid or session.get("role") != "student":
        return None, (jsonify({"error": "Student login required."}), 401)
    user = User.query.get(uid)
    if not user:
        return None, (jsonify({"error": "Student login required."}), 401)
    return user, None


def is_eligible(drive, profile):
    if not profile:
        return False
    if profile.cgpa < drive.min_cgpa:
        return False
    if profile.backlogs > drive.max_backlogs:
        return False
    if drive.eligible_branches and drive.eligible_branches != "All Branches":
        allowed = [b.strip().lower() for b in drive.eligible_branches.split(",")]
        if profile.branch.lower() not in allowed:
            return False
    return True


@student_bp.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    user, err = require_student()
    if err:
        return err
    profile = user.student_profile
    applications = Application.query.filter_by(student_id=user.id).all()
    interviews_count = Interview.query.join(Application).filter(
        Application.student_id == user.id, Interview.status == "Scheduled"
    ).count()
    selected = [a for a in applications if a.status == "Selected"]
    open_drives = Drive.query.filter(Drive.status.in_(["Upcoming", "Ongoing"])).count()

    return jsonify({
        "stats": {
            "applications_count": len(applications),
            "interviews_scheduled": interviews_count,
            "offers_received": len(selected),
            "open_drives": open_drives,
            "ats_score": profile.ats_score if profile else 0,
            "profile_complete": bool(profile and profile.cgpa and profile.skills and profile.resume_filename),
        }
    })


@student_bp.route("/companies", methods=["GET"])
def list_companies():
    user, err = require_student()
    if err:
        return err
    companies = CompanyProfile.query.filter_by(is_approved=True).all()
    result = []
    for c in companies:
        active_drives = Drive.query.filter_by(company_id=c.user_id).filter(Drive.status.in_(["Upcoming", "Ongoing"])).count()
        result.append({
            "id": c.user_id,
            "company_name": c.company_name,
            "industry": c.industry,
            "website": c.website,
            "about": c.about,
            "active_drives": active_drives,
        })
    return jsonify({"companies": result})


@student_bp.route("/drives", methods=["GET"])
def list_drives():
    user, err = require_student()
    if err:
        return err
    profile = user.student_profile
    drives = Drive.query.order_by(Drive.created_at.desc()).all()
    applied_ids = {a.drive_id for a in Application.query.filter_by(student_id=user.id).all()}
    result = []
    for d in drives:
        item = d.to_dict()
        item["eligible"] = is_eligible(d, profile)
        item["already_applied"] = d.id in applied_ids
        result.append(item)
    return jsonify({"drives": result})


@student_bp.route("/apply/<int:drive_id>", methods=["POST"])
def apply_to_drive(drive_id):
    user, err = require_student()
    if err:
        return err
    profile = user.student_profile
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found."}), 404
    if drive.status == "Closed":
        return jsonify({"error": "Applications for this drive are closed."}), 400
    if not is_eligible(drive, profile):
        return jsonify({"error": "You do not meet the eligibility criteria for this drive."}), 400
    if Application.query.filter_by(student_id=user.id, drive_id=drive_id).first():
        return jsonify({"error": "You have already applied to this drive."}), 400
    if not profile.resume_filename:
        return jsonify({"error": "Please upload your resume before applying."}), 400

    application = Application(student_id=user.id, drive_id=drive_id, status="Applied")
    db.session.add(application)
    db.session.add(Notification(
        user_id=user.id,
        message=f"You applied to {drive.role_title} at {drive.company.company_profile.company_name}.",
    ))
    db.session.commit()
    return jsonify({"message": "Application submitted successfully.", "application": application.to_dict()}), 201


@student_bp.route("/applications", methods=["GET"])
def my_applications():
    user, err = require_student()
    if err:
        return err
    apps = Application.query.filter_by(student_id=user.id).order_by(Application.applied_at.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]})


@student_bp.route("/interviews", methods=["GET"])
def my_interviews():
    user, err = require_student()
    if err:
        return err
    interviews = Interview.query.join(Application).filter(Application.student_id == user.id).all()
    return jsonify({"interviews": [i.to_dict() for i in interviews]})


@student_bp.route("/results", methods=["GET"])
def my_results():
    user, err = require_student()
    if err:
        return err
    results = Result.query.join(Application).filter(Application.student_id == user.id).all()
    return jsonify({"results": [r.to_dict() for r in results]})


# ---------------- Resume Creator ----------------

@student_bp.route("/resume-builder", methods=["GET"])
def get_resume_builder():
    user, err = require_student()
    if err:
        return err
    data = user.student_profile.resume_builder_data
    return jsonify({"resume_data": json.loads(data) if data else None})


@student_bp.route("/resume-builder", methods=["POST"])
def save_resume_builder():
    user, err = require_student()
    if err:
        return err
    payload = request.get_json(force=True)
    user.student_profile.resume_builder_data = json.dumps(payload)
    db.session.commit()
    return jsonify({"message": "Resume saved successfully."})


# ---------------- Resume Upload + AI ATS Analyzer ----------------

@student_bp.route("/resume/upload", methods=["POST"])
def upload_resume():
    user, err = require_student()
    if err:
        return err
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["resume"]
    if file.filename == "" or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF file."}), 400

    filename = secure_filename(f"user{user.id}_{file.filename}")
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    text = extract_text_from_pdf(filepath)
    analysis = analyze_resume(text)

    profile = user.student_profile
    profile.resume_filename = filename
    profile.resume_text = text
    profile.ats_score = analysis["ats_score"]
    if not profile.skills:
        profile.skills = extract_skills(text)
    db.session.commit()

    return jsonify({"message": "Resume uploaded and analyzed.", "analysis": analysis, "filename": filename})


@student_bp.route("/resume/analyze", methods=["POST"])
def analyze_existing_resume():
    """Re-run AI ATS analysis on the already-uploaded resume, optionally against a target job description."""
    user, err = require_student()
    if err:
        return err
    profile = user.student_profile
    if not profile.resume_text:
        return jsonify({"error": "Please upload a resume first."}), 400

    data = request.get_json(silent=True) or {}
    target_jd = (data.get("job_description") or "").lower()
    target_keywords = None
    if target_jd:
        import re
        words = set(re.findall(r"[a-zA-Z\+\.#]{3,}", target_jd))
        target_keywords = list(words)[:40]

    analysis = analyze_resume(profile.resume_text, target_keywords=target_keywords)
    profile.ats_score = analysis["ats_score"]
    db.session.commit()
    return jsonify({"analysis": analysis})


# ---------------- Aptitude Tests & Skill Assessments ----------------
# Both share the AptitudeTest/AptitudeResult tables, distinguished by test_type ("aptitude" | "skill")

@student_bp.route("/aptitude-tests", methods=["GET"])
def list_aptitude_tests():
    user, err = require_student()
    if err:
        return err
    test_type = request.args.get("type", "aptitude")
    tests = AptitudeTest.query.filter_by(test_type=test_type).all()
    taken = {r.test_id: r for r in AptitudeResult.query.filter_by(student_id=user.id).all()}
    result = []
    for t in tests:
        item = t.to_dict()
        if t.id in taken:
            item["last_score"] = taken[t.id].score
            item["last_total"] = taken[t.id].total
            item["last_level"] = taken[t.id].level
        result.append(item)
    return jsonify({"tests": result})


@student_bp.route("/aptitude-tests/<int:test_id>", methods=["GET"])
def get_aptitude_test(test_id):
    user, err = require_student()
    if err:
        return err
    test = AptitudeTest.query.get(test_id)
    if not test:
        return jsonify({"error": "Test not found."}), 404
    return jsonify({"test": test.to_dict(include_answers=False)})


@student_bp.route("/aptitude-tests/<int:test_id>/submit", methods=["POST"])
def submit_aptitude_test(test_id):
    user, err = require_student()
    if err:
        return err
    test = AptitudeTest.query.get(test_id)
    if not test:
        return jsonify({"error": "Test not found."}), 404
    answers = request.get_json(force=True).get("answers", {})  # {question_index: selected_option_index}
    questions = json.loads(test.questions_json or "[]")
    score = 0
    for idx, q in enumerate(questions):
        given = answers.get(str(idx))
        if given is not None and int(given) == q.get("answer"):
            score += 1

    level = compute_skill_level(score, len(questions)) if test.test_type == "skill" else None
    result = AptitudeResult(student_id=user.id, test_id=test_id, score=score, total=len(questions), level=level)
    db.session.add(result)
    db.session.commit()
    return jsonify({"message": "Test submitted.", "score": score, "total": len(questions), "level": level})


@student_bp.route("/aptitude-results", methods=["GET"])
def aptitude_results():
    user, err = require_student()
    if err:
        return err
    test_type = request.args.get("type")
    q = AptitudeResult.query.filter_by(student_id=user.id)
    if test_type:
        q = q.join(AptitudeTest).filter(AptitudeTest.test_type == test_type)
    results = q.order_by(AptitudeResult.taken_at.desc()).all()
    return jsonify({"results": [r.to_dict() for r in results]})
