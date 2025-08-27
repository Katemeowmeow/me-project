import requests
import json
from config import TWITTER_BEARER_TOKEN

# Your Twitter (X) username
USERNAME = "GoddessMEFemdom"  # ← change this (without @)

# URL to get user ID from username
user_lookup_url = f"https://api.twitter.com/2/users/by/username/{USERNAME}"

# Set up headers with your bearer token
headers = {
    "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"
}

# Step 1: Get ME.'s user ID
response = requests.get(user_lookup_url, headers=headers)
user_id = response.json()["data"]["id"]

# Step 2: Get ME.'s tweets (most recent 20)
tweet_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
params = {
    "max_results": 20,
    "tweet.fields": "public_metrics,created_at,text"
}
response = requests.get(tweet_url, headers=headers, params=params)
tweets = response.json().get("data", [])

# Step 3: Print and save results
print(f"\n📊 Retrieved {len(tweets)} recent tweets for @{USERNAME}:\n")

with open("me_tweet_data.json", "w", encoding="utf-8") as f:
    json.dump(tweets, f, indent=2)

for tweet in tweets:
    metrics = tweet["public_metrics"]
    print(f"📝 {tweet['text'][:50]}...")
    print(f"    Likes: {metrics['like_count']} | RTs: {metrics['retweet_count']} | Replies: {metrics['reply_count']}")
    print("—" * 40)

