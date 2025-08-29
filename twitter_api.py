# twitter_api.py
import os
import json
import requests
from dotenv import load_dotenv
from twitter_oauth import refresh_access_token

load_dotenv()

API = "https://api.twitter.com/2"

def _headers():
    """
    Build auth headers; refresh the token if we don't have one yet.
    """
    token = os.getenv("TW_ACCESS_TOKEN")
    if not token:
        token = refresh_access_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def _retry_401(func):
    """
    Decorator-ish helper for a simple one-time 401 retry after refresh.
    """
    def wrapper(*args, **kwargs):
        r = func(*args, **kwargs)
        if r.status_code == 401:
            # refresh and try once more
            refresh_access_token()
            r = func(*args, **kwargs)
        return r
    return wrapper

@_retry_401
def _get(url, params=None):
    return requests.get(url, headers=_headers(), params=params)

@_retry_401
def _post(url, payload=None):
    return requests.post(url, headers=_headers(), data=json.dumps(payload or {}))

def who_am_i():
    """
    GET /users/me — returns the authenticated user (verifies tokens work).
    """
    r = _get(f"{API}/users/me")
    r.raise_for_status()
    return r.json()

def post_tweet(text: str):
    """
    POST /tweets — publish a tweet in the user context.
    Returns the JSON response (contains tweet id).
    """
    payload = {"text": text}
    r = _post(f"{API}/tweets", payload)
    r.raise_for_status()
    return r.json()

def get_user_tweets(user_id: str, **params):
    """
    GET /users/:id/tweets — used by analytics code (me_metrics).
    Example params: {"max_results": 100, "tweet.fields": "created_at,public_metrics"}
    """
    r = _get(f"{API}/users/{user_id}/tweets", params=params)
    r.raise_for_status()
    return r.json()
