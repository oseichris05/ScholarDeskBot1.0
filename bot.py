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
# )
# from handlers import main_menu, dashboard, buy_checker

# # Load environment and config
# load_dotenv()
# CONFIG = json.loads(Path("config.json").read_text())

# TOKEN = os.getenv(CONFIG["telegram"]["token_env_var"])
# if not TOKEN:
#     raise RuntimeError("TELEGRAM_TOKEN not set in environment")

# def main() -> None:
#     # Build application
#     app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

#     # --- Registration Flow ---
#     reg_conv = ConversationHandler(
#         entry_points=[CommandHandler("start", main_menu.start)],
#         states={
#             main_menu.EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu.email)],
#             main_menu.USERNAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu.username)],
#         },
#         fallbacks=[],
#     )
#     app.add_handler(reg_conv)

#     # --- Buy Checker Flow ---
#     # Now matches ANY message containing "Buy Checker" (with or without the 🛒)
#     buy_conv = ConversationHandler(
#         entry_points=[MessageHandler(filters.Regex(r"Buy Checker"), buy_checker.start_buy_checker)],
#         states={
#             buy_checker.CHOOSE_CHECKER: [
#                 CallbackQueryHandler(buy_checker.choose_checker, pattern=r"^(?:type:|cancel)$")
#             ],
#             buy_checker.ENTER_QUANTITY:[ 
#                 CallbackQueryHandler(buy_checker.enter_quantity, pattern=r"^(?:qty:|cancel)$")
#             ],
#             buy_checker.VERIFY_PAYMENT:[
#                 CallbackQueryHandler(buy_checker.verify_purchase, pattern=r"^verify:")
#             ],
#         },
#         fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancel$")],
#     )
#     app.add_handler(buy_conv)

#     # --- Dashboard Flow ---
#     # Matches "Dashboard" or "📊 Dashboard"
#     app.add_handler(
#         MessageHandler(filters.Regex(r"Dashboard"), dashboard.handle_dashboard)
#     )
#     dash_pattern = "^(" + "|".join(dashboard.DASHBOARD_OPTIONS) + ")$"
#     app.add_handler(
#         MessageHandler(filters.Regex(dash_pattern), dashboard.handle_dashboard_choice)
#     )

#     # --- Start Polling ---
#     print("Bot is starting…")
#     app.run_polling(poll_interval=1.0)

# if __name__ == "__main__":
#     main()


# bot.py

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from handlers import main_menu, dashboard, buy_checker

# Load .env and config
load_dotenv()
CONFIG = json.loads(Path("config.json").read_text())

TOKEN = os.getenv(CONFIG["telegram"]["token_env_var"])
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN not set")

def main() -> None:
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

    # Registration
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("start", main_menu.start)],
        states={
            main_menu.EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu.email)],
            main_menu.USERNAME:[MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu.username)],
        },
        fallbacks=[],
    )
    app.add_handler(reg_conv)

    # Buy Checker
    buy_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r"Buy Checker"), buy_checker.start_buy_checker)],
        states={
            buy_checker.CHOOSE_CHECKER: [CallbackQueryHandler(buy_checker.choose_checker,   pattern=r"^type:.+")],
            buy_checker.ENTER_QUANTITY:[CallbackQueryHandler(buy_checker.enter_quantity, pattern=r"^qty:\d+$")],
            buy_checker.VERIFY_PAYMENT: [CallbackQueryHandler(buy_checker.verify_purchase, pattern=r"^verify:.+")],
        },
        fallbacks=[CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancel$")],
    )
    app.add_handler(buy_conv)

    # Dashboard
    app.add_handler(MessageHandler(filters.Regex(r"Dashboard"), dashboard.handle_dashboard))
    dash_pattern = "^(" + "|".join(dashboard.DASHBOARD_OPTIONS) + ")$"
    app.add_handler(MessageHandler(filters.Regex(dash_pattern), dashboard.handle_dashboard_choice))

    print("Bot is starting…")
    app.run_polling(poll_interval=0.0)

if __name__ == "__main__":
    main()
