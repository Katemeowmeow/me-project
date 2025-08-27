import os, json, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API = "https://api.twitter.com/2"

def _env(k):
    v = os.getenv(k)
    if not v: raise RuntimeError(f"Missing {k} in .env")
    return v

def _auth():
    return {"Authorization": f"Bearer {_env('TW_ACCESS_TOKEN')}"}

def snapshot_account(save_to="me_account_snapshots.json"):
    """Grab current public metrics (followers, following, tweet count)."""
    r = requests.get(f"{API}/users/me",
                     headers=_auth(),
                     params={"user.fields":"public_metrics"}).json()
    if "data" not in r: raise RuntimeError(f"/users/me failed: {r}")
    pm = r["data"]["public_metrics"]
    snap = {
        "taken_at": datetime.now().isoformat(timespec="seconds"),
        "followers": pm.get("followers_count", 0),
        "following": pm.get("following_count", 0),
        "tweet_count": pm.get("tweet_count", 0),
        "listed_count": pm.get("listed_count", 0),
    }
    # append
    rows = []
    if os.path.exists(save_to):
        try:
            with open(save_to,"r") as f: rows = json.load(f)
        except Exception: rows = []
    rows.append(snap)
    with open(save_to,"w") as f: json.dump(rows,f,indent=2)
    return snap
