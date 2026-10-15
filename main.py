import asyncio
import os
from pyrogram import Client, filters
import yt_dlp
from flask import Flask
from threading import Thread

# Flask वेब सर्वर (Render पर 24/7 लाइव रखने के लिए)
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# Telegram Bot कॉन्फ़िगरेशन
# (यहाँ अपनी API_ID, API_HASH और BOT_TOKEN डालें या एनवायरनमेंट वेरिएbles का इस्तेमाल करें)
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

bot = Client(
    "movie_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("👋 नमस्ते! कोई भी मूवी या वीडियो का नाम/लिंक भेजें, मैं उसे डाउनलोड करके भेज दूंगा।")

@bot.on_message(filters.text & ~filters.command("start"))
async def download_media(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text("⏳ डाउनलोडिंग शुरू हो रही है...")
    
    file_path = None
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True
        }
        
        def run_yol():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                return ydl.prepare_filename(info)

        file_path = await asyncio.to_thread(run_yol)

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
    
    # इवेंट लूप कॉन्फ्लिक्ट को पूरी तरह हल करने का सुरक्षित तरीका
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(bot.start())
        else:
            loop.run_until_complete(bot.start())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.start())
        
    import time
    while True:
        time.sleep(1)
