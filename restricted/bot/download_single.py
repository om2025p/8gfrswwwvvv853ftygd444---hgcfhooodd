# Download a single link and send it to the owner
import sys
import os
import asyncio
from decouple import config

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

async def main_download():
    # Load inputs
    link = os.environ.get("TELEGRAM_LINK") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not link:
        print("Error: No link provided in TELEGRAM_LINK or arguments.")
        return

    print("Connecting to Telegram clients...")
    # On import, main/__init__.py starts bot, userbot and Bot!
    from main import bot, userbot, Bot, AUTH

    owner_id = AUTH or config("OWNER_ID", default=None, cast=int)
    if not owner_id:
        print("Error: OWNER_ID is not configured. Cannot send to owner.")
        return

    print(f"Starting single download for link: {link} to owner: {owner_id}")

    # Send starting message to owner
    msg = await Bot.send_message(owner_id, f"📥 *شروع دانلود لینک درخواستی:*\n`{link}`\n\n🕒 لطفا صبور باشید...")

    from main.plugins.pyroplug import get_msg
    from main.plugins.helpers import get_link, join

    try:
        if 't.me/+' in link or 't.me/joinchat/' in link:
            # Join channel
            res = await join(userbot, link)
            await Bot.edit_message_text(owner_id, msg.id, f"🔑 *نتیجه ورود به کانال خصوصی:*\n{res}")
        else:
            # Download and send
            await get_msg(userbot, Bot, bot, owner_id, msg.id, link, 0)
            await Bot.send_message(owner_id, "✅ *دانلود و ارسال با موفقیت پایان یافت!*")
    except Exception as e:
        print(f"Error during execution: {e}")
        try:
            await Bot.send_message(owner_id, f"❌ *خطا در پردازش لینک تلگرام:*\n`{str(e)}`")
        except:
            pass

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main_download())
