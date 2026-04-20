import os
import telebot
from deep_translator import GoogleTranslator
from flask import Flask, request

# Sozlamalar
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 10 ta asosiy tarjima tili
LANGS = {
    'uz': 'uzbek', 
    'en': 'english', 
    'ru': 'russian', 
    'tr': 'turkish', 
    'ar': 'arabic', 
    'de': 'german', 
    'fr': 'french',
    'ko': 'korean',
    'ja': 'japanese',
    'es': 'spanish'
}

def lang_inline():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [telebot.types.InlineKeyboardButton(text=v.capitalize(), callback_data=f"tr_{k}") for k, v in LANGS.items()]
    markup.add(*btns)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Salom! Tarjima qilinadigan so'z yoki matnni kiriting:")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Matn kelishi bilan darhol 10 ta tilni inline tugmada chiqaradi
    bot.reply_to(message, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    
    # Foydalanuvchi yuborgan asl matnni reply qilingan xabardan olamiz
    try:
        original_text = call.message.reply_to_message.text
        translated = GoogleTranslator(source='auto', target=LANGS[lang_code]).translate(original_text)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ **{LANGS[lang_code].capitalize()} tilida:**\n\n{translated}",
            parse_mode="Markdown"
        )
    except Exception:
        bot.answer_callback_query(call.id, "❌ Xatolik! Matn topilmadi yoki tarjima qilib bo'lmadi.")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}", drop_pending_updates=True)
    return "Tarjimon Bot Online!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
