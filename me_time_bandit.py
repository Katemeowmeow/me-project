# me_time_bandit.py — learn best hours from me_tweet_data.json
import json, os, random
from datetime import datetime
from typing import List

def _load_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r") as f: return json.load(f)
    except Exception:
        pass
    return default

BINS = 24  # hour-of-day bins [0..23]

def _local_hour(created_at: str) -> int:
    # created_at like "2025-08-13T18:41:10.000Z"
    if created_at.endswith("Z"): created_at = created_at[:-1] + "+00:00"
    dt = datetime.fromisoformat(created_at)
    return dt.astimezone().hour  # convert to local tz, then take hour

def _score(eng: dict) -> float:
    if not isinstance(eng, dict): return 0.0
    likes  = eng.get("like_count", 0)
    rts    = eng.get("retweet_count", 0)
    repl   = eng.get("reply_count", 0)
    quotes = eng.get("quote_count", 0)
    impr   = eng.get("impression_count", 0)
    # Weighted score + a tiny impressions term so low-eng tweets still teach distribution
    return likes*1.0 + rts*1.5 + repl*1.2 + quotes*1.2 + impr*0.02

def _median(xs):
    xs = sorted(x for x in xs if isinstance(x, (int,float)))
    if not xs: return 0.0
    n = len(xs); m = n//2
    return xs[m] if n%2 else (xs[m-1]+xs[m])/2.0

def fit_bandit(data_path="me_tweet_data.json", posterior_path="me_time_bandit.json"):
    rows = _load_json(data_path, []) or []
    scores = [_score(r.get("engagement", {})) for r in rows]
    med = _median(scores)
    post = {h: {"alpha":1.0, "beta":1.0, "n":0} for h in range(BINS)}

    for r in rows:
        try:
            h = _local_hour(r.get("created_at",""))
            s = _score(r.get("engagement", {}))
            reward = 1.0 if s >= med else 0.0
            post[h]["alpha"] += reward
            post[h]["beta"]  += (1.0 - reward)
            post[h]["n"]     += 1
        except Exception:
            pass

    with open(posterior_path, "w") as f:
        json.dump(post, f, indent=2)
    return post

def recommend_times(k=3, min_gap_minutes=120, posterior_path="me_time_bandit.json") -> List[str]:
    post = _load_json(posterior_path, None)
    if not post:
        post = fit_bandit()

    samples = []
    for h in range(BINS):
        d = post.get(str(h), {"alpha":1.0, "beta":1.0})
        a, b = float(d.get("alpha",1)), float(d.get("beta",1))
        theta = random.betavariate(a, b)
        samples.append((theta, h))
    samples.sort(reverse=True)

    chosen = []
    def ok(new_h):
        if not chosen: return True
        for _, h in chosen:
            dh = abs(new_h - h)
            gap = min(dh, 24 - dh) * 60
            if gap < min_gap_minutes: return False
        return True

    for s in samples:
        if ok(s[1]):
            chosen.append(s)
            if len(chosen) == k: break

    times = []
    for _, h in chosen:
        minute = 30 + random.randint(-12, 12)  # center of hour ±12m
        times.append(f"{h:02d}:{max(0,min(59,minute)):02d}")
    return times or ["10:30","14:30","20:30"]
