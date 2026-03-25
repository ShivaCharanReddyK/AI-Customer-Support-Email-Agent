"""Orchestration: read → process → respond → mark-read."""

import logging
import time
from dataclasses import dataclass, field
from typing import List

from .ai_processor import AIProcessor
from .config import Config
from .email_reader import EmailMessage, EmailReader
from .email_sender import EmailSender

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Summary of one email processed by the agent."""

    uid: str
    sender: str
    subject: str
    category: str
    response_sent: bool
    error: str = ""


@dataclass
class RunSummary:
    """Summary of a single agent run."""

    emails_fetched: int = 0
    emails_processed: int = 0
    emails_failed: int = 0
    results: List[ProcessingResult] = field(default_factory=list)


class EmailAgent:
    """Main orchestrator for the AI customer support email workflow."""

    def __init__(
        self,
        config: Config,
        reader: EmailReader | None = None,
        sender: EmailSender | None = None,
        processor: AIProcessor | None = None,
    ) -> None:
        self._config = config
        self._reader = reader or EmailReader(config)
        self._sender = sender or EmailSender(config)
        self._processor = processor or AIProcessor(config)

    def run_once(self) -> RunSummary:
        """Fetch unread emails, process them, and send responses.

        Returns:
            A :class:`RunSummary` with processing statistics.
        """
        summary = RunSummary()
        self._reader.connect()
        try:
            messages = self._reader.fetch_unread(max_count=self._config.max_emails_per_run)
            summary.emails_fetched = len(messages)
            logger.info("Fetched %d unread email(s)", summary.emails_fetched)

            for msg in messages:
                result = self._process_message(msg)
                summary.results.append(result)
                if result.error:
                    summary.emails_failed += 1
                else:
                    summary.emails_processed += 1
        finally:
            self._reader.disconnect()

        logger.info(
            "Run complete: fetched=%d processed=%d failed=%d",
            summary.emails_fetched,
            summary.emails_processed,
            summary.emails_failed,
        )
        return summary

    def run_continuous(self) -> None:
        """Poll for new emails at regular intervals until interrupted."""
        logger.info(
            "Starting continuous polling (interval=%ds)", self._config.poll_interval_seconds
        )
        while True:
            try:
                self.run_once()
            except Exception as exc:
                logger.error("Error during agent run: %s", exc)
            time.sleep(self._config.poll_interval_seconds)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _process_message(self, msg: EmailMessage) -> ProcessingResult:
        """Process a single email: categorise, generate reply, send, mark read."""
        logger.info("Processing email uid=%s from=%s subject=%s", msg.uid, msg.sender, msg.subject)
        try:
            processed = self._processor.process(subject=msg.subject, body=msg.body)
            logger.info("Category: %s", processed.category)

            reply_to = msg.reply_to or msg.sender
            self._sender.send(
                to_address=reply_to,
                subject=processed.response_subject,
                body=processed.response_body,
                in_reply_to=msg.message_id,
            )
            self._reader.mark_as_read(msg.uid)

            return ProcessingResult(
                uid=msg.uid,
                sender=msg.sender,
                subject=msg.subject,
                category=processed.category,
                response_sent=True,
            )
        except Exception as exc:
            logger.error("Failed to process email uid=%s: %s", msg.uid, exc)
            return ProcessingResult(
                uid=msg.uid,
                sender=msg.sender,
                subject=msg.subject,
                category="unknown",
                response_sent=False,
                error=str(exc),
            )
