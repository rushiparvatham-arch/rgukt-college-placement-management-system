from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import (
    User, StudentProfile, CompanyProfile, CDPCProfile, Drive, Application,
    Interview, Result, Notification, NotificationBroadcast,
)

cdpc_bp = Blueprint("cdpc", __name__)


def require_cdpc():
    uid = session.get("user_id")
    if not uid or session.get("role") != "cdpc":
        return None, (jsonify({"error": "CDPC / Administrator login required."}), 401)
    user = User.query.get(uid)
    if not user:
        return None, (jsonify({"error": "CDPC / Administrator login required."}), 401)
    return user, None


# ---------------- Dashboard Overview ----------------

@cdpc_bp.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    user, err = require_cdpc()
    if err:
        return err
    total_students = StudentProfile.query.count()
    placed_students = StudentProfile.query.filter_by(placed=True).count()
    total_companies = CompanyProfile.query.count()
    active_drives = Drive.query.filter(Drive.status.in_(["Upcoming", "Ongoing"])).count()
    total_applications = Application.query.count()
    total_offers = Result.query.filter_by(outcome="Selected").count()

    return jsonify({
        "stats": {
            "total_students": total_students,
            "placed_students": placed_students,
            "placement_percent": round((placed_students / total_students) * 100, 1) if total_students else 0,
            "total_companies": total_companies,
            "active_drives": active_drives,
            "total_applications": total_applications,
            "total_offers": total_offers,
        }
    })


@cdpc_bp.route("/analytics", methods=["GET"])
def analytics():
    user, err = require_cdpc()
    if err:
        return err

    # Branch-wise placement stats
    students = StudentProfile.query.all()
    branch_stats = {}
    for s in students:
        b = s.branch or "Unknown"
        branch_stats.setdefault(b, {"total": 0, "placed": 0})
        branch_stats[b]["total"] += 1
        if s.placed:
            branch_stats[b]["placed"] += 1

    # Drive status distribution
    drive_status = {"Upcoming": 0, "Ongoing": 0, "Closed": 0}
    for d in Drive.query.all():
        drive_status[d.status] = drive_status.get(d.status, 0) + 1

    # Application funnel
    funnel = {"Applied": 0, "Shortlisted": 0, "Interview": 0, "Selected": 0, "Rejected": 0}
    for a in Application.query.all():
        funnel[a.status] = funnel.get(a.status, 0) + 1

    # Top recruiting companies
    company_offers = {}
    for r in Result.query.filter_by(outcome="Selected").all():
        cname = r.application.drive.company.company_profile.company_name
        company_offers[cname] = company_offers.get(cname, 0) + 1
    top_companies = sorted(company_offers.items(), key=lambda x: -x[1])[:6]

    return jsonify({
        "branch_stats": branch_stats,
        "drive_status": drive_status,
        "application_funnel": funnel,
        "top_companies": [{"name": k, "offers": v} for k, v in top_companies],
    })


# ---------------- Student Management ----------------

@cdpc_bp.route("/students", methods=["GET"])
def list_students():
    user, err = require_cdpc()
    if err:
        return err
    branch = request.args.get("branch")
    placed = request.args.get("placed")
    q = StudentProfile.query.join(User)
    if branch:
        q = q.filter(StudentProfile.branch == branch)
    if placed in ("true", "false"):
        q = q.filter(StudentProfile.placed == (placed == "true"))
    profiles = q.all()
    result = []
    for p in profiles:
        result.append({
            "id": p.user.id,
            "name": p.user.name,
            "email": p.user.email,
            "phone": p.user.phone,
            **p.to_dict(),
        })
    return jsonify({"students": result})


@cdpc_bp.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    user, err = require_cdpc()
    if err:
        return err
    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"error": "Student not found."}), 404
    data = request.get_json(force=True)
    p = student.student_profile
    if "placed" in data:
        p.placed = bool(data["placed"])
    if "cgpa" in data:
        p.cgpa = float(data["cgpa"])
    if "backlogs" in data:
        p.backlogs = int(data["backlogs"])
    db.session.commit()
    return jsonify({"message": "Student record updated.", "student": p.to_dict()})


# ---------------- Company Management ----------------

@cdpc_bp.route("/companies", methods=["GET"])
def list_companies():
    user, err = require_cdpc()
    if err:
        return err
    companies = CompanyProfile.query.all()
    result = []
    for c in companies:
        drives_count = Drive.query.filter_by(company_id=c.user_id).count()
        result.append({
            "id": c.user_id,
            "email": c.user.email,
            "phone": c.user.phone,
            "drives_count": drives_count,
            **c.to_dict(),
        })
    return jsonify({"companies": result})


