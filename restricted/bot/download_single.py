# Download a single link and send it to the owner
import sys
import os
import asyncio
import time
from decouple import config

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

async def safe_send_message(owner_id, text, disable_web_page_preview=False):
    from main import Bot, bot, userbot
    try:
        # Try Pyrogram Bot first
        return await Bot.send_message(owner_id, text, disable_web_page_preview=disable_web_page_preview)
    except Exception as e:
        print(f"DEBUG: Bot.send_message failed ({e}). Trying Telethon bot...")
        try:
            return await bot.send_message(owner_id, text, link_preview=not disable_web_page_preview)
        except Exception as e2:
            print(f"DEBUG: Telethon bot.send_message failed ({e2}). Trying userbot...")
            try:
                return await userbot.send_message(owner_id, text, disable_web_page_preview=disable_web_page_preview)
            except Exception as e3:
                print(f"DEBUG: All message sending fallbacks failed: {e3}")
                raise e3

async def safe_edit_message(owner_id, msg_obj, text, disable_web_page_preview=False):
    from main import Bot, bot, userbot
    if not msg_obj:
        return await safe_send_message(owner_id, text, disable_web_page_preview)

    is_telethon = hasattr(msg_obj, 'client') or hasattr(msg_obj, 'respond')
    if is_telethon:
        try:
            return await msg_obj.edit(text, link_preview=not disable_web_page_preview)
        except Exception as e:
            print(f"DEBUG: Telethon edit failed ({e}). Sending new message...")
            return await safe_send_message(owner_id, text, disable_web_page_preview)
    else:
        try:
            return await msg_obj.edit_text(text, disable_web_page_preview=disable_web_page_preview)
        except Exception as e:
            print(f"DEBUG: Pyrogram edit_text failed ({e}). Trying Bot.edit_message_text...")
            try:
                return await Bot.edit_message_text(owner_id, msg_obj.id, text, disable_web_page_preview=disable_web_page_preview)
            except Exception as e2:
                print(f"DEBUG: Pyrogram Bot.edit_message_text failed ({e2}). Sending new message...")
                return await safe_send_message(owner_id, text, disable_web_page_preview)

