"""Exercise the actual Nginx -> FastAPI -> PostgreSQL Compose deployment."""
import http.cookiejar
import json
from pathlib import Path
import secrets
import urllib.request
import urllib.error

env = dict(line.split("=", 1) for line in (Path(__file__).resolve().parents[1] / ".env").read_text().splitlines()
           if line and not line.startswith("#") and "=" in line)
base = f"http://127.0.0.1:{env.get('PORT', '8080')}"
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

def request(path, method="GET", body=None, headers=None):
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json", "X-MusicAccess": "1", **(headers or {})})
    try:
        return client.open(req)
    except urllib.error.HTTPError as error:
        return error

assert request("/music?title=Night").status == 200
assert json.load(request("/api/health"))["status"] == "ok"
assert len(json.load(request("/api/tracks?title=Night&artist=Electronic"))) == 1
account = {"login": "smoke_" + secrets.token_hex(5), "password": "Aa1!" + secrets.token_hex(20)}
assert request("/api/register", "POST", account).status == 201
session = json.load(request("/api/login", "POST", account))
assert session["user"]["clearance_level"] == 1
assert request("/api/me").status == 200
stream = request("/api/tracks/1/stream", headers={"Range": "bytes=0-9"})
assert stream.status == 206 and stream.read().startswith(b"RIFF")
assert request("/api/tracks/2/stream").status == 403
assert request("/api/me", "DELETE", {"password": account["password"]}).status == 204
assert request("/api/me").status == 401
print("Compose smoke passed: registration, PostgreSQL persistence, session, search, range stream, MAC, deletion")
