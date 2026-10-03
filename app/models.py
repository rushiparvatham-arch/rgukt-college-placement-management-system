from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student | cdpc | company
    phone = db.Column(db.String(20))
    avatar_color = db.Column(db.String(7), default="#f97316")
    profile_picture = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    auth_provider = db.Column(db.String(20), default="password")  # password | google

    student_profile = db.relationship("StudentProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship("CompanyProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    cdpc_profile = db.relationship("CDPCProfile", backref="user", uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def set_unusable_password(self):
        """Used for Google-authenticated accounts, which never log in with a password."""
        import secrets
        self.password_hash = generate_password_hash(secrets.token_hex(32))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        base = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "avatar_color": self.avatar_color,
            "profile_picture": self.profile_picture,
            "email_verified": self.email_verified,
            "auth_provider": self.auth_provider,
        }
        if self.role == "student" and self.student_profile:
            base["profile"] = self.student_profile.to_dict()
        elif self.role == "company" and self.company_profile:
            base["profile"] = self.company_profile.to_dict()
        elif self.role == "cdpc" and self.cdpc_profile:
            base["profile"] = self.cdpc_profile.to_dict()
        return base


class StudentProfile(db.Model):
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    roll_number = db.Column(db.String(30), unique=True)
    branch = db.Column(db.String(80), default="Computer Science & Engineering")
    batch_year = db.Column(db.String(9), default="2022-2026")
    current_year = db.Column(db.String(20), default="4th Year")
    cgpa = db.Column(db.Float, default=0.0)
    tenth_percent = db.Column(db.Float, default=0.0)
    inter_percent = db.Column(db.Float, default=0.0)
    backlogs = db.Column(db.Integer, default=0)
    address = db.Column(db.String(255))
    gender = db.Column(db.String(15))
    dob = db.Column(db.String(15))
    skills = db.Column(db.Text, default="")  # comma separated
    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))
    resume_filename = db.Column(db.String(255))
    resume_text = db.Column(db.Text)
    resume_builder_data = db.Column(db.Text)  # JSON string from the in-app resume creator
    ats_score = db.Column(db.Integer, default=0)
    placed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "roll_number": self.roll_number,
            "branch": self.branch,
            "batch_year": self.batch_year,
            "current_year": self.current_year,
            "cgpa": self.cgpa,
            "tenth_percent": self.tenth_percent,
            "inter_percent": self.inter_percent,
            "backlogs": self.backlogs,
            "address": self.address,
            "gender": self.gender,
            "dob": self.dob,
            "skills": self.skills,
            "linkedin": self.linkedin,
            "github": self.github,
            "resume_filename": self.resume_filename,
            "resume_builder_data": self.resume_builder_data,
            "ats_score": self.ats_score,
            "placed": self.placed,
        }


class CompanyProfile(db.Model):
    __tablename__ = "company_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    company_name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(120))
    website = db.Column(db.String(200))
    hr_name = db.Column(db.String(120))
    hr_designation = db.Column(db.String(120))
    about = db.Column(db.Text)
    address = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "company_name": self.company_name,
            "industry": self.industry,
            "website": self.website,
            "hr_name": self.hr_name,
            "hr_designation": self.hr_designation,
            "about": self.about,
            "address": self.address,
            "is_approved": self.is_approved,
        }


class CDPCProfile(db.Model):
    __tablename__ = "cdpc_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    designation = db.Column(db.String(120), default="Placement Officer")
    department = db.Column(db.String(120), default="CDPC")

    def to_dict(self):
        return {"designation": self.designation, "department": self.department}


