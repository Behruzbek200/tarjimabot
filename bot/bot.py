# -*- coding: utf-8 -*-
import os
import time
import telebot
from deep_translator import GoogleTranslator
from flask import Flask
from threading import Thread

# 1. BOTNI XAVFSIZ YARATISH
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    # Agar ENV bo'sh bo'lsa, xato bermasligi uchun zaxira (Faqat test uchun)
    TOKEN = '8165546119:AAEifJ5hSmGN3aIEoJM9Bd1IlVNeujKDxKo'

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask('')

user_data = {}

LANGS = {
    'uz': 'uzbek', 'en': 'english', 'ru': 'russian', 'tr': 'turkish', 
    'ar': 'arabic', 'de': 'german', 'fr': 'french', 'ko': 'korean', 
    'ja': 'japanese', 'es': 'spanish'
}

# 2. WEB SERVER (Render Port muammosi chiqmasligi uchun)
@app.route('/')
def home():
    return "Bot status: System Online 24/7"

def run_web_server():
    try:
        port = int(os.environ.get("PORT", 10000))
        app.run(host='0.0.0.0', port=port)
    except:
        pass

# 3. KLAVIATURA
def lang_inline():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [telebot.types.InlineKeyboardButton(text=v.capitalize(), callback_data=f"tr_{k}") for k, v in LANGS.items()]
    markup.add(*btns)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(message.chat.id, "👋 Salom! Istalgan tilda matn yuboring:")
    except:
        pass

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        user_data[message.chat.id] = message.text
        bot.send_message(message.chat.id, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())
    except:
        pass

# 4. TARJIMANI HIMOYALANGAN QISMI
@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    chat_id = call.message.chat.id
    original_text = user_data.get(chat_id)

    if not original_text:
        try: bot.edit_message_text("❌ Matn topilmadi. Qayta yuboring.", chat_id, call.message.message_id)
        except: pass
        return

    try:
        bot.answer_callback_query(call.id, "⏳ Tarjima qilinmoqda...")
        target_lang = LANGS[lang_code]
        
        # --- AQLLI TARJIMA FUNKSIYASI ---
        def try_translate(text, source_mode):
            # 3 marta qayta urinish (Retry logic)
            for _ in range(3):
                try:
                    time.sleep(0.5)
                    return GoogleTranslator(source=source_mode, target=target_lang).translate(text)
                except:
                    time.sleep(1) # Agar server band bo'lsa, 1 soniya kutib qayta urinadi
            return None

        # Avval o'zbekcha urinish
        translated = try_translate(original_text, 'uz')
        
        # Agar natija o'zgarmasa yoki xato bo'lsa, auto rejimga o'tadi
        if not translated or translated.lower() == original_text.lower():
            translated = try_translate(original_text, 'auto')

        if translated:
            result_text = f"✅ {target_lang.capitalize()} tilida:\n\n{translated}"
            bot.edit_message_text(result_text, chat_id, call.message.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("⚠️ Google hozir javob bermadi. Birozdan so'ng tugmani qayta bosing.", chat_id, call.message.message_id)

    except Exception:
        # Eng yomon holatda ham bot o'chmaydi, shunchaki xabar beradi
        try: bot.edit_message_text("❌ Kichik texnik uzilish. Qayta urinib ko'ring.", chat_id, call.message.message_id)
        except: pass

# 5. ABADIY ISHLASH (POLLING RECOVERY)
if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("Super Protected Bot online...")
    
    # Bot o'chib qolsa, avtomatik qayta ulanadi
    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Xatolik yuz berdi, 5 soniyadan so'ng qayta ulanadi: {e}")
            time.sleep(5)
