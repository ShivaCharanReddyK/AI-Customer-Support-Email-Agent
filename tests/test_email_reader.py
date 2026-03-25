"""Unit tests for src/email_reader.py."""

import email
import imaplib
import unittest
from unittest.mock import MagicMock, patch

from src.config import Config
from src.email_reader import EmailReader, EmailMessage, _decode_str, _extract_body


def _make_raw_email(
    sender="Alice <alice@example.com>",
    subject="Test subject",
    body="Hello, this is a test.",
    message_id="<abc123@example.com>",
) -> bytes:
    msg = email.mime.multipart.MIMEMultipart()
    msg["From"] = sender
    msg["To"] = "support@example.com"
    msg["Subject"] = subject
    msg["Message-ID"] = message_id
    from email.mime.text import MIMEText
    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg.as_bytes()


class TestDecodeFunctions(unittest.TestCase):
    def test_decode_str_plain(self):
        self.assertEqual(_decode_str("Hello"), "Hello")

    def test_decode_str_encoded(self):
        # RFC 2047 encoded UTF-8
        encoded = "=?utf-8?b?SGVsbG8gV29ybGQ=?="
        self.assertEqual(_decode_str(encoded), "Hello World")

    def test_extract_body_plain(self):
        raw = _make_raw_email(body="Simple body text")
        msg = email.message_from_bytes(raw)
        body = _extract_body(msg)
        self.assertIn("Simple body text", body)

    def test_extract_body_empty(self):
        msg = email.message_from_string("From: test@example.com\n\n")
        body = _extract_body(msg)
        self.assertEqual(body, "")


class TestEmailReader(unittest.TestCase):
    def _make_reader(self) -> EmailReader:
        cfg = Config()
        cfg.imap_host = "imap.example.com"
        cfg.imap_port = 993
        cfg.imap_username = "user@example.com"
        cfg.imap_password = "secret"
        cfg.imap_mailbox = "INBOX"
        return EmailReader(cfg)

    def test_fetch_unread_returns_messages(self):
        reader = self._make_reader()
        raw = _make_raw_email()

        mock_conn = MagicMock(spec=imaplib.IMAP4_SSL)
        mock_conn.search.return_value = ("OK", [b"1 2"])
        mock_conn.fetch.return_value = ("OK", [(b"1 (RFC822 {123})", raw)])

        reader._connection = mock_conn
        messages = reader.fetch_unread(max_count=10)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].subject, "Test subject")
        self.assertEqual(messages[0].sender, "Alice <alice@example.com>")

    def test_fetch_unread_empty_mailbox(self):
        reader = self._make_reader()
        mock_conn = MagicMock(spec=imaplib.IMAP4_SSL)
        mock_conn.search.return_value = ("OK", [b""])

        reader._connection = mock_conn
        messages = reader.fetch_unread()
        self.assertEqual(messages, [])

    def test_fetch_unread_raises_when_not_connected(self):
        reader = self._make_reader()
        with self.assertRaises(RuntimeError):
            reader.fetch_unread()

    def test_mark_as_read_raises_when_not_connected(self):
        reader = self._make_reader()
        with self.assertRaises(RuntimeError):
            reader.mark_as_read("1")

    def test_mark_as_read_calls_store(self):
        reader = self._make_reader()
        mock_conn = MagicMock(spec=imaplib.IMAP4_SSL)
        reader._connection = mock_conn
        reader.mark_as_read("42")
        mock_conn.store.assert_called_once_with("42", "+FLAGS", "\\Seen")

    def test_disconnect_safe_when_not_connected(self):
        reader = self._make_reader()
        reader.disconnect()  # Should not raise

    @patch("src.email_reader.imaplib.IMAP4_SSL")
    def test_connect(self, mock_ssl_class):
        mock_conn = MagicMock()
        mock_ssl_class.return_value = mock_conn

        reader = self._make_reader()
        reader.connect()

        mock_ssl_class.assert_called_once_with("imap.example.com", 993)
        mock_conn.login.assert_called_once_with("user@example.com", "secret")
        mock_conn.select.assert_called_once_with("INBOX")

    def test_fetch_respects_max_count(self):
        reader = self._make_reader()
        raw = _make_raw_email()

        # Simulate 5 messages in the mailbox
        mock_conn = MagicMock(spec=imaplib.IMAP4_SSL)
        mock_conn.search.return_value = ("OK", [b"1 2 3 4 5"])
        mock_conn.fetch.return_value = ("OK", [(b"1 (RFC822 {123})", raw)])

        reader._connection = mock_conn
        messages = reader.fetch_unread(max_count=3)
        # Should only request 3 messages (the last 3 UIDs)
        self.assertEqual(mock_conn.fetch.call_count, 3)


if __name__ == "__main__":
    unittest.main()
