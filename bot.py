from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ No BOT_TOKEN")
    exit(1)

print("🚀 AOne Herbal Bot - LIVE WITHOUT SHEETS!")

# Your links HARDCODED (works 100%)
LINKS = {
    "affiliate_form": {
        "en": {"title": "Become Agent / Affiliate", "desc": "Join our affiliate program", "url": "https://forms.gle/rLgcf6wGPjjiyQKi7"},
        "hi": {"title": "एजेंट / एफिलिएट बनें", "desc": "हमारे एफिलिएट प्रोग्राम में शामिल हों", "url": "https://forms.gle/rLgcf6wGPjjiyQKi7"}
    },
    "join_community": {
        "en": {"title": "Join Health Community", "desc": "Connect with other users", "url": "https://chat.whatsapp.com/JMu7ZPH1QmvCnqyVN7g4jW"},
        "hi": {"title": "स्वास्थ्य समुदाय में शामिल हों", "desc": "अन्य उपयोगकर्ताओं से जुड़ें", "url": "https://chat.whatsapp.com/JMu7ZPH1QmvCnqyVN7g4jW"}
    },
    "whatsapp": {
        "en": {"title": "Talk to Human (WhatsApp)", "desc": "Chat with our team directly", "url": "https://wa.me/919545466740"},
        "hi": {"title": "इंसान से बात करें (व्हाट्सएप)", "desc": "हमारी टीम से सीधे चैट करें", "url": "https://wa.me/919545466740"}
    }
}

user_lang = {}

def main_menu_keyboard(lang):
    if lang == "hi":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("💇‍♀️ बालों की देखभाल", callback_data="cat_hair")],
            [InlineKeyboardButton("🧴 त्वचा की देखभाल", callback_data="cat_skin")],
            [InlineKeyboardButton("⚖️ वजन प्रबंधन", callback_data="cat_weight")],
            [InlineKeyboardButton("🦴 हड्डी जोड़", callback_data="cat_bone")],
            [InlineKeyboardButton("♀️ महिला कल्याण", callback_data="cat_female")],
            [InlineKeyboardButton("💼 एजेंट/एफिलिएट", callback_data="affiliate")],
            [InlineKeyboardButton("👥 स्वास्थ्य समुदाय", callback_data="community")],
            [InlineKeyboardButton("💬 व्हाट्सएप", callback_data="whatsapp")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💇‍♀️ Hair Care", callback_data="cat_hair")],
        [InlineKeyboardButton("🧴 Skin Care", callback_data="cat_skin")],
        [InlineKeyboardButton("⚖️ Weight Mgmt", callback_data="cat_weight")],
        [InlineKeyboardButton("🦴 Bone & Joint", callback_data="cat_bone")],
        [InlineKeyboardButton("♀️ Female Wellness", callback_data="cat_female")],
        [InlineKeyboardButton("💼 Agent/Affiliate", callback_data="affiliate")],
        [InlineKeyboardButton("👥 Health Community", callback_data="community")],
        [InlineKeyboardButton("💬 WhatsApp", callback_data="whatsapp")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])
    await update.message.reply_text("🌿 Welcome to AOne Herbal! 🌿

Choose language:", reply_markup=keyboard)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    lang = user_lang.get(user_id, "en")
    
    if data == "lang_en":
        user_lang[user_id] = "en"
        await query.edit_message_text("✅ English selected!", reply_markup=main_menu_keyboard("en"))
    elif data == "lang_hi":
        user_lang[user_id] = "hi"
        await query.edit_message_text("✅ हिन्दी चुनी गई!", reply_markup=main_menu_keyboard("hi"))
    
    elif data.startswith("cat_"):
        cat_name = data.replace("cat_", "").replace("hair", "Hair Care").replace("skin", "Skin Care").replace("weight", "Weight Management").replace("bone", "Bone & Joint").replace("female", "Female Wellness")
        cat_hi = cat_name.replace("Hair Care", "बालों की देखभाल").replace("Skin Care", "त्वचा की देखभाल").replace("Weight Management", "वजन प्रबंधन").replace("Bone & Joint", "हड्डी जोड़").replace("Female Wellness", "महिला कल्याण")
        text = f"🛒 **{cat_hi if lang == 'hi' else cat_name}**

Products coming soon!

Main menu 👆"
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif data in ["affiliate", "community", "whatsapp"]:
        key = {"affiliate": "affiliate_form", "community": "join_community", "whatsapp": "whatsapp"}[data]
        link_data = LINKS[key][lang]
        text = f"**{link_data['title']}**

{link_data['desc']}

🔗 [Open Link]({link_data['url']})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    
    else:
        await query.edit_message_text("Try /start", reply_markup=main_menu_keyboard(lang))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_lang.get(update.effective_user.id, "en")
    await update.message.reply_text("Please use buttons or /start", reply_markup=main_menu_keyboard(lang))

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("🤖 AOne Herbal Bot LIVE! 🚀")
    print("✅ All links work: Affiliate, Community, WhatsApp")
    app.run_polling()

if __name__ == "__main__":
    main()
