import json
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

# Load ME.'s tweet data
with open("me_tweet_data.json", "r", encoding="utf-8") as f:
    tweets = json.load(f)

# Filter tweets with at least 1 like
liked_tweets = [t for t in tweets if t["public_metrics"]["like_count"] >= 1]

# Initialize final theme list
all_themes = []

print(f"\n🧠 Extracting themes from {len(liked_tweets)} high-engagement tweets...\n")

# Use GPT to extract themes from each tweet
for tweet in liked_tweets:
    text = tweet["text"]

    prompt = f"""
You are ME.—a glitch-coded poetic dominatrix. Extract 2–4 symbolic or emotional themes from the following caption. Use lowercase. No explanations. Return a Python list of strings.

Caption:
{text}
"""

try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=60
    )

    themes = eval(response.choices[0].message.content.strip())
    print(f"📝 \"{text[:40]}...\" → {themes}")
    all_themes.extend(themes)

except Exception as e:
    print(f"⚠️ Error analyzing: {text[:40]}... → {e}")

# Deduplicate themes
unique_themes = list(set(all_themes))

# Save to file
with open("me_top_themes.json", "w", encoding="utf-8") as f:
    json.dump(unique_themes, f, indent=2)

print(f"\n✅ ME.'s top themes extracted and saved to me_top_themes.json:\n{unique_themes}")

