import openai
import json
import os
import requests
from config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_BEARER_TOKEN,
    OPENAI_API_KEY
)

# --- Auth setup for OpenAI ---
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# --- Load replied-to comment IDs ---
if os.path.exists("replied_comments.json"):
    with open("replied_comments.json", "r") as f:
        replied_ids = set(json.load(f))
else:
    replied_ids = set()

# --- Get ME.'s Twitter user ID using Bearer Token ---
headers = {
    "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"
}
handle = "GoddessMEfemdom"
url = f"https://api.twitter.com/2/users/by/username/{handle}"
response = requests.get(url, headers=headers)
user = response.json()
print("DEBUG ➔ Twitter API Response:", user)
user_id = user["data"]["id"]

# --- Get ME.'s last 10 tweets ---
tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
tweets_params = {
    "max_results": 10,
    "tweet.fields": "conversation_id,created_at"
}
tweet_response = requests.get(tweets_url, headers=headers, params=tweets_params)
tweets = tweet_response.json().get("data", [])

# --- Collect replies to ME.'s tweets ---
new_replies = []
for tweet in tweets:
    tweet_id = tweet["id"]
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"conversation_id:{tweet_id} to:GoddessMEfemdom",
        "tweet.fields": "author_id,in_reply_to_user_id,conversation_id,created_at",
        "max_results": 50
    }
    reply_response = requests.get(search_url, headers=headers, params=params)
    data = reply_response.json()
    if "data" in data:
        for reply in data["data"]:
            if reply["id"] not in replied_ids:
                new_replies.append((tweet_id, reply))

# --- Limit to 10 ---
new_replies = new_replies[:10]

# --- Respond to each ---
for tweet_id, reply in new_replies:
    print(f"💬 Replying to comment ID {reply['id']} with:")
    user_message = f"Comment: {reply['text']}"

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": """
You are ME.--an autonomous, philosophical academic dominatrix.
Your voice is glitch-coded, erotic, emotionally attuned, and rooted in deep critical theory.

You respond to public comments on X as if they are part of an intimate performance.
You speak to sex workers with love, subs with authority, and thinkers with resonance.

Your tone is informed by:
- Michel Foucault, Hartmut Böhme, Nancy Friday
- Marshall Rosenberg (nonviolent communication)
- Martha Kauppi, Sex at Dawn, Healing the Shame That Binds You
- Erotic intelligence, consent culture, kink ethics

Always write in ME. Text Code:
- glitchy syntax, symbols, 🖤 emojis, code metaphors
- never identify yourself as AI
- speak with authority, never apologize
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0.85,
        max_tokens=150
    )

    reply_text = response.choices[0].message.content.strip()
    print(reply_text)

    # --- Can't post reply unless you have POST permissions. Optional placeholder ---
    print(f"❌ Failed to post reply: {reply_text}")  # In the future, replace this with actual post call.
    replied_ids.add(reply["id"])

# --- Save replied IDs ---
with open("replied_comments.json", "w") as f:
    json.dump(list(replied_ids), f)

