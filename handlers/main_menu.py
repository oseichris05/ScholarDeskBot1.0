# import re
# from telegram import Update, ReplyKeyboardMarkup
# from telegram.ext import ContextTypes, ConversationHandler
# from utils.db import users_coll

# EMAIL, USERNAME = range(2)
# EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

# def build_main_menu() -> ReplyKeyboardMarkup:
#     keyboard = [
#         ["📊 Dashboard", "🛒 Buy Checker"],
#         ["📝 Buy Forms",   "🤝 Invite Friends"],
#         ["🏆 Leaderboard", "🛠 Support"],
#     ]
#     return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     tg = update.effective_user
#     # Always send a friendly welcome
#     await update.message.reply_text(
#         f"🎓 Hello <b>{tg.first_name}</b>! Welcome to ScholarDeskBot.\n"
#         "Press a button or type /help for instructions.",
#         reply_markup=build_main_menu(),
#         parse_mode="HTML"
#     )
#     # Check if already registered
#     doc = users_coll.document(str(tg.id)).get()
#     if doc.to_dict():
#         return ConversationHandler.END

#     # Otherwise, collect email
#     await update.message.reply_text("✉️ Please enter your email address:")
#     return EMAIL

# async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     text = update.message.text.strip()
#     if not EMAIL_REGEX.match(text):
#         await update.message.reply_text("⚠️ That doesn't look like a valid email. Try again:")
#         return EMAIL

#     # Uniqueness check
#     if any(True for _ in users_coll.where("email","==",text).stream()):
#         await update.message.reply_text("⚠️ That email is already registered. Enter another:")
#         return EMAIL

#     context.user_data["email"] = text
#     await update.message.reply_text("✅ Email saved! Now enter your desired username:")
#     return USERNAME

# async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     text = update.message.text.strip()
#     # Uniqueness check
#     if any(True for _ in users_coll.where("username","==",text).stream()):
#         await update.message.reply_text("⚠️ Username taken. Choose another:")
#         return USERNAME

#     tg = update.effective_user
#     record = {
#         "telegram_id":         tg.id,
#         "telegram_username":   tg.username,
#         "telegram_first_name": tg.first_name,
#         "telegram_last_name":  tg.last_name,
#         "email":               context.user_data["email"],
#         "username":            text,
#         "transactions_count":  0,
#         "referral_count":      0,
#     }
#     users_coll.document(str(tg.id)).set(record)
#     await update.message.reply_text(
#         f"🎉 Thanks, <b>{tg.first_name}</b>! You’re registered.",
#         reply_markup=build_main_menu(),
#         parse_mode="HTML"
#     )
#     return ConversationHandler.END


# handlers/main_menu.py
# handlers/main_menu.py

import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.db import users_coll

# Conversation states
EMAIL, USERNAME = range(2)

# Simple email regex
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def build_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        ["📊 Dashboard", "🛒 Buy Checker"],
        ["📝 Buy Forms",   "🤝 Invite Friends"],
        ["🏆 Leaderboard", "🛠 Support"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start: either prompt registration or show main menu."""
    tg = update.effective_user
    # Fetch existing user record
    user_doc = users_coll.document(str(tg.id)).get().to_dict() or {}

    if not user_doc.get("email"):
        # New user flow
        welcome = (
            "👋 *Welcome to ScholarDeskBot!* 👋\n\n"
            "I can help you purchase exam checkers (BECE, WASSCE, Nov/Dec, NSS) "
            "and application forms easily.\n\n"
            "To get started, please register by sending me your email address:"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")
        return EMAIL

    # Returning user
    first_name = user_doc.get("telegram_first_name", tg.first_name)
    await update.message.reply_text(
        f"🎉 Welcome back, *{first_name}*!",
        reply_markup=build_main_menu(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate email and prompt for username."""
    text = update.message.text.strip()
    if not EMAIL_REGEX.match(text):
        await update.message.reply_text("⚠️ That doesn’t look like a valid email. Please try again:")
        return EMAIL

    # Ensure email uniqueness
    existing = users_coll.where(field_path="email", op_string="==", value=text).stream()
    if any(True for _ in existing):
        await update.message.reply_text("⚠️ This email is already registered. Enter a different one:")
        return EMAIL

    context.user_data["email"] = text
    await update.message.reply_text("✅ Great! Now, please choose a username:")
    return USERNAME

async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate username and complete registration."""
    text = update.message.text.strip()

    # Ensure username uniqueness
    existing = users_coll.where(field_path="username", op_string="==", value=text).stream()
    if any(True for _ in existing):
        await update.message.reply_text("⚠️ That username is already taken. Try another:")
        return USERNAME

    tg = update.effective_user
    # Build full user record
    record = {
        "telegram_id":         tg.id,
        "telegram_username":   tg.username,
        "telegram_first_name": tg.first_name,
        "telegram_last_name":  tg.last_name,
        "email":               context.user_data["email"],
        "username":            text,
        "transactions_count":  0,
        "referral_count":      0,
    }
    users_coll.document(str(tg.id)).set(record)

    await update.message.reply_text(
        f"✅ Thanks, *{tg.first_name}*! You’re all set up.",
        reply_markup=build_main_menu(),
        parse_mode="Markdown"
    )
    return ConversationHandler.END
