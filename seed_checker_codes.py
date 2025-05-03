# seed_checker_codes.py

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Wipe old codes
codes_col = db.collection("checker_codes")
for doc in codes_col.stream():
    doc.reference.delete()

# Insert 50 codes each
for typ in ["BECE", "WASSCE", "NOVDEC", "NSS"]:
    for i in range(1, 51):
        codes_col.add({
            "checker_type": typ,
            "serial":       f"{typ}-SERIAL-{i:03}",
            "pin":          f"{1000 + i}",
            "used":         False
        })
print("Seeded checker_codes!")
