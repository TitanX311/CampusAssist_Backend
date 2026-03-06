"""
Async email sender for Campus Assist Auth Service.

In development (`SKIP_EMAIL_VERIFICATION=true`) the verification link is
logged to stdout instead of being sent over SMTP — no email credentials
needed in a local / minikube environment.
"""

import logging
from email.message import EmailMessage

import aiosmtplib

from auth.config.settings import get_settings

logger = logging.getLogger(__name__)


async def send_verification_email(to_email: str, token: str) -> None:
    """Send (or log) a verification email to *to_email* containing *token*."""
    settings = get_settings()
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    # Dev / CI bypass ─────────────────────────────────────────────────────────
    if settings.SKIP_EMAIL_VERIFICATION:
        logger.info(
            "[EMAIL SKIP] Verification link for %s → %s", to_email, verify_url
        )
        return

    # Build message ───────────────────────────────────────────────────────────
    expire_hours = settings.EMAIL_VERIFICATION_EXPIRE_MINUTES // 60
    subject = f"Verify your {settings.APP_NAME} email address"

    plain = (
        f"Welcome to {settings.APP_NAME}!\n\n"
        f"Please verify your email address by visiting:\n{verify_url}\n\n"
        f"This link expires in {expire_hours} hour(s).\n\n"
        "If you did not create an account you can safely ignore this email."
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<body style="font-family:sans-serif;color:#333;max-width:600px;margin:0 auto;padding:24px">
  <h2 style="color:#4F46E5">Welcome to {settings.APP_NAME}!</h2>
  <p>Click the button below to verify your email address.<br>
     This link expires in <strong>{expire_hours} hour(s)</strong>.</p>
  <p style="margin:32px 0">
    <a href="{verify_url}"
       style="background:#4F46E5;color:#fff;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-size:15px">
      Verify Email
    </a>
  </p>
  <p style="color:#888;font-size:12px">
    If you did not create a {settings.APP_NAME} account you can safely ignore
    this email.
  </p>
</body>
</html>"""

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USERNAME
    msg["To"] = to_email
    msg.set_content(plain)
    msg.add_alternative(html, subtype="html")

    # Send ────────────────────────────────────────────────────────────────────
    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=settings.SMTP_USE_TLS,
        )
        logger.info("Verification email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
        raise
