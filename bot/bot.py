import os, telebot
from deep_translator import GoogleTranslator
from flask import Flask, request

TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Foydalanuvchi matnini eslab qolish uchun lug'at
user_data = {}

LANGS = {
    'uz': 'uzbek', 'en': 'english', 'ru': 'russian', 'tr': 'turkish', 
    'ar': 'arabic', 'de': 'german', 'fr': 'french', 'ko': 'korean', 
    'ja': 'japanese', 'es': 'spanish'
}

def lang_inline():
    m = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [telebot.types.InlineKeyboardButton(text=v.capitalize(), callback_data=f"tr_{k}") for k, v in LANGS.items()]
    m.add(*btns)
    return m

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "👋 Salom! Tarjima qilinadigan so'zni yuboring:")

@bot.message_handler(func=lambda m: True)
def handle_text(m):
    user_data[m.chat.id] = m.text # Matnni saqlaymiz
    bot.reply_to(m, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_call(call):
    lang_code = call.data.split('_')[1]
    text = user_data.get(call.message.chat.id) # Saqlangan matnni olamiz
    
    if text:
        try:
            bot.edit_message_text("⏳ Tarjima qilinmoqda...", call.message.chat.id, call.message.message_id)
            tr = GoogleTranslator(source='auto', target=LANGS[lang_code]).translate(text)
            bot.edit_message_text(f"✅ **{LANGS[lang_code].capitalize()} tilida:**\n\n{tr}", call.message.chat.id, call.message.message_id)
        except:
            bot.edit_message_text("❌ Xatolik: Tarjima xizmati javob bermadi.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text("❌ Xatolik: Matn topilmadi, qaytadan yuboring.", call.message.chat.id, call.message.message_id)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}", drop_pending_updates=True)
    return "Bot Online", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
