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

# # Conversation states
# CHOOSE_CHECKER, ENTER_QUANTITY, VERIFY_PAYMENT = range(3)

# # Load prices from config.json
# CHECKER_PRICES = {c["code"]: c["price"] for c in CONFIG["checkers"]}


# async def start_buy_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Step 1: Ask which checker type."""
#     codes = list(CHECKER_PRICES.keys())
#     rows = [codes[i : i + 2] for i in range(0, len(codes), 2)]
#     keyboard = [
#         [InlineKeyboardButton(code, callback_data=f"type:{code}") for code in row]
#         for row in rows
#     ]
#     keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

#     await update.message.reply_text(
#         "🛒 Which checker would you like to purchase?",
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )
#     return CHOOSE_CHECKER


# async def choose_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Step 2: Ask for quantity."""
#     q = update.callback_query
#     await q.answer()

#     if q.data == "cancel":
#         await q.edit_message_text("❌ Purchase cancelled.")
#         return ConversationHandler.END

#     _, checker_type = q.data.split(":", 1)
#     context.user_data["checker_type"] = checker_type

#     quantities = [1, 2, 5, 10, 50, 100, 500]
#     qty_rows = [quantities[i : i + 3] for i in range(0, len(quantities), 3)]
#     keyboard = [
#         [InlineKeyboardButton(str(n), callback_data=f"qty:{n}") for n in row]
#         for row in qty_rows
#     ]
#     keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

#     await q.edit_message_text(
#         f"✏️ How many **{checker_type}** checkers do you want?",
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )
#     return ENTER_QUANTITY


# async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Step 3: Create Paystack link & prompt verification."""
#     q = update.callback_query
#     await q.answer()

#     if q.data == "cancel":
#         await q.edit_message_text("❌ Purchase cancelled.")
#         return ConversationHandler.END

#     _, qty_str = q.data.split(":", 1)
#     quantity = int(qty_str)
#     checker_type = context.user_data["checker_type"]

#     # Check stock
#     stock = (
#         await checker_stock_coll.find_one({"checker_type": checker_type})
#     ).get("stock", 0)
#     if quantity > stock:
#         await q.edit_message_text(
#             f"⚠️ Sorry, we do not have that many *{checker_type}* checkers right now.\n"
#             "Please choose a smaller quantity.",
#             parse_mode="Markdown",
#         )
#         return ConversationHandler.END

#     unit_price = CHECKER_PRICES[checker_type]
#     total = unit_price * quantity

#     user = await users_coll.find_one({"telegram_id": q.from_user.id})
#     email = user.get("email", "N/A")

#     # Initialize payment
#     reference = uuid.uuid4().hex
#     auth_url, pay_ref = initialize_payment(email, total, reference)

#     # Record pending transaction
#     await transactions_coll.insert_one({
#         "user_id":    q.from_user.id,
#         "type":       "checker",
#         "item_code":  checker_type,
#         "quantity":   quantity,
#         "amount":     total,
#         "status":     "pending",
#         "reference":  pay_ref,
#     })

#     # Prompt user
#     summary = (
#         f"TID:{pay_ref}\n"
#         f"Quantity: {quantity}\n"
#         f"Type: {checker_type}\n\n"
#         "Tap **Pay Now**, complete payment, then tap **I've Paid**."
#     )
#     keyboard = [[
#         InlineKeyboardButton("💳 Pay Now", url=auth_url),
#         InlineKeyboardButton("✔️ I've Paid", callback_data=f"verify:{pay_ref}")
#     ]]
#     await q.edit_message_text(
#         summary,
#         parse_mode="Markdown",
#         reply_markup=InlineKeyboardMarkup(keyboard),
#     )

#     context.user_data.update(
#         quantity=quantity,
#         reference=pay_ref,
#         checker_type=checker_type,
#     )
#     return VERIFY_PAYMENT


# async def verify_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Step 4: Verify Paystack and deliver serials/pins."""
#     q = update.callback_query
#     await q.answer()

#     if not q.data.startswith("verify:"):
#         return ConversationHandler.END

#     _, ref = q.data.split(":", 1)
#     try:
#         verify_payment(ref)
#     except PaystackError as e:
#         await q.edit_message_text(f"❌ Verification failed: {e}")
#         return ConversationHandler.END

#     # Mark transaction success
#     await transactions_coll.update_one(
#         {"reference": ref},
#         {"$set": {"status": "success"}}
#     )

#     # Fetch codes
#     qty = context.user_data["quantity"]
#     typ = context.user_data["checker_type"]
#     docs = await checker_codes_coll.find(
#         {"checker_type": typ, "used": False}
#     ).to_list(length=qty)

#     if len(docs) < qty:
#         await q.edit_message_text("❌ Not enough codes available.")
#         return ConversationHandler.END

#     # Mark used and collect
#     codes = []
#     for doc in docs:
#         await checker_codes_coll.update_one(
#             {"_id": doc["_id"]}, {"$set": {"used": True}}
#         )
#         codes.append((doc["serial"], doc["pin"]))

#     # Update transaction with codes
#     await transactions_coll.update_one(
#         {"reference": ref},
#         {"$set": {"codes_assigned": [{"serial": s, "pin": p} for s, p in codes]}}
#     )

#     # Build delivery message
#     lines = [f"TID:{ref}"]
#     for i, (s, p) in enumerate(codes, start=1):
#         lines.append(f"#{i}\n-\n{typ}\nSERIAL|PIN\n{s}|{p}\n")
#     lines.append("Check your results here\nghana.waecdirect.org\n-")
#     delivery = "\n".join(lines)

#     await q.edit_message_text(delivery, parse_mode="Markdown")

