import asyncio

# Python 3.11+ के लिए इवेंट लूप सेटअप
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
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
    await message.reply_text("👋 नमस्ते! किसी भी गाने, वीडियो या मूवी का **नाम** लिखकर भेजें, मैं उसे डाउनलोड करके आपके पास भेज दूंगा।")

@bot.on_message(filters.text & ~filters.command("start"))
async def download_media(client, message):
    query = message.text.strip()
    
    status_msg = await message.reply_text(f"🔍 '{query}' को खोजा और डाउनलोड किया जा रहा है...")
    
    file_path = None
    try:
        os.makedirs("downloads", exist_ok=True)
        
        # नाम से सर्च करके डाउनलोड करने की कमांड
        search_target = f"ytsearch1:{query}"
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'geo_bypass': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }
        
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_target, download=True)
                if 'entries' in info:
                    if not info['entries']:
                        raise Exception("कोई वीडियो नहीं मिला।")
                    info = info['entries'][0]
                return ydl.prepare_filename(info)

        # बैकग्राउंड में डाउनलोड प्रक्रिया
        file_path = await asyncio.to_thread(run_ydl)

        await status_msg.edit_text("📤 डाउनलोड पूरा हो गया है, अब टेलीग्राम पर फाइल भेज रहा हूँ...")

        # टेलीग्राम पर वीडियो भेजना
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
    
