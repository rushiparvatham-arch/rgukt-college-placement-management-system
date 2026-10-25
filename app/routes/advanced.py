"""Advanced placement-portal capabilities.

This module intentionally builds on the existing Student / Company / CDPC roles
instead of replacing the original APIs.  It adds career intelligence, talent
search, shortlist/offer tracking, governance/audit logs and richer reporting.
"""
import csv
import io
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, session, Response
from app.extensions import db
from app.models import (
    User, StudentProfile, CompanyProfile, Drive, Application, Interview, Result, Notification,
    StudentPreference, SavedDrive, CompanyShortlist, Offer, AuditLog, InterviewFeedback,
)

advanced_bp = Blueprint("advanced", __name__)


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def require_role(role=None):
    user = current_user()
    if not user or (role and user.role != role):
        return None, (jsonify({"error": f"{role.title() if role else 'Authenticated'} access required."}), 401)
    return user, None


def audit(actor, action, entity_type, entity_id=None, details=None):
    row = AuditLog(
        actor_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=json.dumps(details or {}),
    )
    db.session.add(row)
    return row


def skill_tokens(text):
    return {x.strip().lower() for x in (text or "").replace(";", ",").split(",") if x.strip()}


def recommendation_score(student, drive):
    p = student.student_profile
    if not p:
        return 0, []
    reasons = []
    score = 0
    if p.cgpa >= (drive.min_cgpa or 0):
        score += 30
        reasons.append("CGPA eligible")
    else:
        return 0, ["CGPA below requirement"]
    if p.backlogs <= (drive.max_backlogs or 0):
        score += 15
        reasons.append("Backlog criteria met")
    else:
        return 0, ["Backlog limit not met"]
    branches = [x.strip().lower() for x in (drive.eligible_branches or "All Branches").split(",")]
    if "all branches" in branches or p.branch.lower() in branches:
        score += 20
        reasons.append("Branch eligible")
    else:
        return 0, ["Branch not eligible"]

    prefs = StudentPreference.query.filter_by(student_id=student.id).first()
    if prefs:
        locations = skill_tokens(prefs.preferred_locations)
        roles = skill_tokens(prefs.preferred_roles)
        if locations and any(x in (drive.location or "").lower() for x in locations):
            score += 10; reasons.append("Preferred location")
        if roles and any(x in (drive.role_title or "").lower() for x in roles):
            score += 10; reasons.append("Preferred role")
        if prefs.preferred_job_type and prefs.preferred_job_type.lower() == (drive.job_type or "").lower():
            score += 5; reasons.append("Preferred job type")

    # Skill overlap against a free-form description/role. This is deliberately
    # transparent rather than pretending to be an opaque ML recommendation.
    student_skills = skill_tokens(p.skills)
    text = f"{drive.role_title} {drive.description}".lower()
    known = {"python", "java", "javascript", "react", "node", "flask", "django", "sql", "mysql", "mongodb", "html", "css", "git", "aws", "docker", "kubernetes", "c", "cpp", "c++", "machine learning", "data structures", "spring", "excel", "power bi"}
    overlap = [s for s in student_skills if s in text and s in known]
    if overlap:
        score += min(10, len(overlap) * 3)
        reasons.append(f"Skill match: {', '.join(overlap[:3])}")
    return min(100, score), reasons


# ---------------- Student: career intelligence ----------------

@advanced_bp.route("/student/readiness", methods=["GET"])
def student_readiness():
    user, err = require_role("student")
    if err: return err
    p = user.student_profile
    applications = Application.query.filter_by(student_id=user.id).all()
    completed = Result.query.join(Application).filter(Application.student_id == user.id, Result.outcome == "Selected").count()
    components = {
        "profile": 100 if p and p.cgpa and p.skills and p.resume_filename else 55 if p else 0,
        "academics": min(100, int((p.cgpa / 10) * 100)) if p else 0,
        "resume": min(100, p.ats_score or 0) if p else 0,
        "skills": min(100, len(skill_tokens(p.skills)) * 12) if p else 0,
        "engagement": min(100, len(applications) * 15),
    }
    overall = round(sum(components.values()) / len(components)) if components else 0
    return jsonify({"overall": overall, "components": components, "applications": len(applications), "offers": completed})


