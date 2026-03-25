"""Email sending via SMTP."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import Config

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends email responses using SMTP."""

    def __init__(self, config: Config) -> None:
        self._config = config

    def send(
        self,
        to_address: str,
        subject: str,
        body: str,
        in_reply_to: str = "",
    ) -> None:
        """Send a plain-text email response.

        Args:
            to_address: Recipient email address.
            subject: Email subject line.
            body: Plain-text message body.
            in_reply_to: Optional Message-ID of the email being replied to.
        """
        from_address = f"{self._config.smtp_from_name} <{self._config.smtp_username}>"

        msg = MIMEMultipart()
        msg["From"] = from_address
        msg["To"] = to_address
        msg["Subject"] = subject
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = in_reply_to

        msg.attach(MIMEText(body, "plain", "utf-8"))

        logger.info("Sending email to %s | subject: %s", to_address, subject)
        with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(self._config.smtp_username, self._config.smtp_password)
            server.sendmail(self._config.smtp_username, to_address, msg.as_string())
        logger.info("Email sent successfully to %s", to_address)
