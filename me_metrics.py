# me_metrics.py
import os, json, requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
API = "https://api.twitter.com/2"

def _env(key):
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f"Missing {key} in .env")
    return v

def _auth_headers():
    return {"Authorization": f"Bearer {_env('TW_ACCESS_TOKEN')}"}

def score_engagement(m):
    if not isinstance(m, dict): return 0.0
    likes  = m.get("like_count", 0)
    rts    = m.get("retweet_count", 0)
    repl   = m.get("reply_count", 0)
    quotes = m.get("quote_count", 0)
    # simple weighted score
    return likes*1.0 + rts*1.5 + repl*1.2 + quotes*1.2

def _load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r") as f: return json.load(f)
    except Exception:
        pass
    return default

def update_me_tweet_data(max_results=100, exclude_replies=True, exclude_retweets=True):
    """
    Fetches your latest tweets and merges into me_tweet_data.json:
    [{id, text, created_at, public_metrics, score}]
    """
    # who am i
    me = requests.get(f"{API}/users/me",
                      headers=_auth_headers(),
                      params={"user.fields":"public_metrics"}).json()
    if "data" not in me:
        raise RuntimeError(f"/users/me failed: {me}")
    uid = me["data"]["id"]

    exclude = []
    if exclude_replies:  exclude.append("replies")
    if exclude_retweets: exclude.append("retweets")
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
    }
    if exclude: params["exclude"] = ",".join(exclude)

    resp = requests.get(f"{API}/users/{uid}/tweets",
                        headers=_auth_headers(), params=params).json()
    if "data" not in resp:
        raise RuntimeError(f"/users/:id/tweets failed: {resp}")

    existing = _load_json("me_tweet_data.json", [])
    by_id = {row.get("id"): row for row in existing if isinstance(row, dict)}
    for t in resp["data"]:
        row = {
            "id": t["id"],
            "text": t.get("text", ""),
            "created_at": t.get("created_at"),
            "engagement": t.get("public_metrics", {}),
        }
        row["score"] = score_engagement(row["engagement"])
        by_id[row["id"]] = row

    merged = list(by_id.values())
    with open("me_tweet_data.json", "w") as f:
        json.dump(merged, f, indent=2)
    return merged
