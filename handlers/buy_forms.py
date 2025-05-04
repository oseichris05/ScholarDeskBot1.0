# handlers/buy_forms.py

import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler
from utils.config import CONFIG
from utils.db import users_coll, transactions_coll
from utils.paystack import initialize_payment

# States
FORM_CATEGORY, CHOOSE_UNIVERSITY = range(2)

async def start_buy_forms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    kb = [
        [InlineKeyboardButton("🏛 University Forms", callback_data="cat:university")],
        [InlineKeyboardButton("🎓 College Forms",    callback_data="cat:college")],
        [InlineKeyboardButton("🩺 Nursing Forms",    callback_data="cat:nursing")],
        [InlineKeyboardButton("❌ Cancel",           callback_data="cancel")],
    ]
    await update.message.reply_text(
        "📝 Which type of form would you like to buy?",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return FORM_CATEGORY

async def choose_form_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    if q.data == "cancel":
        return await cancel_forms(q, context)

    _, cat = q.data.split(":", 1)
    context.user_data["form_category"] = cat

    if cat == "university":
        # Show list of universities
        unis = CONFIG["forms"]["university"]
        kb = [
            [InlineKeyboardButton(u["name"], callback_data=f"uni:{u['code']}")]
            for u in unis
        ]
        kb.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        await q.edit_message_text(
            "Select a university:",
            reply_markup=InlineKeyboardMarkup(kb),
        )
        return CHOOSE_UNIVERSITY

    # college or nursing: price from config
    key = "college" if cat == "college" else "nursing"
    price = CONFIG["forms"][key]["default_price"]
    return await _confirm_form(q, context, cat, price)

async def choose_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q: CallbackQuery = update.callback_query  # type: ignore
    await q.answer()
    if q.data == "cancel":
        return await cancel_forms(q, context)

    _, code = q.data.split(":", 1)
    # find university entry
    uni = next(
        (u for u in CONFIG["forms"]["university"] if u["code"] == code),
        None
    )
    if not uni:
        await q.edit_message_text("⚠️ Selection invalid.")
        return ConversationHandler.END

    return await _confirm_form(q, context, code, uni["price"])

async def _confirm_form(
    q: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    form_type: str,
    price: int
) -> int:
    """Build summary, init Paystack, record transaction."""
    await q.answer()
    uid = q.from_user.id
    user = users_coll.document(str(uid)).get().to_dict() or {}
    email = user.get("email", "N/A")

    ref, amount = uuid.uuid4().hex, price
    pay_url, _ = initialize_payment(email, amount, ref)

    transactions_coll.document(ref).set({
        "user_id":    uid,
        "item_code":  form_type,
        "quantity":   1,
        "amount":     amount,
        "status":     "pending",
        "reference":  ref,
        "is_form":    True,
    })

    summary = (
        f"✨ *Form Order Summary* ✨\n"
        f"• Email: `{email}`\n"
        f"• User: {q.from_user.full_name}\n"
        f"• Form: *{form_type}*\n"
        f"• Price: *₵{amount}*\n"
        f"• TID: `{ref}`\n\n"
        "Tap below to pay now."
    )
    kb = [[InlineKeyboardButton("💳 Pay Now", url=pay_url)]]
    await q.edit_message_text(
        summary,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return ConversationHandler.END

async def cancel_forms(
    update_or_q: Update | CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Cancel and end conversation."""
    if hasattr(update_or_q, "callback_query"):
        q: CallbackQuery = update_or_q.callback_query  # type: ignore
        await q.answer()
        await q.edit_message_text(
            "❌ Purchase cancelled. Use /start to see the main menu again."
        )
    else:
        await update_or_q.message.reply_text(
            "❌ Purchase cancelled. Use /start to see the main menu again."
        )
    return ConversationHandler.END
