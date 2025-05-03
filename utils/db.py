# from motor.motor_asyncio import AsyncIOMotorClient
# import os
# from dotenv import load_dotenv
# load_dotenv()


# MONGO_URI = os.getenv("MONGODB_URI")
# MONGO_DB = os.getenv("MONGODB_DB", "ScholarDeskBot")

# if not MONGO_URI:
#     raise RuntimeError("MONGODB_URI not set")

# _client = AsyncIOMotorClient(MONGO_URI, tlsAllowInvalidCertificates=True)
# db = _client[MONGO_DB]

# users_coll = db["users"]
# transactions_coll = db["transactions"]
# referrals_coll = db["referrals"]
# checker_stock_coll = db["checker_stock"]
# # NEW: holds {checker_type, serial, pin, used}
# checker_codes_coll = db["checker_codes"]

# utils/db.py
# utils/db.py

import os
from pathlib import Path
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# 1. Load .env
load_dotenv()

# 2. Point to your service account key JSON
cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_path or not Path(cred_path).exists():
    raise RuntimeError("Set GOOGLE_APPLICATION_CREDENTIALS to your Firebase key JSON")

# 3. Initialize Firebase
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# 4. Firestore client
db = firestore.client()

# 5. Collections
users_coll         = db.collection("users")
transactions_coll  = db.collection("transactions")
checker_stock_coll = db.collection("checker_stock")
checker_codes_coll = db.collection("checker_codes")
