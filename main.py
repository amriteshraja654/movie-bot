import asyncio

# Python 3.11+ ke liye event loop setup
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import os
from pyrogram import Client, filters
import yt_dlp
from flask import Flask
from threading import Thread

# 1. Flask web server (Render ko live rakhne ke liye)
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

# 2. Telegram Bot configuration
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
    await message.reply_text("👋 Namaste! Aap kisi bhi Bollywood, Hollywood, Bhojpuri movie ya Web Series ka naam likhkar bhejein, main usey dhoondhakar aapke paas bhej dunga.")

@bot.on_message(filters.text & ~filters.command("start"))
async def download_media(client, message):
    user_input = message.text.strip()
    
    # Check karein ki link hai ya movie ka naam
    if user_input.startswith(("http://", "https://")):
        target = user_input
        status_msg = await message.reply_text(f"⏳ Diye gaye link se download kiya ja raha hai...")
    else:
        # Naam se search karne ke liye smart query
        target = f"ytsearch1:{user_input} full movie OR official trailer"
        status_msg = await message.reply_text(f"🔍 '{user_input}' ko khoja aur download kiya ja raha hai...")
    
    file_path = None
    try:
        os.makedirs("downloads", exist_ok=True)
        
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
                info = ydl.extract_info(target, download=True)
                if 'entries' in info:
                    if not info['entries']:
                        raise Exception("Koi video nahi mila.")
                    info = info['entries'][0]
                return ydl.prepare_filename(info)

        # Background mein file download hogi
        file_path = await asyncio.to_thread(run_ydl)

        await status_msg.edit_text("📤 Download pura ho gaya hai, ab Telegram par file bhej raha hoon...")

        # Telegram par video bhejna
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎬 **{os.path.basename(file_path)}**"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Download karne mein samasya aayi:\n{e}")
    finally:
        # Server space khali rakhne ke liye local file hatana
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("🚀 Web server shuru ho raha hai...")
    keep_alive()
    print("🤖 Telegram bot shuru ho raha hai...")
    bot.run()
    
