import os
import asyncio
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
import yt_dlp

# --- छोटा वेब सर्वर (Render के लिए जरूरी) ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- टेलीग्राम बॉट कोड ---
API_ID = 33941688
API_HASH = "12610a9246f01ea25abd0d76af3e66"
BOT_TOKEN = "8910426207:AAFhmVFuu3KEQkjtTJVHMSMPQkP2kc5Sm_k"

bot = Client(
    "real_video_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    user_name = message.from_user.first_name if message.from_user else "दोस्त"
    await message.reply_text(
        f"🎬 **नमस्ते {user_name}!**\n\n"
        "📥 यह 24/7 क्लाउड बॉट है! अब आप कभी भी कोई भी **मूवी, गाने या वीडियो का नाम** यहाँ भेज सकते हैं:"
    )

@bot.on_message(filters.text & ~filters.command("start"))
async def download_and_send_video(client, message):
    query = message.text
    status_msg = await message.reply_text(
        f"⏳ **'{query}'** को क्लाउड सर्वर से खोजा और डाउनलोड किया जा रहा है...\nकृपया थोड़ा इंतजार करें।"
    )
    
    file_path = f"video_{message.chat.id}_{message.id}.mp4"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'default_search': 'ytsearch1:',
        'noplaylist': True,
        'max_filesize': 1900 * 1024 * 1024,
        'quiet': True
    }
    
    try:
        def run_ydl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if 'entries' in info:
                    info = info['entries'][0]
                return info.get('title', query)

        title = await asyncio.to_thread(run_ydl)
            
        await status_msg.edit_text("📤 वीडियो तैयार है! अब टेलीग्राम पर भेजा जा रहा है...")
        
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=(
                f"🎬 **{title}**\n\n"
                "✅ ऊपर वीडियो के कोने में 3 डॉट्स (⋮) पर क्लिक करके **'Save to Gallery'** करें।"
            )
        )
        await status_msg.delete()
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await status_msg.edit_text(
            f"❌ डाउनलोड करने में समस्या आई:\n`{str(e)[:150]}`"
        )
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("🚀 वेब सर्वर और बॉट शुरू हो रहे हैं...")
    keep_alive()
    bot.run()
