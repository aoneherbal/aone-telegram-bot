import os
import json
from typing import Optional, Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

import gspread
from google.oauth2.service_account import Credentials

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDS_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

if not all([BOT_TOKEN, SHEET_ID, CREDS_JSON]):
    raise RuntimeError("Missing required environment variables: BOT_TOKEN, GOOGLE_SHEET_ID, or GOOGLE_SERVICE_ACCOUNT_JSON")

# Google Sheets setup - FIXED JSON parsing
try:
    credentials_info = json.loads(CREDS_JSON)
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SHEET_ID)
except Exception as e:
    print(f"Google Sheets setup failed: {e}")
    raise

# Load sheets with error handling
try:
    product_master = sh.worksheet("PRODUCT_MASTER")
    product_benefits = sh.worksheet("PRODUCT_BENEFITS")
    future_links = sh.worksheet("FUTURE_LINKS")
    
    products_data = product_master.get_all_records()
    benefits_data = product_benefits.get_all_records()
    links_data = future_links.get_all_records()
    
    products_by_id = {row.get("Product_ID", ""): row for row in products_data}
    benefits_by_id = {row.get("Product_ID", ""): row for row in benefits_data}
    links_by_key = {row.get("Key", ""): row for row in links_data}
except Exception as e:
    print(f"Sheet loading failed: {e}")
    raise

# Language state
user_lang = {}
user_state = {}

TEXTS = {
    "welcome": {
        "en": "🌿 Welcome to AOne Herbal 🌿

One Name for All Health Solutions",
        "hi": "🌿 AOne Herbal में आपका स्वागत है 🌿

सभी स्वास्थ्य समाधान का एक नाम"
    },
    "menu_title": {
        "en": "Please choose what you need:",
        "hi": "कृपया चुनें आपको क्या चाहिए:"
    },
    "unknown": {
        "en": "Type /start to see the menu again.",
        "hi": "/start लिखकर मेनू फिर से देखें।"
    }
}

def get_lang(user_id: int) -> str:
    return user_lang.get(user_id, "en")

def get_text(key: str, lang: str) -> str:
    return TEXTS.get(key, {}).get(lang, "")

def get_bilingual_text(row: dict, field: str, lang: str) -> str:
    hi_field = f"{field}_HI"
    if lang == "hi" and hi_field in row and row[hi_field]:
        return row[hi_field]
    return row.get(field, "")

def get_category_products(category: str, lang: str) -> list:
    products = []
    for p in products_data:
        cat_en = p.get("Category", "")
        cat_hi = p.get("Category_HI", "")
        if cat_en == category or (lang == "hi" and cat_hi == category):
            products.append(p)
    return products

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    if lang == "hi":
        buttons = [
            [InlineKeyboardButton("💇‍♀️ बालों की देखभाल", callback_data="cat_hair")],
            [InlineKeyboardButton("🧴 त्वचा की देखभाल", callback_data="cat_skin")],
            [InlineKeyboardButton("⚖️ वजन प्रबंधन", callback_data="cat_weight")],
            [InlineKeyboardButton("🦴 हड्डी और जोड़ों की देखभाल", callback_data="cat_bone")],
            [InlineKeyboardButton("♀️ महिला कल्याण", callback_data="cat_female")],
            [InlineKeyboardButton("💼 एजेंट/एफिलिएट बनें", callback_data="affiliate")],
            [InlineKeyboardButton("👥 स्वास्थ्य समुदाय में शामिल हों", callback_data="community")],
            [InlineKeyboardButton("💬 इंसान से बात करें (व्हाट्सएप)", callback_data="whatsapp")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("💇‍♀️ Hair Care", callback_data="cat_hair")],
            [InlineKeyboardButton("🧴 Skin Care", callback_data="cat_skin")],
            [InlineKeyboardButton("⚖️ Weight Management", callback_data="cat_weight")],
            [InlineKeyboardButton("🦴 Bone & Joint Care", callback_data="cat_bone")],
            [InlineKeyboardButton("♀️ Female Wellness", callback_data="cat_female")],
            [InlineKeyboardButton("💼 Become Agent/Affiliate", callback_data="affiliate")],
            [InlineKeyboardButton("👥 Join Health Community", callback_data="community")],
            [InlineKeyboardButton("💬 Talk to Human (WhatsApp)", callback_data="whatsapp")]
        ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])
    user_lang[user_id] = "en"
    user_state.pop(user_id, None)
    lang = get_lang(user_id)
    await update.message.reply_text(get_text("welcome", lang), reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    lang = get_lang(user_id)

    if data in ("lang_en", "lang_hi"):
        user_lang[user_id] = "en" if data == "lang_en" else "hi"
        lang = user_lang[user_id]
        await query.edit_message_text(
            get_text("menu_title", lang),
            reply_markup=main_menu_keyboard(lang)
        )
        return

    if data.startswith("cat_"):
        category_map = {
            "cat_hair": "Hair Care",
            "cat_skin": "Skin Care", 
            "cat_weight": "Weight Management",
            "cat_bone": "Bone & Joint Care",
            "cat_female": "Female Wellness"
        }
        category = category_map.get(data)
        if category:
            products = get_category_products(category, lang)
            if products:
                text = f"**{category}** Products:" if lang == "en" else f"**{category}** उत्पाद:"
                for p in products[:6]:
                    name = get_bilingual_text(p, "Product_Name", lang)
                    text += f"
• {name}"
                text += "

Tap any product or use main menu."
                await query.edit_message_text(text, parse_mode="Markdown")
            else:
                await query.edit_message_text("No products found.")
            return

    # Special links
    link_keys = {"affiliate": "affiliate_form", "community": "join_community", "whatsapp": "whatsapp"}
    if data in link_keys:
        key = link_keys[data]
        link_row = links_by_key.get(key, {})
        title = get_bilingual_text(link_row, "Title", lang)
        url = link_row.get("URL", "")
        desc = link_row.get("Description", "")
        text = f"**{title}**

{desc}

🔗 [Open Link]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    await update.message.reply_text(get_text("unknown", lang))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("🤖 AOne Herbal Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
