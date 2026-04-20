Tarjimon, [4/20/2026 4:50 AM]
👇 Qaysi tilga tarjima qilamiz?

$$$, [4/20/2026 4:55 AM]
import os
import time
import telebot
from deep_translator import GoogleTranslator
from flask import Flask
from threading import Thread

# 1. BOT SOZLAMALARI
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask('')

# Foydalanuvchi matnlarini saqlash
user_data = {}

LANGS = {
    'uz': 'uzbek', 'en': 'english', 'ru': 'russian', 'tr': 'turkish', 
    'ar': 'arabic', 'de': 'german', 'fr': 'french', 'ko': 'korean', 
    'ja': 'japanese', 'es': 'spanish'
}

# 2. WEB SERVER (Render port xatoligini bermasligi uchun)
@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 3. KLAVIATURA (Inline Buttons)
def lang_inline():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [telebot.types.InlineKeyboardButton(text=v.capitalize(), callback_data=f"tr_{k}") for k, v in LANGS.items()]
    markup.add(*btns)
    return markup

# 4. BOT BUYRUQLARI
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Salom! Istalgan tilda matn yuboring:")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_data[message.chat.id] = message.text
    bot.send_message(message.chat.id, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())

# 5. TARJIMA QILISH (Callback Query)
@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    chat_id = call.message.chat.id
    original_text = user_data.get(chat_id)

    if original_text:
        try:
            bot.answer_callback_query(call.id, "⏳ Tayyorlanmoqda...")
            target_lang = LANGS[lang_code]
            
            # Google bloklamasligi uchun qisqa pauza
            time.sleep(0.3)

            # Tarjima mantiqi: Avval 'uz' deb urinadi, natija o'zgarmasa 'auto' rejimiga o'tadi
            translated = GoogleTranslator(source='uz', target=target_lang).translate(original_text)

            if translated.lower() == original_text.lower():
                translated = GoogleTranslator(source='auto', target=target_lang).translate(original_text)

            result_text = f"✅ {target_lang.capitalize()} tilida:\n\n{translated}"
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=result_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            error_str = str(e).lower()
            if "too many requests" in error_str:
                bot.edit_message_text("⚠️ Server band. Birozdan keyin urinib ko'ring.", chat_id, call.message.message_id)
            else:
                bot.edit_message_text("❌ Tarjima xatosi yuz berdi.", chat_id, call.message.message_id)
    else:
        bot.edit_message_text("❌ Matn topilmadi. Qaytadan yuboring.", chat_id, call.message.message_id)

# 6. ASOSIY ISHGA TUSHIRISH QISMI
if name == "main":
    # Web-serverni alohida oqimda (Thread) boshlash
    server_thread = Thread(target=run_web_server)
    server_thread.start()
    
    print("Bot va Web-server muvaffaqiyatli ishga tushdi...")
    
    # Botni polling rejimida ishga tushirish
    bot.remove_webhook()
    bot.polling(none_stop=True)
