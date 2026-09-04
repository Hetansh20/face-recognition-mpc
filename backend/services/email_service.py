"""
email_service.py
Sends attendance CSV reports to faculty via Brevo API (preferred) with
Gmail SMTP fallback — mirrors the legacy web app's email_service.py so the
mobile confirm-attendance flow behaves identically.
"""

import re
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

import requests

from backend.config import Config

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class EmailService:
    """Sends CSV attachments to faculty; Brevo HTTP API first, SMTP fallback."""

    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.sender_email = Config.SENDER_EMAIL
        self.sender_password = Config.SENDER_PASSWORD
        self.brevo_api_key = Config.BREVO_API_KEY

    def validate_email(self, email: str) -> bool:
        return bool(EMAIL_PATTERN.match(str(email).strip()))

    def is_configured(self) -> bool:
        return bool(self.brevo_api_key or (self.sender_email and self.sender_password))

    def send_csv_attachment(self, recipient_email: str, recipient_name: str,
                             csv_bytes: bytes, filename: str,
                             subject: str = None, extra_html: str = None):
        """Send a CSV as an in-memory attachment. Returns (success: bool, message: str)."""
        try:
            recipient_email = str(recipient_email).strip()
            if not self.validate_email(recipient_email):
                return False, f"Invalid email: {recipient_email}"

            if not self.is_configured():
                return False, "Email service not configured (missing BREVO_API_KEY or SENDER_EMAIL/SENDER_PASSWORD)"

            subject = subject or f"Attendance Report — {datetime.now().strftime('%d %b %Y %H:%M')}"
            plain = (
                f"Dear {recipient_name},\n\n"
                f"Please find the attendance report attached.\n\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Best regards,\nAttendance System"
            )

            if self.brevo_api_key:
                ok, msg = self._send_via_brevo(recipient_email, recipient_name, subject, plain, extra_html, csv_bytes, filename)
                if ok:
                    return True, msg
                print(f"[EmailService] Brevo failed, falling back to SMTP: {msg}")

            return self._send_via_smtp(recipient_email, subject, plain, extra_html, csv_bytes, filename)
        except Exception as e:
            return False, f"Email prep error: {str(e)}"

    def _send_via_brevo(self, recipient_email, recipient_name, subject, plain, extra_html, csv_bytes, filename):
        try:
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": self.brevo_api_key,
                "content-type": "application/json"
            }
            payload = {
                "sender": {"name": "Attendance System", "email": self.sender_email},
                "to": [{"email": recipient_email, "name": recipient_name}],
                "subject": subject,
                "textContent": plain,
                "attachment": [
                    {"content": base64.b64encode(csv_bytes).decode("utf-8"), "name": filename}
                ]
            }
            if extra_html:
                payload["htmlContent"] = extra_html

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code in (200, 201, 202):
                return True, f"Report emailed to {recipient_email} via Brevo"
            return False, f"Brevo API error ({response.status_code}): {response.text}"
        except Exception as e:
            return False, f"Brevo error: {str(e)}"

    def _send_via_smtp(self, recipient_email, subject, plain, extra_html, csv_bytes, filename):
        try:
            if not (self.sender_email and self.sender_password):
                return False, "SMTP not configured (missing SENDER_EMAIL/SENDER_PASSWORD)"

            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = f"Attendance System <{self.sender_email}>"
            msg['To'] = recipient_email

            msg.attach(MIMEText(plain, 'plain'))
            if extra_html:
                msg.attach(MIMEText(extra_html, 'html'))

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(csv_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            return True, f"Report emailed to {recipient_email} via SMTP"
        except Exception as e:
            return False, f"SMTP error: {str(e)}"


email_service = EmailService()