@advanced_bp.route("/student/recommendations", methods=["GET"])
def student_recommendations():
    user, err = require_role("student")
    if err: return err
    limit = min(max(int(request.args.get("limit", 12)), 1), 30)
    applied_ids = {x.drive_id for x in Application.query.filter_by(student_id=user.id).all()}
    saved_ids = {x.drive_id for x in SavedDrive.query.filter_by(student_id=user.id).all()}
    drives = Drive.query.filter(Drive.status.in_(["Upcoming", "Ongoing"])).all()
    items = []
    for d in drives:
        score, reasons = recommendation_score(user, d)
        if score > 0:
            items.append({"drive": d.to_dict(), "match_score": score, "reasons": reasons, "applied": d.id in applied_ids, "saved": d.id in saved_ids})
    items.sort(key=lambda x: (-x["match_score"], x["drive"].get("application_deadline") or ""))
    return jsonify({"recommendations": items[:limit]})


@advanced_bp.route("/student/preferences", methods=["GET", "PUT"])
def student_preferences():
    user, err = require_role("student")
    if err: return err
    prefs = StudentPreference.query.filter_by(student_id=user.id).first()
    if request.method == "GET":
        return jsonify({"preferences": prefs.to_dict() if prefs else {"preferred_locations":"", "preferred_roles":"", "preferred_job_type":"", "work_mode":"Any", "target_ctc":""}})
    data = request.get_json(force=True)
    if not prefs:
        prefs = StudentPreference(student_id=user.id)
        db.session.add(prefs)
    for field in ["preferred_locations", "preferred_roles", "preferred_job_type", "work_mode", "target_ctc"]:
        if field in data: setattr(prefs, field, str(data.get(field) or "").strip())
    audit(user, "updated_preferences", "student_preference", prefs.id, data)
    db.session.commit()
    return jsonify({"message":"Career preferences saved.", "preferences":prefs.to_dict()})


@advanced_bp.route("/student/saved-drives", methods=["GET"])
def saved_drives():
    user, err = require_role("student")
    if err: return err
    rows = SavedDrive.query.filter_by(student_id=user.id).order_by(SavedDrive.created_at.desc()).all()
    return jsonify({"saved_drives":[{"id":r.id,"saved_at":r.created_at.strftime("%d %b %Y"),"drive":r.drive.to_dict() if r.drive else None} for r in rows]})


@advanced_bp.route("/student/offers", methods=["GET"])
def student_offers():
    user, err = require_role("student")
    if err: return err
    return jsonify({"offers":[x.to_dict() for x in Offer.query.filter_by(student_id=user.id).order_by(Offer.created_at.desc()).all()]})


@advanced_bp.route("/student/offers/<int:offer_id>", methods=["PUT"])
def student_offer_status(offer_id):
    user, err = require_role("student")
    if err: return err
    offer = Offer.query.filter_by(id=offer_id, student_id=user.id).first()
    if not offer: return jsonify({"error":"Offer not found."}),404
    status = (request.get_json(force=True).get("status") or "").strip()
    if status not in {"Accepted", "Declined"}: return jsonify({"error":"Invalid offer status."}),400
    offer.status = status
    if user.student_profile and status == "Accepted":
        user.student_profile.placed = True
    db.session.add(Notification(user_id=offer.company_id, message=f"{user.name} has {status.lower()} the placement offer."))
    audit(user,"updated_offer_response","offer",offer.id,{"status":status})
    db.session.commit()
    return jsonify({"message":f"Offer {status.lower()}.","offer":offer.to_dict()})


@advanced_bp.route("/student/saved-drives/<int:drive_id>", methods=["POST", "DELETE"])
def toggle_saved_drive(drive_id):
    user, err = require_role("student")
    if err: return err
    drive = Drive.query.get(drive_id)
    if not drive: return jsonify({"error":"Drive not found."}), 404
    row = SavedDrive.query.filter_by(student_id=user.id, drive_id=drive_id).first()
    if request.method == "DELETE":
        if row: db.session.delete(row)
        db.session.commit()
        return jsonify({"saved":False})
    if row: return jsonify({"saved":True})
    db.session.add(SavedDrive(student_id=user.id, drive_id=drive_id))
    audit(user, "saved_drive", "drive", drive_id)
    db.session.commit()
    return jsonify({"saved":True})


# ---------------- Company: talent intelligence ----------------

