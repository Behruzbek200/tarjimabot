import os
import telebot
import requests
import speech_recognition as sr
import pytesseract
from PIL import Image
import io
from pydub import AudioSegment
from googletrans import Translator
from gtts import gTTS
import PyPDF2
import docx
from flask import Flask, request

TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')
bot = telebot.TeleBot(TOKEN)
translator = Translator()
recognizer = sr.Recognizer()
app = Flask(__name__)

LANGUAGES = {'uz': 'O\'zbekcha', 'en': 'Inglizcha', 'ru': 'Ruscha', 'tr': 'Turkcha', 'ar': 'Arabcha'}

# --- Klaviaturalar ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🌐 10 ta tilga tarjima", "🎤 Ovozli Tarjima")
    markup.row("🖼 Rasmda matn o'qish", "📂 Hujjat Tarjimasi")
    return markup

def lang_inline():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btns = [telebot.types.InlineKeyboardButton(text=v, callback_data=f"tr_{k}") for k, v in LANGUAGES.items()]
    markup.add(*btns)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Salom! Men API-larsiz ishlaydigan mukkammal tarjimonman.", reply_markup=main_menu())

# --- 🖼 RASM TAHLILI (Pytesseract - API-siz) ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "🔍 Rasmdagi matn o'qilmoqda...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded_file))
        
        # Pytesseract yordamida matnni aniqlash
        text = pytesseract.image_to_string(img, lang='eng+rus') # O'zbekcha uchun eng+rus yaqin
        
        if text.strip():
            bot.edit_message_text(f"📝 **Aniqlangan matn:**\n\n{text[:1000]}\n\nQaysi tilga tarjima qilamiz?", 
                                  message.chat.id, msg.message_id, reply_markup=lang_inline())
        else:
            bot.edit_message_text("❌ Rasmdan matn topilmadi.", message.chat.id, msg.message_id)
    except:
        bot.edit_message_text("❌ Xatolik: Serverda Tesseract o'rnatilmagan bo'lishi mumkin.", message.chat.id, msg.message_id)

# --- 📂 HUJJAT TARJIMASI (PDF/Word) ---
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_ext = message.document.file_name.split('.')[-1].lower()
    msg = bot.reply_to(message, "📄 Hujjat o'qilmoqda...")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    text = ""
    if file_ext == 'pdf':
        reader = PyPDF2.PdfReader(io.BytesIO(downloaded_file))
        text = " ".join([page.extract_text() for page in reader.pages[:3]]) # Dastlabki 3 bet
    elif file_ext == 'docx':
        doc = docx.Document(io.BytesIO(downloaded_file))
        text = " ".join([p.text for p in doc.paragraphs])

    if text:
        bot.edit_message_text(f"📄 **Hujjatdan parcha:**\n\n{text[:500]}...", 
                              message.chat.id, msg.message_id, reply_markup=lang_inline())
    else:
        bot.edit_message_text("❌ Hujjatni o'qib bo'lmadi.", message.chat.id, msg.message_id)

# --- 🔊 TALLAFUZ VA TARJIMA ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('tr_'))
def translate_callback(call):
    lang = call.data.split('_')[1]
    # Matnni ajratib olish (biroz soddalashtirilgan)
    text = call.message.text.split('\n\n')[1] if '\n\n' in call.message.text else call.message.text
    
    translated = translator.translate(text, dest=lang).text
    bot.send_message(call.message.chat.id, f"✅ **Tarjima ({LANGUAGES[lang]}):**\n\n{translated}")
    
    try:
        tts = gTTS(translated[:200], lang=lang if lang != 'uz' else 'tr')
        tts.save("s.mp3")
        with open("s.mp3", "rb") as f:
            bot.send_voice(call.message.chat.id, f)
        os.remove("s.mp3")
    except: pass

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    return "API-siz Bot Online!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
