from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from handlers.main_menu import build_main_menu
from utils.db import users_coll

# Conversation state for Dashboard
DASH_STATE = 1

# Dashboard button labels
DASHBOARD_OPTIONS = [
    "Purchase History",
    "Referral Program",
    "Retrieve Lost Item",
    "🏫 ScholarDeskAI",
    "Educational Resources",
    "◀ Back to Main Menu",
]
DASHBOARD_BUTTONS = [[opt] for opt in DASHBOARD_OPTIONS]


def build_dashboard_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(DASHBOARD_BUTTONS, resize_keyboard=True)


async def handle_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry into Dashboard conversation."""
    tg_user = update.effective_user
    user = await users_coll.find_one({"telegram_id": tg_user.id})
    username = user.get("username", tg_user.first_name)
    await update.message.reply_text(
        f"👤 Dashboard for {username}",
        reply_markup=build_dashboard_menu()
    )
    return DASH_STATE


async def handle_dashboard_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user’s choice inside Dashboard."""
    text = update.message.text

    if text == "◀ Back to Main Menu":
        await update.message.reply_text(
            "Returning to main menu:",
            reply_markup=build_main_menu()
        )
        return ConversationHandler.END

    responses = {
        "Purchase History": "Here is your purchase history (coming soon).",
        "Referral Program": "Your referral program details (coming soon).",
        "Retrieve Lost Item": "Retrieve lost item flow (coming soon).",
        "🏫 ScholarDeskAI": "Launching ScholarDeskAI (coming soon).",
        "Educational Resources": "Educational resources (coming soon).",
    }
    await update.message.reply_text(responses.get(text, "Unknown option."))
    # Stay in DASH_STATE until user presses Back
    return DASH_STATE
