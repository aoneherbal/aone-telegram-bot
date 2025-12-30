import os
import json
import base64
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import gspread
from google.oauth2.service_account import Credentials

# Safe environment variable loading
def safe_get_env(key):
    value = os.getenv(key)
    if not value:
        print(f"❌ Missing env var: {key}")
        return None
    return value.strip()

BOT_TOKEN = safe_get_env("BOT_TOKEN")
SHEET_ID = safe_get_env("GOOGLE_SHEET_ID")
CREDS_JSON = safe_get_env("GOOGLE_SERVICE_ACCOUNT_JSON")

if not all([BOT_TOKEN, SHEET_ID, CREDS_JSON]):
    print("❌ Missing required environment variables")
    print(f"BOT_TOKEN: {'OK' if BOT_TOKEN else 'MISSING'}")
    print(f"SHEET_ID: {'OK' if SHEET_ID else 'MISSING'}")
    print(f"CREDS_JSON: {'OK' if CREDS_JSON else 'MISSING'}")
    exit(1)

print("✅ All environment variables loaded")

# Ultra-safe JSON parsing
try:
    # Try base64 decode first (if somehow encoded)
    try:
        creds_data = json.loads(base64.b64decode(CREDS_JSON).decode())
        print("✅ Loaded via base64 decode")
    except:
        # Direct JSON parse
        creds_data = json.loads(CREDS_JSON)
        print("✅ Loaded direct JSON")
    
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(SHEET_ID)
    print("✅ Google Sheets connected")
    
    product_master = sh.worksheet("PRODUCT_MASTER")
    product_benefits = sh.worksheet("PRODUCT_BENEFITS")
    future_links = sh.worksheet("FUTURE_LINKS")
    
    products_data = product_master.get_all_records()
    benefits_data = product_benefits.get_all_records()
    links_data = future_links.get_all_records()
    
    print(f"✅ Loaded {len(products_data)} products, {len(benefits_data)} benefits, {len(links_data)} links")
    
except Exception as e:
    print(f"❌ Google Sheets error: {str(e)}")
    print("⚠️ Bot will run in demo mode without sheet data")
    products_data = benefits_data = links_data = []
    products_by_id = benefits_by_id = links_by_key = {}

# Simplified bot handlers (no complex logic that could break)
user_lang = {}

TEXTS = {
    "en": {
        "welcome": "🌿 Welcome to AOne Herbal! 🌿

Choose language:",
        "menu": "Choose category:",
        "error": "Sorry, try /start again."
    },
    "hi": {
        "welcome": "🌿 AOne Herbal में स्वागत है! 🌿

भाषा चुनें:",
        "menu": "श्रेणी चुनें:",
        "error": "क्षमा करें, फिर से /start करें।"
    }
}

def get_lang(user_id):
    return user_lang.get(user_id, "en")

async def start(update: Update, context):
    user_id = update.effective_user.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])
    await update.message.reply_text(TEXTS["en"]["welcome"], reply_markup=keyboard)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    if data == "lang_en":
        user_lang[user_id] = "en"
        await query.edit_message_text("✅ English selected!

Bot ready. Type /start", parse_mode="Markdown")
    elif data == "lang_hi":
        user_lang[user_id] = "hi"
        await query.edit_message_text("✅ हिन्दी चुनी गई!

बॉट तैयार। /start लिखें", parse_mode="Markdown")
    else:
        lang = get_lang(user_id)
        await query.edit_message_text(TEXTS[lang]["error"])

async def message(update: Update, context):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(TEXTS[lang]["error"])

def main():
    print("🚀 Starting AOne Herbal Bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    print("🤖 AOne Herbal Bot started successfully!")
    print("📱 Test with /start in Telegram")
    app.run_polling()

if __name__ == "__main__":
    main()
