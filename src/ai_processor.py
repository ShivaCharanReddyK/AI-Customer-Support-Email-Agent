"""AI-powered email processing using OpenAI."""

import logging
from dataclasses import dataclass
from typing import List

from openai import OpenAI

from .config import Config

logger = logging.getLogger(__name__)

CATEGORIES = [
    "billing",
    "technical support",
    "returns & refunds",
    "shipping & delivery",
    "account management",
    "general inquiry",
    "complaint",
    "other",
]

SYSTEM_PROMPT = """\
You are a professional customer support agent. Your role is to:
1. Carefully read the customer's email.
2. Determine the category of the inquiry.
3. Draft a helpful, empathetic, and professional response.

Always:
- Address the customer by name if possible.
- Acknowledge their concern before providing a solution.
- Keep responses concise and clear.
- End with an offer for further assistance.
- Sign off as "Customer Support Team".
"""

CATEGORISE_PROMPT = """\
Categorise the following customer support email into exactly one of these categories:
{categories}

Reply with the category name only, nothing else.

Email subject: {subject}
Email body:
{body}
"""

RESPOND_PROMPT = """\
Write a professional customer support response to the following email.

Category: {category}
Customer email subject: {subject}
Customer email body:
{body}

Provide only the email body text (no subject line, no headers).
"""


@dataclass
class ProcessedEmail:
    """Result of AI processing for a single customer email."""

    category: str
    response_body: str
    response_subject: str


class AIProcessor:
    """Categorises customer emails and generates AI-powered responses."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = OpenAI(api_key=config.openai_api_key)

    def process(self, subject: str, body: str) -> ProcessedEmail:
        """Categorise *subject*/*body* and generate an appropriate reply.

        Args:
            subject: The email subject line.
            body: The plain-text email body.

        Returns:
            A :class:`ProcessedEmail` with category and draft response.
        """
        category = self._categorise(subject, body)
        response_body = self._generate_response(subject, body, category)
        response_subject = self._build_reply_subject(subject)

        return ProcessedEmail(
            category=category,
            response_body=response_body,
            response_subject=response_subject,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _categorise(self, subject: str, body: str) -> str:
        """Return the best-matching support category for the email."""
        prompt = CATEGORISE_PROMPT.format(
            categories="\n".join(f"- {c}" for c in CATEGORIES),
            subject=subject,
            body=body[:2000],  # Truncate to avoid excessive token usage
        )
        response = self._client.chat.completions.create(
            model=self._config.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=20,
        )
        raw = response.choices[0].message.content.strip().lower()
        # Validate against known categories; default to "other"
        for cat in CATEGORIES:
            if cat in raw:
                return cat
        return "other"

    def _generate_response(self, subject: str, body: str, category: str) -> str:
        """Generate a professional email response body."""
        prompt = RESPOND_PROMPT.format(
            category=category,
            subject=subject,
            body=body[:3000],
        )
        response = self._client.chat.completions.create(
            model=self._config.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _build_reply_subject(subject: str) -> str:
        """Prepend 'Re: ' to a subject line if not already present."""
        stripped = subject.strip()
        if stripped.lower().startswith("re:"):
            return stripped
        return f"Re: {stripped}"

    @staticmethod
    def get_categories() -> List[str]:
        """Return the list of supported email categories."""
        return list(CATEGORIES)
