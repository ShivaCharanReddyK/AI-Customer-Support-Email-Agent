"""Email reading via IMAP."""

import email
import imaplib
import logging
from dataclasses import dataclass, field
from email.header import decode_header
from typing import List

from .config import Config

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Represents a parsed customer support email."""

    uid: str
    sender: str
    subject: str
    body: str
    reply_to: str = ""
    message_id: str = ""


def _decode_str(value: str) -> str:
    """Decode an encoded email header string."""
    parts = decode_header(value)
    decoded_parts = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts)


def _extract_body(msg: email.message.Message) -> str:
    """Return the plain-text body of an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


class EmailReader:
    """Fetches unread emails from an IMAP mailbox."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._connection: imaplib.IMAP4_SSL | None = None

    def connect(self) -> None:
        """Open and authenticate an IMAP connection."""
        logger.info("Connecting to IMAP server %s:%d", self._config.imap_host, self._config.imap_port)
        self._connection = imaplib.IMAP4_SSL(self._config.imap_host, self._config.imap_port)
        self._connection.login(self._config.imap_username, self._config.imap_password)
        self._connection.select(self._config.imap_mailbox)
        logger.info("IMAP connection established")

    def disconnect(self) -> None:
        """Close the IMAP connection."""
        if self._connection:
            try:
                self._connection.close()
                self._connection.logout()
            except Exception:
                pass
            self._connection = None

    def fetch_unread(self, max_count: int = 10) -> List[EmailMessage]:
        """Return up to *max_count* unread messages from the mailbox."""
        if not self._connection:
            raise RuntimeError("Not connected. Call connect() first.")

        status, data = self._connection.search(None, "UNSEEN")
        if status != "OK" or not data or not data[0]:
            return []

        uids = data[0].split()
        # Limit to the requested number, taking the most recent first
        uids = uids[-max_count:]

        messages: List[EmailMessage] = []
        for uid in uids:
            try:
                msg = self._fetch_message(uid.decode())
                if msg:
                    messages.append(msg)
            except Exception as exc:
                logger.warning("Failed to fetch message uid=%s: %s", uid, exc)

        return messages

    def mark_as_read(self, uid: str) -> None:
        """Mark an email as read (Seen) by UID."""
        if not self._connection:
            raise RuntimeError("Not connected. Call connect() first.")
        self._connection.store(uid, "+FLAGS", "\\Seen")

    def _fetch_message(self, uid: str) -> EmailMessage | None:
        """Fetch and parse a single message by UID."""
        status, data = self._connection.fetch(uid, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            return None

        raw = data[0][1]
        msg = email.message_from_bytes(raw)

        sender = _decode_str(msg.get("From", ""))
        subject = _decode_str(msg.get("Subject", "(no subject)"))
        reply_to = _decode_str(msg.get("Reply-To", "")) or sender
        message_id = msg.get("Message-ID", "")
        body = _extract_body(msg)

        return EmailMessage(
            uid=uid,
            sender=sender,
            subject=subject,
            body=body,
            reply_to=reply_to,
            message_id=message_id,
        )
