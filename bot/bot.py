# -*- coding: utf-8 -*-
import os
import time
import telebot
from deep_translator import GoogleTranslator
from flask import Flask
from threading import Thread

# 1. SOZLAMALAR
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask('')

user_data = {}

LANGS = {
    'uz': 'uzbek', 'en': 'english', 'ru': 'russian', 'tr': 'turkish', 
    'ar': 'arabic', 'de': 'german', 'fr': 'french', 'ko': 'korean', 
    'ja': 'japanese', 'es': 'spanish'
}

# 2. WEB SERVER (Render uchun)
@app.route('/')
def home():
    return "Bot status: OK"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 3. KLAVIATURA
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
    user_data[message.chat.id] = message.text
    bot.send_message(message.chat.id, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())

# 4. TARJIMA QILISH (Xatolarni aqlli ushlash bilan)
@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    chat_id = call.message.chat.id
    original_text = user_data.get(chat_id)

    if not original_text:
        bot.edit_message_text("❌ Matn topilmadi.", chat_id, call.message.message_id)
        return

    bot.answer_callback_query(call.id, "⏳ Tarjima qilinmoqda...")
    target_lang = LANGS[lang_code]

    try:
        # Bloklanmaslik uchun 0.5 soniya kutish
        time.sleep(0.5)

        # Tarjima mantiqi (Siz yuborgan skrinshotdagi kabi)
        translator = GoogleTranslator(source='uz', target=target_lang)
        translated = translator.translate(original_text)

        # Agar natija o'zgarmasa, auto-ga o'tadi
        if translated.lower() == original_text.lower():
            translated = GoogleTranslator(source='auto', target=target_lang).translate(original_text)

        result_text = f"✅ {target_lang.capitalize()} tilida:\n\n{translated}"
        bot.edit_message_text(result_text, chat_id, call.message.message_id, parse_mode="Markdown")

    except Exception as e:
        error_msg = str(e).lower()
        if "too many requests" in error_msg:
            # Agar band bo'lsa, foydalanuvchiga tushunarli javob beramiz
            bot.edit_message_text("⚠️ Google Translate band. 10 soniyadan so'ng qayta urinib ko'ring.", chat_id, call.message.message_id)
        else:
            bot.edit_message_text(f"❌ Xatolik: Server javob bermadi.", chat_id, call.message.message_id)

# 5. ISHGA TUSHIRISH
if name == "main":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Bot Render-da online...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
