# import uuid
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
# from telegram.ext import ContextTypes, ConversationHandler
# from utils.config import CONFIG
# from utils.db import (
#     users_coll,
#     checker_stock_coll,
#     transactions_coll,
#     checker_codes_coll,
# )
# from utils.paystack import initialize_payment, verify_payment, PaystackError

# CHOOSE_CHECKER, ENTER_QUANTITY, _ = range(3)

# CHECKER_PRICES = {c["code"]: c["price"] for c in CONFIG["checkers"]}

# async def start_buy_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     codes = list(CHECKER_PRICES.keys())
#     rows = [codes[i:i+2] for i in range(0,len(codes),2)]
#     kb = [[
#         InlineKeyboardButton(code, callback_data=f"type:{code}") for code in row
#     ] for row in rows]
#     kb.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
#     await update.message.reply_text("🛒 Which checker?", reply_markup=InlineKeyboardMarkup(kb))
#     return CHOOSE_CHECKER

# async def choose_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     q = update.callback_query; await q.answer()
#     if q.data=="cancel":
#         await q.edit_message_text("❌ Cancelled"); return ConversationHandler.END
#     _, typ = q.data.split(":",1)
#     context.user_data["checker_type"] = typ

#     qtys = [1,2,5,10,50,100,500]
#     rows=[qtys[i:i+3] for i in range(0,len(qtys),3)]
#     kb = [[InlineKeyboardButton(str(n), callback_data=f"qty:{n}") for n in row] for row in rows]
#     kb.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
#     await q.edit_message_text(f"✏️ How many *{typ}*?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
#     return ENTER_QUANTITY

# async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     q = update.callback_query; await q.answer()
#     if q.data=="cancel":
#         await q.edit_message_text("❌ Cancelled"); return ConversationHandler.END
#     _, qty_s = q.data.split(":",1)
#     quantity = int(qty_s)
#     typ      = context.user_data["checker_type"]

#     stock_doc = checker_stock_coll.document(typ).get()
#     available = (stock_doc.to_dict() or {}).get("stock",0)
#     if quantity>available:
#         await q.edit_message_text(
#             f"⚠️ You requested {quantity} but only {available} in stock. Choose less.",
#             parse_mode="Markdown"
#         )
#         return ConversationHandler.END

#     total = CHECKER_PRICES[typ]*quantity
#     user_doc = users_coll.document(str(q.from_user.id)).get().to_dict() or {}
#     email    = user_doc.get("email","N/A")

#     ref       = uuid.uuid4().hex
#     pay_url,_ = initialize_payment(email,total,ref)

#     transactions_coll.document(ref).set({
#         "user_id":   q.from_user.id,
#         "item_code": typ,
#         "quantity":  quantity,
#         "amount":    total,
#         "status":    "pending",
#         "reference": ref,
#     })

#     await q.edit_message_text(
#         f"TID:{ref}\nQty:{quantity}\nType:{typ}\n\n💳 Tap *Pay Now* above to pay.",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Now", url=pay_url)]])
#     )
#     return ConversationHandler.END


# handlers/buy_checker.py




# handlers/buy_checker.py
# handlers/buy_checker.py
# handlers/buy_checker.py

import uuid
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler
from utils.config import CONFIG
from utils.db import (
    users_coll,
    checker_stock_coll,
    transactions_coll,
    checker_codes_coll,
)
from utils.paystack import initialize_payment

# States
CHOOSE_CHECKER, ENTER_QUANTITY = range(2)

# Load checker prices from config
CHECKER_PRICES = {c["code"]: c["price"] for c in CONFIG["checkers"]}


async def start_buy_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Prompt for checker type
    codes = list(CHECKER_PRICES.keys())
    rows = [codes[i : i + 2] for i in range(0, len(codes), 2)]
    kb = [
        [InlineKeyboardButton(code, callback_data=f"type:{code}") for code in row]
        for row in rows
    ]
    kb.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    await update.message.reply_text(
        "🛒 Which checker would you like to purchase?",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return CHOOSE_CHECKER


async def choose_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    if q.data == "cancel":
        return await cancel_purchase(update, context)

    _, checker_type = q.data.split(":", 1)
    context.user_data["checker_type"] = checker_type

    # Prompt for quantity inline
    quantities = [1, 2, 5, 10, 50, 100, 500]
    rows = [quantities[i : i + 3] for i in range(0, len(quantities), 3)]
    kb = [
        [InlineKeyboardButton(str(n), callback_data=f"qty:{n}") for n in row]
        for row in rows
    ]
    kb.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    await q.edit_message_text(
        f"👍 You chose *{checker_type}*. How many would you like?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )
    return ENTER_QUANTITY


async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()

    if q.data == "cancel":
        return await cancel_purchase(update, context)

    _, qty_str = q.data.split(":", 1)
    quantity = int(qty_str)
    checker_type = context.user_data["checker_type"]

    # Check stock
    stock_doc = checker_stock_coll.document(checker_type).get()
    available = (stock_doc.to_dict() or {}).get("stock", 0)
    if quantity > available:
        await q.edit_message_text(
            f"⚠️ You requested *{quantity}* but only *{available}* available.\n"
            "Please choose a smaller quantity.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # Calculate price
    unit_price = CHECKER_PRICES[checker_type]
    total = unit_price * quantity

    # Fetch user email
    user_doc = users_coll.document(str(q.from_user.id)).get()
    email = (user_doc.to_dict() or {}).get("email", "N/A")

    # Initialize Paystack
    ref = uuid.uuid4().hex
    pay_url, _ = initialize_payment(email, total, ref)

    # Record transaction
    transactions_coll.document(ref).set(
        {
            "user_id":   q.from_user.id,
            "item_code": checker_type,
            "quantity":  quantity,
            "amount":    total,
            "status":    "pending",
            "reference": ref,
        }
    )

    # Build summary
    summary = (
        f"✨ *Order Summary* ✨\n"
        f"• Email: `{email}`\n"
        f"• User: {q.from_user.full_name}\n"
        f"• Type: *{checker_type}* x{quantity}\n"
        f"• Total: *₵{total}*\n"
        f"• TID: `{ref}`\n\n"
        "Tap below to pay:"
    )
    pay_button = InlineKeyboardButton("💳 Pay Now", url=pay_url)
    await q.edit_message_text(
        summary,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[pay_button]]),
    )

    return ConversationHandler.END


async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Unified cancel handler for both callback-query and message contexts.
    """
    if update.callback_query:
        q = update.callback_query
        await q.answer()
        # Edit the original message to indicate cancellation
        await q.edit_message_text(
            "❌ Purchase cancelled.\nUse /start to see the main menu again."
        )
    else:
        # Fallback if called via a text command
        await update.message.reply_text(
            "❌ Purchase cancelled.\nUse /start to see the main menu again."
        )
    return ConversationHandler.END