class Drive(db.Model):
    __tablename__ = "drives"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role_title = db.Column(db.String(150), nullable=False)
    job_type = db.Column(db.String(30), default="Full-Time")  # Full-Time, Internship
    description = db.Column(db.Text)
    ctc = db.Column(db.String(50))
    location = db.Column(db.String(120))
    min_cgpa = db.Column(db.Float, default=0.0)
    max_backlogs = db.Column(db.Integer, default=0)
    eligible_branches = db.Column(db.String(255), default="All Branches")
    drive_date = db.Column(db.String(20))
    application_deadline = db.Column(db.String(20))
    status = db.Column(db.String(20), default="Upcoming")  # Upcoming, Ongoing, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="drive", cascade="all, delete-orphan")
    company = db.relationship("User", foreign_keys=[company_id])

    def to_dict(self, include_company=True):
        d = {
            "id": self.id,
            "role_title": self.role_title,
            "job_type": self.job_type,
            "description": self.description,
            "ctc": self.ctc,
            "location": self.location,
            "min_cgpa": self.min_cgpa,
            "max_backlogs": self.max_backlogs,
            "eligible_branches": self.eligible_branches,
            "drive_date": self.drive_date,
            "application_deadline": self.application_deadline,
            "status": self.status,
            "applicants_count": len(self.applications),
        }
        if include_company and self.company and self.company.company_profile:
            d["company_name"] = self.company.company_profile.company_name
            d["company_id"] = self.company_id
        return d


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("drives.id"), nullable=False)
    status = db.Column(db.String(30), default="Applied")
    # Applied -> Shortlisted -> Interview -> Selected / Rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("User", foreign_keys=[student_id])
    interviews = db.relationship("Interview", backref="application", cascade="all, delete-orphan")
    result = db.relationship("Result", backref="application", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else None,
            "roll_number": self.student.student_profile.roll_number if self.student and self.student.student_profile else None,
            "branch": self.student.student_profile.branch if self.student and self.student.student_profile else None,
            "cgpa": self.student.student_profile.cgpa if self.student and self.student.student_profile else None,
            "drive_id": self.drive_id,
            "role_title": self.drive.role_title if self.drive else None,
            "company_name": self.drive.company.company_profile.company_name if self.drive and self.drive.company and self.drive.company.company_profile else None,
            "status": self.status,
            "applied_at": self.applied_at.strftime("%d %b %Y"),
        }


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    round_name = db.Column(db.String(100), default="Technical Round 1")
    scheduled_at = db.Column(db.String(40))
    mode = db.Column(db.String(20), default="Online")  # Online, Offline
    venue_or_link = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Scheduled")  # Scheduled, Completed, Cancelled
    feedback = db.Column(db.Text)

    def to_dict(self):
        app = self.application
        return {
            "id": self.id,
            "application_id": self.application_id,
            "round_name": self.round_name,
            "scheduled_at": self.scheduled_at,
            "mode": self.mode,
            "venue_or_link": self.venue_or_link,
            "status": self.status,
            "feedback": self.feedback,
            "role_title": app.drive.role_title if app and app.drive else None,
            "company_name": app.drive.company.company_profile.company_name if app and app.drive and app.drive.company.company_profile else None,
            "student_name": app.student.name if app and app.student else None,
        }


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False, unique=True)
    outcome = db.Column(db.String(20))  # Selected, Rejected, Waitlisted
    package_offered = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        app = self.application
        return {
            "id": self.id,
            "application_id": self.application_id,
            "outcome": self.outcome,
            "package_offered": self.package_offered,
            "remarks": self.remarks,
            "published_at": self.published_at.strftime("%d %b %Y"),
            "role_title": app.drive.role_title if app and app.drive else None,
            "company_name": app.drive.company.company_profile.company_name if app and app.drive and app.drive.company.company_profile else None,
            "student_name": app.student.name if app and app.student else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "link": self.link,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%d %b, %I:%M %p"),
        }


class NotificationBroadcast(db.Model):
    """Audit trail for CDPC-sent announcements (fans out into individual
    Notification rows for each matching recipient at send time)."""
    __tablename__ = "notification_broadcasts"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    audience = db.Column(db.String(30), nullable=False)  # all_students | all_companies | branch | everyone
    branch = db.Column(db.String(120))  # only set when audience == "branch"
    message = db.Column(db.String(255), nullable=False)
    recipient_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])

    def to_dict(self):
        audience_labels = {
            "all_students": "All Students",
            "all_companies": "All Companies",
            "branch": f"Branch: {self.branch}",
            "everyone": "Everyone",
        }
        return {
            "id": self.id,
            "sender_name": self.sender.name if self.sender else None,
            "audience": self.audience,
            "audience_label": audience_labels.get(self.audience, self.audience),
            "message": self.message,
            "recipient_count": self.recipient_count,
            "created_at": self.created_at.strftime("%d %b %Y, %I:%M %p"),
        }


class AptitudeTest(db.Model):
    __tablename__ = "aptitude_tests"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), default="General")
    test_type = db.Column(db.String(20), default="aptitude")  # aptitude | skill
    duration_minutes = db.Column(db.Integer, default=15)
    questions_json = db.Column(db.Text)  # JSON string of question list

    def to_dict(self, include_answers=False):
        import json
        questions = json.loads(self.questions_json or "[]")
        if not include_answers:
            questions = [{k: v for k, v in q.items() if k != "answer"} for q in questions]
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "test_type": self.test_type,
            "duration_minutes": self.duration_minutes,
            "questions": questions,
            "total_questions": len(questions),
        }


class AptitudeResult(db.Model):
    __tablename__ = "aptitude_results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("aptitude_tests.id"), nullable=False)
    score = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    level = db.Column(db.String(20))  # Beginner / Intermediate / Advanced — used for skill-type tests
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    test = db.relationship("AptitudeTest")

    def to_dict(self):
        return {
            "id": self.id,
            "test_id": self.test_id,
            "test_title": self.test.title if self.test else None,
            "category": self.test.category if self.test else None,
            "score": self.score,
            "total": self.total,
            "percent": round((self.score / self.total) * 100) if self.total else 0,
            "level": self.level,
            "taken_at": self.taken_at.strftime("%d %b %Y"),
        }


class EmailOTP(db.Model):
    """One-time codes for verifying an email address during manual registration.
    Google sign-in never uses this table — Google has already verified the email."""
    __tablename__ = "email_otps"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.String(30), default="register")
    attempts = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_otp(self, raw_otp):
        self.otp_hash = generate_password_hash(raw_otp)

    def check_otp(self, raw_otp):
        return check_password_hash(self.otp_hash, raw_otp)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at


def compute_skill_level(score, total):
    if total == 0:
        return "Beginner"
    pct = (score / total) * 100
    if pct >= 75:
        return "Advanced"
    if pct >= 40:
        return "Intermediate"
    return "Beginner"
