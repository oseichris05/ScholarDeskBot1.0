import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler
from utils.sessions import reminder_callback
from utils.config   import CONFIG
from utils.db       import users_coll, checker_stock_coll, transactions_coll, checker_codes_coll
from utils.paystack import initialize_payment

CHOOSE_CHECKER, ENTER_QUANTITY = range(2)
CHECKER_PRICES = {c["code"]:c["price"] for c in CONFIG["checkers"]}

async def start_buy_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = update.effective_user.id
    app = context.application
    if app.bot_data["sessions"].get(uid):
        return await update.message.reply_text(
            "❗ Finish your current session or send /start to reset."
        )
    app.bot_data["sessions"][uid] = "buy_checker"
    job = app.job_queue.run_once(reminder_callback,600.0,
        data={"user_id":uid,"flow":"buy_checker"})
    app.bot_data["reminder_jobs"][uid] = job

    codes = list(CHECKER_PRICES.keys())
    rows = [codes[i:i+2] for i in range(0,len(codes),2)]
    kb = [[InlineKeyboardButton(c,callback_data=f"type:{c}") for c in row] for row in rows]
    kb.append([InlineKeyboardButton("❌ Cancel",callback_data="cancel")])
    await update.message.reply_text(
        "🛒 Which checker would you like?",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return CHOOSE_CHECKER

async def choose_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    if q.data=="cancel":
        return await cancel_purchase(update, context)

    typ = q.data.split(":",1)[1]
    context.user_data["checker_type"] = typ

    quantities = [1,2,5,10,50,100,500]
    rows = [quantities[i:i+3] for i in range(0,len(quantities),3)]
    kb = [[InlineKeyboardButton(str(n),callback_data=f"qty:{n}") for n in row] for row in rows]
    kb.append([InlineKeyboardButton("❌ Cancel",callback_data="cancel")])
    await q.edit_message_text(
        f"👍 You chose *{typ}*. How many?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return ENTER_QUANTITY

async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    if q.data=="cancel":
        return await cancel_purchase(update, context)

    qty = int(q.data.split(":",1)[1])
    typ = context.user_data["checker_type"]

    stock = (checker_stock_coll.document(typ).get().to_dict() or {}).get("stock",0)
    if qty>stock:
        await q.edit_message_text(
            f"⚠️ Only *{stock}* available. Send /start to retry.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    total = CHECKER_PRICES[typ]*qty
    email = users_coll.document(str(q.from_user.id)).get().to_dict().get("email","N/A")
    ref   = uuid.uuid4().hex
    pay_url,_ = initialize_payment(email,total,ref)

    transactions_coll.document(ref).set({
        "user_id":q.from_user.id,"item_code":typ,"quantity":qty,
        "amount":total,"status":"pending","reference":ref,
    })

    summary = (
        f"✨ *Order Summary* ✨\n"
        f"• Email: `{email}`\n"
        f"• Type: *{typ}* x{qty}\n"
        f"• Total: *₵{total}*\n"
        f"• TID: `{ref}`\n\nTap to pay."
    )
    kb = [[InlineKeyboardButton("💳 Pay Now",url=pay_url)]]
    await q.edit_message_text(summary,parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb))

    # clear session & reminder
    uid = q.from_user.id
    job = context.application.bot_data["reminder_jobs"].pop(uid,None)
    if job: job.schedule_removal()
    context.application.bot_data["sessions"].pop(uid,None)

    return ConversationHandler.END

async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    await q.edit_message_text("❌ Purchase cancelled. Send /start to reset.")
    uid = q.from_user.id
    job = context.application.bot_data["reminder_jobs"].pop(uid,None)
    if job: job.schedule_removal()
    context.application.bot_data["sessions"].pop(uid,None)
    return ConversationHandler.END
