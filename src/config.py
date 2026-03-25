"""Configuration management for the AI Customer Support Email Agent."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Holds all runtime configuration sourced from environment variables."""

    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))

    # IMAP
    imap_host: str = field(default_factory=lambda: os.getenv("IMAP_HOST", "imap.gmail.com"))
    imap_port: int = field(default_factory=lambda: int(os.getenv("IMAP_PORT", "993")))
    imap_username: str = field(default_factory=lambda: os.getenv("IMAP_USERNAME", ""))
    imap_password: str = field(default_factory=lambda: os.getenv("IMAP_PASSWORD", ""))
    imap_mailbox: str = field(default_factory=lambda: os.getenv("IMAP_MAILBOX", "INBOX"))

    # SMTP
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_username: str = field(default_factory=lambda: os.getenv("SMTP_USERNAME", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    smtp_from_name: str = field(
        default_factory=lambda: os.getenv("SMTP_FROM_NAME", "Customer Support")
    )

    # Agent behaviour
    max_emails_per_run: int = field(
        default_factory=lambda: int(os.getenv("MAX_EMAILS_PER_RUN", "10"))
    )
    poll_interval_seconds: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
    )

    def validate(self) -> None:
        """Raise ValueError if required configuration is missing."""
        required = {
            "OPENAI_API_KEY": self.openai_api_key,
            "IMAP_USERNAME": self.imap_username,
            "IMAP_PASSWORD": self.imap_password,
            "SMTP_USERNAME": self.smtp_username,
            "SMTP_PASSWORD": self.smtp_password,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
