# generate_token.py — Confidential client + PKCE
import base64, hashlib, os, secrets, sys, urllib.parse, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID     = os.getenv("TW_CLIENT_ID")
CLIENT_SECRET = os.getenv("TW_CLIENT_SECRET")
REDIRECT_URI  = os.getenv("TW_REDIRECT_URI")
SCOPE         = os.getenv("TW_OAUTH_SCOPE", "tweet.read tweet.write users.read offline.access")

AUTH_URL  = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    print("Missing TW_CLIENT_ID / TW_CLIENT_SECRET / TW_REDIRECT_URI in .env"); sys.exit(1)

# PKCE
code_verifier  = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).rstrip(b"=").decode()
state          = secrets.token_urlsafe(16)

params = dict(
    response_type="code",
    client_id=CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    state=state,
    code_challenge=code_challenge,
    code_challenge_method="S256",
)
url = AUTH_URL + "?" + urllib.parse.urlencode(params)
print("\nIf your browser doesn't open, paste this URL into it:\n", url, "\n")
webbrowser.open(url)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = qs.get("code", [None])[0]; st = qs.get("state", [None])[0]
        if not code or st != state:
            self.send_response(400); self.end_headers(); self.wfile.write(b"Invalid auth response."); return

        data = {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
            "code": code,
        }
        # Confidential client: include client auth
        r = requests.post(TOKEN_URL, data=data, auth=requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))

        self.send_response(200); self.end_headers(); self.wfile.write(b"You can close this tab.")
        print("\nToken response:", r.status_code, r.text)

        if r.ok:
            tok = r.json()
            access  = tok.get("access_token", "")
            refresh = tok.get("refresh_token", "")
            lines = []
            if os.path.exists(".env"):
                with open(".env","r") as f: lines = f.readlines()
            def set_line(k,v):
                v = f'"{v}"' if " " in v else v
                for i, line in enumerate(lines):
                    if line.strip().startswith(k+"="): lines[i] = f"{k}={v}\n"; return
                lines.append(f"{k}={v}\n")
            set_line("TW_ACCESS_TOKEN", access)
            set_line("TW_REFRESH_TOKEN", refresh)
            with open(".env","w") as f: f.writelines(lines)
            print("\nSaved TW_ACCESS_TOKEN and TW_REFRESH_TOKEN to .env")

server = HTTPServer(("localhost", 8000), Handler)
print("Waiting on http://localhost:8000/ ...")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
