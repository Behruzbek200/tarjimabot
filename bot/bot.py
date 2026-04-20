import os
import telebot
from deep_translator import GoogleTranslator

# 1. TOKEN va boshqa sozlamalarni ENV orqali olamiz
# Render Dashboard'da BOT_TOKEN kalitini qo'shishni unutmang
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=False)

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
    bot.send_message(message.chat.id, "👋 Salom! Istalgan tilda matn yuboring:")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_data[message.chat.id] = message.text
    bot.send_message(message.chat.id, "👇 Qaysi tilga tarjima qilamiz?", reply_markup=lang_inline())

@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang_code = call.data.split('_')[1]
    chat_id = call.message.chat.id
    original_text = user_data.get(chat_id)

    if original_text:
        try:
            bot.answer_callback_query(call.id, "⏳ Tarjima qilinmoqda...")
            target_lang = LANGS[lang_code]

            # Mantiq: Avval o'zbekcha deb tekshiradi, o'xshamasa 'auto' rejimiga o'tadi
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
            bot.edit_message_text(f"❌ Tarjima xatosi: {str(e)[:30]}", chat_id, call.message.message_id)
    else:
        bot.edit_message_text("❌ Matn topilmadi. Qaytadan yuboring.", chat_id, call.message.message_id)

if name == "main":
    print("Bot Environment Variables orqali ishga tushdi...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
