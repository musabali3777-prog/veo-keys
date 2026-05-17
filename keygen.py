#!/usr/bin/env python3
"""
Veo Key Generator
Generates license keys and manages them via a GitHub-hosted keys.json file.

Usage:
  python keygen.py generate <duration>    Generate a new key (1min, 1day, 1week, 1month, 1year)
  python keygen.py list                   List all keys
  python keygen.py revoke <key>           Revoke a key
  python keygen.py push                   Push keys.json to GitHub

Setup:
  1. Create a GitHub repo (public or private)
  2. Create a Personal Access Token with repo scope
  3. Set these environment variables or edit the config below:
     - VEO_GITHUB_TOKEN=ghp_xxxxxxxxxxxx
     - VEO_GITHUB_REPO=username/repo-name
     - VEO_GITHUB_BRANCH=main
"""

import json
import os
import sys
import secrets
import string
import base64
from datetime import datetime, timedelta, timezone

# ===== CONFIG =====
GITHUB_TOKEN  = os.environ.get("VEO_GITHUB_TOKEN", "YOUR_GITHUB_TOKEN_HERE")
GITHUB_REPO   = os.environ.get("VEO_GITHUB_REPO",  "YOUR_USERNAME/veo-keys")
GITHUB_BRANCH = os.environ.get("VEO_GITHUB_BRANCH", "main")
KEYS_FILE     = "keys.json"
LOCAL_KEYS     = os.path.join(os.path.dirname(os.path.abspath(__file__)), KEYS_FILE)
# ==================

DURATIONS = {
    "1min":   timedelta(minutes=1),
    "1day":   timedelta(days=1),
    "1week":  timedelta(weeks=1),
    "1month": timedelta(days=30),
    "1year":  timedelta(days=365),
}

def generate_key():
    """Generate a VEO-XXXX-XXXX-XXXX format key"""
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
    return f"VEO-{parts[0]}-{parts[1]}-{parts[2]}"

def load_keys():
    if os.path.exists(LOCAL_KEYS):
        with open(LOCAL_KEYS, "r") as f:
            return json.load(f)
    return {"keys": {}}

def save_keys(data):
    with open(LOCAL_KEYS, "w") as f:
        json.dump(data, f, indent=2)

def cmd_generate(duration_str):
    if duration_str not in DURATIONS:
        print(f"Invalid duration: {duration_str}")
        print(f"Valid: {', '.join(DURATIONS.keys())}")
        return

    data = load_keys()
    key = generate_key()
    now = datetime.now(timezone.utc)
    expires = now + DURATIONS[duration_str]

    data["keys"][key] = {
        "created":  now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires":  expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration": duration_str,
        "active":   True
    }

    save_keys(data)
    print(f"\n  Key:      {key}")
    print(f"  Duration: {duration_str}")
    print(f"  Expires:  {expires.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"\n  Saved to {LOCAL_KEYS}")
    print(f"  Run 'python keygen.py push' to upload to GitHub.\n")

def cmd_list():
    data = load_keys()
    now = datetime.now(timezone.utc)
    
    if not data["keys"]:
        print("No keys found.")
        return

    print(f"\n{'Key':<22} {'Duration':<10} {'Expires':<22} {'Status'}")
    print("-" * 75)
    for key, info in data["keys"].items():
        exp = datetime.strptime(info["expires"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        active = info.get("active", True)
        if not active:
            status = "REVOKED"
        elif exp < now:
            status = "EXPIRED"
        else:
            status = "ACTIVE"
        print(f"{key:<22} {info['duration']:<10} {info['expires']:<22} {status}")
    print()

def cmd_revoke(key):
    data = load_keys()
    if key not in data["keys"]:
        print(f"Key not found: {key}")
        return
    data["keys"][key]["active"] = False
    save_keys(data)
    print(f"Revoked: {key}")

def cmd_push():
    """Push keys.json to GitHub via the API"""
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        print("urllib required")
        return

    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN_HERE":
        print("Set VEO_GITHUB_TOKEN environment variable or edit keygen.py config.")
        return

    data = load_keys()
    content = json.dumps(data, indent=2)
    encoded = base64.b64encode(content.encode()).decode()

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{KEYS_FILE}"

    # Check if file exists (to get sha for update)
    sha = None
    req = urllib.request.Request(api_url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        resp = urllib.request.urlopen(req)
        existing = json.loads(resp.read().decode())
        sha = existing.get("sha")
    except urllib.error.HTTPError:
        pass  # File doesn't exist yet

    payload = {
        "message": f"Update keys - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "content": encoded,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        },
        method="PUT"
    )

    try:
        resp = urllib.request.urlopen(req)
        print(f"Pushed keys.json to {GITHUB_REPO}/{GITHUB_BRANCH}")
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{KEYS_FILE}"
        print(f"Raw URL: {raw_url}")
    except urllib.error.HTTPError as e:
        print(f"Failed: {e.code} {e.read().decode()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "generate" and len(sys.argv) >= 3:
        cmd_generate(sys.argv[2].lower())
    elif cmd == "list":
        cmd_list()
    elif cmd == "revoke" and len(sys.argv) >= 3:
        cmd_revoke(sys.argv[2])
    elif cmd == "push":
        cmd_push()
    else:
        print(__doc__)
