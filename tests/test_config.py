"""Unit tests for src/config.py."""

import os
import unittest


class TestConfig(unittest.TestCase):
    def _make_config(self, overrides=None):
        # Import inside test so env vars can be patched
        from src.config import Config
        cfg = Config()
        if overrides:
            for key, value in overrides.items():
                setattr(cfg, key, value)
        return cfg

    def test_defaults(self):
        from src.config import Config
        cfg = Config()
        self.assertEqual(cfg.imap_host, "imap.gmail.com")
        self.assertEqual(cfg.imap_port, 993)
        self.assertEqual(cfg.smtp_host, "smtp.gmail.com")
        self.assertEqual(cfg.smtp_port, 587)
        self.assertEqual(cfg.max_emails_per_run, 10)
        self.assertEqual(cfg.poll_interval_seconds, 60)

    def test_validate_raises_when_missing(self):
        cfg = self._make_config()
        cfg.openai_api_key = ""
        cfg.imap_username = ""
        cfg.imap_password = ""
        cfg.smtp_username = ""
        cfg.smtp_password = ""
        with self.assertRaises(ValueError) as ctx:
            cfg.validate()
        self.assertIn("OPENAI_API_KEY", str(ctx.exception))

    def test_validate_passes_when_complete(self):
        cfg = self._make_config({
            "openai_api_key": "sk-test",
            "imap_username": "user@example.com",
            "imap_password": "secret",
            "smtp_username": "user@example.com",
            "smtp_password": "secret",
        })
        # Should not raise
        cfg.validate()

    def test_validate_lists_all_missing_fields(self):
        cfg = self._make_config()
        cfg.openai_api_key = ""
        cfg.imap_username = ""
        cfg.imap_password = ""
        cfg.smtp_username = ""
        cfg.smtp_password = ""
        with self.assertRaises(ValueError) as ctx:
            cfg.validate()
        msg = str(ctx.exception)
        for field in ("OPENAI_API_KEY", "IMAP_USERNAME", "IMAP_PASSWORD",
                      "SMTP_USERNAME", "SMTP_PASSWORD"):
            self.assertIn(field, msg)

    def test_env_var_override(self):
        original = os.environ.get("OPENAI_MODEL")
        try:
            os.environ["OPENAI_MODEL"] = "gpt-4"
            from src.config import Config
            cfg = Config()
            self.assertEqual(cfg.openai_model, "gpt-4")
        finally:
            if original is None:
                os.environ.pop("OPENAI_MODEL", None)
            else:
                os.environ["OPENAI_MODEL"] = original


if __name__ == "__main__":
    unittest.main()
