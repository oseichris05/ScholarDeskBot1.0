
import uuid
from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.db import users_coll

EMAIL, USERNAME = range(2)

MAIN_MENU_BUTTONS = [
    ["📊 Dashboard", "🛒 Buy Checker"],
    ["📃 Buy Forms", "🏆 Leaderboard"],
    ["🤝 Invite Friends", "💬 Support"],
]


def build_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(MAIN_MENU_BUTTONS, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = update.effective_user
    first = tg_user.first_name or ""
    last = tg_user.last_name or ""
    full_name = f"{first} {last}".strip()

    existing = await users_coll.find_one({"telegram_id": tg_user.id})
    if existing:
        await update.message.reply_text(
            f"👋 Welcome back, {full_name}! Here’s the main menu:",
            reply_markup=build_main_menu()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"👋 Hello, {full_name}! Welcome to ScholarDeskBot! To get started, please enter your email address:"
    )
    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["email"] = update.message.text.strip()
    await update.message.reply_text("✅ Got it! Now please enter your desired username:")
    return USERNAME


async def username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = update.message.text.strip()
    tg_user = update.effective_user
    email = context.user_data.get("email")
    referral_code = uuid.uuid4().hex[:8]

    new_user = {
        "telegram_id": tg_user.id,
        "email": email,
        "username": username,
        "referral_code": referral_code,
        "referred_by": None,
        "created_at": datetime.utcnow(),
    }
    await users_coll.insert_one(new_user)

    await update.message.reply_text(
        f"🎉 Registration complete! Your referral code is `{referral_code}`.\n"
        "Here’s the main menu:",
        reply_markup=build_main_menu()
    )
    return ConversationHandler.END
