# from telegram import Update, ReplyKeyboardMarkup
# from telegram.ext import (
#     ContextTypes,
#     ConversationHandler,
#     MessageHandler,
#     filters,
# )
# from utils.db import users_coll, transactions_coll

# RETRIEVE_TID = 1

# DASHBOARD_OPTIONS = [
#     "Purchases History",
#     "Referral Program",
#     "Retrieve Checker",
#     "Back to Main Menu",
# ]

# def build_dashboard_menu() -> ReplyKeyboardMarkup:
#     return ReplyKeyboardMarkup([[opt] for opt in DASHBOARD_OPTIONS], resize_keyboard=True)

# async def handle_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     tg   = update.effective_user
#     doc  = users_coll.document(str(tg.id)).get()
#     data = doc.to_dict() or {}
#     name = data.get("telegram_first_name", tg.first_name)
#     await update.message.reply_text(
#         f"Hello <b>{name}</b>! What would you like to do?",
#         reply_markup=build_dashboard_menu(),
#         parse_mode="HTML"
#     )
#     return RETRIEVE_TID

# async def handle_dashboard_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     choice = update.message.text
#     uid    = update.effective_user.id

#     if choice == "Purchases History":
#         txns = transactions_coll.where(
#             field_path="user_id", op_string="==", value=uid
#         ).stream()
#         recs = [d.to_dict() for d in txns]
#         if not recs:
#             await update.message.reply_text("You have no purchase history.")
#         else:
#             lines = ["🛒 <b>Your Purchases:</b>"]
#             for t in recs:
#                 lines.append(
#                     f"TID:{t['reference']} – {t['item_code']} x{t['quantity']} ({t['status']})"
#                 )
#             await update.message.reply_text("\n".join(lines), parse_mode="HTML")
#         return RETRIEVE_TID

#     if choice == "Referral Program":
#         await update.message.reply_text("🤝 Referral program: coming soon!")
#         return RETRIEVE_TID

#     if choice == "Retrieve Checker":
#         await update.message.reply_text("🔍 Please enter your TID to retrieve your codes:")
#         return RETRIEVE_TID

#     if choice == "Back to Main Menu":
#         from handlers.main_menu import build_main_menu
#         await update.message.reply_text(
#             "🔙 Back to main menu:", reply_markup=build_main_menu()
#         )
#         return ConversationHandler.END

#     # Otherwise, treat input as TID
#     tid = choice.strip()
#     doc = transactions_coll.document(tid).get().to_dict() or {}
#     codes = doc.get("codes_assigned", [])
#     if not codes:
#         await update.message.reply_text("❌ No codes found for that TID.")
#     else:
#         lines = [f"TID:{tid}"]
#         for i, entry in enumerate(codes, start=1):
#             serial = entry.get("serial")
#             pin    = entry.get("pin")
#             lines.append(f"#{i}\n{serial}|{pin}")
#         await update.message.reply_text("\n".join(lines))
#     from handlers.main_menu import build_main_menu
#     await update.message.reply_text(
#         "🔙 Main menu:", reply_markup=build_main_menu()
#     )
#     return ConversationHandler.END


# handlers/dashboard.py

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils.db import users_coll, transactions_coll

RETRIEVE_TID = 1

DASHBOARD_OPTIONS = [
    "Purchases History",
    "Referral Program",
    "Retrieve Checker",
    "Educational Resources",
    "ScholarDeskAI",
    "Back to Main Menu",
]

def build_dashboard_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[opt] for opt in DASHBOARD_OPTIONS], resize_keyboard=True)

async def handle_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg   = update.effective_user
    doc  = users_coll.document(str(tg.id)).get()
    name = (doc.to_dict() or {}).get("telegram_first_name", tg.first_name)
    await update.message.reply_text(
        f"🗂 Hey <b>{name}</b>, what would you like to do?",
        reply_markup=build_dashboard_menu(),
        parse_mode="HTML"
    )
    return RETRIEVE_TID

async def handle_dashboard_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    uid    = update.effective_user.id

    if choice == "Purchases History":
        txns = transactions_coll.where(field_path="user_id", op_string="==", value=uid).stream()
        recs = [d.to_dict() for d in txns]
        if not recs:
            await update.message.reply_text("You haven’t made any purchases yet.")
        else:
            lines = ["🛒 <b>Your Purchase History:</b>"]
            for t in recs:
                lines.append(
                    f"TID:{t['reference']} – {t['item_code']} x{t['quantity']} ({t['status']})"
                )
            await update.message.reply_text("\n".join(lines), parse_mode="HTML")
        return RETRIEVE_TID

    if choice == "Referral Program":
        await update.message.reply_text("🤝 Invite friends and earn points! (Coming soon)")
        return RETRIEVE_TID

    if choice == "Retrieve Checker":
        await update.message.reply_text("🔍 Please send me your TID to retrieve codes:")
        return RETRIEVE_TID

    if choice == "Educational Resources":
        await update.message.reply_text(
            "📚 Access resources here: https://scholardesk.example.com/resources"
        )
        return RETRIEVE_TID

    if choice == "ScholarDeskAI":
        await update.message.reply_text("🤖 Ask me anything! Just type your question.")
        return RETRIEVE_TID

    if choice == "Back to Main Menu":
        from handlers.main_menu import build_main_menu
        await update.message.reply_text(
            "🔙 Returning to main menu...",
            reply_markup=build_main_menu()
        )
        return ConversationHandler.END

    # Otherwise treat as TID lookup
    tid  = choice.strip()
    doc  = transactions_coll.document(tid).get().to_dict() or {}
    codes= doc.get("codes_assigned", [])
    if not codes:
        await update.message.reply_text("❌ No codes found for that TID.")
    else:
        lines = [f"TID:{tid}"]
        for i, entry in enumerate(codes, start=1):
            lines.append(f"#{i}\n{entry['serial']}|{entry['pin']}")
        lines.append("\nReturn anytime with /dashboard")
        await update.message.reply_text("\n".join(lines))
    from handlers.main_menu import build_main_menu
    await update.message.reply_text(
        "🔙 Back to main menu", reply_markup=build_main_menu()
    )
    return ConversationHandler.END