@advanced_bp.route("/company/talent", methods=["GET"])
def company_talent():
    user, err = require_role("company")
    if err: return err
    q = (request.args.get("q") or "").strip()
    branch = (request.args.get("branch") or "").strip()
    skill = (request.args.get("skill") or "").strip().lower()
    min_cgpa = float(request.args.get("min_cgpa", 0) or 0)
    profiles = StudentProfile.query.join(User).filter(StudentProfile.cgpa >= min_cgpa, StudentProfile.placed == False).all()
    out = []
    for p in profiles:
        hay = f"{p.user.name} {p.roll_number or ''} {p.branch or ''} {p.skills or ''}".lower()
        if q and q.lower() not in hay: continue
        if branch and p.branch.lower() != branch.lower(): continue
        if skill and skill not in (p.skills or "").lower(): continue
        shortlisted = CompanyShortlist.query.filter_by(company_id=user.id, student_id=p.user_id).first()
        out.append({"id":p.user_id,"name":p.user.name,"email":p.user.email,"branch":p.branch,"cgpa":p.cgpa,"backlogs":p.backlogs,"skills":p.skills,"ats_score":p.ats_score,"resume_filename":p.resume_filename,"shortlisted":bool(shortlisted)})
    out.sort(key=lambda x:(-x["cgpa"], -x["ats_score"]))
    return jsonify({"students":out[:100]})


@advanced_bp.route("/company/shortlists", methods=["GET", "POST"])
def company_shortlists():
    user, err = require_role("company")
    if err: return err
    if request.method == "GET":
        rows = CompanyShortlist.query.filter_by(company_id=user.id).order_by(CompanyShortlist.created_at.desc()).all()
        return jsonify({"shortlists":[r.to_dict() for r in rows]})
    data = request.get_json(force=True)
    student_id = int(data.get("student_id"))
    if not StudentProfile.query.filter_by(user_id=student_id).first(): return jsonify({"error":"Student not found."}),404
    row = CompanyShortlist.query.filter_by(company_id=user.id, student_id=student_id).first()
    if not row:
        row = CompanyShortlist(company_id=user.id, student_id=student_id, note=data.get("note",""))
        db.session.add(row)
        db.session.add(Notification(user_id=student_id, message=f"{user.company_profile.company_name} added you to its talent shortlist."))
        audit(user,"shortlisted_student","student",student_id)
        db.session.commit()
    return jsonify({"message":"Student shortlisted.","shortlist":row.to_dict()}),201


@advanced_bp.route("/company/shortlists/<int:student_id>", methods=["DELETE"])
def remove_shortlist(student_id):
    user, err = require_role("company")
    if err: return err
    row = CompanyShortlist.query.filter_by(company_id=user.id, student_id=student_id).first()
    if row: db.session.delete(row); db.session.commit()
    return jsonify({"message":"Removed from shortlist."})


@advanced_bp.route("/company/offers", methods=["GET", "POST"])
def company_offers():
    user, err = require_role("company")
    if err: return err
    if request.method == "GET":
        rows = Offer.query.filter_by(company_id=user.id).order_by(Offer.created_at.desc()).all()
        return jsonify({"offers":[r.to_dict() for r in rows]})
    data = request.get_json(force=True)
    student_id = int(data.get("student_id"))
    drive_id = int(data.get("drive_id")) if data.get("drive_id") else None
    if drive_id and not Drive.query.filter_by(id=drive_id, company_id=user.id).first(): return jsonify({"error":"Drive does not belong to this company."}),403
    offer = Offer(company_id=user.id, student_id=student_id, drive_id=drive_id, package_offered=data.get("package_offered",""), designation=data.get("designation",""), joining_date=data.get("joining_date",""), status="Offered")
    db.session.add(offer)
    if drive_id:
        app = Application.query.filter_by(student_id=student_id, drive_id=drive_id).first()
        if app:
            app.status = "Selected"
            if app.student and app.student.student_profile:
                app.student.student_profile.placed = True
    db.session.add(Notification(user_id=student_id, message=f"{user.company_profile.company_name} issued a placement offer.", link="#results"))
    audit(user,"created_offer","offer",None,{"student_id":student_id,"package":offer.package_offered})
    db.session.commit()
    return jsonify({"message":"Offer created.","offer":offer.to_dict()}),201


@advanced_bp.route("/company/offers/<int:offer_id>", methods=["PUT"])
def update_company_offer(offer_id):
    user, err = require_role("company")
    if err: return err
    row = Offer.query.filter_by(id=offer_id, company_id=user.id).first()
    if not row: return jsonify({"error":"Offer not found."}),404
    data = request.get_json(force=True)
    for f in ["package_offered","designation","joining_date","status"]:
        if f in data: setattr(row,f,str(data[f] or ""))
    audit(user,"updated_offer","offer",row.id,data)
    db.session.commit()
    return jsonify({"offer":row.to_dict()})