@cdpc_bp.route("/companies/<int:company_id>/approve", methods=["PUT"])
def approve_company(company_id):
    user, err = require_cdpc()
    if err:
        return err
    company = CompanyProfile.query.filter_by(user_id=company_id).first()
    if not company:
        return jsonify({"error": "Company not found."}), 404
    company.is_approved = True
    db.session.add(Notification(user_id=company_id, message="Your company profile has been approved by CDPC."))
    db.session.commit()
    return jsonify({"message": "Company approved."})


# ---------------- Drive Management ----------------

@cdpc_bp.route("/drives", methods=["GET"])
def list_drives():
    user, err = require_cdpc()
    if err:
        return err
    drives = Drive.query.order_by(Drive.created_at.desc()).all()
    return jsonify({"drives": [d.to_dict() for d in drives]})


@cdpc_bp.route("/drives", methods=["POST"])
def create_drive():
    user, err = require_cdpc()
    if err:
        return err
    data = request.get_json(force=True)
    company_id = data.get("company_id")
    company = User.query.get(company_id)
    if not company or company.role != "company":
        return jsonify({"error": "Please select a valid company."}), 400

    drive = Drive(
        company_id=company_id,
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
        status=data.get("status", "Upcoming"),
    )
    db.session.add(drive)
    db.session.flush()

    # Notify all students
    students = User.query.filter_by(role="student").all()
    for s in students:
        db.session.add(Notification(
            user_id=s.id,
            message=f"New placement drive: {drive.role_title} at {company.company_profile.company_name}.",
        ))
    db.session.commit()
    return jsonify({"message": "Drive created successfully.", "drive": drive.to_dict()}), 201


@cdpc_bp.route("/drives/<int:drive_id>", methods=["PUT"])
def update_drive(drive_id):
    user, err = require_cdpc()
    if err:
        return err
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found."}), 404
    data = request.get_json(force=True)
    for field in ["role_title", "job_type", "description", "ctc", "location",
                  "eligible_branches", "drive_date", "application_deadline", "status"]:
        if field in data:
            setattr(drive, field, data[field])
    if "min_cgpa" in data:
        drive.min_cgpa = float(data["min_cgpa"])
    if "max_backlogs" in data:
        drive.max_backlogs = int(data["max_backlogs"])
    db.session.commit()
    return jsonify({"message": "Drive updated.", "drive": drive.to_dict()})


@cdpc_bp.route("/drives/<int:drive_id>", methods=["DELETE"])
def delete_drive(drive_id):
    user, err = require_cdpc()
    if err:
        return err
    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({"error": "Drive not found."}), 404
    db.session.delete(drive)
    db.session.commit()
    return jsonify({"message": "Drive deleted."})


# ---------------- Application / Interview Management ----------------

@cdpc_bp.route("/applications", methods=["GET"])
def list_applications():
    user, err = require_cdpc()
    if err:
        return err
    drive_id = request.args.get("drive_id")
    q = Application.query
    if drive_id:
        q = q.filter_by(drive_id=drive_id)
    apps = q.order_by(Application.applied_at.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps]})