#     # Back to main menu
#     from handlers.main_menu import build_main_menu
#     await q.message.reply_text(
#         "Here’s the main menu:",
#         reply_markup=build_main_menu()
#     )
#     return ConversationHandler.END


# handlers/buy_checker.py

import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.config import CONFIG
from utils.db import (
    users_coll,
    checker_stock_coll,
    transactions_coll,
    checker_codes_coll,
)
from utils.paystack import initialize_payment, verify_payment, PaystackError

# Conversation states
CHOOSE_CHECKER, ENTER_QUANTITY, VERIFY_PAYMENT = range(3)

# Prices from config.json
CHECKER_PRICES = {c["code"]: c["price"] for c in CONFIG["checkers"]}


async def start_buy_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 1: Show checker types."""
    codes = list(CHECKER_PRICES.keys())
    rows = [codes[i : i + 2] for i in range(0, len(codes), 2)]
    keyboard = [
        [InlineKeyboardButton(code, callback_data=f"type:{code}") for code in row]
        for row in rows
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
    await update.message.reply_text(
        "🛒 Which checker would you like to purchase?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_CHECKER


async def choose_checker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 2: Handle type selection and ask quantity."""
    q = update.callback_query
    await q.answer()

    if q.data == "cancel":
        await q.edit_message_text("❌ Purchase cancelled.")
        return ConversationHandler.END

    _, checker_type = q.data.split(":", 1)
    context.user_data["checker_type"] = checker_type

    quantities = [1, 2, 5, 10, 50, 100, 500]
    qty_rows = [quantities[i : i + 3] for i in range(0, len(quantities), 3)]
    keyboard = [
        [InlineKeyboardButton(str(n), callback_data=f"qty:{n}") for n in row]
        for row in qty_rows
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])

    await q.edit_message_text(
        f"✏️ How many **{checker_type}** checkers do you want?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ENTER_QUANTITY


async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 3: Create payment and prompt verification."""
    q = update.callback_query
    await q.answer()

    if q.data == "cancel":
        await q.edit_message_text("❌ Purchase cancelled.")
        return ConversationHandler.END

    _, qty_str = q.data.split(":", 1)
    quantity = int(qty_str)
    checker_type = context.user_data["checker_type"]

    stock = (await checker_stock_coll.find_one({"checker_type": checker_type}) or {}).get("stock", 0)
    if quantity > stock:
        await q.edit_message_text(
            f"⚠️ Only {stock} *{checker_type}* checkers available.\n"
            "Please choose a smaller quantity.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    unit_price = CHECKER_PRICES[checker_type]
    total = unit_price * quantity

    user = await users_coll.find_one({"telegram_id": q.from_user.id})
    email = user.get("email", "N/A")

    # Initialize Paystack
    reference = uuid.uuid4().hex
    auth_url, pay_ref = initialize_payment(email, total, reference)

    # Record transaction
    await transactions_coll.insert_one({
        "user_id":    q.from_user.id,
        "type":       "checker",
        "item_code":  checker_type,
        "quantity":   quantity,
        "amount":     total,
        "status":     "pending",
        "reference":  pay_ref,
    })

    summary = (
        f"TID:{pay_ref}\n"
        f"Quantity: {quantity}\n"
        f"Type: {checker_type}\n\n"
        "💳 Tap **Pay Now**, then once done, tap **I've Paid**."
    )
    keyboard = [[
        InlineKeyboardButton("💳 Pay Now", url=auth_url),
        InlineKeyboardButton("✔️ I've Paid", callback_data=f"verify:{pay_ref}")
    ]]
    await q.edit_message_text(
        summary,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    context.user_data.update(
        quantity=quantity,
        reference=pay_ref,
        checker_type=checker_type,
    )
    return VERIFY_PAYMENT


async def verify_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Step 4: Verify payment, assign codes, and deliver."""
    q = update.callback_query
    await q.answer()

    if not q.data.startswith("verify:"):
        return ConversationHandler.END

    _, ref = q.data.split(":", 1)
    try:
        verify_payment(ref)
    except PaystackError as e:
        await q.edit_message_text(f"❌ Verification failed: {e}")
        return ConversationHandler.END

    # Mark transaction success
    await transactions_coll.update_one(
        {"reference": ref},
        {"$set": {"status": "success"}}
    )

    qty = context.user_data["quantity"]
    typ = context.user_data["checker_type"]
    docs = await checker_codes_coll.find(
        {"checker_type": typ, "used": False}
    ).to_list(length=qty)

    if len(docs) < qty:
        await q.edit_message_text("❌ Not enough codes available.")
        return ConversationHandler.END

    codes = []
    for doc in docs:
        await checker_codes_coll.update_one(
            {"_id": doc["_id"]}, {"$set": {"used": True}}
        )
        codes.append((doc["serial"], doc["pin"]))

    # Save assigned codes on transaction
    await transactions_coll.update_one(
        {"reference": ref},
        {"$set": {"codes_assigned": [{"serial": s, "pin": p} for s, p in codes]}}
    )

    # Build delivery message
    lines = [f"TID:{ref}"]
    for i, (s, p) in enumerate(codes, start=1):
        lines.append(f"#{i}\n-\n{typ}\nSERIAL|PIN\n{s}|{p}\n")
    lines.append("Check your results here\nghana.waecdirect.org\n-")
    message = "\n".join(lines)

    await q.edit_message_text(message, parse_mode="Markdown")

    # Return to main menu
    from handlers.main_menu import build_main_menu
    await q.message.reply_text(
        "Here’s the main menu:",
        reply_markup=build_main_menu()
    )
    return ConversationHandler.END
