"""Unit tests for src/ai_processor.py."""

import unittest
from unittest.mock import MagicMock, patch

from src.config import Config
from src.ai_processor import AIProcessor, ProcessedEmail, CATEGORIES


def _make_processor() -> AIProcessor:
    cfg = Config()
    cfg.gemini_api_key = "AIza-test-key"
    cfg.gemini_model = "gemini-1.5-flash"
    return AIProcessor(cfg)


def _mock_gemini_response(text: str) -> MagicMock:
    """Build a mock Gemini GenerateContentResponse."""
    response = MagicMock()
    response.text = text
    return response


class TestAIProcessor(unittest.TestCase):
    @patch("src.ai_processor.genai.Client")
    def test_process_returns_processed_email(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.side_effect = [
            _mock_gemini_response("billing"),
            _mock_gemini_response("Thank you for contacting us about billing."),
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

    @patch("src.ai_processor.genai.Client")
    def test_categorise_falls_back_to_other(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.side_effect = [
            _mock_gemini_response("something completely unrecognised"),
            _mock_gemini_response("We will look into this."),
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

    @patch("src.ai_processor.genai.Client")
    def test_process_calls_gemini_twice(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.side_effect = [
            _mock_gemini_response("technical support"),
            _mock_gemini_response("We will help with your technical issue."),
        ]

        processor = _make_processor()
        processor.process(subject="App crash", body="The app crashes on startup.")

        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    @patch("src.ai_processor.genai.Client")
    def test_categorise_recognises_all_categories(self, mock_client_class):
        """Verify that each known category string is correctly mapped."""
        for category in CATEGORIES:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.models.generate_content.side_effect = [
                _mock_gemini_response(category),
                _mock_gemini_response("Response text."),
            ]
            processor = _make_processor()
            result = processor.process(subject="Test", body="Test body")
            self.assertEqual(result.category, category, f"Failed for category: {category}")

    @patch("src.ai_processor.genai.Client")
    def test_client_initialised_with_api_key(self, mock_client_class):
        mock_client_class.return_value = MagicMock()
        _make_processor()
        mock_client_class.assert_called_once_with(api_key="AIza-test-key")

    @patch("src.ai_processor.genai.Client")
    def test_generate_content_uses_configured_model(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.generate_content.side_effect = [
            _mock_gemini_response("billing"),
            _mock_gemini_response("Response."),
        ]
        processor = _make_processor()
        processor.process(subject="Test", body="Test body")
        for call in mock_client.models.generate_content.call_args_list:
            self.assertEqual(call.kwargs.get("model") or call.args[0], "gemini-1.5-flash")


if __name__ == "__main__":
    unittest.main()
