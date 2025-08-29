# twitter_oauth.py
import os
import requests

TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

def refresh_access_token():
    """
    Exchange a refresh token for a new access token (OAuth2).
    - Reads TW_CLIENT_ID, TW_CLIENT_SECRET, TW_REFRESH_TOKEN, TW_REDIRECT_URI
      from the environment (Render Environment page).
    - Puts the new access token into os.environ['TW_ACCESS_TOKEN'] so callers
      can use it immediately.
    - If Twitter returns a new refresh_token, we also update it in os.environ.
      (You'll still need to copy it into Render if you want it to persist.)
    """
    client_id = os.getenv("TW_CLIENT_ID")
    client_secret = os.getenv("TW_CLIENT_SECRET")
    refresh_token = os.getenv("TW_REFRESH_TOKEN")
    redirect_uri = os.getenv("TW_REDIRECT_URI")

    if not all([client_id, client_secret, refresh_token, redirect_uri]):
        raise RuntimeError("Missing one of TW_CLIENT_ID / TW_CLIENT_SECRET / TW_REFRESH_TOKEN / TW_REDIRECT_URI")

    data = {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": redirect_uri,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # Basic auth (client_id, client_secret) is accepted by X
    resp = requests.post(TOKEN_URL, data=data, headers=headers, auth=(client_id, client_secret))
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to refresh token: {resp.status_code} {resp.text}")

    tokens = resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        raise RuntimeError(f"No access_token in refresh response: {tokens}")

    os.environ["TW_ACCESS_TOKEN"] = access_token

    # Sometimes Twitter rotates the refresh token
    if "refresh_token" in tokens and tokens["refresh_token"]:
        os.environ["TW_REFRESH_TOKEN"] = tokens["refresh_token"]

    return access_token
