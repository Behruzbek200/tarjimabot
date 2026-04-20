import os, telebot, requests, io, PyPDF2, docx, os
import speech_recognition as sr
import pytesseract
from PIL import Image
from pydub import AudioSegment
from deep_translator import GoogleTranslator
from gtts import gTTS
from flask import Flask, request

TOKEN = os.environ.get('BOT_TOKEN')
RENDER_URL = os.environ.get('RENDER_URL')
bot = telebot.TeleBot(TOKEN)
recognizer = sr.Recognizer()
app = Flask(__name__)

# 10 ta asosiy til (Rasm va Ovoz uchun)
MAIN_LANGS = {
    'uz': 'uzbek', 'en': 'english', 'ru': 'russian', 'tr': 'turkish', 
    'ar': 'arabic', 'de': 'german', 'fr': 'french', 'ko': 'korean', 
    'ja': 'japanese', 'es': 'spanish'
}

# Hujjatlar uchun barcha tillar ro'yxati (DeepTranslator yordamida)
ALL_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)

def main_menu():
    m = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.row("🖼 Rasm tahlili", "🎤 Ovozli tarjima")
    m.row("📂 Hujjat tarjimasi", "🌐 Matn yuboring")
    return m

def lang_inline(langs_dict, prefix="tr_"):
    m = telebot.types.InlineKeyboardMarkup(row_width=3)
    btns = []
    # Faqat birinchi 15-20 tasini ko'rsatamiz (Telegram limiti uchun)
    for k, v in list(langs_dict.items())[:18]: 
        btns.append(telebot.types.InlineKeyboardButton(text=v.capitalize(), callback_data=f"{prefix}{k}"))
    m.add(*btns)
    return m

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "👋 Mukkammal Tarjimon botiga xush kelibsiz!", reply_markup=main_menu())

# --- 🎤 OVOZLI TARJIMA ---
@bot.message_handler(content_types=['voice'])
def handle_voice(m):
    msg = bot.reply_to(m, "⏳ Ovoz tahlil qilinmoqda...")
    try:
        f_info = bot.get_file(m.voice.file_id)
        f_content = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{f_info.file_path}").content
        with open("v.ogg", "wb") as f: f.write(f_content)
        AudioSegment.from_ogg("v.ogg").export("v.wav", format="wav")
        with sr.AudioFile("v.wav") as source:
            text = recognizer.recognize_google(recognizer.record(source), language="uz-UZ")
        bot.edit_message_text(f"🎤 **Siz dedingiz:**\n{text}\n\nQaysi tilga tarjima qilamiz?", m.chat.id, msg.message_id, reply_markup=lang_inline(MAIN_LANGS))
    except: bot.edit_message_text("❌ Ovozni tushunib bo'lmadi.", m.chat.id, msg.message_id)

# --- 🖼 RASM TAHLILI ---
@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    msg = bot.reply_to(m, "🔍 Matn o'qilmoqda...")
    try:
        img = Image.open(io.BytesIO(bot.download_file(bot.get_file(m.photo[-1].file_id).file_path)))
        text = pytesseract.image_to_string(img, lang='eng+rus')
        if text.strip():
            bot.edit_message_text(f"📝 **Aniqlangan matn:**\n`{text[:500]}`\n\nTarjima tilini tanlang:", m.chat.id, msg.message_id, reply_markup=lang_inline(MAIN_LANGS))
        else: bot.edit_message_text("❌ Matn topilmadi.", m.chat.id, msg.message_id)
    except: bot.edit_message_text("❌ Rasmda xatolik.", m.chat.id, msg.message_id)

# --- 📂 HUJJAT TARJIMASI ---
@bot.message_handler(content_types=['document'])
def handle_docs(m):
    file_ext = m.document.file_name.split('.')[-1].lower()
    if file_ext not in ['pdf', 'docx']:
        bot.reply_to(m, "❌ Faqat PDF yoki DOCX yuboring.")
        return
    msg = bot.reply_to(m, "📄 Hujjat yuklanmoqda...")
    try:
        f_content = bot.download_file(bot.get_file(m.document.file_id).file_path)
        text = ""
        if file_ext == 'pdf':
            reader = PyPDF2.PdfReader(io.BytesIO(f_content))
            text = " ".join([p.extract_text() for p in reader.pages[:2]])
        else:
            doc = docx.Document(io.BytesIO(f_content))
            text = " ".join([p.text for p in doc.paragraphs[:10]])
        
        bot.edit_message_text(f"📄 **Hujjat matni:**\n`{text[:400]}`\n\n100 dan ortiq tillardan birini tanlang:", m.chat.id, msg.message_id, reply_markup=lang_inline(ALL_LANGS, "doc_"))
    except: bot.edit_message_text("❌ Faylni o'qib bo'lmadi.", m.chat.id, msg.message_id)

# --- 🌐 TARJIMA VA OVOZLI QILISH ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    prefix = call.data.split('_')[0]
    lang_code = call.data.split('_')[1]
    
    # Matnni xabardan tozalab olish
    text = call.message.text.split('\n\n')[0].replace('🎤 Siz dedingiz:', '').replace('📝 Aniqlangan matn:', '').replace('📄 Hujjat matni:', '')

    try:
        target_lang = MAIN_LANGS[lang_code] if prefix == "tr" else ALL_LANGS[lang_code]
        tr = GoogleTranslator(source='auto', target=target_lang).translate(text)
        
        bot.send_message(call.message.chat.id, f"✅ **Tarjima:**\n\n{tr}")
        
        # Faqat 10 ta asosiy til uchun ovozli talaffuz qilamiz
        if prefix == "tr":
            tts_lang = lang_code if lang_code in ['en', 'ru', 'tr', 'fr', 'de', 'es'] else 'en'
            tts = gTTS(tr[:200], lang=tts_lang)
            tts.save("s.mp3")
            with open("s.mp3", "rb") as f:
                bot.send_voice(call.message.chat.id, f, caption="🔊 Talaffuzi")
            os.remove("s.mp3")
    except:
        bot.send_message(call.message.chat.id, "❌ Tarjima xatosi.")

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    return "Bot Online!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
