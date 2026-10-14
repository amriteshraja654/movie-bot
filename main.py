import os
import asyncio
from pyrogram import Client, filters
import yt_dlp
from flask import Flask
from threading import Thread

# Flask वेब सर्वर (Render को चालू रखने के लिए)
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "🤖 Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Pyrogram बॉट सेटअप (अपनी API_ID, API_HASH और BOT_TOKEN यहाँ डालें)
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

bot = Client(
    "movie_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👋 नमस्कार!\n\n🎬 कोई भी वीडियो या मूवी लिंक भेजें, मैं उसे डाउनलोड करके आपको भेज दूंगा।"
    )

@bot.on_message(filters.text & ~filters.command("start"))
async def download_media(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text("⏳ डाउनलोडिंग शुरू हो रही है, कृपया प्रतीक्षा करें...")
    
    file_path = None
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True
        }
        
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                return ydl.prepare_filename(info), info.get('title', 'Video')

        file_path, title = await asyncio.to_thread(run_ydl)
        
        await status_msg.edit_text("📤 वीडियो तैयार है! अब टेलीग्राम पर भेजा जा रहा है...")
        
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎬 **{title}**"
        )
        await status_msg.delete()
        
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ डाउनलोड करने में समस्या आई:\n`{str(e)[:150]}`")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("🚀 वेब सर्वर और बॉट शुरू हो रहे हैं...")
    keep_alive()
    bot.run()
    
