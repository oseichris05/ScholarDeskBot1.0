# import json
# from pathlib import Path
# from dotenv import load_dotenv

# # 1) Load environment variables from .env
# load_dotenv()

# # 2) Load JSON config
# CONFIG_PATH = Path(__file__).parent.parent / "config.json"
# if not CONFIG_PATH.exists():
#     raise FileNotFoundError(f"Missing config.json at {CONFIG_PATH}")

# with open(CONFIG_PATH, "r") as f:
#     CONFIG = json.load(f)

# utils/config.py

import os
import json
import base64
from pathlib import Path
from dotenv import load_dotenv

# 1) Load local .env for development
load_dotenv()

# 2) Telegram & Paystack secrets
BOT_TOKEN   = os.getenv("TELEGRAM_TOKEN")
PAYSTACK_SK = os.getenv("PAYSTACK_SECRET")

if not BOT_TOKEN:
    raise RuntimeError("Missing TELEGRAM_TOKEN in environment")
if not PAYSTACK_SK:
    raise RuntimeError("Missing PAYSTACK_SECRET in environment")

# 3) Firebase service account (base64‑encoded JSON in HEROKU_FIREBASE_CRED)
_fb_b64 = os.getenv("HEROKU_FIREBASE_CRED")
if not _fb_b64:
    raise RuntimeError("Missing HEROKU_FIREBASE_CRED in environment")
try:
    _fb_json = json.loads(base64.b64decode(_fb_b64))
except Exception as e:
    raise RuntimeError("Invalid base64 in HEROKU_FIREBASE_CRED") from e

FIREBASE_CREDENTIALS = _fb_json

# 4) Firebase Realtime/Firestore URL
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
if not FIREBASE_DB_URL:
    raise RuntimeError("Missing FIREBASE_DB_URL in environment")

# 5) Static app configuration (universities, prices, etc.)
CONFIG_PATH = Path(__file__).parent.parent / "config.json"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Missing config.json at {CONFIG_PATH}")
with open(CONFIG_PATH, "r") as f:
    STATIC = json.load(f)
