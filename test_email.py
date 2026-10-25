"""Send a test email to check your SMTP settings:  python test_email.py you@example.com"""
import sys
from app import create_app
from app.utils.email_utils import send_email, smtp_configured

app = create_app()
with app.app_context():
    if not smtp_configured():
        sys.exit("SMTP not configured: set SMTP_USER and SMTP_PASSWORD in .env first.")
    to = sys.argv[1] if len(sys.argv) > 1 else app.config["SMTP_USER"]
    ok, err = send_email(to, "RGUKT portal test email", "Your SMTP settings work.")
    print("Sent to", to) if ok else print("FAILED:", err)
