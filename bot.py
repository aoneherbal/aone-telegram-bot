import os
import json
import ast
import base64
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEET_AVAILABLE = True
except ImportError:
    GSHEET_AVAILABLE = False
    print("⚠️ gspread not available - demo mode")

print("🚀 AOne Herbal Bot starting...")

# Safe env loading
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
CREDS_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

print(f"BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
print(f"SHEET_ID: {'✅' if SHEET_ID else '❌'}") 
print(f"CREDS_JSON: {'✅' if CREDS_JSON else '❌'} ({len(CREDS_JSON) if CREDS_JSON else 0} chars)")

if not BOT_TOKEN:
    print("❌ No BOT_TOKEN - exiting")
    exit(1)

# Global data with fallback
products_data = benefits_data = links_data = []
products_by_id = benefits_by_id = links_by_key = {}

# Safe Google Sheets connection
if GSHEET_AVAILABLE and SHEET_ID and CREDS_JSON:
    try:
        # Try multiple JSON parsing methods
        creds_data = None
        parsers = [
            lambda x: json.loads(x),
            lambda x: json.loads(base64.b64decode(x).decode() if base64.b64decode(x, validate=False) else x),
            lambda x: ast.literal_eval(x)
        ]
        
        for i, parser in enumerate(parsers):
            try:
                creds_data = parser(CREDS_JSON)
                print(f"✅ JSON parsed with method {i+1}")
                break
            except Exception as e:
                print(f"Parser {i+1} failed: {e}")
                continue
        
        if creds_data:
            SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
            gc = gspread.authorize(credentials)
            sh = gc.open_by_key(SHEET_ID)
            
            product_master = sh.worksheet("PRODUCT_MASTER")
            product_benefits = sh.worksheet("PRODUCT_BENEFITS")
            future_links = sh.worksheet("FUTURE_LINKS")
            
            products_data = product_master.get_all_records()
            benefits_data = product_benefits.get_all_records()
            links_data = future_links.get_all_records()
            
            products_by_id = {row.get("Product_ID", ""): row for row in products_data}
            benefits_by_id = {row.get("Product_ID", ""): row for row in benefits_data}
            links_by_key = {row.get("Key", ""): row for row in links_data}
            
            print(f"✅ Sheets: {len(products_data)} products, {len(links_data)} links")
        else:
            print("⚠️ All JSON parsers failed")
    except Exception as e:
        print(f"⚠️ Sheets failed: {str(e)}")
else:
    print("⚠️ No sheets - running demo mode")

# Bot logic
user_lang = {}

TEXTS = {
    "en": {"welcome": "🌿 Welcome to AOne Herbal! 🌿

Choose language:", "error": "Try /start"},
    "hi": {"welcome": "🌿 AOne Herbal में स्वागत! 🌿

भाषा चुनें:", "error": "फिर /start करें"}
}

def get_lang(user_id): 
    return user_lang.get(user_id, "en")

def get_text(key, lang): 
    return TEXTS.get(lang, TEXTS["en"]).get(key, "")

def main_menu_keyboard(lang):
    buttons = []
    if lang == "hi":
        buttons = [
            [InlineKeyboardButton("💇‍♀️ बालों की देखभाल", callback_data="cat_hair")],
            [InlineKeyboardButton("🧴 त्वचा की देखभाल", callback_data="cat_skin")],
            [InlineKeyboardButton("⚖️ वजन प्रबंधन", callback_data="cat_weight")],
            [InlineKeyboardButton("🦴 हड्डी जोड़", callback_data="cat_bone")],
            [InlineKeyboardButton("♀️ महिला कल्याण", callback_data="cat_female")],
            [InlineKeyboardButton("💼 एजेंट/एफिलिएट", callback_data="affiliate")],
            [InlineKeyboardButton("👥 स्वास्थ्य समुदाय", callback_data="community")],
            [InlineKeyboardButton("💬 व्हाट्सएप", callback_data="whatsapp")]
        ]
    else:
        buttons = [
            [InlineKeyboardButton("💇‍♀️ Hair Care", callback_data="cat_hair")],
            [InlineKeyboardButton("🧴 Skin Care", callback_data="cat_skin")],
            [InlineKeyboardButton("⚖️ Weight Mgmt", callback_data="cat_weight")],
            [InlineKeyboardButton("🦴 Bone & Joint", callback_data="cat_bone")],
            [InlineKeyboardButton("♀️ Female Wellness", callback_data="cat_female")],
            [InlineKeyboardButton("💼 Agent/Affiliate", callback_data="affiliate")],
            [InlineKeyboardButton("👥 Health Community", callback_data="community")],
            [InlineKeyboardButton("💬 WhatsApp", callback_data="whatsapp")]
        ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])
    await update.message.reply_text(get_text("welcome", "en"), reply_markup=keyboard)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    lang = get_lang(user_id)
    
    if data == "lang_en":
        user_lang[user_id] = "en"
        await query.edit_message_text("✅ English selected!", reply_markup=main_menu_keyboard("en"))
    elif data == "lang_hi":
        user_lang[user_id] = "hi" 
        await query.edit_message_text("✅ हिन्दी चुनी गई!", reply_markup=main_menu_keyboard("hi"))
    
    elif data.startswith("cat_"):
        await query.edit_message_text(f"🛒 **{data.replace('cat_', '').title().replace('Mgmt', 'Management')} products coming soon...**

Main menu 👆", parse_mode="Markdown")
    
    elif data in ["affiliate", "community", "whatsapp"]:
        key_map = {"affiliate": "affiliate_form", "community": "join_community", "whatsapp": "whatsapp"}
        key = key_map[data]
        link_row = links_by_key.get(key, {})
        
        title = link_row.get("Title_HI" if lang == "hi" else "Title", key.replace("_", " ").title())
        title_hi = link_row.get("Title_HI", title)
        url = link_row.get("URL", "https://aoneherbal.com")
        desc = link_row.get("Description_HI" if lang == "hi" else "Description", "")
        
        text = f"**{title if lang == 'en' else title_hi}**

{desc}

🔗 [Open Link]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    
    else:
        await query.edit_message_text(get_text("error", lang), reply_markup=main_menu_keyboard(lang))

async def message(update: Update, context):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(get_text("error", lang), reply_markup=main_menu_keyboard(lang))

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))
    print("🤖 AOne Herbal Bot LIVE! 🚀")
    print("📱 Test: /start → English → Agent/Affiliate → Your form!")
    app.run_polling()
