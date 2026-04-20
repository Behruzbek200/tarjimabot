import os
import telebot
from deep_translator import GoogleTranslator
from flask import Flask, request

# Sozlamalar
TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Foydalanuvchi matnlarini vaqtincha saqlash uchun
user_data = {}

LANGS = {
    'uz': 'uzbek', 'en': 'english', 'ru': 'russian', 'tr': 'turkish', 
    'ar': 'arabic', 'de': 'german', 'fr': 'french', 'ko': 'korean', 
    'ja': 'japanese', 'es': 'spanish'
}

def lang_inline():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [telebot.types.InlineKeyboardButton(text=v.capitalize(), callback_data=f"tr_{k}") for k, v in LANGS.items()]
    markup.add(*btns)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Salom! Tarjima qilinadigan matnni yuboring:")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Foydalanuvchi matnini xotiraga saqlaymiz
    user_data[message.chat.id] = message.text
    bot.reply_to(message, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    chat_id = call.message.chat.id
    
    # Xotiradan matnni qidiramiz
    text_to_translate = user_data.get(chat_id)

    if not text_to_translate:
        # Agar xotirada bo'lmasa, reply qilingan xabardan qidiradi
        if call.message.reply_to_message and call.message.reply_to_message.text:
            text_to_translate = call.message.reply_to_message.text
    
    if text_to_translate:
        try:
            bot.edit_message_text("⏳ Tarjima qilinmoqda...", chat_id, call.message.message_id)
            translated = GoogleTranslator(source='auto', target=LANGS[lang_code]).translate(text_to_translate)
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"✅ **{LANGS[lang_code].capitalize()}:**\n\n{translated}",
                parse_mode="Markdown"
            )
        except Exception:
            bot.edit_message_text("❌ Tarjima qilishda xatolik yuz berdi. Matn juda uzun bo'lishi mumkin.", chat_id, call.message.message_id)
    else:
        bot.edit_message_text("❌ Kechirasiz, tarjima qilinadigan matn topilmadi. Qaytadan yuboring.", chat_id, call.message.message_id)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}", drop_pending_updates=True)
    return "Bot ishlamoqda...", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
