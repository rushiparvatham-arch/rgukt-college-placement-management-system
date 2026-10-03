import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "rgukt-ongole-placement-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'placement.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # check_same_thread=False is required for SQLite once the dev server runs
    # threaded (see run.py) — otherwise SQLite raises its own thread-safety
    # error when two concurrent requests are served on different threads.
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "resumes")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    ALLOWED_RESUME_EXTENSIONS = {"pdf"}
    PROFILE_PICTURE_FOLDER = os.path.join(BASE_DIR, "uploads", "profile_pictures")
    ALLOWED_PICTURE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    MAX_PICTURE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
    SESSION_COOKIE_SAMESITE = "Lax"

    # ---- Email OTP (used for verifying email during manual registration) ----
    # If SMTP_HOST/SMTP_USER/SMTP_PASSWORD are not set, the app falls back to
    # printing the OTP to the server console so registration is still testable
    # locally without a real mail account. See README for setup instructions.
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "no-reply@rguktong.ac.in"))
    OTP_EXPIRY_MINUTES = 10
    OTP_MAX_ATTEMPTS = 5

    # ---- Google OAuth ("Continue with Google") ----
    # These MUST be created by you in Google Cloud Console (APIs & Services ->
    # Credentials -> OAuth Client ID -> Web application). No one else can issue
    # these on your behalf. If unset, the Google button shows a clear message
    # instead of pretending to work. See README for the exact setup steps.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
