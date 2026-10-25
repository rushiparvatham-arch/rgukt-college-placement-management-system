import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session, redirect, url_for, current_app
from app.extensions import db, oauth
from app.models import User, StudentProfile, CompanyProfile, CDPCProfile, Notification, EmailOTP
import time
from app.utils.email_utils import generate_otp, send_otp_email, otp_expiry, smtp_configured

# email -> unix time of the last reset request. Kept in memory (not the DB) so the
# cooldown applies identically whether or not the account exists (no enumeration).
_reset_last_request = {}

auth_bp = Blueprint("auth", __name__)

VALID_ROLES = ("student", "cdpc", "company")
DASHBOARD_ROUTES = {
    "student": "/student/dashboard",
    "cdpc": "/cdpc/dashboard",
    "company": "/company/dashboard",
}


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


def _create_profile_for_role(user, role, data, name):
    """Shared by manual registration and Google sign-up so both paths create
    identical, correctly-defaulted profile rows."""
    if role == "student":
        db.session.add(StudentProfile(
            user_id=user.id,
            roll_number=data.get("roll_number") or f"N{user.id:04d}",
            branch=data.get("branch", "Computer Science & Engineering"),
        ))
    elif role == "company":
        db.session.add(CompanyProfile(
            user_id=user.id,
            company_name=data.get("company_name", name),
            industry=data.get("industry", ""),
            hr_name=name,
        ))
    elif role == "cdpc":
        db.session.add(CDPCProfile(user_id=user.id, designation=data.get("designation", "Placement Officer")))


@auth_bp.route("/config", methods=["GET"])
def auth_config():
    """Lets the frontend know whether Google Sign-In is actually configured,
    instead of showing a button that would otherwise fail silently."""
    return jsonify({
        "google_oauth_enabled": current_app.config.get("GOOGLE_OAUTH_ENABLED", False),
        "email_configured": smtp_configured(),
        "otp_resend_seconds": current_app.config["OTP_RESEND_SECONDS"],
    })


# ---------------- Email OTP verification ----------------

@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    purpose = data.get("purpose", "register")

    if not email or "@" not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400
    if purpose == "register" and User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists. Please sign in instead."}), 409

    # Clear any previous unconsumed codes for this email+purpose before issuing a new one.
    EmailOTP.query.filter_by(email=email, purpose=purpose).delete()

    otp = generate_otp()
    record = EmailOTP(email=email, purpose=purpose, expires_at=otp_expiry())
    record.set_otp(otp)
    db.session.add(record)
    db.session.commit()

    sent_via_smtp, err = send_otp_email(email, otp, purpose)
    return jsonify({
        "message": "Verification code sent to your email." if sent_via_smtp
        else "Email delivery is not configured on this server (see .env.example), so the code was printed to the server console instead.",
        "sent_via_smtp": sent_via_smtp,
    })


def _verify_otp_or_error(email, otp, purpose="register"):
    """Returns None on success, or an (response, status_code) tuple on failure."""
    record = (
        EmailOTP.query.filter_by(email=email, purpose=purpose)
        .order_by(EmailOTP.created_at.desc())
        .first()
    )
    if not record:
        return jsonify({"error": "Please request a verification code first."}), 400
    if record.is_expired():
        return jsonify({"error": "This code has expired. Please request a new one."}), 400
    if record.attempts >= current_app.config["OTP_MAX_ATTEMPTS"]:
        return jsonify({"error": "Too many incorrect attempts. Please request a new code."}), 400
    if not otp or not record.check_otp(otp):
        record.attempts += 1
        db.session.commit()
        return jsonify({"error": "Incorrect verification code. Please try again."}), 400

    db.session.delete(record)
    db.session.commit()
    return None


# ---------------- Forgot password / password reset ----------------

@auth_bp.route("/forgot-password/send-otp", methods=["POST"])
def forgot_password_send_otp():
    """Start a password reset with an email OTP.

    The response deliberately does not reveal whether the email exists. This
    prevents account-enumeration through the forgot-password form.
    """
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    # Cooldown (same for existing and non-existing accounts).
    cooldown = current_app.config["OTP_RESEND_SECONDS"]
    wait = cooldown - (time.time() - _reset_last_request.get(email, 0))
    if wait > 0:
        return jsonify({
            "error": f"Please wait {int(wait) + 1} seconds before requesting another code.",
            "retry_after": int(wait) + 1,
        }), 429
    _reset_last_request[email] = time.time()

    configured = smtp_configured()
    generic = ("A 6-digit verification code has been sent to your email. It is valid for "
               f"{current_app.config['OTP_EXPIRY_MINUTES']} minutes. Check your Spam folder if you don't see it.")
    if not configured:
        generic = ("Email delivery isn't configured on this server yet, so the code was printed in the "
                   "server console (see .env.example to enable real emails).")

    # The outward response is identical whether or not the account exists.
    user = User.query.filter_by(email=email).first()
    if user:
        EmailOTP.query.filter_by(email=email, purpose="forgot_password").delete()
        otp = generate_otp()
        record = EmailOTP(email=email, purpose="forgot_password", expires_at=otp_expiry())
        record.set_otp(otp)
        db.session.add(record)
        db.session.commit()
        sent_via_smtp, err = send_otp_email(email, otp, purpose="forgot_password")
        if configured and not sent_via_smtp:
            # Server-side misconfiguration (bad app password, network...) - not
            # account-specific, so it is safe and far more useful to surface it.
            return jsonify({"error": "We couldn't send the email right now. Please try again in a moment "
                                     "or contact the CDPC office.", "detail": err}), 502

    return jsonify({"message": generic, "sent_via_smtp": configured})


