import os, time, json, schedule
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from twitter_api import post_tweet
from generate_me_caption import generate_caption
from me_metrics import update_me_tweet_data
from me_time_bandit import fit_bandit, recommend_times

load_dotenv()

STATE_FILE = "me_time_state.json"
POSTS_PER_DAY = int(os.getenv("ME_POSTS_PER_DAY", "3"))
MIN_GAP_MIN   = int(os.getenv("ME_MIN_GAP_MIN", "120"))
RETRAIN_DAYS  = int(os.getenv("ME_RETRAIN_DAYS", "14"))  # ← change if you want

def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_retrain": None}

def _save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f, indent=2)

def safe_post_once():
    try:
        caption = generate_caption()
        res = post_tweet(caption)
        tid = res.get("data", {}).get("id")
        print(f"[{datetime.now().isoformat(timespec='seconds')}] ✅ Tweeted {tid}: {caption}")
        with open("me_caption_log.csv", "a") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')},\"{caption.replace('\"','''')}\",{tid}\n")
    except Exception as e:
        print(f"[{datetime.now().isoformat(timespec='seconds')}] ❌ {e}")

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
        fit_bandit()
        state["last_retrain"] = datetime.now().isoformat(timespec="seconds")
        _save_state(state)

    # 3) Recommend today's local times and schedule tweets
    times = recommend_times(k=POSTS_PER_DAY, min_gap_minutes=MIN_GAP_MIN)
    print("📅 Today’s adaptive times:", times)
    for t in times:
        schedule.every().day.at(t).do(safe_post_once)

def reset_plan():
    schedule.clear()
    plan_today()
    # schedule next midnight refresh
    schedule.every().day.at("00:05").do(reset_plan)
    schedule.every().day.at("23:55").do(snapshot_account)
    schedule.every().day.at("23:55").do(snapshot_account)

if __name__ == "__main__":
    reset_plan()
    while True:
        schedule.run_pending()
        time.sleep(5)
