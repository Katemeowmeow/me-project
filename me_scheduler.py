# me_scheduler.py — clean, robust scheduler for ME.

import os, time, json, csv, schedule
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

from twitter_api import post_tweet
from generate_me_caption import generate_caption
from me_metrics import update_me_tweet_data
from me_time_bandit import fit_bandit, recommend_times

load_dotenv()

# ---- Config ---------------------------------------------------------------

STATE_FILE   = "me_time_state.json"
POSTS_PER_DAY = int(os.getenv("ME_POSTS_PER_DAY", "3"))
MIN_GAP_MIN   = int(os.getenv("ME_MIN_GAP_MIN", "120"))
RETRAIN_DAYS  = int(os.getenv("ME_RETRAIN_DAYS", "14"))

# Where to store the caption log (Render disk by default)
LOG_PATH = os.environ.get("LOG_PATH", "/var/me/me_caption_log.csv")
SNAPSHOT_PATH = os.environ.get("SNAPSHOT_PATH", "/var/me/me_snapshot.jsonl")

# ---- Small helpers --------------------------------------------------------

def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_retrain": None}

def _save_state(s: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def log_post(caption: str, tweet_id):
    """Append one row to the caption log safely (CSV quoting)."""
    _ensure_dir(LOG_PATH)
    is_new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["ts", "caption", "tweet_id"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), caption, tweet_id])

# ---- Tweeting -------------------------------------------------------------

def safe_post_once():
    """Generate a caption, post it, and log the result (never crash the loop)."""
    try:
        caption = generate_caption()
        res = post_tweet(caption)
        tid = (res or {}).get("data", {}).get("id")
        print(f"[{datetime.now().isoformat(timespec='seconds')}] ✅ Tweeted {tid}: {caption}")
        log_post(caption, tid)
    except Exception as e:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] ❌ {e}")

# ---- Nightly snapshot (optional, resilient) -------------------------------

def snapshot_account():
    """Record a lightweight daily snapshot; fails closed (no crash)."""
    try:
        _ensure_dir(SNAPSHOT_PATH)
        payload = {"ts": datetime.now().isoformat(timespec="seconds")}
        # If me_report.summarize exists, include a tiny summary
        try:
            from me_report import summarize
            rep = summarize(days=14)
            payload["engagement_rate"] = rep.get("engagement_rate")
            payload["tweet_count"] = rep.get("tweet_count")
            payload["suggested_times_local"] = rep.get("suggested_times_local")
        except Exception:
            pass
        with open(SNAPSHOT_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        print(f"[{payload['ts']}] 📸 Snapshot written")
    except Exception as e:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] ⚠️ Snapshot failed: {e}")

# ---- Daily planning -------------------------------------------------------

def plan_today():
    # 1) Update local metrics (pulls latest from X)
    try:
        rows = update_me_tweet_data(max_results=100, exclude_replies=False, exclude_retweets=False)
        print(f"📥 Updated metrics. Rows: {len(rows)}")
    except Exception as e:
        print("⚠️ update_me_tweet_data failed:", e)

    # 2) Retrain every N days
    state = _load_state()
    today = date.today()
    last = None
    if state.get("last_retrain"):
        try:
            last = datetime.fromisoformat(state["last_retrain"]).date()
        except Exception:
            last = None
    need_retrain = (last is None) or ((today - last) >= timedelta(days=RETRAIN_DAYS))
    if need_retrain:
        print("🧠 Retraining time-bandit…")
        try:
            fit_bandit()
            state["last_retrain"] = datetime.now().isoformat(timespec="seconds")
            _save_state(state)
        except Exception as e:
            print("⚠️ Retrain failed:", e)

    # 3) Recommend today's local times and schedule tweets
    try:
        times = recommend_times(k=POSTS_PER_DAY, min_gap_minutes=MIN_GAP_MIN)
        print("📅 Today’s adaptive times:", times)
        for t in times:
            schedule.every().day.at(t).do(safe_post_once)
    except Exception as e:
        print("⚠️ recommend_times failed:", e)

# ---- Scheduler bootstrap --------------------------------------------------

def reset_plan():
    schedule.clear()
    plan_today()
    # Midnight refresh & nightly snapshot
    schedule.every().day.at("00:05").do(reset_plan)
    schedule.every().day.at("23:55").do(snapshot_account)

# ---- Main loop ------------------------------------------------------------

if __name__ == "__main__":
    reset_plan()
    while True:
        schedule.run_pending()
        time.sleep(5)
