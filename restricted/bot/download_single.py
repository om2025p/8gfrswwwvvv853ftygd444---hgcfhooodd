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

    # Ensure Pyrogram clients are started (crucial for Pyrogram v2+ in async contexts)
    import inspect
    for client_obj in [userbot, Bot]:
        if not client_obj.is_connected:
            try:
                print(f"Starting client dynamically: {client_obj.name if hasattr(client_obj, 'name') else 'Client'}")
                res = client_obj.start()
                if inspect.iscoroutine(res):
                    await res
            except Exception as e:
                print(f"Error starting client dynamically: {e}")

    try:
        owner_id = AUTH or config("OWNER_ID", default=None, cast=int)
        if not owner_id:
            print("Error: OWNER_ID is not configured. Cannot send to owner.")
            return

        # Check if this is a deep Telegram search request
        if isinstance(link, str) and link.startswith("search:"):
            query = link[7:].strip()
            print(f"Starting deep Telegram search for: {query} for owner: {owner_id}")

            # Send starting message to owner
            msg = await Bot.send_message(owner_id, f"🔎 *در حال جستجوی عمیق کلمه «{query}» در سرورهای رسمی تلگرام (تا سقف ۱۰۰۰ نتیجه)...*\n\n🕒 لطفا صبور باشید...")

            try:
                from pyrogram.raw.functions.contacts import Search
                # Invoke raw global search with a limit of 1000
                found = await userbot.invoke(Search(q=query, limit=1000))

                channels = []
                if found and hasattr(found, 'chats'):
                    for chat in found.chats:
                        username = getattr(chat, 'username', None)
                        if username:
                            title = getattr(chat, 'title', "بدون عنوان")
                            members = getattr(chat, 'participants_count', None)
                            channels.append((title, username, members))

                if not channels:
                    await Bot.edit_message_text(owner_id, msg.id, f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
                    return

                # Format and send results in chunks if text gets too long
                response_text = f"🎯 *نتایج جستجوی رسمی تلگرام برای «{query}» (یافت شده: {len(channels)} کانال):*\n\n"
                chunk_num = 1
                for i, (title, username, members) in enumerate(channels, 1):
                    members_str = f" ({members:,} عضو)" if members is not None else ""
                    line = f"{i}. 📣 *{title}*\n   🔗 شناسه: @{username}{members_str}\n   👉 [ورود به کانال](https://t.me/{username})\n\n"

                    # Check if adding this exceeds Telegram's 4096 character limit
                    if len(response_text) + len(line) > 3900:
                        if chunk_num == 1:
                            await Bot.edit_message_text(owner_id, msg.id, response_text, disable_web_page_preview=True)
                        else:
                            await Bot.send_message(owner_id, response_text, disable_web_page_preview=True)
                        response_text = f"🎯 *ادامه نتایج جستجو برای «{query}» (بخش {chunk_num + 1}):*\n\n"
                        chunk_num += 1
                    response_text += line

                if response_text:
                    if chunk_num == 1:
                        await Bot.edit_message_text(owner_id, msg.id, response_text, disable_web_page_preview=True)
                    else:
                        await Bot.send_message(owner_id, response_text, disable_web_page_preview=True)
                else:
                    if chunk_num > 1:
                        pass
                    else:
                        await Bot.delete_messages(owner_id, msg.id)

                await Bot.send_message(owner_id, "✅ *جستجوی عمیق تلگرام با موفقیت کامل شد!*")

            except Exception as e:
                print(f"Error during execution of search: {e}")
                try:
                    await Bot.edit_message_text(owner_id, msg.id, f"❌ *خطا در اجرای جستجوی عمیق تلگرام:*\n`{str(e)}`")
                except:
                    pass
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
    finally:
        print("Stopping Pyrogram clients before exit...")
        for client_obj in [userbot, Bot]:
            if client_obj.is_connected:
                try:
                    print(f"Stopping client dynamically: {client_obj.name if hasattr(client_obj, 'name') else 'Client'}")
                    res = client_obj.stop()
                    if inspect.iscoroutine(res):
                        await res
                except Exception as e:
                    print(f"Error stopping client: {e}")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main_download())
