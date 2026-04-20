# -*- coding: utf-8 -*-
import os
import time
import telebot
from deep_translator import GoogleTranslator, MyMemoryTranslator
from flask import Flask
from threading import Thread

# 1. SOZLAMALAR
TOKEN = os.environ.get('BOT_TOKEN') or '8165546119:AAEifJ5hSmGN3aIEoJM9Bd1IlVNeujKDxKo'
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
def home(): return "System Online"

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
    bot.send_message(message.chat.id, "👋 Matn yuboring, men uni har qanday holatda tarjima qilaman:")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_data[message.chat.id] = message.text
    bot.send_message(message.chat.id, "👇 Tilni tanlang:", reply_markup=lang_inline())

# 4. UNIVERSAL TARJIMA FUNKSIYASI (Xatolik chiqmaydigan qismi)
def universal_translate(text, target_lang):
    # 1-urinish: Google (Asosiy)
    try:
        # Avval o'zbekcha urinish
        res = GoogleTranslator(source='uz', target=target_lang).translate(text)
        if res.lower() == text.lower(): # Agar tarjima qilmasa (auto)
            res = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return res
    except:
        # 2-urinish: Google band bo'lsa, MyMemory-ga o'tadi (Zaxira)
        try:
            time.sleep(1) # Ozgina kutish
            return MyMemoryTranslator(source='auto', target=target_lang).translate(text)
        except:
            return "⚠️ Hozirda barcha tarjima serverlari band. Birozdan so'ng urinib ko'ring."

# 5. CALLBACK QUERY
@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    chat_id = call.message.chat.id
    text = user_data.get(chat_id)

    if text:
        bot.answer_callback_query(call.id, "⏳...")
        # Tarjima qilish
        translated = universal_translate(text, LANGS[lang_code])
        
        # Natijani chiqarish
        bot.edit_message_text(
            f"✅ {LANGS[lang_code].capitalize()} tilida:\n\n{translated}",
            chat_id, 
            call.message.message_id,
            parse_mode="Markdown"
        )

# 6. ASOSIY QISM
if name == "main":
    Thread(target=run_web_server, daemon=True).start()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except:
            time.sleep(5)
