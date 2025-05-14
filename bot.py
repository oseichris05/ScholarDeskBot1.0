
# # bot.py

# import warnings
# warnings.filterwarnings(
#     "ignore",
#     category=UserWarning,
#     module="google.cloud.firestore_v1.base_collection",
# )



# # bot.py

# import warnings

# # ── SILENCE PTBUserWarning about per_message=False ───────────────────────────
# warnings.filterwarnings(
#     "ignore",
#     message=r"If 'per_message=False',.*",
# )

# # ── ignore Firestore library warnings too ─────────────────────────────────────
# warnings.filterwarnings(
#     "ignore",
#     category=UserWarning,
#     module="google.cloud.firestore_v1.base_collection",
# )

# import os
# import json
# from pathlib import Path
# from dotenv import load_dotenv
# from telegram import Update
# from telegram.error import TimedOut
# from telegram.ext import (
#     ApplicationBuilder,
#     CommandHandler,
#     MessageHandler,
#     CallbackQueryHandler,
#     ConversationHandler,
#     filters,
#     ContextTypes,
# )

# # Handler imports
# from handlers.help        import help_command
# from handlers.main_menu   import start, email, username, EMAIL, USERNAME, build_main_menu
# from handlers.dashboard   import handle_dashboard, handle_dashboard_choice, RETRIEVE_TID
# from handlers.buy_checker import (
#     start_buy_checker, choose_checker, enter_quantity, cancel_purchase,
#     CHOOSE_CHECKER, ENTER_QUANTITY
# )
# from handlers.buy_forms   import (
#     start_buy_forms, choose_form_category, choose_university, cancel_forms,
#     FORM_CATEGORY, CHOOSE_UNIVERSITY
# )

# # Sessions & reminder
# from utils.sessions import reminder_callback

# # Database & payment
# from utils.db       import transactions_coll, checker_codes_coll
# from utils.paystack import verify_payment

# # Load environment & config
# load_dotenv()
# CONFIG = json.loads(Path("config.json").read_text())
# TOKEN  = os.getenv(CONFIG["telegram"]["token_env_var"])
# if not TOKEN:
#     raise RuntimeError("TELEGRAM_TOKEN is not set")


# # -----------------------------------------------------------------------------
# # Auto‑deliver paid checkers
# # -----------------------------------------------------------------------------
# async def check_pending_job(context: ContextTypes.DEFAULT_TYPE):
#     for doc in transactions_coll.where("status", "==", "pending").stream():
#         txn = doc.to_dict()
#         ref, uid, qty, typ = (
#             txn["reference"],
#             txn["user_id"],
#             txn["quantity"],
#             txn["item_code"],
#         )
#         try:
#             verify_payment(ref)
#         except Exception:
#             continue
#         transactions_coll.document(ref).update({"status": "success"})
#         docs = list(
#             checker_codes_coll
#             .where("checker_type", "==", typ)
#             .where("used", "==", False)
#             .limit(qty)
#             .stream()
#         )
#         codes = []
#         for d in docs:
#             data = d.to_dict()
#             codes.append((data["serial"], data["pin"]))
#             checker_codes_coll.document(d.id).update({"used": True})
#         lines = [f"TID:{ref}"]
#         for i, (s, p) in enumerate(codes, 1):
#             lines.append(f"#{i}\n-\n{typ}\nSERIAL|PIN\n{s}|{p}")
#         lines.append("\nCheck your results here\nghana.waecdirect.org\n-")
#         await context.bot.send_message(uid, "\n".join(lines))


# # -----------------------------------------------------------------------------
# # Global error handler
# # -----------------------------------------------------------------------------
# async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
#     if isinstance(context.error, TimedOut):
#         return
#     import traceback
#     traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
#     if isinstance(update, Update) and update.effective_message:
#         await update.effective_message.reply_text(
#             "⚠️ Something went wrong. Please try again later."
#         )


# def main():
#     app = ApplicationBuilder().token(TOKEN).build()

#     # In‑memory session & reminder storage
#     app.bot_data["sessions"]      = {}  # user_id → flow_name
#     app.bot_data["reminder_jobs"] = {}  # user_id → Job

#     # Wrapped /start: clear any session + reminder
#     async def wrapped_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#         uid = update.effective_user.id
#         app.bot_data["sessions"].pop(uid, None)
#         job = app.bot_data["reminder_jobs"].pop(uid, None)
#         if job:
#             job.schedule_removal()
#         return await start(update, context)

#     # --- /start registration ---
#     reg_conv = ConversationHandler(
#         entry_points=[CommandHandler("start", wrapped_start)],
#         states={
#             EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
#             USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
#         },
#         fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
#     )
#     app.add_handler(reg_conv)

#     # --- /help ---
#     app.add_handler(CommandHandler("help", help_command))

