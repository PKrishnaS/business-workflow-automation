# ============================================================
# email_sender/mailer.py — Email automation
# ============================================================
# Sends emails (with optional attachments) via SMTP.
# Uses Gmail by default — works with any SMTP provider.
# Credentials are loaded from the .env file — NEVER hardcoded.
# ============================================================

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Union, Optional

from config.settings import (
    EMAIL_SENDER, EMAIL_PASSWORD,
    EMAIL_SMTP_HOST, EMAIL_SMTP_PORT
)
from utils.logger import get_logger, log_function_call
from utils.validators import validate_email, validate_file_exists, ValidationError

logger = get_logger(__name__)


class Mailer:
    """
    Send emails with optional file attachments.

    HOW TO USE:
        mailer = Mailer()
        mailer.send(
            to="client@example.com",
            subject="Your Monthly Report",
            body="Please find your report attached.",
            attachments=["data/output/report.pdf"]
        )

    SETUP REQUIRED:
        1. Copy config/.env.example to config/.env
        2. Fill in your EMAIL_SENDER and EMAIL_PASSWORD
        3. For Gmail, use an App Password (not your main password)
    """

    def __init__(self, sender: str = None, password: str = None):
        """
        Args:
            sender:   The "from" email address. Defaults to EMAIL_SENDER from .env
            password: SMTP password. Defaults to EMAIL_PASSWORD from .env
        """
        self.sender   = sender   or EMAIL_SENDER
        self.password = password or EMAIL_PASSWORD
        self.smtp_host = EMAIL_SMTP_HOST
        self.smtp_port = EMAIL_SMTP_PORT

        if not self.sender:
            logger.warning("No email sender configured. Set EMAIL_SENDER in your .env file.")
        if not self.password:
            logger.warning("No email password configured. Set EMAIL_PASSWORD in your .env file.")

    @log_function_call(logger)
    def send(self,
             to: Union[str, list],
             subject: str,
             body: str,
             body_html: Optional[str] = None,
             attachments: Optional[list] = None,
             cc: Union[str, list, None] = None,
             bcc: Union[str, list, None] = None) -> bool:
        """
        Send an email.

        Args:
            to:          Recipient(s). Can be a single email string or a list.
            subject:     Email subject line.
            body:        Plain text email body (always required).
            body_html:   Optional HTML version of the body (shown if recipient supports HTML).
            attachments: Optional list of file paths to attach.
            cc:          CC recipients (string or list).
            bcc:         BCC recipients (string or list).

        Returns:
            True if sent successfully, False otherwise.

        Raises:
            ValidationError: If any email address is invalid.
        """
        # ── Validate credentials ──────────────────────────────
        if not self.sender or not self.password:
            raise RuntimeError(
                "Email credentials not configured. "
                "Add EMAIL_SENDER and EMAIL_PASSWORD to your .env file. "
                "See config/.env.example for instructions."
            )

        # ── Normalize recipients to lists ────────────────────
        to_list  = [to]  if isinstance(to, str)  else list(to)
        cc_list  = [cc]  if isinstance(cc, str)  else (list(cc)  if cc  else [])
        bcc_list = [bcc] if isinstance(bcc, str) else (list(bcc) if bcc else [])

        # ── Validate all email addresses ─────────────────────
        all_recipients = to_list + cc_list + bcc_list
        for addr in all_recipients:
            validate_email(addr)

        # ── Build the email message ───────────────────────────
        msg = MIMEMultipart("alternative")
        msg["From"]    = self.sender
        msg["To"]      = ", ".join(to_list)
        msg["Subject"] = subject
        if cc_list:
            msg["Cc"] = ", ".join(cc_list)
        # BCC recipients are included in SMTP but NOT in headers (that's how BCC works)

        # Attach plain text body
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Attach HTML body if provided (displayed instead of plain text in modern email clients)
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        # ── Attach files ──────────────────────────────────────
        if attachments:
            for filepath in attachments:
                self._attach_file(msg, filepath)

        # ── Send via SMTP ─────────────────────────────────────
        all_smtp_recipients = to_list + cc_list + bcc_list

        try:
            # TLS (Transport Layer Security) encrypts the connection
            # This is the secure way to send email over port 587
            context = ssl.create_default_context()

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()                      # Identify ourselves to the server
                server.starttls(context=context)   # Upgrade to encrypted connection
                server.login(self.sender, self.password)
                server.sendmail(
                    self.sender,
                    all_smtp_recipients,
                    msg.as_string()
                )

            logger.info(f"Email sent to {to_list}: '{subject}'")
            if attachments:
                logger.info(f"  Attachments: {[Path(a).name for a in attachments]}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed. Check your EMAIL_SENDER and EMAIL_PASSWORD. "
                "For Gmail, make sure you're using an App Password, not your main password."
            )
            return False

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error while sending to {to_list}: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending email: {type(e).__name__}: {e}")
            return False

    def _attach_file(self, msg: MIMEMultipart, filepath: Union[str, Path]):
        """
        Attach a single file to the email message.

        Args:
            msg:      The email message object to add the attachment to.
            filepath: Path to the file.
        """
        filepath = Path(filepath)
        try:
            validate_file_exists(filepath)
        except ValidationError as e:
            logger.warning(f"Skipping attachment — {e}")
            return

        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())

        # Encode the binary file as base64 so it can be sent over email (which is text-based)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=filepath.name
        )
        msg.attach(part)
        logger.debug(f"Attached file: {filepath.name} ({filepath.stat().st_size:,} bytes)")

    def send_report(self, to: Union[str, list],
                    report_path: Union[str, Path],
                    custom_message: str = "") -> bool:
        """
        Convenience method: send a report file with a professional email template.

        Args:
            to:             Recipient(s)
            report_path:    Path to the report file (PDF, Excel, etc.)
            custom_message: Optional extra text to add to the email body.

        Returns:
            True if sent successfully.
        """
        report_path = Path(report_path)
        report_name = report_path.name

        subject = f"Report: {report_name}"

        body = f"""Hello,

Please find your automated report attached.

Report: {report_name}
Generated: {__import__('datetime').datetime.now().strftime('%d %B %Y at %H:%M')}
"""
        if custom_message:
            body += f"\nAdditional notes:\n{custom_message}\n"

        body += f"""
This report was generated automatically by the Business Workflow Automation Suite.

Best regards,
{__import__('config.settings', fromlist=['REPORT_AUTHOR']).REPORT_AUTHOR}
"""

        return self.send(
            to=to,
            subject=subject,
            body=body,
            attachments=[str(report_path)]
        )
