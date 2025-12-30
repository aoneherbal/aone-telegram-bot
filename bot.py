import os
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
    raise RuntimeError("Missing required environment variables")

# Google Sheets setup
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(eval(CREDS_JSON), scopes=SCOPES)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(SHEET_ID)

# Load sheets
product_master = sh.worksheet("PRODUCT_MASTER")
product_benefits = sh.worksheet("PRODUCT_BENEFITS")
future_links = sh.worksheet("FUTURE_LINKS")  # Affiliate/Franchise links

# Load data
products_data = product_master.get_all_records()
benefits_data = product_benefits.get_all_records()
links_data = future_links.get_all_records()

# Convert to dicts for fast lookup
products_by_id: Dict[str, dict] = {row["Product_ID"]: row for row in products_data}
benefits_by_id: Dict[str, dict] = {row["Product_ID"]: row for row in benefits_data}
links_by_key: Dict[str, dict] = {row["Key"]: row for row in links_data}

# Language state
user_lang: Dict[int, str] = {}
user_state: Dict[int, str] = {}

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
    """Get text from row, preferring _HI for Hindi, fallback to English."""
    hi_field = f"{field}_HI"
    if lang == "hi" and hi_field in row and row[hi_field]:
        return row[hi_field]
    return row.get(field, "")

def get_category_products(category: str, lang: str) -> List[dict]:
    """Get products in a category."""
    return [p for p in products_data if p.get("Category") == category or 
            (lang == "hi" and p.get("Category_HI") == category)]

def main_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Main menu with 8 buttons from your design."""
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
    
    return InlineKeyboardMarkup(buttons)

# Handlers
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

    # Language selection
    if data in ("lang_en", "lang_hi"):
        user_lang[user_id] = "en" if data == "lang_en" else "hi"
        lang = user_lang[user_id]
        await query.edit_message_text(
            get_text("menu_title", lang),
            reply_markup=main_menu_keyboard(lang)
        )
        return

    # Category buttons (Hair, Skin, etc.)
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
                for p in products[:6]:  # Show max 6 products
                    name = get_bilingual_text(p, "Product_Name", lang)
                    text += f"
• {name}"
                text += "

Tap any product above or use main menu."
                await query.edit_message_text(text, parse_mode="Markdown")
            else:
                await query.edit_message_text("No products found in this category.")
            return

    # Special links (Affiliate, Community, WhatsApp)
    if data == "affiliate":
        link_row = links_by_key.get("affiliate_form", {})
        title = get_bilingual_text(link_row, "Title", lang)
        url = link_row.get("URL", "")
        text = f"**{title}**

{link_row.get('Description', '')}

🔗 [Fill Form]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
        return

    if data == "community":
        link_row = links_by_key.get("join_community", {})
        title = get_bilingual_text(link_row, "Title", lang)
        url = link_row.get("URL", "")
        text = f"**{title}**

{link_row.get('Description', '')}

🔗 [Join Now]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
        return

    if data == "whatsapp":
        link_row = links_by_key.get("whatsapp", {})
        title = get_bilingual_text(link_row, "Title", lang)
        url = link_row.get("URL", "")
        text = f"**{title}**

{link_row.get('Description', '')}

💬 [Chat on WhatsApp]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
        return

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)
    await update.message.reply_text(get_text("unknown", lang))

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("🤖 AOne Herbal Bot with Google Sheets started...")
    app.run_polling()

if __name__ == "__main__":
    main()