@auth_bp.route("/forgot-password/verify-otp", methods=["POST"])
def forgot_password_verify_otp():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return jsonify({"error": "Please enter your email and 6-digit verification code."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid or expired verification code."}), 400

    otp_error = _verify_otp_or_error(email, otp, purpose="forgot_password")
    if otp_error:
        return otp_error

    # The verified email is stored only in the signed Flask session and is
    # valid for a short period. No password can be changed without this step.
    from datetime import datetime
    session["password_reset_email"] = email
    session["password_reset_verified_at"] = datetime.utcnow().timestamp()
    return jsonify({"message": "Code verified. You can now create a new password."})


@auth_bp.route("/forgot-password/reset", methods=["POST"])
def forgot_password_reset():
    data = request.get_json(force=True)
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    email = session.get("password_reset_email")
    verified_at = session.get("password_reset_verified_at")
    if not email or not verified_at:
        return jsonify({"error": "Please verify the password-reset code first."}), 400

    from datetime import datetime, timedelta
    verified_time = datetime.fromtimestamp(float(verified_at))
    if datetime.utcnow() - verified_time > timedelta(minutes=current_app.config["PASSWORD_RESET_SESSION_MINUTES"]):
        session.pop("password_reset_email", None)
        session.pop("password_reset_verified_at", None)
        return jsonify({"error": "Your password-reset session has expired. Please request a new code."}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400
    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        session.pop("password_reset_email", None)
        session.pop("password_reset_verified_at", None)
        return jsonify({"error": "Unable to reset the password. Please start again."}), 400

    user.set_password(new_password)
    # A successful password reset means this account can authenticate with
    # email/password. Google identity, if present, is intentionally retained.
    user.auth_provider = "password"
    user.email_verified = True
    db.session.commit()

    session.pop("password_reset_email", None)
    session.pop("password_reset_verified_at", None)
    session.pop("user_id", None)
    session.pop("role", None)

    return jsonify({"message": "Password reset successfully. Please sign in with your new password."})


# ---------------- Manual registration / login ----------------

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")
    phone = data.get("phone", "")
    otp = (data.get("otp") or "").strip()

    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role selected."}), 400
    if not name or not email or len(password) < 6:
        return jsonify({"error": "Please provide a valid name, email and a password of at least 6 characters."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    otp_error = _verify_otp_or_error(email, otp, purpose="register")
    if otp_error:
        return otp_error

    user = User(name=name, email=email, role=role, phone=phone, email_verified=True, auth_provider="password")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    _create_profile_for_role(user, role, data, name)

    db.session.add(Notification(user_id=user.id, message=f"Welcome to RGUKT Ongole Placement Portal, {name.split()[0]}!"))
    db.session.commit()

    session["user_id"] = user.id
    session["role"] = user.role
    return jsonify({"message": "Account created successfully.", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")

    user = User.query.filter_by(email=email).first()
    if not user or user.auth_provider != "password" or not user.check_password(password):
        if user and user.auth_provider == "google":
            return jsonify({"error": "This account uses Google Sign-In. Please continue with Google instead."}), 401
        return jsonify({"error": "Invalid email or password."}), 401
    if role and user.role != role:
        return jsonify({"error": f"This account is not registered as {role}. Please choose the correct portal."}), 403

    session["user_id"] = user.id
    session["role"] = user.role
    return jsonify({"message": "Login successful.", "user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})


@auth_bp.route("/me", methods=["GET"])
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"user": user.to_dict()})


# ---------------- Google OAuth ("Continue with Google") ----------------

@auth_bp.route("/google/login", methods=["GET"])
def google_login():
    role = request.args.get("role")
    if role not in VALID_ROLES:
        return redirect("/login?error=missing_role")
    if not current_app.config.get("GOOGLE_OAUTH_ENABLED"):
        return redirect(f"/login?role={role}&error=google_not_configured")

    session["oauth_role"] = role
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback", methods=["GET"])
def google_callback():
    role = session.pop("oauth_role", None)
    if role not in VALID_ROLES:
        return redirect("/login?error=missing_role")
    if not current_app.config.get("GOOGLE_OAUTH_ENABLED"):
        return redirect(f"/login?role={role}&error=google_not_configured")

    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or {}
        google_id = userinfo.get("sub")
        email = (userinfo.get("email") or "").strip().lower()
        name = userinfo.get("name") or (email.split("@")[0] if email else "Google User")
        google_email_verified = bool(userinfo.get("email_verified"))
    except Exception:
        current_app.logger.exception("Google OAuth callback failed")
        return redirect(f"/login?role={role}&error=google_auth_failed")

    if not email or not google_id:
        return redirect(f"/login?role={role}&error=google_auth_failed")

    user = User.query.filter_by(google_id=google_id).first()

    if not user:
        existing = User.query.filter_by(email=email).first()
        if existing:
            if existing.role != role:
                return redirect(f"/login?role={role}&error=role_mismatch")
            # Link this Google identity to their existing password-based account.
            existing.google_id = google_id
            if google_email_verified:
                existing.email_verified = True
            user = existing
        else:
            user = User(
                name=name, email=email, role=role,
                google_id=google_id, auth_provider="google",
                email_verified=google_email_verified,
            )
            user.set_unusable_password()
            db.session.add(user)
            db.session.flush()
            _create_profile_for_role(user, role, {}, name)
            db.session.add(Notification(user_id=user.id, message=f"Welcome to RGUKT Ongole Placement Portal, {name.split()[0]}!"))

    db.session.commit()
    session["user_id"] = user.id
    session["role"] = user.role
    return redirect(DASHBOARD_ROUTES[user.role])


# ---------------- Profile management ----------------

def _allowed_picture_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_PICTURE_EXTENSIONS"]


@auth_bp.route("/profile-picture", methods=["POST"])
def upload_profile_picture():
    """Works identically for all three roles — the profile picture lives on
    the shared User record, not the role-specific profile table."""
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401

    if "picture" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    file = request.files["picture"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not _allowed_picture_file(file.filename):
        return jsonify({"error": "Please upload a JPG, PNG, or WEBP image."}), 400

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > current_app.config["MAX_PICTURE_SIZE_BYTES"]:
        return jsonify({"error": "Image is too large. Please upload one under 2 MB."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = secure_filename(f"user{user.id}.{ext}")

    # Remove any previous picture (possibly a different extension) so old
    # files don't pile up unreferenced on disk.
    if user.profile_picture:
        old_path = os.path.join(current_app.config["PROFILE_PICTURE_FOLDER"], user.profile_picture)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    filepath = os.path.join(current_app.config["PROFILE_PICTURE_FOLDER"], filename)
    file.save(filepath)

    user.profile_picture = filename
    db.session.commit()
    return jsonify({"message": "Profile picture updated.", "profile_picture": filename})


@auth_bp.route("/profile-picture", methods=["DELETE"])
def delete_profile_picture():
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401

    if user.profile_picture:
        old_path = os.path.join(current_app.config["PROFILE_PICTURE_FOLDER"], user.profile_picture)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
        user.profile_picture = None
        db.session.commit()
    return jsonify({"message": "Profile picture removed."})


@auth_bp.route("/update-profile", methods=["PUT"])
def update_profile():
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401

    data = request.get_json(force=True)
    user.name = data.get("name", user.name).strip() or user.name
    user.phone = data.get("phone", user.phone)

    if user.role == "student" and user.student_profile:
        p = user.student_profile
        p.branch = data.get("branch", p.branch)
        p.current_year = data.get("current_year", p.current_year)
        p.batch_year = data.get("batch_year", p.batch_year)
        if "cgpa" in data and data["cgpa"] not in (None, ""):
            p.cgpa = float(data["cgpa"])
        if "tenth_percent" in data and data["tenth_percent"] not in (None, ""):
            p.tenth_percent = float(data["tenth_percent"])
        if "inter_percent" in data and data["inter_percent"] not in (None, ""):
            p.inter_percent = float(data["inter_percent"])
        if "backlogs" in data and data["backlogs"] not in (None, ""):
            p.backlogs = int(data["backlogs"])
        p.address = data.get("address", p.address)
        p.gender = data.get("gender", p.gender)
        p.dob = data.get("dob", p.dob)
        p.skills = data.get("skills", p.skills)
        p.linkedin = data.get("linkedin", p.linkedin)
        p.github = data.get("github", p.github)

    elif user.role == "company" and user.company_profile:
        p = user.company_profile
        p.company_name = data.get("company_name", p.company_name)
        p.industry = data.get("industry", p.industry)
        p.website = data.get("website", p.website)
        p.hr_name = data.get("hr_name", p.hr_name)
        p.hr_designation = data.get("hr_designation", p.hr_designation)
        p.about = data.get("about", p.about)
        p.address = data.get("address", p.address)

    elif user.role == "cdpc" and user.cdpc_profile:
        p = user.cdpc_profile
        p.designation = data.get("designation", p.designation)
        p.department = data.get("department", p.department)

    db.session.commit()
    return jsonify({"message": "Profile updated successfully.", "user": user.to_dict()})


@auth_bp.route("/change-password", methods=["PUT"])
def change_password():
    user = current_user()
    if not user:
        return jsonify({"error": "Not authenticated."}), 401
    if user.auth_provider == "google":
        return jsonify({"error": "This account signs in with Google and doesn't have a password to change."}), 400
    data = request.get_json(force=True)
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    if not user.check_password(old_password):
        return jsonify({"error": "Current password is incorrect."}), 400
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters."}), 400
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully."})