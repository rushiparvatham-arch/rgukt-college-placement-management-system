"""
Email OTP utility for verifying an address during manual registration.

Sends a real email via SMTP when SMTP_HOST/SMTP_USER/SMTP_PASSWORD are
configured (see app/config.py). If they are not configured — the common case
for local development/grading without a real mailbox — the OTP is printed to
the server console instead, clearly labelled, so registration is still fully
testable without pretending an email was actually delivered.
"""

import random
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from flask import current_app


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def send_otp_email(to_email, otp, purpose="register"):
    """
    Returns (sent_via_smtp: bool, error: str | None).
    Never raises — a failed send should not crash registration; the caller
    decides how to react (e.g. still allow the console-fallback OTP to work).
    """
    cfg = current_app.config
    subject = "Your RGUKT Ongole Placement Portal verification code"
    body = (
        f"Your verification code is: {otp}\n\n"
        f"This code expires in {cfg['OTP_EXPIRY_MINUTES']} minutes. "
        f"If you did not request this, you can safely ignore this email.\n\n"
        f"— RGUKT Ongole CDPC Placement Portal"
    )

    if not (cfg.get("SMTP_HOST") and cfg.get("SMTP_USER") and cfg.get("SMTP_PASSWORD")):
        # Local-dev / not-yet-configured fallback: print clearly to the console.
        print(
            f"\n{'='*60}\n"
            f"[DEV MODE — SMTP not configured] Verification code for {to_email}: {otp}\n"
            f"{'='*60}\n"
        )
        return False, None

    try:
        msg = MIMEMultipart()
        msg["From"] = cfg["SMTP_FROM"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=10) as server:
            server.starttls(context=context)
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            server.sendmail(cfg["SMTP_FROM"], [to_email], msg.as_string())
        return True, None
    except Exception as e:
        # Fall back to console so the user isn't blocked if SMTP creds are wrong.
        print(
            f"\n{'='*60}\n"
            f"[SMTP SEND FAILED — falling back to console] "
            f"Verification code for {to_email}: {otp}\n"
            f"Error: {e}\n"
            f"{'='*60}\n"
        )
        return False, str(e)


def otp_expiry():
    from flask import current_app
    return datetime.utcnow() + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])
