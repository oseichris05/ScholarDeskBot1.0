# from motor.motor_asyncio import AsyncIOMotorClient
# import os
# from dotenv import load_dotenv
# load_dotenv()


# MONGO_URI = os.getenv("MONGODB_URI")
# MONGO_DB = os.getenv("MONGODB_DB", "ScholarDeskBot")

# if not MONGO_URI:
#     raise RuntimeError("MONGODB_URI is not set in environment")

# _client = AsyncIOMotorClient(MONGO_URI, tlsAllowInvalidCertificates=True)
# db = _client[MONGO_DB]

# # Existing collections
# users_coll = db["users"]
# transactions_coll = db["transactions"]
# referrals_coll = db["referrals"]
# config_coll = db["config"]

# # New stock collection – put documents like { "checker_type": "WASSCE", "stock": 42 }
# checker_stock_coll = db["checker_stock"]


# utils/db.py

from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
load_dotenv()


MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DB", "ScholarDeskBot")

if not MONGO_URI:
    raise RuntimeError("MONGODB_URI not set")

_client = AsyncIOMotorClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = _client[MONGO_DB]

users_coll = db["users"]
transactions_coll = db["transactions"]
referrals_coll = db["referrals"]
checker_stock_coll = db["checker_stock"]
# NEW: holds {checker_type, serial, pin, used}
checker_codes_coll = db["checker_codes"]
