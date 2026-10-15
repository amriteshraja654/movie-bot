import asyncio

# Python 3.11+ के लिए इवेंट लूप सेटअप (सबसे ऊपर होना जरूरी है)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
from pyrogram import Client, filters
import yt_dlp
from flask import Flask
from threading import Thread

# 1. Flask वेब सर्वर (Render को Live रखने के लिए)
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# 2. Telegram Bot कॉन्फ़िगरेशन (Render के Environment Variables से लेगा)
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
    await message.reply_text("👋 नमस्ते! कोई भी मूवी या वीडियो का नाम या लिंक भेजें, मैं उसे डाउनलोड करके भेज दूंगा।")

@bot.on_message(filters.text & ~filters.command("start"))
async def download_media(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text(f"⏳ '{query}' को ढूँढा और डाउनलोड किया जा रहा है...")
    
    file_path = None
    try:
        os.makedirs("downloads", exist_ok=True)
        
        search_query = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }
        
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                if 'entries' in info:
                    if not info['entries']:
                        raise Exception("कोई वीडियो नहीं मिला।")
                    info = info['entries'][0]
                return ydl.prepare_filename(info)

        file_path = await asyncio.to_thread(run_ydl)

        await status_msg.edit_text("📤 वीडियो तैयार है, अब टेलीग्राम पर भेज रहा हूँ...")

        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎬 **{os.path.basename(file_path)}**"
        )
        await status_msg.delete()

        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await status_msg.edit_text(f"❌ डाउनलोड करने में समस्या आई:\n{e}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("🚀 वेब सर्वर और बॉट शुरू हो रहे हैं...")
    keep_alive()
    bot.run()
    
