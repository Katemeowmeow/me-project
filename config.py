# config.py

import os

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Twitter
TWITTER_CLIENT_ID = os.getenv("TW_CLIENT_ID")
TWITTER_CLIENT_SECRET = os.getenv("TW_CLIENT_SECRET")
TWITTER_REDIRECT_URI = os.getenv("TW_REDIRECT_URI")

# (optional if you’re using OAuth2)
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
TW_REFRESH_TOKEN = os.getenv("TW_REFRESH_TOKEN")
