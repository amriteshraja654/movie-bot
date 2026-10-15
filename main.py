import os
import asyncio
from pyrogram import Client, filters
import yt_dlp
from flask import Flask
from threading import Thread

# 1. Flask वेब सर्वर (Render को Live रखने के लिए)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# 2. Telegram Bot कॉन्फ़िगरेशन
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

bot = Client(
    "movie_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("👋 नमस्ते! Vegamovies या किसी भी मूवी वेबसाइट का **डायरेक्ट डाउनलोड लिंक** (जैसे PixelDrain या HubCloud का लिंक) भेजें, मैं उसे डाउनलोड करके फाइल भेज दूंगा।")

@bot.on_message(filters.text & ~filters.command("start"))
async def download_media(client, message):
    url = message.text.strip()
    
    # चेक करें कि यूजर ने वैध लिंक भेजा है या नहीं
    if not url.startswith(("http://", "https://")):
        await message.reply_text("⚠️ कृपया केवल किसी वेबसाइट का **वैध डायरेक्ट लिंक (URL)** भेजें!")
        return

    status_msg = await message.reply_text("⏳ लिंक से वीडियो/मूवी डाउनलोड की जा रही है...")
    
    file_path = None
    try:
        os.makedirs("downloads", exist_ok=True)
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'geo_bypass': True
        }
        
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                return ydl.prepare_filename(info)

        # बैकग्राउंड में सुरक्षित डाउनलोड
        file_path = await asyncio.to_thread(run_ydl)

        await status_msg.edit_text("📤 डाउनलोड पूरा हो गया है, अब टेलीग्राम पर फाइल भेज रहा हूँ...")

        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎬 **{os.path.basename(file_path)}**"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ डाउनलोड करने में समस्या आई:\n{e}")
    finally:
        # सर्वर स्पेस खाली रखने के लिए लोकल फाइल हटाना
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("🚀 वेब सर्वर शुरू हो रहा है...")
    keep_alive()
    print("🤖 टेलीग्राम बॉट शुरू हो रहा है...")
    bot.run()
    
