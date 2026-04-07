"""Email service: send and read emails via SMTP/Gmail."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send emails via SMTP (Gmail compatible)."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email_from: Optional[str] = None,
    ):
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.username = username or settings.SMTP_USERNAME
        self.password = password or settings.SMTP_PASSWORD
        self.email_from = email_from or settings.EMAIL_FROM or self.username

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an email."""
        if not self.username or not self.password:
            return {"success": False, "error": "SMTP credentials not configured."}
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = ", ".join(to)
            if cc:
                msg["Cc"] = ", ".join(cc)

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            recipients = to + (cc or []) + (bcc or [])

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.email_from, recipients, msg.as_string())

            logger.info("Email sent to %s", to)
            return {"success": True, "to": to, "subject": subject}
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "error": "SMTP authentication failed. Check credentials."}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Email send failed: %s", exc)
            return {"success": False, "error": str(exc)}
