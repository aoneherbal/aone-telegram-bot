import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.getenv("BOT_TOKEN")
app = ApplicationBuilder().token(BOT_TOKEN).build()

user_lang = {}

async def start(update: Update, context):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")], [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]])
    await update.message.reply_text("🌿 AOne Herbal Bot 🌿
Choose language:", reply_markup=keyboard)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    
    if data == "lang_en": 
        user_lang[user_id] = "en"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💼 Agent/Affiliate", callback_data="affiliate")], [InlineKeyboardButton("👥 Community", callback_data="community")], [InlineKeyboardButton("💬 WhatsApp", callback_data="whatsapp")]])
        await query.edit_message_text("✅ English!", reply_markup=keyboard)
    elif data == "lang_hi":
        user_lang[user_id] = "hi"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("💼 एजेंट/एफिलिएट", callback_data="affiliate")], [InlineKeyboardButton("👥 समुदाय", callback_data="community")], [InlineKeyboardButton("💬 व्हाट्सएप", callback_data="whatsapp")]])
        await query.edit_message_text("✅ हिन्दी!", reply_markup=keyboard)
    elif data == "affiliate":
        url = "https://forms.gle/rLgcf6wGPjjiyQKi7"
        text = f"💼 **Agent/Affiliate**

Join program
🔗 [Apply Now]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    elif data == "community":
        url = "https://chat.whatsapp.com/JMu7ZPH1QmvCnqyVN7g4jW"
        text = f"👥 **Health Community**

Join WhatsApp group
🔗 [Join Now]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    elif data == "whatsapp":
        url = "https://wa.me/919545466740"
        text = f"💬 **Talk to Human**

Direct chat
🔗 [WhatsApp]({url})"
        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
print("🤖 AOne Herbal Bot LIVE!")
app.run_polling()
