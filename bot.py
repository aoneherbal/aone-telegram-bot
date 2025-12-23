import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

# Simple in‑memory language store: {user_id: "en" or "hi"}
user_lang = {}

# ---------- Texts ----------
TEXTS = {
    "start": {
        "en": "Welcome to AOne Herbal 🌿

Please choose your language.",
        "hi": "AOne Herbal में आपका स्वागत है 🌿

कृपया अपनी भाषा चुनें।",
    },
    "menu_title": {
        "en": "What would you like to do?",
        "hi": "आप क्या करना चाहते हैं?",
    },
    "menu_buttons": {
        "en": ["🧴 Product info", "🛒 Order / Enquiry"],
        "hi": ["🧴 प्रोडक्ट जानकारी", "🛒 ऑर्डर / पूछताछ"],
    },
    "product_info": {
        "en": "Share the product name or concern (e.g. hairfall, gas, diabetes).",
        "hi": "प्रोडक्ट का नाम या समस्या लिखें (जैसे hairfall, gas, diabetes)।",
    },
    "order_info": {
        "en": "Please share:
Name
City
Product name
Preferred contact (WhatsApp/Call).",
        "hi": "कृपया भेजें:
नाम
शहर
प्रोडक्ट का नाम
संपर्क तरीका (WhatsApp/कॉल)।",
    },
    "unknown": {
        "en": "Type /start to see the menu again.",
        "hi": "/start लिखकर मेनू फिर से देखें।",
    },
}
# ---------- Helpers ----------
def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, "en")


def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    labels = TEXTS["menu_buttons"][lang]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(labels[0], callback_data="menu_product")],
            [InlineKeyboardButton(labels[1], callback_data="menu_order")],
        ]
    )

# ---------- Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Language select buttons
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
                InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi"),
            ]
        ]
    )
    user_lang[user_id] = "en"  # default
    await update.message.reply_text(TEXTS["start"]["en"], reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    # Language selection
    if data in ("lang_en", "lang_hi"):
        lang = "en" if data == "lang_en" else "hi"
        user_lang[user_id] = lang
        await query.edit_message_text(
            TEXTS["menu_title"][lang],
            reply_markup=main_menu_keyboard(lang),
        )
        return

    lang = get_lang(user_id)

    # Main menu actions
    if data == "menu_product":
        await query.edit_message_text(TEXTS["product_info"][lang])
    elif data == "menu_order":
        await query.edit_message_text(TEXTS["order_info"][lang])

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    # For now just echo a friendly message; later we’ll connect Google Sheets.
    await update.message.reply_text(TEXTS["unknown"][lang])

# ---------- Main ----------
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot started with polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
