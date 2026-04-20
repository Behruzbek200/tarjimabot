import telebot
from deep_translator import GoogleTranslator

# 1. TOKENNI TEKSHIRING
TOKEN = '8165546119:AAEifJ5hSmGN3aIEoJM9Bd1IlVNeujKDxKo'
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

            # 1-QADAM: Avval o'zbekcha deb o'ylab tarjima qilamiz
            translated = GoogleTranslator(source='uz', target=target_lang).translate(original_text)

            # 2-QADAM: Agar tarjima matni bilan bir xil bo'lib qolsa, demak bu o'zbekcha emas
            # U holda 'auto' rejimida qayta tarjima qilamiz
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
        bot.edit_message_text("❌ Matn topilmadi.", chat_id, call.message.message_id)

if name == "main":
    print("Bot 100% universal rejimda ishga tushdi...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
