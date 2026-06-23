# X AI Bot 🤖

A browser-based X (Twitter) bot that monitors keywords and auto-comments using a **local Ollama LLM** — no X API key required.

Built with Python, Playwright, and llama3.1:8b running locally via Ollama.

---

## Features

- 🔍 **Keyword monitoring** — searches X live feed for crypto terms (bitcoin, ethereum, defi, solana, etc.)
- 🧠 **AI-generated comments** — uses local `llama3.1:8b` via Ollama to write genuine, contextual replies
- 🕵️ **Human-like behavior** — randomized delays, character-by-character typing, session limits
- 📝 **Activity logging** — every action logged to `activity_log.json` and `bot.log`
- 🚫 **No X API needed** — runs entirely via browser automation

---

#Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core language |
| Playwright | Browser automation |
| Ollama (llama3.1:8b) | Local LLM for comment generation |
| httpx | Async HTTP client for Ollama |

---

#Setup

Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- llama3.1:8b pulled: `ollama pull llama3.1:8b`
- A dedicated X account for the bot (don't use your main)

Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

Configure credentials

```bash
cp config.example.json config.json
```

Edit `config.json` with your X bot account credentials:

```json
{
  "username": "your_x_username",
  "password": "your_x_password"
}
```

> ⚠️ `config.json` is gitignored — never commit your credentials.

Run the bot

```bash
python bot.py
```

The browser will open visibly so you can watch it work. To run headless, change `headless=False` to `headless=True` in `bot.py`.

---

Config

Edit the top of `bot.py` to customize behavior:

```python
KEYWORDS = ["bitcoin", "ethereum", "crypto", ...]  # what to search for
MIN_DELAY = 45          # minimum seconds between comments
MAX_DELAY = 120         # maximum seconds between comments
MAX_COMMENTS_PER_SESSION = 10  # stop after this many comments
OLLAMA_MODEL = "llama3.1:8b"   # swap for any model you have locally
```

---

## How It Works

```
1. Login to X via Playwright browser automation
2. Search live feed for a random keyword
3. Parse posts — skip retweets, skip short posts
4. Send post text to local Ollama LLM
5. Ollama generates a contextual, human-sounding reply
6. Bot types the reply character-by-character (random delays)
7. Submits the comment, logs the activity
8. Waits a randomized delay before the next comment
9. Repeats until session limit is hit
```

---

## Activity Log

Every comment attempt is logged to `activity_log.json`:

```json
{
  "timestamp": "2026-06-22T14:30:00",
  "keyword": "bitcoin",
  "post_snippet": "BTC holding strong above 60k despite macro...",
  "comment": "The on-chain data has been supporting this level for weeks now.",
  "success": true
}
```

---

## ⚠️ Disclaimer

This project is for **educational and portfolio purposes**. Use responsibly:
- Use a dedicated bot account, not your personal account
- Keep `MAX_COMMENTS_PER_SESSION` low to avoid detection
- X may suspend accounts for aggressive automation
- Don't spam, shill coins, or post misleading content

---

## Author

**David Hall** — [GitHub: David-Hall4](https://github.com/David-Hall4)

Built as part of an AI/automation portfolio. Stack also powers [Backyard Paintball Mobile](https://bypbmobile.com).
