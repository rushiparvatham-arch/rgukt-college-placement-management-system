"""
Email utilities: OTP generation and SMTP delivery.

Real email is sent when SMTP_USER + SMTP_PASSWORD are configured (in the
environment or in the project's .env file - see .env.example).  Both STARTTLS
(port 587) and implicit SSL (port 465) are supported.

If SMTP is not configured the code is printed to the server console, clearly
labelled [DEV MODE], so the flow can still be demonstrated locally.
"""
import html
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from flask import current_app


def generate_otp():
    # secrets (CSPRNG) instead of random: OTPs are security credentials.
    return f"{secrets.randbelow(1_000_000):06d}"


def smtp_configured(cfg=None):
    cfg = cfg or current_app.config
    return bool(cfg.get("SMTP_HOST") and cfg.get("SMTP_USER") and cfg.get("SMTP_PASSWORD"))


def _html_shell(title, intro, big_text, footer):
    t, i, b, f = (html.escape(x) for x in (title, intro, big_text, footer))
    return f"""<!doctype html><html><body style="margin:0;background:#0b1220;padding:24px;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"><tr><td align="center">
<table role="presentation" width="480" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:14px;overflow:hidden;max-width:480px;">
<tr><td style="background:linear-gradient(135deg,#0f3d91,#1c7ed6);padding:22px 28px;color:#fff;">
<div style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.85;">RGUKT Ongole</div>
<div style="font-size:20px;font-weight:700;margin-top:4px;">Training &amp; Placement Cell</div></td></tr>
<tr><td style="padding:28px;color:#1b2433;">
<h2 style="margin:0 0 10px;font-size:20px;">{t}</h2>
<p style="margin:0 0 20px;font-size:14px;line-height:1.6;color:#4a5568;">{i}</p>
<div style="text-align:center;margin:8px 0 22px;"><span style="display:inline-block;font-size:34px;font-weight:700;letter-spacing:10px;padding:14px 22px;border-radius:10px;background:#eef4ff;color:#0f3d91;border:1px dashed #1c7ed6;">{b}</span></div>
<p style="margin:0;font-size:12px;line-height:1.6;color:#718096;">{f}</p>
</td></tr></table></td></tr></table></body></html>"""


def send_email(to_email, subject, text_body, html_body=None):
    """Send one email. Returns (sent: bool, error: str | None). Never raises."""
    cfg = current_app.config
    if not smtp_configured(cfg):
        return False, "SMTP is not configured"
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((cfg.get("SMTP_FROM_NAME") or "", cfg["SMTP_FROM"]))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()
        if cfg.get("SMTP_SSL"):
            server = smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15, context=context)
        else:
            server = smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
        with server:
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
            server.sendmail(cfg["SMTP_FROM"], [to_email], msg.as_string())
        return True, None
    except smtplib.SMTPAuthenticationError:
        return False, ("SMTP login was rejected. For Gmail you must use a 16-character App Password "
                       "(Google Account -> Security -> 2-Step Verification -> App passwords), not your normal password.")
    except Exception as e:  # network, TLS, DNS ...
        return False, f"{type(e).__name__}: {e}"


def send_otp_email(to_email, otp, purpose="register"):
    """
    Returns (sent_via_smtp: bool, error: str | None).
    Falls back to printing the code on the server console if SMTP is missing or
    failing, so the user is never completely blocked in local development.
    """
    cfg = current_app.config
    minutes = cfg["OTP_EXPIRY_MINUTES"]
    if purpose == "forgot_password":
        subject = f"{otp} is your RGUKT password reset code"
        title = "Reset your password"
        intro = "Use the verification code below to reset your RGUKT Ongole Placement Portal password."
        footer = (f"This code expires in {minutes} minutes and can be used once. "
                  "If you did not request a password reset, you can safely ignore this email - your password will not change.")
    else:
        subject = f"{otp} is your RGUKT verification code"
        title = "Verify your email"
        intro = "Use the verification code below to finish creating your RGUKT Ongole Placement Portal account."
        footer = f"This code expires in {minutes} minutes. If you did not request it, you can ignore this email."

    text = f"{title}\n\n{intro}\n\nYour code: {otp}\n\n{footer}\n\n- RGUKT Ongole CDPC Placement Portal"
    sent, err = send_email(to_email, subject, text, _html_shell(title, intro, otp, footer))
    if sent:
        return True, None

    print(
        f"\n{'=' * 60}\n"
        f"[DEV MODE - email NOT delivered] {purpose} code for {to_email}: {otp}\n"
        + (f"Reason: {err}\n" if err else "")
        + f"{'=' * 60}\n",
        flush=True,
    )
    current_app.logger.warning("OTP email to %s not sent: %s", to_email, err)
    return False, err


def otp_expiry():
    return datetime.utcnow() + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])