async def main_download():
    # Load inputs
    link = os.environ.get("TELEGRAM_LINK") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not link:
        print("Error: No link provided in TELEGRAM_LINK or arguments.")
        return

    print("Connecting to Telegram clients...")
    # On import, main/__init__.py creates client instances without auto-starting if in async context
    from main import bot, userbot, Bot, AUTH, BOT_TOKEN

    import inspect

    # Start Telethon Bot safely under async context
    try:
        if not bot.is_connected():
            print("Starting Telethon bot dynamically...")
            await bot.connect()
            if not await bot.is_user_authorized():
                await bot.sign_in(bot_token=BOT_TOKEN)
    except Exception as e:
        print(f"Error starting Telethon bot dynamically: {e}")

    # Start Pyrogram clients (attempt unconditionally to bypass stale is_connected states)
    for client_obj in [userbot, Bot]:
        name = getattr(client_obj, 'name', 'Client')
        try:
            print(f"Starting client dynamically: {name}")
            res = client_obj.start()
            if inspect.iscoroutine(res):
                await res
        except Exception as e:
            err_msg = str(e)
            print(f"Error starting client dynamically: {err_msg}")

            # Format and present friendly diagnostic errors instead of failing silently or throwing obscure tracebacks
            if "AUTH_KEY_DUPLICATED" in err_msg:
                friendly_err = (
                    f"\n❌ خطای امنیتی تلگرام [406 AUTH_KEY_DUPLICATED]:\n"
                    f"رئیس بزرگ، سشن تلگرام شما (SESSION_STRING) همزمان در جای دیگری فعال است یا باطل شده است!\n"
                    f"لطفاً ربات‌ها یا اسکریپت‌های دیگر خود را خاموش کنید و یا با استفاده از @TgDevToolBot یک سشن جدید بسازید و جایگزین کنید.\n"
                )
                print(friendly_err)
                sys.exit(1)
            elif "FLOOD_WAIT" in err_msg or "FLOOD_WAIT_" in err_msg:
                friendly_err = (
                    f"\n❌ خطای محدودیت تلگرام [420 FLOOD_WAIT]:\n"
                    f"تلگرام اکانت شما را به دلیل درخواست‌های مکرر و فلو لیمیت به طور موقت محدود کرده است.\n"
                    f"لطفاً چند دقیقه صبر کنید و سپس دوباره تلاش نمایید.\n"
                )
                print(friendly_err)
                sys.exit(1)
            elif "already started" in err_msg.lower() or "active" in err_msg.lower():
                # Ignore harmless already started warnings
                pass
            else:
                friendly_err = (
                    f"\n❌ خطا در راه‌اندازی کلاینت {name}:\n"
                    f"متن خطا: {err_msg}\n"
                    f"لطفاً مطمئن شوید API_ID، API_HASH و سشن معتبر هستند.\n"
                )
                print(friendly_err)
                sys.exit(1)

    try:
        owner_id = AUTH or config("OWNER_ID", default=None, cast=int)
        if not owner_id:
            print("Error: OWNER_ID is not configured. Cannot send to owner.")
            return

        # Force resolve owner_id with userbot to populate internal cache
        try:
            print(f"DEBUG: Resolving owner_id ({owner_id}) using userbot...")
            await userbot.get_users(owner_id)
            print("DEBUG: Successfully resolved owner_id using userbot.")
        except Exception as ex:
            print(f"DEBUG: Warning resolving owner_id with userbot: {ex}")

        # Check if this is a deep Telegram search request
        if isinstance(link, str) and link.startswith("search:"):
            query = link[7:].strip()
            print(f"Starting deep Telegram search for: {query} for owner: {owner_id}")

            # Send starting message to owner
            msg = await safe_send_message(owner_id, f"🔎 *در حال جستجوی عمیق کلمه «{query}» در سرورهای رسمی تلگرام (تا سقف ۱۰۰۰ نتیجه)...*\n\n🕒 لطفا صبور باشید...")

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

                # REVOLUTIONARY FIX: Also search globally in public messages to find even more relevant channels!
                try:
                    print("Running global public message search to extract more relevant channels...")
                    async for message in userbot.search_global_messages(query=query, limit=1000):
                        if message.chat and getattr(message.chat, 'username', None):
                            title = getattr(message.chat, 'title', "بدون عنوان")
                            username = getattr(message.chat, 'username')
                            members = getattr(message.chat, 'participants_count', None) or getattr(message.chat, 'members_count', None)

                            # Add if not already in channels list
                            if not any(username.lower() == c[1].lower() for c in channels):
                                channels.append((title, username, members))
                except Exception as ex:
                    print(f"Global message search failed or ignored: {ex}")

                if not channels:
                    await safe_edit_message(owner_id, msg, f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
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
                            await safe_edit_message(owner_id, msg, response_text, disable_web_page_preview=True)
                        else:
                            await safe_send_message(owner_id, response_text, disable_web_page_preview=True)
                        response_text = f"🎯 *ادامه نتایج جستجو برای «{query}» (بخش {chunk_num + 1}):*\n\n"
                        chunk_num += 1
                    response_text += line

                if response_text:
                    if chunk_num == 1:
                        await safe_edit_message(owner_id, msg, response_text, disable_web_page_preview=True)
                    else:
                        await safe_send_message(owner_id, response_text, disable_web_page_preview=True)
                else:
                    if chunk_num > 1:
                        pass
                    else:
                        try:
                            if hasattr(msg, 'delete'):
                                await msg.delete()
                            else:
                                await Bot.delete_messages(owner_id, msg.id)
                        except:
                            pass

                await safe_send_message(owner_id, "✅ *جستجوی عمیق تلگرام با موفقیت کامل شد!*")

            except Exception as e:
                print(f"Error during execution of search: {e}")
                try:
                    await safe_edit_message(owner_id, msg, f"❌ *خطا در اجرای جستجوی عمیق تلگرام:*\n`{str(e)}`")
                except:
                    pass
            return

        print(f"Starting single download for link: {link} to owner: {owner_id}")

        # Send starting message to owner
        msg = await safe_send_message(owner_id, f"📥 *شروع دانلود لینک درخواستی:*\n`{link}`\n\n🕒 لطفا صبور باشید...")

        from main.plugins.pyroplug import get_msg
        from main.plugins.helpers import get_link, join

        try:
            if 't.me/+' in link or 't.me/joinchat/' in link:
                # Join channel
                res = await join(userbot, link)
                await safe_edit_message(owner_id, msg, f"🔑 *نتیجه ورود به کانال خصوصی:*\n{res}")
            else:
                # Download and send
                await get_msg(userbot, Bot, bot, owner_id, msg.id, link, 0)
                await safe_send_message(owner_id, "✅ *دانلود و ارسال با موفقیت پایان یافت!*")
        except Exception as e:
            print(f"Error during execution: {e}")
            try:
                await safe_send_message(owner_id, f"❌ *خطا در پردازش لینک تلگرام:*\n`{str(e)}`")
            except:
                pass
    finally:
        print("Stopping Pyrogram clients before exit...")
        for client_obj in [userbot, Bot]:
            try:
                # Use is_connected property method
                is_conn = client_obj.is_connected
                if inspect.iscoroutine(is_conn):
                    is_conn = await is_conn

                if is_conn:
                    print(f"Stopping client dynamically: {client_obj.name if hasattr(client_obj, 'name') else 'Client'}")
                    res = client_obj.stop()
                    if inspect.iscoroutine(res):
                        await res
            except Exception as e:
                print(f"Error stopping client: {e}")

        try:
            if bot.is_connected():
                print("Stopping Telethon bot...")
                res = bot.disconnect()
                if inspect.iscoroutine(res):
                    await res
        except Exception as e:
            print(f"Error disconnecting Telethon: {e}")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main_download())
