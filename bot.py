# import warnings
# warnings.filterwarnings(
#     "ignore",
#     category=UserWarning,
#     module="google.cloud.firestore_v1.base_collection",
# )

# import os
# import json
# from pathlib import Path
# from dotenv import load_dotenv
# from telegram.ext import (
#     ApplicationBuilder,
#     CommandHandler,
#     MessageHandler,
#     CallbackQueryHandler,
#     ConversationHandler,
#     filters,
#     ContextTypes,
# )
# from handlers.help        import help_command
# from handlers.main_menu   import start, email, username, EMAIL, USERNAME, build_main_menu
# from handlers.dashboard   import handle_dashboard, handle_dashboard_choice, RETRIEVE_TID
# from handlers.buy_checker import start_buy_checker, choose_checker, enter_quantity, CHOOSE_CHECKER, ENTER_QUANTITY
# from utils.db             import transactions_coll, checker_codes_coll
# from utils.paystack       import verify_payment

# # Load environment
# load_dotenv()
# CONFIG = json.loads(Path("config.json").read_text())
# TOKEN  = os.getenv(CONFIG["telegram"]["token_env_var"])
# if not TOKEN:
#     raise RuntimeError("TELEGRAM_TOKEN is not set")

# # Background job callback to auto‑deliver paid checkers
# async def check_pending_job(context: ContextTypes.DEFAULT_TYPE):
#     # Run this every 30s
#     for doc in transactions_coll.where("status", "==", "pending").stream():
#         txn = doc.to_dict()
#         ref = txn["reference"]
#         try:
#             verify_payment(ref)
#         except Exception:
#             continue  # still unpaid
#         # Mark success
#         transactions_coll.document(ref).update({"status": "success"})
#         # Assign codes
#         qty = txn["quantity"]
#         typ = txn["item_code"]
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

#         # Send to user
#         lines = [f"TID:{ref}"]
#         for i, (s, p) in enumerate(codes, start=1):
#             lines.append(f"#{i}\n{s}|{p}")
#         lines.append("Check your results here\nghana.waecdirect.org")
#         await context.bot.send_message(txn["user_id"], "\n".join(lines))

# def main():
#     app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

#     # Registration (/start)
#     reg_conv = ConversationHandler(
#         entry_points=[CommandHandler("start", start)],
#         states={
#             EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
#             USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
#         },
#         fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
#     )
#     app.add_handler(reg_conv)

#     # /help
#     app.add_handler(CommandHandler("help", help_command))

#     # Dashboard (command + button)
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

#     # Buy Checker (command + button)
#     app.add_handler(CommandHandler("buy_checker", start_buy_checker))
#     buy_conv = ConversationHandler(
#         entry_points=[
#             MessageHandler(filters.Regex(r"^🛒 Buy Checker$|^Buy Checker$"), start_buy_checker)
#         ],
#         states={
#             CHOOSE_CHECKER:  [CallbackQueryHandler(choose_checker, pattern=r"^type:.+")],
#             ENTER_QUANTITY: [CallbackQueryHandler(enter_quantity, pattern=r"^qty:\d+$")],
#         },
#         fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
#     )
#     app.add_handler(buy_conv)

#     # Schedule the pending‑check job every 30 seconds
#     # use the built‑in JobQueue rather than APScheduler
#     jq = app.job_queue
#     jq.run_repeating(check_pending_job, interval=30.0, first=15.0)

#     print("Bot is starting…")
#     app.run_polling(poll_interval=0.0)

# if __name__ == "__main__":
#     main()


# bot.py



# bot.py


# bot.py



# bot.py

import warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="google.cloud.firestore_v1.base_collection",
)

import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
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

# Handler imports
from handlers.help import help_command
from handlers.main_menu import start, email, username, EMAIL, USERNAME, build_main_menu
from handlers.dashboard import (
    handle_dashboard,
    handle_dashboard_choice,
    RETRIEVE_TID,
)
from handlers.buy_checker import (
    start_buy_checker,
    choose_checker,
    enter_quantity,
    cancel_purchase,
    CHOOSE_CHECKER,
    ENTER_QUANTITY,
)

# Database & payment utils
from utils.db import transactions_coll, checker_codes_coll
from utils.paystack import verify_payment

# Load environment and config
load_dotenv()
CONFIG = json.loads(Path("config.json").read_text())
TOKEN = os.getenv(CONFIG["telegram"]["token_env_var"])
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")


# Background job: auto‑deliver paid checkers
async def check_pending_job(context: ContextTypes.DEFAULT_TYPE):
    for doc in transactions_coll.where(
        field_path="status", op_string="==", value="pending"
    ).stream():
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
        # Mark success
        transactions_coll.document(ref).update({"status": "success"})
        # Allocate codes
        docs = list(
            checker_codes_coll
            .where(field_path="checker_type", op_string="==", value=typ)
            .where(field_path="used", op_string="==", value=False)
            .limit(qty)
            .stream()
        )
        codes = []
        for d in docs:
            data = d.to_dict()
            codes.append((data["serial"], data["pin"]))
            checker_codes_coll.document(d.id).update({"used": True})

        # Send delivery message
        lines = [f"TID:{ref}"]
        for i, (s, p) in enumerate(codes, start=1):
            lines.append(f"#{i}\n-\n{typ}\nSERIAL|PIN\n{s}|{p}")
        lines.append("\nCheck your results here\nghana.waecdirect.org\n-")
        await context.bot.send_message(uid, "\n".join(lines))


# Global error handler (keeps the bot alive)
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, TimedOut):
        return
    import traceback
    traceback.print_exception(
        type(context.error), context.error, context.error.__traceback__
    )
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Sorry, something went wrong. Please try again later."
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # --- Registration (/start) ---
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    app.add_handler(reg_conv)

    # --- Help (/help) ---
    app.add_handler(CommandHandler("help", help_command))

    # --- Dashboard (button + /dashboard) ---
    app.add_handler(CommandHandler("dashboard", handle_dashboard))
    dash_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^📊 Dashboard$|^Dashboard$"), handle_dashboard)
        ],
        states={
            RETRIEVE_TID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dashboard_choice)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
            MessageHandler(filters.Regex(r"^Back to Main Menu$"), lambda u, c: ConversationHandler.END),
        ],
    )
    app.add_handler(dash_conv)

    # --- Buy Checker (button + /buy_checker) ---
    app.add_handler(CommandHandler("buy_checker", start_buy_checker))
    buy_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🛒 Buy Checker$|^Buy Checker$"), start_buy_checker),
            CommandHandler("buy_checker", start_buy_checker),
        ],
        states={
            CHOOSE_CHECKER: [
                CallbackQueryHandler(choose_checker, pattern=r"^type:.+"),
                CallbackQueryHandler(cancel_purchase, pattern=r"^cancel$"),
            ],
            ENTER_QUANTITY: [
                CallbackQueryHandler(enter_quantity, pattern=r"^qty:\d+$"),
                CallbackQueryHandler(cancel_purchase, pattern=r"^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_purchase)],
    )
    app.add_handler(buy_conv)

    # --- Schedule auto‑delivery every 30 seconds ---
    jq = app.job_queue
    jq.run_repeating(check_pending_job, interval=30.0, first=10.0)

    # --- Global error handler ---
    app.add_error_handler(error_handler)

    print("Bot is starting…")
    app.run_polling(poll_interval=0.0)


if __name__ == "__main__":
    main()
