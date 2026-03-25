# AI Customer Support Email Agent

An AI-powered agent that reads customer support emails from an IMAP mailbox, classifies them, generates professional responses using OpenAI, and sends replies via SMTP.

## Features

- **Email ingestion** – connects to any IMAP server (e.g. Gmail, Outlook, custom) and fetches unread messages
- **AI categorisation** – classifies each email into one of 8 support categories:
  - billing, technical support, returns & refunds, shipping & delivery,
    account management, general inquiry, complaint, other
- **AI response generation** – uses OpenAI's Chat Completions API (GPT-3.5 / GPT-4) to draft professional, empathetic replies
- **Automated sending** – delivers the reply via SMTP and marks the original as read
- **Flexible run modes** – process emails once (cron-friendly) or poll continuously

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
│   ├── ai_processor.py   # OpenAI categorisation & response generation
│   └── agent.py          # Orchestration pipeline
└── tests/
    ├── test_config.py
    ├── test_email_reader.py
    ├── test_email_sender.py
    ├── test_ai_processor.py
    └── test_agent.py
```

## Requirements

- Python 3.12+
- An OpenAI API key
- An email account with IMAP/SMTP access (app password recommended for Gmail)

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
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | Model to use (default: `gpt-3.5-turbo`) |
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
  [✓] uid=12 category=billing       to=alice@example.com
  [✓] uid=13 category=technical support to=bob@example.com
  [✓] uid=14 category=returns & refunds to=carol@example.com
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

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
                                     │ AIProcessor  │ ──▶ OpenAI API
                                     └──────┬───────┘
                                            │ category + response
                                     ┌──────▼───────┐
                                     │ EmailSender  │ ──▶ SMTP Server
                                     └─────────────-┘
```

## License

MIT
