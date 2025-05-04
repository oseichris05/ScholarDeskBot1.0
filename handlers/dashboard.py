from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from utils.sessions import reminder_callback
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
    return ReplyKeyboardMarkup([[o] for o in DASHBOARD_OPTIONS], resize_keyboard=True)

async def handle_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    app = context.application
    if app.bot_data["sessions"].get(uid):
        return await update.message.reply_text(
            "❗ You have an active session. Send /start to reset."
        )
    # start session + schedule reminder
    app.bot_data["sessions"][uid] = "dashboard"
    job = app.job_queue.run_once(reminder_callback, 600.0,
        data={"user_id":uid,"flow":"dashboard"})
    app.bot_data["reminder_jobs"][uid] = job

    doc = users_coll.document(str(uid)).get().to_dict() or {}
    name = doc.get("telegram_first_name", update.effective_user.first_name)
    await update.message.reply_text(
        f"🗂 Hello *{name}*! Choose an option:",
        reply_markup=build_dashboard_menu(),
        parse_mode="Markdown"
    )
    return RETRIEVE_TID

async def handle_dashboard_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    uid  = update.effective_user.id
    # clear session + reminder
    job = context.application.bot_data["reminder_jobs"].pop(uid, None)
    if job:
        job.schedule_removal()
    context.application.bot_data["sessions"].pop(uid, None)

    if text == "Back to Main Menu":
        from handlers.main_menu import build_main_menu
        await update.message.reply_text("🔙 Back to main menu",
            reply_markup=build_main_menu())
        return ConversationHandler.END

    # ... (rest of your choice handling, unchanged) ...

    return RETRIEVE_TID
