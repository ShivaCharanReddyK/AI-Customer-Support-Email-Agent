"""Unit tests for src/email_sender.py."""

import smtplib
import unittest
from unittest.mock import MagicMock, patch

from src.config import Config
from src.email_sender import EmailSender


def _make_sender() -> EmailSender:
    cfg = Config()
    cfg.smtp_host = "smtp.example.com"
    cfg.smtp_port = 587
    cfg.smtp_username = "support@example.com"
    cfg.smtp_password = "secret"
    cfg.smtp_from_name = "Support Team"
    return EmailSender(cfg)


class TestEmailSender(unittest.TestCase):
    @patch("src.email_sender.smtplib.SMTP")
    def test_send_basic(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        sender = _make_sender()
        sender.send(
            to_address="customer@example.com",
            subject="Re: Your order",
            body="Thank you for reaching out.",
        )

        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("support@example.com", "secret")
        mock_server.sendmail.assert_called_once()

    @patch("src.email_sender.smtplib.SMTP")
    def test_send_sets_in_reply_to_header(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        sender = _make_sender()
        sender.send(
            to_address="customer@example.com",
            subject="Re: Your order",
            body="Thank you for reaching out.",
            in_reply_to="<original-message-id@example.com>",
        )

        # Verify that sendmail was called and the raw message contains headers
        call_args = mock_server.sendmail.call_args
        raw_message = call_args[0][2]
        self.assertIn("In-Reply-To:", raw_message)
        self.assertIn("<original-message-id@example.com>", raw_message)

    @patch("src.email_sender.smtplib.SMTP")
    def test_send_from_address_includes_name(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        sender = _make_sender()
        sender.send(
            to_address="customer@example.com",
            subject="Hello",
            body="Hi there.",
        )

        call_args = mock_server.sendmail.call_args
        raw_message = call_args[0][2]
        self.assertIn("Support Team", raw_message)
        self.assertIn("support@example.com", raw_message)


if __name__ == "__main__":
    unittest.main()
