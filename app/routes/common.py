from flask import Blueprint, jsonify, session, request, send_from_directory, current_app
from app.extensions import db
from app.models import User, Notification, Drive, CompanyProfile, StudentProfile

common_bp = Blueprint("common", __name__)


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


def require_login():
    user = current_user()
    if not user:
        return None, (jsonify({"error": "Not authenticated."}), 401)
    return user, None


@common_bp.route("/notifications", methods=["GET"])
def get_notifications():
    user, err = require_login()
    if err:
        return err
    notes = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(30).all()
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({"notifications": [n.to_dict() for n in notes], "unread_count": unread})


@common_bp.route("/notifications/<int:note_id>/read", methods=["PUT"])
def mark_read(note_id):
    user, err = require_login()
    if err:
        return err
    note = Notification.query.filter_by(id=note_id, user_id=user.id).first()
    if not note:
        return jsonify({"error": "Notification not found."}), 404
    note.is_read = True
    db.session.commit()
    return jsonify({"message": "Marked as read."})


@common_bp.route("/notifications/read-all", methods=["PUT"])
def mark_all_read():
    user, err = require_login()
    if err:
        return err
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read."})


@common_bp.route("/search", methods=["GET"])
def search():
    user, err = require_login()
    if err:
        return err
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 1:
        return jsonify({"results": []})

    results = []
    if user.role == "student":
        drives = Drive.query.filter(Drive.role_title.ilike(f"%{q}%")).limit(6).all()
        for d in drives:
            results.append({"type": "Drive", "label": d.role_title, "sub": d.company.company_profile.company_name if d.company and d.company.company_profile else "", "link": "#drives"})
        companies = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f"%{q}%")).limit(6).all()
        for c in companies:
            results.append({"type": "Company", "label": c.company_name, "sub": c.industry or "", "link": "#companies"})
    elif user.role == "cdpc":
        students = StudentProfile.query.join(User).filter(User.name.ilike(f"%{q}%")).limit(6).all()
        for s in students:
            results.append({"type": "Student", "label": s.user.name, "sub": s.roll_number or "", "link": "#students"})
        companies = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f"%{q}%")).limit(6).all()
        for c in companies:
            results.append({"type": "Company", "label": c.company_name, "sub": c.industry or "", "link": "#companies"})
        drives = Drive.query.filter(Drive.role_title.ilike(f"%{q}%")).limit(6).all()
        for d in drives:
            results.append({"type": "Drive", "label": d.role_title, "sub": "", "link": "#drives"})
    elif user.role == "company":
        students = StudentProfile.query.join(User).filter(User.name.ilike(f"%{q}%")).limit(8).all()
        for s in students:
            results.append({"type": "Student", "label": s.user.name, "sub": f"{s.branch} · CGPA {s.cgpa}", "link": "#students"})

    return jsonify({"results": results})


@common_bp.route("/resume/<path:filename>", methods=["GET"])
def get_resume_file(filename):
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)


@common_bp.route("/profile-picture/<path:filename>", methods=["GET"])
def get_profile_picture(filename):
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401
    return send_from_directory(current_app.config["PROFILE_PICTURE_FOLDER"], filename, as_attachment=False)
