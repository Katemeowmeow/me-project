import os, json, argparse
from datetime import datetime, timedelta
from me_metrics import _load_json, score_engagement, update_me_tweet_data
from me_time_bandit import recommend_times
from me_account import snapshot_account

def _within_days(ts_iso: str, days: int) -> bool:
    try:
        ts = datetime.fromisoformat(ts_iso.replace("Z","+00:00"))
        return ts >= (datetime.now(ts.tzinfo) - timedelta(days=days))
    except Exception:
        return False

def summarize(days: int):
    # Make sure we’re up to date
    rows = update_me_tweet_data(max_results=100, exclude_replies=False, exclude_retweets=False)
    tweets = [r for r in rows if r.get("created_at") and _within_days(r["created_at"], days)]
    n = len(tweets)
    totals = {"likes":0,"retweets":0,"replies":0,"quotes":0,"impressions":0,"score":0.0}
    for t in tweets:
        m = t.get("engagement", {})
        totals["likes"]       += m.get("like_count",0)
        totals["retweets"]    += m.get("retweet_count",0)
        totals["replies"]     += m.get("reply_count",0)
        totals["quotes"]      += m.get("quote_count",0)
        totals["impressions"] += m.get("impression_count",0)
        totals["score"]       += score_engagement(m)

    er = (totals["likes"]+totals["retweets"]+totals["replies"]+totals["quotes"])
    imp = max(1, totals["impressions"])
    engagement_rate = er/imp

    # Top 5 tweets
    top = sorted(tweets, key=lambda t: score_engagement(t.get("engagement",{})), reverse=True)[:5]
    top_fmt = [{"id":t["id"], "score": score_engagement(t.get("engagement",{})), "text": (t.get("text","")[:120]+"…") if len(t.get("text",""))>120 else t.get("text","")} for t in top]

    # Next suggested times (quick view)
    suggested = recommend_times(k=3, min_gap_minutes=120)

    return {
        "window_days": days,
        "tweet_count": n,
        "totals": totals,
        "engagement_rate": round(engagement_rate,4),
        "top_tweets": top_fmt,
        "suggested_times_local": suggested
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14, help="Window size (days)")
    ap.add_argument("--snapshot", action="store_true", help="Record a follower snapshot before reporting")
    args = ap.parse_args()

    if args.snapshot:
        snap = snapshot_account()
        print("Snapshot:", snap)

    report = summarize(args.days)
    print(json.dumps(report, indent=2))
