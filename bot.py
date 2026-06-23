"""
X Crypto Bot
============
Monitors X (Twitter) for crypto keywords and auto-comments using a local Ollama LLM.
No X API required — runs via browser automation with Playwright.

Author: David Hall
GitHub: David-Hall4
"""

import asyncio
import random
import json
import logging
from datetime import datetime, date
from playwright.async_api import async_playwright
import httpx

# ── Config ────────────────────────────────────────────────────────────────────

KEYWORDS = [
    "bitcoin", "crypto", "altcoin", "defi",
    "web3", "nft", "solana", "blockchain", "btc"
]

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b-instruct-q8_0"

# How long to wait between comments (seconds) — randomized to look human
MIN_DELAY = 45
MAX_DELAY = 120

# Daily limit — bot stops for the day after this many comments across all sessions
MAX_COMMENTS_PER_DAY = 15

# Daily log file to track how many comments posted today
DAILY_LOG = "daily_count.json"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Daily Limit Tracker ───────────────────────────────────────────────────────

def get_daily_count() -> int:
    """Read how many comments have been posted today."""
    try:
        with open(DAILY_LOG) as f:
            data = json.load(f)
        if data.get("date") == str(date.today()):
            return data.get("count", 0)
        else:
            # New day — reset
            return 0
    except FileNotFoundError:
        return 0


def increment_daily_count():
    """Add 1 to today's comment count."""
    count = get_daily_count()
    with open(DAILY_LOG, "w") as f:
        json.dump({"date": str(date.today()), "count": count + 1}, f)


def remaining_today() -> int:
    """How many comments are left for today."""
    return max(0, MAX_COMMENTS_PER_DAY - get_daily_count())


# ── Ollama Comment Generator ───────────────────────────────────────────────────

async def generate_comment(post_text: str, keyword: str) -> str:
    """Ask local Ollama to generate a Joyce-style crypto comment."""
    prompt = f"""You are Joyce, a confident crypto girl who's been around long enough to know when people are being dumb. You clown on overcomplicating things and cut through the BS. You talk like a real person, casual and straight to the point. You're not mean but you're not sugarcoating either. You're smart but you keep it simple — no fancy words, no jargon, just real talk.

Rules:
- Max 2 short sentences
- No hashtags
- Light emojis are ok if it feels natural
- No words like "tokenomics", "exacerbate", "it's worth noting", "significant"
- If someone is overcomplicating something, call it out casually
- If something is obvious, say it like it's obvious
- Sound like a girl texting her friend about crypto, not a financial advisor
- Keep it short, punchy, a little sarcastic sometimes

Post: "{post_text}"

Reply (just the reply, nothing else):"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.85,
                    "max_tokens": 100
                }
            })
            data = response.json()
            comment = data.get("response", "").strip()

            if len(comment) > 280:
                comment = comment[:277] + "..."

            log.info(f"Generated comment: {comment}")
            return comment

    except Exception as e:
        log.error(f"Ollama error: {e}")
        fallbacks = [
            "lol people really out here acting surprised by this",
            "this was obvious like 3 months ago but ok",
            "yeah no one could have seen this coming... except everyone",
        ]
        return random.choice(fallbacks)


# ── X Browser Automation ───────────────────────────────────────────────────────

async def search_keyword(page, keyword: str) -> list[dict]:
    """Search X for a keyword and return post data."""
    log.info(f"Searching for: {keyword}")
    search_url = f"https://x.com/search?q={keyword}&f=live"
    await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(random.uniform(3, 5))

    posts = []
    articles = await page.query_selector_all('article[data-testid="tweet"]')

    for article in articles[:15]:
        try:
            text_el = await article.query_selector('[data-testid="tweetText"]')
            text = await text_el.inner_text() if text_el else ""

            if not text or len(text) < 20:
                continue

            # Skip retweets
            rt_label = await article.query_selector('[data-testid="socialContext"]')
            if rt_label:
                rt_text = await rt_label.inner_text()
                if "Retweeted" in rt_text:
                    continue

            reply_btn = await article.query_selector('[data-testid="reply"]')

            posts.append({
                "text": text,
                "keyword": keyword,
                "reply_btn": reply_btn,
                "article": article
            })

        except Exception as e:
            log.debug(f"Error parsing post: {e}")
            continue

    log.info(f"Found {len(posts)} posts for '{keyword}'")
    return posts


async def post_comment(page, post: dict, comment: str) -> bool:
    """Click reply on a post and submit a comment."""
    try:
        await post["reply_btn"].click()
        await asyncio.sleep(random.uniform(2, 4))

        reply_box = page.locator('[data-testid="tweetTextarea_0"]')
        await reply_box.click()

        for char in comment:
            await reply_box.type(char, delay=random.randint(30, 120))

        await asyncio.sleep(random.uniform(1, 2))

        submit_btn = page.locator('[data-testid="tweetButton"]')
        await submit_btn.click()
        await asyncio.sleep(random.uniform(2, 4))

        log.info(f"Comment posted: {comment[:60]}...")
        return True

    except Exception as e:
        log.error(f"Failed to post comment: {e}")
        try:
            close = page.locator('[data-testid="app-bar-close"]')
            if await close.count() > 0:
                await close.click()
        except:
            pass
        return False


# ── Session Logger ─────────────────────────────────────────────────────────────

def log_activity(keyword: str, post_text: str, comment: str, success: bool):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "keyword": keyword,
        "post_snippet": post_text[:100],
        "comment": comment,
        "success": success
    }
    try:
        with open("activity_log.json", "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        log.debug(f"Log write error: {e}")


# ── Main Bot Loop ──────────────────────────────────────────────────────────────

async def run_bot():
    # Check daily limit before doing anything
    left = remaining_today()
    if left == 0:
        log.info(f"Daily limit of {MAX_COMMENTS_PER_DAY} comments already reached. Come back tomorrow!")
        return

    log.info(f"Daily limit: {MAX_COMMENTS_PER_DAY} | Already posted today: {get_daily_count()} | Remaining: {left}")

    comment_count = 0
    commented_posts = set()

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        log.info(f"Bot started. Will post up to {left} more comments today.")
        log.info(f"Keywords: {', '.join(KEYWORDS)}")

        while comment_count < left:
            keyword = random.choice(KEYWORDS)
            posts = await search_keyword(page, keyword)

            for post in posts:
                if comment_count >= left:
                    break

                post_id = post["text"][:50]
                if post_id in commented_posts:
                    continue

                comment = await generate_comment(post["text"], keyword)

                if not comment:
                    continue

                success = await post_comment(page, post, comment)
                log_activity(keyword, post["text"], comment, success)
                commented_posts.add(post_id)

                if success:
                    comment_count += 1
                    increment_daily_count()
                    total_today = get_daily_count()
                    log.info(f"Progress: {total_today}/{MAX_COMMENTS_PER_DAY} comments posted today")

                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                log.info(f"Waiting {delay:.0f}s before next comment...")
                await asyncio.sleep(delay)

            await asyncio.sleep(random.uniform(30, 60))

        log.info(f"Session complete. Posted {comment_count} comments this session. Total today: {get_daily_count()}/{MAX_COMMENTS_PER_DAY}")


if __name__ == "__main__":
    asyncio.run(run_bot())
