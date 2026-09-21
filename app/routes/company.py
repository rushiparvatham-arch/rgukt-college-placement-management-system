from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import User, StudentProfile, Drive, Application, Interview, Result, Notification

company_bp = Blueprint("company", __name__)


def require_company():
    uid = session.get("user_id")
    if not uid or session.get("role") != "company":
        return None, (jsonify({"error": "Company login required."}), 401)
    user = User.query.get(uid)
    if not user:
        return None, (jsonify({"error": "Company login required."}), 401)
    return user, None


@company_bp.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    user, err = require_company()
    if err:
        return err
    drives = Drive.query.filter_by(company_id=user.id).all()
    drive_ids = [d.id for d in drives]
    total_applicants = Application.query.filter(Application.drive_id.in_(drive_ids)).count() if drive_ids else 0
    shortlisted = Application.query.filter(
        Application.drive_id.in_(drive_ids), Application.status.in_(["Shortlisted", "Interview"])
    ).count() if drive_ids else 0
    selected = Application.query.filter(Application.drive_id.in_(drive_ids), Application.status == "Selected").count() if drive_ids else 0

    return jsonify({
        "stats": {
            "active_drives": len([d for d in drives if d.status in ("Upcoming", "Ongoing")]),
            "total_drives": len(drives),
            "total_applicants": total_applicants,
            "shortlisted": shortlisted,
            "selected": selected,
        }
    })


@company_bp.route("/drives", methods=["GET"])
def my_drives():
    user, err = require_company()
    if err:
        return err
    drives = Drive.query.filter_by(company_id=user.id).order_by(Drive.created_at.desc()).all()
    return jsonify({"drives": [d.to_dict(include_company=False) for d in drives]})


@company_bp.route("/drives", methods=["POST"])
def create_drive_request():
    """Company submits a drive request; CDPC still oversees via the CDPC dashboard."""
    user, err = require_company()
    if err:
        return err
    data = request.get_json(force=True)
    drive = Drive(
        company_id=user.id,
        role_title=data.get("role_title"),
        job_type=data.get("job_type", "Full-Time"),
        description=data.get("description", ""),
        ctc=data.get("ctc", ""),
        location=data.get("location", ""),
        min_cgpa=float(data.get("min_cgpa", 0) or 0),
        max_backlogs=int(data.get("max_backlogs", 0) or 0),
        eligible_branches=data.get("eligible_branches", "All Branches"),
        drive_date=data.get("drive_date", ""),
        application_deadline=data.get("application_deadline", ""),
        status="Upcoming",
    )
    db.session.add(drive)

    # Notify CDPC staff
    cdpc_users = User.query.filter_by(role="cdpc").all()
    for c in cdpc_users:
        db.session.add(Notification(
            user_id=c.id,
            message=f"{user.company_profile.company_name} posted a new drive: {drive.role_title}.",
        ))
    db.session.commit()
    return jsonify({"message": "Drive posted successfully.", "drive": drive.to_dict(include_company=False)}), 201


@company_bp.route("/drives/<int:drive_id>", methods=["PUT"])
def update_my_drive(drive_id):
    user, err = require_company()
    if err:
        return err
    drive = Drive.query.filter_by(id=drive_id, company_id=user.id).first()
    if not drive:
        return jsonify({"error": "Drive not found."}), 404
    data = request.get_json(force=True)
    for field in ["role_title", "job_type", "description", "ctc", "location",
                  "eligible_branches", "drive_date", "application_deadline", "status"]:
        if field in data:
            setattr(drive, field, data[field])
    db.session.commit()
    return jsonify({"message": "Drive updated.", "drive": drive.to_dict(include_company=False)})


@company_bp.route("/applications", methods=["GET"])
def drive_applications():
    user, err = require_company()
    if err:
        return err
    drive_id = request.args.get("drive_id")
    q = Application.query.join(Drive).filter(Drive.company_id == user.id)
    if drive_id:
        q = q.filter(Application.drive_id == drive_id)
    apps = q.order_by(Application.applied_at.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]})


@company_bp.route("/applications/<int:app_id>/status", methods=["PUT"])
def update_application_status(app_id):
    user, err = require_company()
    if err:
        return err
    application = Application.query.join(Drive).filter(Application.id == app_id, Drive.company_id == user.id).first()
    if not application:
        return jsonify({"error": "Application not found."}), 404
    data = request.get_json(force=True)
    new_status = data.get("status")
    if new_status not in ("Applied", "Shortlisted", "Interview", "Selected", "Rejected"):
        return jsonify({"error": "Invalid status."}), 400
    application.status = new_status
    db.session.add(Notification(
        user_id=application.student_id,
        message=f"Update from {user.company_profile.company_name}: your application is now {new_status}.",
    ))
    if new_status == "Selected":
        application.student.student_profile.placed = True
    db.session.commit()
    return jsonify({"message": "Status updated.", "application": application.to_dict()})


@company_bp.route("/students", methods=["GET"])
def browse_students():
    """Company can browse the eligible student pool to simplify shortlisting."""
    user, err = require_company()
    if err:
        return err
    min_cgpa = request.args.get("min_cgpa", type=float)
    branch = request.args.get("branch")
    q = StudentProfile.query.join(User)
    if min_cgpa is not None:
        q = q.filter(StudentProfile.cgpa >= min_cgpa)
    if branch:
        q = q.filter(StudentProfile.branch == branch)
    students = q.all()
    result = []
    for s in students:
        result.append({
            "id": s.user.id,
            "name": s.user.name,
            "branch": s.branch,
            "cgpa": s.cgpa,
            "backlogs": s.backlogs,
            "skills": s.skills,
            "resume_filename": s.resume_filename,
            "placed": s.placed,
            "linkedin": s.linkedin,
            "github": s.github,
        })
    return jsonify({"students": result})
