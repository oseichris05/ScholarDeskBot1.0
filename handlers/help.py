# handlers/help.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

HELP_TEXT = """
<b>ScholarDeskBot Commands</b>

<code>/start</code> – Register or see main menu  
<code>/help</code>  – Show this message  
<code>/dashboard</code> – Open Dashboard  
<code>/buy_checker</code> – Purchase exam checkers  

You can also press the buttons in the menu.
"""

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML
    )
