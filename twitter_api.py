import os, json, requests
from dotenv import load_dotenv

load_dotenv()
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
TOKEN_FILE = os.getenv("ME_TOKEN_FILE", "/var/me/tokens.json")  # persistent on Render

def _env(key, default=None):
    v = os.getenv(key, default)
    if v is None or v == "":
        raise RuntimeError(f"Missing {key} in environment/.env")
    return v

def _load_tokens():
    access = os.getenv("TW_ACCESS_TOKEN", "")
    refresh = os.getenv("TW_REFRESH_TOKEN", "")
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                d = json.load(f)
                access  = d.get("access_token", access)
                refresh = d.get("refresh_token", refresh)
    except Exception:
        pass
    return access, refresh

def _save_tokens(access, refresh):
    try:
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            json.dump({"access_token": access, "refresh_token": refresh}, f)
    except Exception:
        pass
    os.environ["TW_ACCESS_TOKEN"] = access
    os.environ["TW_REFRESH_TOKEN"] = refresh

def refresh_access_token() -> str:
    client_id     = _env("TW_CLIENT_ID")
    client_secret = _env("TW_CLIENT_SECRET")
    _, refresh_token = _load_tokens()
    if not refresh_token:
        raise RuntimeError("No TW_REFRESH_TOKEN available.")
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    r = requests.post(TOKEN_URL, data=data,
                      auth=requests.auth.HTTPBasicAuth(client_id, client_secret),
                      timeout=30)
    if not r.ok:
        raise RuntimeError(f"Refresh failed {r.status_code}: {r.text}")
    tok = r.json()
    access = tok.get("access_token")
    new_refresh = tok.get("refresh_token", refresh_token)
    _save_tokens(access, new_refresh)
    return access

def post_tweet(text: str) -> dict:
    def _send(token):
        return requests.post(
            "https://api.twitter.com/2/tweets",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json={"text": text},
            timeout=30
        )
    access, _ = _load_tokens()
    r = _send(access)
    if r.status_code == 401:
        access = refresh_access_token()
        r = _send(access)
    if not r.ok:
        raise RuntimeError(f"Tweet failed {r.status_code}: {r.text}")
    return r.json()