#     # --- Dashboard ---
#     app.add_handler(CommandHandler("dashboard", handle_dashboard))
#     dash_conv = ConversationHandler(
#         entry_points=[
#             MessageHandler(filters.Regex(r"^📊 Dashboard$|^Dashboard$"), handle_dashboard)
#         ],
#         states={
#             RETRIEVE_TID: [
#                 MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dashboard_choice)
#             ]
#         },
#         fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
#     )
#     app.add_handler(dash_conv)

#     # --- Buy Checker ---
#     app.add_handler(CommandHandler("buy_checker", start_buy_checker))
#     buy_conv = ConversationHandler(
#         entry_points=[
#             MessageHandler(filters.Regex(r"^🛒 Buy Checker$|^Buy Checker$"), start_buy_checker),
#             CommandHandler("buy_checker", start_buy_checker),
#         ],
#         states={
#             CHOOSE_CHECKER: [
#                 CallbackQueryHandler(choose_checker,   pattern=r"^type:.+"),
#                 CallbackQueryHandler(cancel_purchase, pattern=r"^cancel$"),
#             ],
#             ENTER_QUANTITY: [
#                 CallbackQueryHandler(enter_quantity,   pattern=r"^qty:\d+$"),
#                 CallbackQueryHandler(cancel_purchase, pattern=r"^cancel$"),
#             ],
#         },
#         fallbacks=[CommandHandler("cancel", cancel_purchase)],
#     )
#     app.add_handler(buy_conv)

#     # --- Buy Forms ---
#     app.add_handler(CommandHandler("buy_forms", start_buy_forms))
#     forms_conv = ConversationHandler(
#         entry_points=[
#             MessageHandler(filters.Regex(r"^📝 Buy Forms$|^Buy Forms$"), start_buy_forms),
#             CommandHandler("buy_forms", start_buy_forms),
#         ],
#         states={
#             FORM_CATEGORY: [
#                 CallbackQueryHandler(choose_form_category, pattern=r"^cat:.+"),
#                 CallbackQueryHandler(cancel_forms,         pattern=r"^cancel$"),
#             ],
#             CHOOSE_UNIVERSITY: [
#                 CallbackQueryHandler(choose_university,    pattern=r"^uni:.+"),
#                 CallbackQueryHandler(cancel_forms,         pattern=r"^cancel$"),
#             ],
#         },
#         fallbacks=[CommandHandler("cancel", cancel_forms)],
#     )
#     app.add_handler(forms_conv)

#     # --- Schedule auto‑delivery every 30s ---
#     app.job_queue.run_repeating(check_pending_job, interval=30.0, first=10.0)

#     # --- Global error handler ---
#     app.add_error_handler(error_handler)

#     print("Bot is starting…")
#     app.run_polling(poll_interval=0.0)


# if __name__ == "__main__":
#     main()



# bot.py


# bot.py
import os
import json
import warnings
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# ── SILENCE irrelevant warnings ────────────────────────────────────────────────
warnings.filterwarnings("ignore", message=r"If 'per_message=False',.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud")

# ── Load environment variables ─────────────────────────────────────────────────
load_dotenv()

# ── Telegram & Paystack tokens ────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PAYSTACK_SK    = os.getenv("PAYSTACK_SECRET")
if not TELEGRAM_TOKEN or not PAYSTACK_SK:
    raise RuntimeError("Missing TELEGRAM_TOKEN or PAYSTACK_SECRET in environment")

# ── Firestore credentials JSON ─────────────────────────────────────────────────
#   Expect the raw JSON of your serviceAccountKey.json in this env var
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
if not GOOGLE_CREDS_JSON:
    raise RuntimeError("Missing GOOGLE_CREDENTIALS_JSON in environment")

# Validate and write to a temp file for the Firebase SDK
try:
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
except json.JSONDecodeError as e:
    raise RuntimeError("Invalid JSON in GOOGLE_CREDENTIALS_JSON") from e

tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
tf.write(GOOGLE_CREDS_JSON.encode())
tf.flush()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tf.name

# ── Firebase Realtime‑DB / Firestore URL ────────────────────────────────────────
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
if not FIREBASE_DB_URL:
    raise RuntimeError("Missing FIREBASE_DB_URL in environment")

# ── Static JSON config (universities, prices, etc.) ────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.json"
if not CONFIG_PATH.exists():
    raise FileNotFoundError(f"Missing config.json at {CONFIG_PATH}")
with CONFIG_PATH.open() as f:
    STATIC_CFG = json.load(f)

# ── Initialize Firebase Admin ─────────────────────────────────────────────────
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate(creds_dict)
firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

