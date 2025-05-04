import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler
from utils.sessions import reminder_callback
from utils.config   import CONFIG
from utils.db       import users_coll, transactions_coll
from utils.paystack import initialize_payment

FORM_CATEGORY, CHOOSE_UNIVERSITY = range(2)

async def start_buy_forms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    app = context.application
    if app.bot_data["sessions"].get(uid):
        return await update.message.reply_text(
            "❗ Finish your current session or send /start to reset."
        )
    app.bot_data["sessions"][uid] = "buy_forms"
    job = app.job_queue.run_once(reminder_callback,600.0,
        data={"user_id":uid,"flow":"buy_forms"})
    app.bot_data["reminder_jobs"][uid] = job

    kb = [
        [InlineKeyboardButton("🏛 University Forms", callback_data="cat:university")],
        [InlineKeyboardButton("🎓 College Forms",    callback_data="cat:college")],
        [InlineKeyboardButton("🩺 Nursing Forms",    callback_data="cat:nursing")],
        [InlineKeyboardButton("❌ Cancel",           callback_data="cancel")],
    ]
    await update.message.reply_text(
        "📝 Which form category?",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return FORM_CATEGORY

async def choose_form_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    if q.data=="cancel":
        return await cancel_forms(update,context)
    cat = q.data.split(":",1)[1]
    context.user_data["form_category"] = cat
    if cat=="university":
        unis = CONFIG["forms"]["university"]
        kb = [[InlineKeyboardButton(u["name"],callback_data=f"uni:{u['code']}")] for u in unis]
        kb.append([InlineKeyboardButton("❌ Cancel",callback_data="cancel")])
        await q.edit_message_text("Select a university:",reply_markup=InlineKeyboardMarkup(kb))
        return CHOOSE_UNIVERSITY
    price = CONFIG["forms"][cat]["default_price"]
    return await _confirm_form(q,context,cat,price)

async def choose_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    if q.data=="cancel":
        return await cancel_forms(update,context)
    code = q.data.split(":",1)[1]
    uni = next((u for u in CONFIG["forms"]["university"] if u["code"]==code),None)
    if not uni:
        await q.edit_message_text("⚠️ Invalid choice.")
        return ConversationHandler.END
    return await _confirm_form(q,context,code,uni["price"])

async def _confirm_form(q: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, form_type: str, price: int) -> int:
    await q.answer()
    uid = q.from_user.id
    email = users_coll.document(str(uid)).get().to_dict().get("email","N/A")
    ref, pay_url = uuid.uuid4().hex, initialize_payment(email,price,uuid.uuid4().hex)[0]
    transactions_coll.document(ref).set({
        "user_id":uid,"item_code":form_type,"quantity":1,
        "amount":price,"status":"pending","reference":ref,"is_form":True
    })
    summary = (
        f"✨ *Form Summary* ✨\n"
        f"• Email: `{email}`\n"
        f"• Form: *{form_type}*\n"
        f"• Price: *₵{price}*\n"
        f"• TID: `{ref}`\n\nTap to pay."
    )
    kb = [[InlineKeyboardButton("💳 Pay Now",url=pay_url)]]
    await q.edit_message_text(summary,parse_mode="Markdown",reply_markup=InlineKeyboardMarkup(kb))

    # clear session & reminder
    job = context.application.bot_data["reminder_jobs"].pop(uid,None)
    if job: job.schedule_removal()
    context.application.bot_data["sessions"].pop(uid,None)
    return ConversationHandler.END

async def cancel_forms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query if hasattr(update,"callback_query") else None  # type: ignore
    if q:
        await q.answer()
        await q.edit_message_text("❌ Purchase cancelled. Send /start to reset.")
        uid = q.from_user.id
    else:
        await update.message.reply_text("❌ Purchase cancelled. Send /start to reset.")
        uid = update.effective_user.id
    job = context.application.bot_data["reminder_jobs"].pop(uid,None)
    if job: job.schedule_removal()
    context.application.bot_data["sessions"].pop(uid,None)
    return ConversationHandler.END
