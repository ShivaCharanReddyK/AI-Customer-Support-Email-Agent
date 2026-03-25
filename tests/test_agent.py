"""Unit tests for src/agent.py."""

import unittest
from unittest.mock import MagicMock, patch, call

from src.agent import EmailAgent, RunSummary, ProcessingResult
from src.config import Config
from src.email_reader import EmailMessage
from src.ai_processor import ProcessedEmail


def _make_config() -> Config:
    cfg = Config()
    cfg.openai_api_key = "sk-test"
    cfg.imap_username = "user@example.com"
    cfg.imap_password = "secret"
    cfg.smtp_username = "user@example.com"
    cfg.smtp_password = "secret"
    cfg.max_emails_per_run = 5
    return cfg


def _make_email(uid="1") -> EmailMessage:
    return EmailMessage(
        uid=uid,
        sender="customer@example.com",
        subject="Help needed",
        body="I have a problem with my order.",
        reply_to="customer@example.com",
        message_id=f"<msg{uid}@example.com>",
    )


class TestEmailAgent(unittest.TestCase):
    def _make_agent(self, messages=None, processed=None):
        cfg = _make_config()

        mock_reader = MagicMock()
        mock_sender = MagicMock()
        mock_processor = MagicMock()

        mock_reader.fetch_unread.return_value = messages or []
        mock_processor.process.return_value = processed or ProcessedEmail(
            category="general inquiry",
            response_body="Thank you for contacting us.",
            response_subject="Re: Help needed",
        )

        agent = EmailAgent(
            config=cfg,
            reader=mock_reader,
            sender=mock_sender,
            processor=mock_processor,
        )
        return agent, mock_reader, mock_sender, mock_processor

    def test_run_once_with_no_emails(self):
        agent, reader, sender, processor = self._make_agent(messages=[])
        summary = agent.run_once()

        self.assertEqual(summary.emails_fetched, 0)
        self.assertEqual(summary.emails_processed, 0)
        self.assertEqual(summary.emails_failed, 0)
        reader.connect.assert_called_once()
        reader.disconnect.assert_called_once()

    def test_run_once_processes_emails(self):
        msgs = [_make_email("1"), _make_email("2")]
        agent, reader, sender, processor = self._make_agent(messages=msgs)

        summary = agent.run_once()

        self.assertEqual(summary.emails_fetched, 2)
        self.assertEqual(summary.emails_processed, 2)
        self.assertEqual(summary.emails_failed, 0)
        self.assertEqual(processor.process.call_count, 2)
        self.assertEqual(sender.send.call_count, 2)
        self.assertEqual(reader.mark_as_read.call_count, 2)

    def test_run_once_marks_emails_as_read(self):
        msgs = [_make_email("42")]
        agent, reader, sender, processor = self._make_agent(messages=msgs)
        agent.run_once()
        reader.mark_as_read.assert_called_once_with("42")

    def test_run_once_handles_processing_error(self):
        msgs = [_make_email("1")]
        agent, reader, sender, processor = self._make_agent(messages=msgs)
        processor.process.side_effect = RuntimeError("OpenAI unavailable")

        summary = agent.run_once()

        self.assertEqual(summary.emails_fetched, 1)
        self.assertEqual(summary.emails_processed, 0)
        self.assertEqual(summary.emails_failed, 1)
        self.assertFalse(summary.results[0].response_sent)
        self.assertIn("OpenAI unavailable", summary.results[0].error)

    def test_run_once_disconnects_on_error(self):
        cfg = _make_config()
        mock_reader = MagicMock()
        mock_reader.fetch_unread.side_effect = RuntimeError("Connection lost")

        agent = EmailAgent(config=cfg, reader=mock_reader)

        with self.assertRaises(RuntimeError):
            agent.run_once()

        mock_reader.disconnect.assert_called_once()

    def test_result_contains_category(self):
        msgs = [_make_email("1")]
        processed = ProcessedEmail(
            category="billing",
            response_body="We are reviewing your bill.",
            response_subject="Re: Help needed",
        )
        agent, reader, sender, processor = self._make_agent(messages=msgs, processed=processed)
        summary = agent.run_once()
        self.assertEqual(summary.results[0].category, "billing")

    def test_sender_receives_correct_arguments(self):
        msg = _make_email("1")
        processed = ProcessedEmail(
            category="general inquiry",
            response_body="Thank you for contacting us.",
            response_subject="Re: Help needed",
        )
        agent, reader, sender, processor = self._make_agent(messages=[msg], processed=processed)
        agent.run_once()

        sender.send.assert_called_once_with(
            to_address="customer@example.com",
            subject="Re: Help needed",
            body="Thank you for contacting us.",
            in_reply_to="<msg1@example.com>",
        )


if __name__ == "__main__":
    unittest.main()