# ── Telegram imports & your handler modules ────────────────────────────────────
from telegram import Update
from telegram.error import TimedOut
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from handlers.help        import help_command
from handlers.main_menu   import start, email, username, EMAIL, USERNAME, build_main_menu
from handlers.dashboard   import handle_dashboard, handle_dashboard_choice, RETRIEVE_TID
from handlers.buy_checker import (
    start_buy_checker, choose_checker, enter_quantity, cancel_purchase,
    CHOOSE_CHECKER, ENTER_QUANTITY
)
from handlers.buy_forms   import (
    start_buy_forms, choose_form_category, choose_university, cancel_forms,
    FORM_CATEGORY, CHOOSE_UNIVERSITY
)

# … rest of your code unchanged …


# Sessions & reminder
from utils.sessions import reminder_callback

# Database & payment
from utils.db       import transactions_coll, checker_codes_coll
from utils.paystack import verify_payment

# -----------------------------------------------------------------------------
# Auto‑deliver pending checkers
# -----------------------------------------------------------------------------
async def check_pending_job(context: ContextTypes.DEFAULT_TYPE):
    for doc in transactions_coll.where("status", "==", "pending").stream():
        txn = doc.to_dict()
        ref, uid, qty, typ = (
            txn["reference"],
            txn["user_id"],
            txn["quantity"],
            txn["item_code"],
        )
        try:
            verify_payment(ref)
        except Exception:
            continue

        # Mark success and pull codes
        transactions_coll.document(ref).update({"status": "success"})
        docs = list(
            checker_codes_coll
            .where("checker_type", "==", typ)
            .where("used", "==", False)
            .limit(qty)
            .stream()
        )

        codes = []
        for d in docs:
            data = d.to_dict()
            codes.append((data["serial"], data["pin"]))
            checker_codes_coll.document(d.id).update({"used": True})

        # Build and send message
        lines = [f"TID: {ref}"]
        for i, (s, p) in enumerate(codes, 1):
            lines.append(f"#{i}\n{typ}\nSERIAL|PIN\n{s}|{p}")
        lines.append("\nCheck your results here:\nhttps://ghana.waecdirect.org\n-")
        await context.bot.send_message(uid, "\n".join(lines))


# -----------------------------------------------------------------------------
# Global error handler
# -----------------------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, TimedOut):
        return  # ignore timeouts
    import traceback
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong. Please try again later."
        )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # In‑memory session & reminder storage
    app.bot_data["sessions"]      = {}
    app.bot_data["reminder_jobs"] = {}

    # Wrapped /start to clear jobs & sessions
    async def wrapped_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        app.bot_data["sessions"].pop(uid, None)
        job = app.bot_data["reminder_jobs"].pop(uid, None)
        if job:
            job.schedule_removal()
        return await start(update, context)

    # --- Registration (ConversationHandler) ---
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", wrapped_start)],
        states={
            EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    app.add_handler(reg_conv)

    # --- /help ---
    app.add_handler(CommandHandler("help", help_command))

    # --- Dashboard ---
    app.add_handler(CommandHandler("dashboard", handle_dashboard))
    dash_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"^📊 Dashboard$|^Dashboard$"), handle_dashboard)],
        states={ RETRIEVE_TID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dashboard_choice)] },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    app.add_handler(dash_conv)

    # --- Buy Checker ---
    app.add_handler(CommandHandler("buy_checker", start_buy_checker))
    buy_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🛒 Buy Checker$|^Buy Checker$"), start_buy_checker),
            CommandHandler("buy_checker", start_buy_checker),
        ],
        states={
            CHOOSE_CHECKER: [
                CallbackQueryHandler(choose_checker,   pattern=r"^type:.+"),
                CallbackQueryHandler(cancel_purchase, pattern=r"^cancel$"),
            ],
            ENTER_QUANTITY: [
                CallbackQueryHandler(enter_quantity,   pattern=r"^qty:\d+$"),
                CallbackQueryHandler(cancel_purchase, pattern=r"^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_purchase)],
    )
    app.add_handler(buy_conv)

    # --- Buy Forms ---
    app.add_handler(CommandHandler("buy_forms", start_buy_forms))
    forms_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^📝 Buy Forms$|^Buy Forms$"), start_buy_forms),
            CommandHandler("buy_forms", start_buy_forms),
        ],
        states={
            FORM_CATEGORY: [
                CallbackQueryHandler(choose_form_category, pattern=r"^cat:.+"),
                CallbackQueryHandler(cancel_forms,         pattern=r"^cancel$"),
            ],
            CHOOSE_UNIVERSITY: [
                CallbackQueryHandler(choose_university, pattern=r"^uni:.+"),
                CallbackQueryHandler(cancel_forms,     pattern=r"^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_forms)],
    )
    app.add_handler(forms_conv)

    # --- Schedule auto‑delivery every 30s ---
    app.job_queue.run_repeating(check_pending_job, interval=30.0, first=10.0)

    # --- Global error handler ---
    app.add_error_handler(error_handler)

    print("🤖 ScholarDeskBot is starting…")
    app.run_polling(poll_interval=0.0)


if __name__ == "__main__":
    main()
