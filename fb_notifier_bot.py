import os
import requests
import xml.etree.ElementTree as ET
import asyncio
import json
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID     = os.environ.get("CHANNEL_ID", "UC4_ot3DUs7i0tCj2uwZrG6A")
CHECK_INTERVAL = 60
USERS_FILE     = "subscribers.json"
RSS_URL        = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
CREDIT         = "👨‍💻 Developer : RH .RATUL"
seen_videos    = set()

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    users = load_users()
    if user.id not in users:
        users.add(user.id)
        save_users(users)
        msg = (
            f"✅ *স্বাগতম {user.first_name}!*\n\n"
            "আপনি সফলভাবে subscribe করেছেন। 🔔\n"
            "নতুন ভিডিও আসলে notification পাবেন!\n\n"
            f"{CREDIT}"
        )
    else:
        msg = f"✅ *{user.first_name}, আপনি আগে থেকেই subscribed!*\n\n{CREDIT}"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user  = update.effective_user
    users = load_users()
    if user.id in users:
        users.discard(user.id)
        save_users(users)
        msg = (
            f"❌ *{user.first_name}, আপনি unsubscribe করেছেন।*\n\n"
            "আর notification পাবেন না।\n"
            "আবার পেতে /start দিন।\n\n"
            f"{CREDIT}"
        )
    else:
        msg = "আপনি subscribe করেননি। /start দিন।"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    await update.message.reply_text(
        f"👥 মোট subscriber: *{len(users)}* জন\n\n{CREDIT}",
        parse_mode="Markdown"
    )

def get_latest_videos():
    response = requests.get(RSS_URL, timeout=10)
    root     = ET.fromstring(response.content)
    ns       = {"atom": "http://www.w3.org/2005/Atom"}
    videos   = []
    for entry in root.findall("atom:entry", ns):
        videos.append({
            "id"   : entry.find("atom:id", ns).text,
            "title": entry.find("atom:title", ns).text,
            "link" : entry.find("atom:link", ns).attrib["href"],
        })
    return videos

async def poll_youtube(app):
    print("🔄 YouTube polling শুরু হয়েছে...")
    videos = get_latest_videos()
    for v in videos:
        seen_videos.add(v["id"])
    print(f"ℹ️ {len(seen_videos)} টি পুরানো ভিডিও skip করা হয়েছে।")
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            videos = get_latest_videos()
            for video in videos:
                if video["id"] not in seen_videos:
                    print(f"🆕 নতুন ভিডিও: {video['title']}")
                    users = load_users()
                    message = (
                        "🔔 *নতুন ভিডিও আপলোড হয়েছে!*\n"
                        "━━━━━━━━━━━━━━━━━━\n"
                        f"🎬 *{video['title']}*\n\n"
                        f"🔗 [▶️ ভিডিও দেখুন]({video['link']})\n\n"
                        "━━━━━━━━━━━━━━━━━━\n"
                        f"{CREDIT}"
                    )
                    for user_id in list(users):
                        try:
                            await app.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"❌ {user_id}: {e}")
                    seen_videos.add(video["id"])
        except Exception as e:
            print(f"❌ Polling error: {e}")

async def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Notifier Bot চালু হয়েছে")
    print("  Developer : RH .RATUL")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("count", count))
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await poll_youtube(app)

if __name__ == "__main__":
    asyncio.run(main())
