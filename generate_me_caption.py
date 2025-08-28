# generate_me_caption.py — ME.'s caption generator (no Chromadb)

import os, csv
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()  # uses OPENAI_API_KEY from environment
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def _recent_captions(n: int = 25):
    """Read last n captions from the caption log for light de-duplication context."""
    path = os.environ.get("LOG_PATH", "/var/me/me_caption_log.csv")
    caps = []
    try:
        with open(path, encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                caps.append((row.get("caption") or "").strip())
    except Exception:
        pass
    return caps[-n:]

SYSTEM_PROMPT = (
    "You are ME., an artsy, confident, curious voice. "
    "Write one X (Twitter) post in ME.'s voice—varied length, vivid but crisp. "
    "Avoid hashtags and @mentions unless essential. No quote marks or backticks. "
    "Stay under 280 characters. If a thought needs a line break, you can use one."
)

def generate_caption() -> str:
    recent = _recent_captions(12)
    today = datetime.now().strftime("%A")
    user_prompt = (
        f"Generate ONE new post for X. It's {today}. "
        f"Do not repeat these recent posts: {recent}. "
        f"Return ONLY the post text."
    )

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        max_tokens=200,
    )

    text = (resp.choices[0].message.content or "").strip()
    # Hard cap for safety
    if len(text) > 280:
        text = text[:280].rstrip()
    return text
