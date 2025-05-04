# utils/sessions.py

from telegram.ext import ContextTypes

async def reminder_callback(context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a friendly nudge if a user abandons a session for >10 minutes.
    Expects job.data = {"user_id": <int>, "flow": <str>}.
    """
    data    = context.job.data
    user_id = data["user_id"]
    flow    = data["flow"]
    # only remind if session still active
    if context.application.bot_data["sessions"].get(user_id) == flow:
        friendly_map = {
            "buy_checker": "Buy Checker",
            "buy_forms":   "Buy Forms",
            "dashboard":   "Dashboard",
        }
        friendly = friendly_map.get(flow, flow)
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"👋 You started a *{friendly}* session but didn’t finish.\n"
                f"Use /start then tap *{friendly}* to continue."
            ),
            parse_mode="Markdown",
        )