@cdpc_bp.route("/applications/<int:app_id>/status", methods=["PUT"])
def update_application_status(app_id):
    user, err = require_cdpc()
    if err:
        return err
    application = Application.query.get(app_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404
    data = request.get_json(force=True)
    new_status = data.get("status")
    if new_status not in ("Applied", "Shortlisted", "Interview", "Selected", "Rejected"):
        return jsonify({"error": "Invalid status."}), 400
    application.status = new_status
    db.session.add(Notification(
        user_id=application.student_id,
        message=f"Your application for {application.drive.role_title} is now: {new_status}.",
    ))
    if new_status == "Selected":
        application.student.student_profile.placed = True
    db.session.commit()
    return jsonify({"message": "Application status updated.", "application": application.to_dict()})


@cdpc_bp.route("/interviews", methods=["GET"])
def list_interviews():
    user, err = require_cdpc()
    if err:
        return err
    interviews = Interview.query.all()
    return jsonify({"interviews": [i.to_dict() for i in interviews]})


@cdpc_bp.route("/interviews", methods=["POST"])
def schedule_interview():
    user, err = require_cdpc()
    if err:
        return err
    data = request.get_json(force=True)
    application_id = data.get("application_id")
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    interview = Interview(
        application_id=application_id,
        round_name=data.get("round_name", "Technical Round 1"),
        scheduled_at=data.get("scheduled_at", ""),
        mode=data.get("mode", "Online"),
        venue_or_link=data.get("venue_or_link", ""),
        status="Scheduled",
    )
    db.session.add(interview)
    application.status = "Interview"
    db.session.add(Notification(
        user_id=application.student_id,
        message=f"Interview scheduled: {interview.round_name} for {application.drive.role_title}.",
    ))
    db.session.commit()
    return jsonify({"message": "Interview scheduled.", "interview": interview.to_dict()}), 201


@cdpc_bp.route("/interviews/<int:interview_id>", methods=["PUT"])
def update_interview(interview_id):
    user, err = require_cdpc()
    if err:
        return err
    interview = Interview.query.get(interview_id)
    if not interview:
        return jsonify({"error": "Interview not found."}), 404
    data = request.get_json(force=True)
    for field in ["round_name", "scheduled_at", "mode", "venue_or_link", "status", "feedback"]:
        if field in data:
            setattr(interview, field, data[field])
    db.session.commit()
    return jsonify({"message": "Interview updated.", "interview": interview.to_dict()})


# ---------------- Results Management ----------------

@cdpc_bp.route("/results", methods=["GET"])
def list_results():
    user, err = require_cdpc()
    if err:
        return err
    results = Result.query.order_by(Result.published_at.desc()).all()
    return jsonify({"results": [r.to_dict() for r in results]})


@cdpc_bp.route("/results", methods=["POST"])
def publish_result():
    user, err = require_cdpc()
    if err:
        return err
    data = request.get_json(force=True)
    application_id = data.get("application_id")
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"error": "Application not found."}), 404

    existing = Result.query.filter_by(application_id=application_id).first()
    outcome = data.get("outcome", "Selected")
    if existing:
        existing.outcome = outcome
        existing.package_offered = data.get("package_offered", existing.package_offered)
        existing.remarks = data.get("remarks", existing.remarks)
        result = existing
    else:
        result = Result(
            application_id=application_id,
            outcome=outcome,
            package_offered=data.get("package_offered", ""),
            remarks=data.get("remarks", ""),
        )
        db.session.add(result)

    application.status = "Selected" if outcome == "Selected" else "Rejected"
    if outcome == "Selected":
        application.student.student_profile.placed = True
    db.session.add(Notification(
        user_id=application.student_id,
        message=f"Result published for {application.drive.role_title}: {outcome}.",
    ))
    db.session.commit()
    return jsonify({"message": "Result published.", "result": result.to_dict()}), 201


# ---------------- Send Notifications (CDPC broadcast) ----------------

VALID_AUDIENCES = ("all_students", "all_companies", "branch", "everyone")


@cdpc_bp.route("/notifications/branches", methods=["GET"])
def list_notification_branches():
    """Distinct branches currently in use, for the audience-picker dropdown."""
    user, err = require_cdpc()
    if err:
        return err
    branches = [row[0] for row in db.session.query(StudentProfile.branch).distinct().all() if row[0]]
    return jsonify({"branches": sorted(branches)})


@cdpc_bp.route("/notifications/send", methods=["POST"])
def send_notification():
    user, err = require_cdpc()
    if err:
        return err
    data = request.get_json(force=True)
    audience = data.get("audience")
    branch = (data.get("branch") or "").strip()
    message = (data.get("message") or "").strip()
    link = (data.get("link") or "").strip() or None

    if audience not in VALID_AUDIENCES:
        return jsonify({"error": "Please choose who this notification is for."}), 400
    if not message:
        return jsonify({"error": "Please write a message to send."}), 400
    if len(message) > 255:
        return jsonify({"error": "Message is too long (255 characters max)."}), 400
    if audience == "branch" and not branch:
        return jsonify({"error": "Please choose a branch."}), 400

    if audience == "all_students":
        recipients = User.query.filter_by(role="student").all()
    elif audience == "all_companies":
        recipients = User.query.filter_by(role="company").all()
    elif audience == "branch":
        recipients = (
            User.query.join(StudentProfile)
            .filter(User.role == "student", StudentProfile.branch == branch)
            .all()
        )
    else:  # everyone
        recipients = User.query.filter(User.id != user.id).all()

    if not recipients:
        return jsonify({"error": "No matching recipients were found for that audience."}), 400

    for recipient in recipients:
        db.session.add(Notification(user_id=recipient.id, message=message, link=link))

    broadcast = NotificationBroadcast(
        sender_id=user.id, audience=audience, branch=branch if audience == "branch" else None,
        message=message, recipient_count=len(recipients),
    )
    db.session.add(broadcast)
    db.session.commit()

    return jsonify({
        "message": f"Notification sent to {len(recipients)} recipient(s).",
        "broadcast": broadcast.to_dict(),
    }), 201


@cdpc_bp.route("/notifications/sent", methods=["GET"])
def list_sent_notifications():
    user, err = require_cdpc()
    if err:
        return err
    broadcasts = NotificationBroadcast.query.order_by(NotificationBroadcast.created_at.desc()).limit(50).all()
    return jsonify({"broadcasts": [b.to_dict() for b in broadcasts]})