# ---------------- CDPC: command centre, governance and reports ----------------

@advanced_bp.route("/cdpc/command-center", methods=["GET"])
def cdpc_command_center():
    user, err = require_role("cdpc")
    if err: return err
    total = StudentProfile.query.count()
    placed = StudentProfile.query.filter_by(placed=True).count()
    offers = Offer.query.count()
    accepted = Offer.query.filter_by(status="Accepted").count()
    interviews = Interview.query.filter_by(status="Scheduled").count()
    active_drives = Drive.query.filter(Drive.status.in_(["Upcoming","Ongoing"])).count()
    avg_ats = round(sum((p.ats_score or 0) for p in StudentProfile.query.all()) / total, 1) if total else 0
    branch = {}
    for p in StudentProfile.query.all():
        b = p.branch or "Unknown"; branch.setdefault(b,{"students":0,"placed":0,"avg_cgpa":0}); branch[b]["students"] += 1; branch[b]["placed"] += int(bool(p.placed)); branch[b]["avg_cgpa"] += p.cgpa or 0
    for v in branch.values(): v["avg_cgpa"] = round(v["avg_cgpa"]/v["students"],2) if v["students"] else 0; v["placement_rate"] = round(v["placed"]/v["students"]*100,1) if v["students"] else 0
    return jsonify({"kpis":{"students":total,"placed":placed,"placement_rate":round(placed/total*100,1) if total else 0,"offers":offers,"accepted_offers":accepted,"active_drives":active_drives,"scheduled_interviews":interviews,"avg_ats":avg_ats},"branch":branch})


@advanced_bp.route("/cdpc/audit-logs", methods=["GET"])
def cdpc_audit_logs():
    user, err = require_role("cdpc")
    if err: return err
    rows = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return jsonify({"logs":[r.to_dict() for r in rows]})


@advanced_bp.route("/cdpc/offers", methods=["GET"])
def cdpc_offers():
    user, err = require_role("cdpc")
    if err: return err
    return jsonify({"offers":[x.to_dict() for x in Offer.query.order_by(Offer.created_at.desc()).all()]})


@advanced_bp.route("/cdpc/interview-feedback", methods=["POST"])
def cdpc_interview_feedback():
    user, err = require_role("cdpc")
    if err: return err
    data = request.get_json(force=True)
    interview_id = int(data.get("interview_id"))
    interview = Interview.query.get(interview_id)
    if not interview: return jsonify({"error":"Interview not found."}),404
    row = InterviewFeedback.query.filter_by(interview_id=interview_id).first()
    if not row:
        row = InterviewFeedback(interview_id=interview_id)
        db.session.add(row)
    row.rating = int(data.get("rating",0) or 0)
    row.technical = int(data.get("technical",0) or 0)
    row.communication = int(data.get("communication",0) or 0)
    row.problem_solving = int(data.get("problem_solving",0) or 0)
    row.comments = data.get("comments","")
    audit(user,"recorded_interview_feedback","interview",interview_id,data)
    db.session.commit()
    return jsonify({"message":"Interview feedback saved.","feedback":row.to_dict()})


@advanced_bp.route("/cdpc/report/applications.csv", methods=["GET"])
def applications_csv():
    user, err = require_role("cdpc")
    if err: return err
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["Student","Email","Roll Number","Branch","CGPA","Company","Role","Status","Applied At"])
    for a in Application.query.order_by(Application.applied_at.desc()).all():
        p=a.student.student_profile if a.student else None; c=a.drive.company.company_profile if a.drive and a.drive.company else None
        writer.writerow([a.student.name if a.student else "",a.student.email if a.student else "",p.roll_number if p else "",p.branch if p else "",p.cgpa if p else "",c.company_name if c else "",a.drive.role_title if a.drive else "",a.status,a.applied_at.strftime("%Y-%m-%d %H:%M") if a.applied_at else ""])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=placement-applications.csv"})


@advanced_bp.route("/cdpc/report/offers.csv", methods=["GET"])
def offers_csv():
    user, err = require_role("cdpc")
    if err: return err
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(["Student","Company","Role","Package","Designation","Joining Date","Status"])
    for o in Offer.query.order_by(Offer.created_at.desc()).all():
        writer.writerow([o.student.name if o.student else "",o.company.company_profile.company_name if o.company and o.company.company_profile else "",o.drive.role_title if o.drive else "",o.package_offered,o.designation,o.joining_date,o.status])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=placement-offers.csv"})