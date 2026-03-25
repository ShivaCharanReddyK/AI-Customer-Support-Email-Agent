"""Unit tests for src/ai_processor.py."""

import unittest
from unittest.mock import MagicMock, patch

from src.config import Config
from src.ai_processor import AIProcessor, ProcessedEmail, CATEGORIES


def _make_processor() -> AIProcessor:
    cfg = Config()
    cfg.openai_api_key = "sk-test"
    cfg.openai_model = "gpt-3.5-turbo"
    return AIProcessor(cfg)


def _mock_completion(text: str) -> MagicMock:
    """Build a mock OpenAI ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = text
    response = MagicMock()
    response.choices = [choice]
    return response


class TestAIProcessor(unittest.TestCase):
    @patch("src.ai_processor.OpenAI")
    def test_process_returns_processed_email(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            _mock_completion("billing"),
            _mock_completion("Thank you for contacting us about billing."),
        ]

        processor = _make_processor()
        result = processor.process(
            subject="Invoice problem",
            body="I was charged twice this month.",
        )

        self.assertIsInstance(result, ProcessedEmail)
        self.assertEqual(result.category, "billing")
        self.assertEqual(result.response_subject, "Re: Invoice problem")
        self.assertTrue(len(result.response_body) > 0)

    @patch("src.ai_processor.OpenAI")
    def test_categorise_falls_back_to_other(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            _mock_completion("something completely unrecognised"),
            _mock_completion("We will look into this."),
        ]

        processor = _make_processor()
        result = processor.process(subject="Random", body="Unrelated content")
        self.assertEqual(result.category, "other")

    def test_build_reply_subject_adds_re(self):
        self.assertEqual(AIProcessor._build_reply_subject("My issue"), "Re: My issue")

    def test_build_reply_subject_no_duplicate_re(self):
        self.assertEqual(AIProcessor._build_reply_subject("Re: My issue"), "Re: My issue")

    def test_build_reply_subject_case_insensitive(self):
        self.assertEqual(AIProcessor._build_reply_subject("RE: My issue"), "RE: My issue")

    def test_get_categories_returns_list(self):
        cats = AIProcessor.get_categories()
        self.assertIsInstance(cats, list)
        self.assertIn("billing", cats)
        self.assertIn("technical support", cats)
        self.assertIn("general inquiry", cats)

    @patch("src.ai_processor.OpenAI")
    def test_process_calls_openai_twice(self, mock_openai_class):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            _mock_completion("technical support"),
            _mock_completion("We will help with your technical issue."),
        ]

        processor = _make_processor()
        processor.process(subject="App crash", body="The app crashes on startup.")

        self.assertEqual(mock_client.chat.completions.create.call_count, 2)

    @patch("src.ai_processor.OpenAI")
    def test_categorise_recognises_all_categories(self, mock_openai_class):
        """Verify that each known category string is correctly mapped."""
        for category in CATEGORIES:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                _mock_completion(category),
                _mock_completion("Response text."),
            ]
            processor = _make_processor()
            result = processor.process(subject="Test", body="Test body")
            self.assertEqual(result.category, category, f"Failed for category: {category}")


if __name__ == "__main__":
    unittest.main()
