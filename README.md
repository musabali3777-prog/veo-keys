# Veo Key System — Setup Guide

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Web Panel   │────>│  GitHub Repo │<────│  Veo Loader  │
│  (index.html)│     │  keys.json   │     │  (veo.exe)   │
│  Generate &  │     │              │     │  Validates   │
│  Manage Keys │     │  Raw URL     │     │  before      │
└──────────────┘     └──────────────┘     │  injecting   │
                                          └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │  Payload DLL │
                                          │  Re-validates│
                                          │  every 60s   │
                                          └──────────────┘
```

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Name it something like `veo-keys`
3. Make it **public** (so the raw URL is accessible without auth)
4. Initialize with a README

## Step 2: Get a Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it the `repo` scope
4. Copy the token (starts with `ghp_`)

## Step 3: Set Up the Web Dashboard

### Option A: GitHub Pages (recommended)
1. Copy the `keygen/` folder contents into your `veo-keys` repo
2. Go to repo **Settings → Pages → Source: main → / (root)**
3. Your dashboard will be at `https://YOUR_USERNAME.github.io/veo-keys/`

### Option B: Local
1. Just open `keygen/index.html` in your browser

## Step 4: Configure the Raw URL in the Code

Find the raw URL for your keys.json:
```
https://raw.githubusercontent.com/YOUR_USERNAME/veo-keys/main/keys.json
```

Update it in **two** files:

1. **Injector** — `injector/key_auth.h` line 13:
   ```cpp
   inline const char* KEYS_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/veo-keys/main/keys.json";
   ```

2. **Payload** — `payload/sdk/key_validator.hpp` line 11:
   ```cpp
   inline const char* KEYS_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/veo-keys/main/keys.json";
   ```

3. **Rebuild** the project after changing the URLs.

## Step 5: Generate Keys

1. Open the web dashboard
2. Enter your GitHub token and repo name (e.g. `yourname/veo-keys`)
3. Click **Connect & Load Keys**
4. Click any duration button to generate a key
5. Copy the key and give it to your user

## Step 6: Distribute

Give users:
- `veo.exe` (the injector)
- Their license key

When they run `veo.exe`, it will:
1. Ask for their key
2. Download `keys.json` from your repo
3. Validate the key
4. Inject only if valid
5. Re-check every 60 seconds after injection

## Key Durations

| Button   | Duration |
|----------|----------|
| 1 Minute | Testing  |
| 1 Day    | 24 hours |
| 1 Week   | 7 days   |
| 1 Month  | 30 days  |
| 1 Year   | 365 days |

## Revoking Keys

Click **Revoke** on any key in the dashboard. The change pushes to GitHub immediately.
The next time the payload re-checks (within 60 seconds), it will terminate the user's game.

## Python CLI (Alternative)

You can also use `keygen/keygen.py` from the command line:

```bash
# Set env vars
set VEO_GITHUB_TOKEN=ghp_xxxxxxxxxxxx
set VEO_GITHUB_REPO=yourname/veo-keys

# Generate
python keygen.py generate 1day

# List
python keygen.py list

# Revoke
python keygen.py revoke VEO-XXXX-XXXX-XXXX

# Push to GitHub
python keygen.py push
```
