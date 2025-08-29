# me_metrics.py
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# We rely on the helper functions in twitter_api.py
# These should refresh tokens automatically on 401s.
from twitter_api import who_am_i, get_user_tweets

DATA_FILE = "me_tweet_data.json"


def _load_json(path: str, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def score_engagement(m: Dict[str, Any]) -> int:
    """A simple, tweakable engagement score."""
    if not m:
        return 0
    return (
        int(m.get("like_count", 0))
        + 2 * int(m.get("reply_count", 0))
        + 2 * int(m.get("retweet_count", 0))
        + int(m.get("quote_count", 0))
        + int(m.get("bookmark_count", 0))
    )


def update_me_tweet_data(
    max_results: int = 100,
    exclude_replies: bool = True,
    exclude_retweets: bool = True,
) -> List[Dict[str, Any]]:
    """
    Pulls latest tweets for the authenticated user (OAuth2),
    merges with the local cache, computes a score, and persists.
    Returns the merged rows (most-recent first).
    """
    # 1) Resolve authenticated user id
    me = who_am_i()
    if "data" not in me or "id" not in me["data"]:
        raise RuntimeError(f"/users/me failed: {me}")
    uid = me["data"]["id"]

    # 2) Build params for /users/:id/tweets
    params = {
        "max_results": max_results,
        "tweet.fields": "created_at,public_metrics",
    }
    exclude = []
    if exclude_replies:
        exclude.append("replies")
    if exclude_retweets:
        exclude.append("retweets")
    if exclude:
        params["exclude"] = ",".join(exclude)

    # 3) Fetch tweets
    resp = get_user_tweets(uid, **params)
    if "data" not in resp:
        raise RuntimeError(f"/users/:id/tweets failed: {resp}")

    # 4) Merge with existing cache
    existing = _load_json(DATA_FILE, [])
    by_id = {
        row["id"]: row
        for row in existing
        if isinstance(row, dict) and "id" in row
    }

    for t in resp["data"]:
        row = {
            "id": t["id"],
            "text": t.get("text", ""),
            "created_at": t.get("created_at"),
            "engagement": t.get("public_metrics", {}),
        }
        row["score"] = score_engagement(row["engagement"])
        by_id[row["id"]] = row

    merged = sorted(
        by_id.values(),
        key=lambda r: r.get("created_at", ""),
        reverse=True,
    )

    # 5) Persist
    _save_json(DATA_FILE, merged)
    return merged
