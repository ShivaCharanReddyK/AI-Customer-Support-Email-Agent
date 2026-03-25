# AI Customer Support Email Agent

## Project Title
**AI Customer Support Email Agent — Gemini-Powered Inbox Automation**

---

## Project Overview

### What Problem This Solves
Customer support teams are overwhelmed by high email volumes. Manually reading, categorising, and responding to every inquiry is slow, error-prone, and expensive — especially at scale. Response times suffer, customers churn, and support staff burn out handling repetitive queries.

This project automates the entire first-response workflow:

1. **Reads** unread customer emails from any IMAP mailbox
2. **Classifies** each email into one of 8 support categories using Google Gemini AI
3. **Drafts and sends** a professional, empathetic reply via SMTP — personalised to the inquiry
4. **Marks** the email as read so the queue stays clean

### Why It Matters
- **Faster response times** — customers receive an immediate, contextual acknowledgement 24/7
- **Consistent quality** — every reply follows the same professional tone and structure
- **Lower operational cost** — Gemini handles the repetitive long-tail of inquiries so agents focus on complex cases
- **Flexible deployment** — runs as a one-shot cron job or as a continuously polling daemon

---

## Weekly Timeline

Today: **25 March 2026** | Deadline: **10 May 2026** *(7 weeks)*

| Week | Dates | Milestone |
|------|-------|-----------|
| **Week 1** | Mar 25 – Mar 31 | Project setup: repository structure, `google-genai` SDK integration, `.env` configuration, CI skeleton |
| **Week 2** | Apr 1 – Apr 7 | IMAP email reader: connect, fetch unread messages, parse RFC 822 (multi-part, encoded headers) |
| **Week 3** | Apr 8 – Apr 14 | SMTP email sender: compose replies, STARTTLS, `In-Reply-To` threading headers |
| **Week 4** | Apr 15 – Apr 21 | Gemini AI processor: email categorisation (8 categories) + professional response generation |
| **Week 5** | Apr 22 – Apr 28 | Agent orchestration: `run_once` and `run_continuous` modes; error handling and retry logic |
| **Week 6** | Apr 29 – May 5 | Full test suite (unit + integration mocks); logging; edge-case hardening |
| **Week 7** | May 6 – May 10 | Final polish: README, demo walkthrough, performance tuning, deliverable hand-off |

---

## Expected Outcome

By **10 May 2026** the following will be delivered:

| Deliverable | Description |
|---|---|
| **Working agent** | Fully functional `python main.py --mode once/continuous` CLI that reads, classifies, and replies to customer emails |
| **Gemini AI integration** | Uses `google-genai` SDK with `gemini-1.5-flash` (configurable) for zero-shot categorisation and response generation |
| **8 support categories** | billing · technical support · returns & refunds · shipping & delivery · account management · general inquiry · complaint · other |
| **IMAP/SMTP support** | Compatible with Gmail, Outlook, and any standard mail server |
| **38+ unit tests** | All modules fully tested with mocked I/O; no live API calls required |
| **Configuration template** | `.env.example` with all required and optional variables documented |
| **README & docs** | Setup guide, variable reference, architecture diagram, usage examples |

---

## Features

- **Email ingestion** – connects to any IMAP server and fetches unread messages
- **AI categorisation** – classifies emails using Gemini into one of 8 support categories
- **AI response generation** – drafts professional, empathetic replies via Gemini
- **Automated sending** – delivers the reply via SMTP and marks the original as read
- **Flexible run modes** – process emails once (cron-friendly) or poll continuously

---

## Project Structure

```
AI-Customer-Support-Email-Agent/
├── main.py               # Entry point / CLI
├── requirements.txt
├── .env.example          # Template for environment variables
├── src/
│   ├── config.py         # Configuration via environment variables
│   ├── email_reader.py   # IMAP email fetching & parsing
│   ├── email_sender.py   # SMTP response sending
│   ├── ai_processor.py   # Gemini AI categorisation & response generation
│   └── agent.py          # Orchestration pipeline
└── tests/
    ├── test_config.py
    ├── test_email_reader.py
    ├── test_email_sender.py
    ├── test_ai_processor.py
    └── test_agent.py
```

---

## Requirements

- Python 3.12+
- A [Google Gemini API key](https://ai.google.dev/gemini-api/docs/api-key)
- An email account with IMAP/SMTP access (app password recommended for Gmail)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/ShivaCharanReddyK/AI-Customer-Support-Email-Agent.git
cd AI-Customer-Support-Email-Agent
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GEMINI_MODEL` | Gemini model to use (default: `gemini-1.5-flash`) |
| `IMAP_HOST` | IMAP server hostname (e.g. `imap.gmail.com`) |
| `IMAP_PORT` | IMAP port (default: `993`) |
| `IMAP_USERNAME` | Email address |
| `IMAP_PASSWORD` | Email password / app password |
| `IMAP_MAILBOX` | Mailbox to monitor (default: `INBOX`) |
| `SMTP_HOST` | SMTP server hostname (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |
| `SMTP_USERNAME` | Sending email address |
| `SMTP_PASSWORD` | Email password / app password |
| `SMTP_FROM_NAME` | Display name for outgoing emails (default: `Customer Support`) |
| `MAX_EMAILS_PER_RUN` | Max emails processed per run (default: `10`) |
| `POLL_INTERVAL_SECONDS` | Polling interval in continuous mode (default: `60`) |

> **Gmail users**: enable 2-factor authentication, then generate an [App Password](https://support.google.com/accounts/answer/185833) to use in place of your regular password.

---

## Usage

### Process emails once (suitable for cron jobs)

```bash
python main.py --mode once
```

### Poll continuously

```bash
python main.py --mode continuous
```

### Enable verbose / debug logging

```bash
python main.py --mode once --verbose
```

### Example output

```
Run complete: fetched=3 processed=3 failed=0
  [✓] uid=12 category=billing             to=alice@example.com
  [✓] uid=13 category=technical support   to=bob@example.com
  [✓] uid=14 category=returns & refunds   to=carol@example.com
```

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Architecture

```
┌─────────────┐    unread emails     ┌──────────────┐
│  IMAP Server│ ──────────────────▶  │ EmailReader  │
└─────────────┘                      └──────┬───────┘
                                            │ EmailMessage
                                     ┌──────▼───────┐
                                     │  EmailAgent  │ (orchestrator)
                                     └──────┬───────┘
                                            │ subject + body
                                     ┌──────▼───────┐
                                     │ AIProcessor  │ ──▶ Google Gemini API
                                     └──────┬───────┘
                                            │ category + response
                                     ┌──────▼───────┐
                                     │ EmailSender  │ ──▶ SMTP Server
                                     └─────────────-┘
```

---

## License

MIT

