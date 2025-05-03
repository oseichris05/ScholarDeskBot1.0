# import os
# import requests
# from utils.config import CONFIG

# # 1) Read the env‑var name for Paystack secret
# SECRET_ENV = CONFIG["paystack"]["secret_key_env_var"]
# SECRET_KEY = os.getenv(SECRET_ENV, "").strip()
# if not SECRET_KEY:
#     raise RuntimeError(
#         f"❌ Paystack secret not found. Set `{SECRET_ENV}` in your .env")

# PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"


# class PaystackError(Exception):
#     """Custom exception for Paystack errors."""
#     pass


# def initialize_payment(email: str, amount: float, reference: str):
#     """
#     Initialize a Paystack transaction.
#     - email: customer email
#     - amount: in GH¢ (converted to kobo)
#     - reference: unique per transaction
#     Returns (authorization_url, reference).
#     """
#     headers = {
#         "Authorization": f"Bearer {SECRET_KEY}",
#         "Content-Type":  "application/json",
#     }
#     payload = {
#         "email":     email,
#         "amount":    int(amount * 100),  # GH¢ → kobo
#         "reference": reference,
#     }
#     resp = requests.post(PAYSTACK_INIT_URL, json=payload,
#                          headers=headers, timeout=30)
#     data = resp.json()

#     if not resp.ok:
#         message = data.get("message", "Unknown error")
#         raise PaystackError(f"{resp.status_code} {message}")

#     auth_url = data["data"].get("authorization_url")
#     ref = data["data"].get("reference")
#     if not auth_url or not ref:
#         raise PaystackError("Invalid response from Paystack.")
#     return auth_url, ref


# utils/paystack.py

import os
import requests
from utils.config import CONFIG

SECRET_KEY = os.getenv(CONFIG["paystack"]["secret_key_env_var"], "").strip()
if not SECRET_KEY:
    raise RuntimeError("Paystack secret not set in .env")

INIT_URL = "https://api.paystack.co/transaction/initialize"
VERIFY_URL = "https://api.paystack.co/transaction/verify/{reference}"


class PaystackError(Exception):
    pass


def initialize_payment(email: str, amount: float, reference: str):
    headers = {"Authorization": f"Bearer {SECRET_KEY}",
               "Content-Type": "application/json"}
    payload = {"email": email, "amount": int(
        amount * 100), "reference": reference}
    resp = requests.post(INIT_URL, json=payload, headers=headers, timeout=30)
    data = resp.json()
    if not resp.ok:
        raise PaystackError(f"{resp.status_code} {data.get('message')}")
    d = data["data"]
    return d["authorization_url"], d["reference"]


def verify_payment(reference: str):
    headers = {"Authorization": f"Bearer {SECRET_KEY}"}
    url = VERIFY_URL.format(reference=reference)
    resp = requests.get(url, headers=headers, timeout=30)
    data = resp.json()
    if not resp.ok or data.get("data", {}).get("status") != "success":
        raise PaystackError(f"Payment not verified: {data.get('message')}")
    return True
