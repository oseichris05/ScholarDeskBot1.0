# seed_checker_stock.py

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize (reuse your utils/db approach if preferred)
cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Define initial stock per checker type
stock = {
    "BECE":  50,
    "WASSCE":50,
    "NOVDEC":50,
    "NSS":   50
}

# Seed
for typ, count in stock.items():
    db.collection("checker_stock").document(typ).set({"stock": count})
    print(f"Seeded {typ}: {count}")
