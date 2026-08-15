# Download a single link and send it to the owner
import sys
import os
import asyncio
import time
from decouple import config

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def send_channel_notice(text):
    token = os.environ.get("NOTIF_BOT_TOKEN") or config("NOTIF_BOT_TOKEN", default=None)
    chat_id = os.environ.get("NOTIF_CHAT_ID") or config("NOTIF_CHAT_ID", default=None)
    if not token or not chat_id:
        return
    import urllib.request, json
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            pass
    except Exception as e:
        print(f"DEBUG: send_channel_notice error: {e}")

async def safe_send_message(owner_id, text, disable_web_page_preview=False):
    from main import Bot, bot, userbot, BOT_TOKEN

    # 1. Try Pyrogram Bot FIRST so messages land directly in the Bot Chat with the user!
    try:
        if getattr(Bot, 'is_connected', False):
            return await Bot.send_message(owner_id, text, disable_web_page_preview=disable_web_page_preview)
    except Exception as e:
        print(f"DEBUG: Bot.send_message failed: {e}")

    # 2. Try Direct Telegram Bot API HTTP Request
    try:
        if BOT_TOKEN:
            import urllib.request, json
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': owner_id,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': disable_web_page_preview
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as resp:
                print("DEBUG: Direct Telegram Bot API sendMessage succeeded.")
                return True
    except Exception as e_api:
        print(f"DEBUG: Direct Telegram Bot API failed: {e_api}")

    # 3. Try Telethon Bot
    try:
        if bot.is_connected():
            return await bot.send_message(owner_id, text, link_preview=not disable_web_page_preview)
    except Exception as e2:
        print(f"DEBUG: Telethon bot.send_message failed: {e2}")

    # 4. Fallback to userbot (User Account -> Saved Messages)
    try:
        if getattr(userbot, 'is_connected', False):
            res = await userbot.send_message(owner_id, text, disable_web_page_preview=disable_web_page_preview)
            send_channel_notice("📢 رئیس بزرگ! به دلیل محدودیت موقت چند دقیقه‌ای تلگرام روی ربات اصلی، نتیجه جدید به پیام‌های ذخیره‌شده (Saved Messages) شما فرستاده شد. 💎")
            return res
    except Exception as e3:
        print(f"DEBUG: userbot fallback failed: {e3}")
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
                print(f"DEBUG: Pyrogram Bot.edit_message_text failed ({e2}). Trying userbot edit...")
                try:
                    return await userbot.edit_message_text(owner_id, msg_obj.id, text, disable_web_page_preview=disable_web_page_preview)
                except Exception as e3:
                    print(f"DEBUG: All edits failed. Sending new message...")
                    return await safe_send_message(owner_id, text, disable_web_page_preview)

def expand_persian_query(query):
    queries = [query]

    # 1. Handle "هام" suffix (e.g., عکسهام -> عکس, عکس هام, عکسهایم, عکس های من)
    if query.endswith("هام") and len(query) > 3:
        base = query[:-3]
        queries.extend([
            f"{base} هام",
            f"{base}هایم",
            f"{base} هایم",
            f"{base}های من",
            f"{base} های من",
            f"{base}ام",
            f"{base} ام"
        ])
    # 2. Handle "ام" suffix (e.g., عکسام -> عکس, عکسهام, عکس های من)
    elif query.endswith("ام") and len(query) > 2 and not query.endswith("هام"):
        base = query[:-2]
        queries.extend([
            f"{base} ام",
            f"{base}هام",
            f"{base} هام",
            f"{base}هایم",
            f"{base} هایم",
            f"{base}های من",
            f"{base} های من"
        ])
    # 3. Handle "هایم" suffix (e.g., عکسهایم -> عکس, عکسهام, عکس های من)
    elif query.endswith("هایم") and len(query) > 4:
        base = query[:-4]
        queries.extend([
            f"{base} هایم",
            f"{base}هام",
            f"{base} هام",
            f"{base}های من",
            f"{base} های من",
            f"{base}ام",
            f"{base} ام"
        ])
    # 4. Handle "های من" suffix (e.g., عکس های من -> عکسهام)
    elif "های من" in query:
        base = query.replace("های من", "").strip()
        queries.extend([
            f"{base}های من",
            f"{base}هام",
            f"{base} هام",
            f"{base}هایم",
            f"{base} هایم",
            f"{base}ام",
            f"{base} ام"
        ])
    # 5. Handle "هایم" with space "هایم"
    elif " هایم" in query:
        base = query.replace(" هایم", "").strip()
        queries.extend([
            f"{base}هایم",
            f"{base}هام",
            f"{base} هام",
            f"{base}های من",
            f"{base} های من",
            f"{base}ام",
            f"{base} ام"
        ])

    # Finglish / Transliteration mapping for extremely deep search results
    finglish_map = {
        "عکس": ["aks", "ax"],
        "عکسام": ["aksam", "axam"],
        "عکسهام": ["aksham", "axham", "akshaye", "axaye"],
        "عکس هام": ["aks ham", "ax ham"],
        "عکسهایم": ["akshaye", "axaye"],
        "عکس هایم": ["aks haye", "ax haye"],
        "عکس های من": ["aks haye man", "ax haye man"],
        "فیلم": ["film"],
        "فیلمام": ["filmam"],
        "فیلمهام": ["filmham"],
        "آهنگ": ["ahang"],
        "آهنگام": ["ahangam"],
        "آهنگهام": ["ahangham"],
        "موزیک": ["music", "muzik"]
    }

    # Synonym mapping for "spider" deep synonym matching
    synonym_map = {
        "خاطرات": ["خاطره", "خاطرات من", "دفتر خاطرات", "khaterat", "khatereh", "khatere"],
        "خاطره": ["خاطرات", "خاطرات من", "دفتر خاطرات", "khaterat", "khatereh", "khatere"],
        "فیلم": ["فیلم‌ها", "سینما", "سریال", "film", "serial", "cinema"],
        "سریال": ["فیلم", "سینما", "سریال‌ها", "film", "serial", "cinema"],
        "آهنگ": ["موزیک", "موسیقی", "ترانه", "music", "muzik", "ahang", "taraneh"],
        "موزیک": ["آهنگ", "موسیقی", "ترانه", "music", "muzik", "ahang", "taraneh"],
        "موسیقی": ["آهنگ", "موزیک", "ترانه", "music", "muzik", "ahang", "taraneh"],
        "کتاب": ["رمان", "داستان", "ketab", "roman", "dastan", "book"],
        "رمان": ["کتاب", "داستان", "ketab", "roman", "dastan", "book"],
        "بورس": ["سهام", "ارز دیجیتال", "کریپتو", "bourse", "sahm", "crypto"],
        "ارز دیجیتال": ["بورس", "سهام", "ارزدیجیتال", "کریپتو", "crypto", "bitcoin"]
    }

    # Match substrings for query and its expanded variants
    matched_finglish = []
    for persian_word, f_list in finglish_map.items():
        if persian_word in query or query in persian_word:
            matched_finglish.extend(f_list)
        for q_var in list(queries):
            if persian_word in q_var or q_var in persian_word:
                matched_finglish.extend(f_list)

    # Match synonyms
    matched_synonyms = []
    for p_word, s_list in synonym_map.items():
        if p_word in query or query in p_word:
            matched_synonyms.extend(s_list)
        for q_var in list(queries):
            if p_word in q_var or q_var in p_word:
                matched_synonyms.extend(s_list)

    queries.extend(matched_finglish)
    queries.extend(matched_synonyms)

    # Clean up duplicates and keep original order
    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            unique_queries.append(q_clean)

    # Comprehensive deep search expansion (up to 12 variations)
    return unique_queries[:12]

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

    # Start Userbot (the actual user session) - critical blocking start
    try:
        print("Starting Userbot (SESSION_STRING) dynamically...")
        res = userbot.start()
        if inspect.iscoroutine(res):
            await res
        print("Userbot started successfully.")
    except Exception as e:
        err_msg = str(e)
        print(f"Fatal error starting Userbot: {err_msg}")
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
                f"تلگرام اکانت کاربری شما را به دلیل درخواست‌های مکرر به طور موقت محدود کرده است.\n"
                f"لطفاً چند دقیقه صبر کنید و سپس دوباره تلاش نمایید.\n"
            )
            print(friendly_err)
            sys.exit(1)
        else:
            friendly_err = (
                f"\n❌ خطا در راه‌اندازی اکانت کاربری (Userbot):\n"
                f"متن خطا: {err_msg}\n"
                f"لطفاً مطمئن شوید SESSION_STRING معتبر است.\n"
            )
            print(friendly_err)
            sys.exit(1)

    # Start Pyrogram Bot - Soft, non-blocking fallback start (won't crash on FLOOD_WAIT or Auth errors)
    try:
        print("Starting Pyrogram Bot dynamically...")
        res = Bot.start()
        if inspect.iscoroutine(res):
            await res
        print("Pyrogram Bot started successfully.")
    except Exception as e:
        print(f"Warning: Soft-start failed for Pyrogram Bot: {e}. We will safely fall back to Userbot for sending messages.")

    # Start Telethon Bot safely under async context - Soft, non-blocking fallback start
    try:
        if not bot.is_connected():
            print("Starting Telethon bot dynamically...")
            await bot.connect()
            if not await bot.is_user_authorized():
                await bot.sign_in(bot_token=BOT_TOKEN)
            print("Telethon Bot started successfully.")
    except Exception as e:
        print(f"Warning: Soft-start failed for Telethon bot dynamically: {e}. We will safely fall back to Userbot.")

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
            msg = await safe_send_message(owner_id, f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای رسمی تلگرام...*\n\n🕒 لطفا صبور باشید...")

            try:
                from pyrogram.raw.functions.contacts import Search

                # Get expanded queries
                expanded_queries = expand_persian_query(query)
                print(f"DEBUG: Expanded search queries for execution: {expanded_queries}")

                channels = []
                seen_usernames = set()

                for q_term in expanded_queries:
                    print(f"DEBUG: Executing search for term variation: {q_term}")
                    try:
                        # Invoke raw global search with a limit of 1000
                        found = await userbot.invoke(Search(q=q_term, limit=1000))
                        if found and hasattr(found, 'chats'):
                            for chat in found.chats:
                                username = getattr(chat, 'username', None)
                                if username and username.lower() not in seen_usernames:
                                    seen_usernames.add(username.lower())
                                    title = getattr(chat, 'title', "بدون عنوان")
                                    members = getattr(chat, 'participants_count', None)
                                    channels.append((title, username, members))
                    except Exception as e_search:
                        print(f"DEBUG: Search variation '{q_term}' contacts.Search failed: {e_search}")

                    try:
                        # Global message search for variation
                        # Try Pyrogram v2 search_global first, then fallback to Pyrogram v1 search_global_messages
                        search_iterator = None
                        try:
                            search_iterator = userbot.search_global(query=q_term, limit=300)
                        except AttributeError:
                            try:
                                search_iterator = userbot.search_global_messages(query=q_term, limit=300)
                            except AttributeError:
                                pass

                        if search_iterator:
                            async for message in search_iterator:
                                if message.chat and getattr(message.chat, 'username', None):
                                    username = getattr(message.chat, 'username')
                                    if username and username.lower() not in seen_usernames:
                                        seen_usernames.add(username.lower())
                                        title = getattr(message.chat, 'title', "بدون عنوان")
                                        members = getattr(message.chat, 'participants_count', None) or getattr(message.chat, 'members_count', None)
                                        channels.append((title, username, members))
                    except Exception as e_msg_search:
                        print(f"DEBUG: Search variation '{q_term}' search_global failed: {e_msg_search}")

                    # Small sleep to prevent rate limiting
                    await asyncio.sleep(0.5)

                # SPIDER CRAWL: Get similar channels for the top 10 largest found channels to expand exponentially!
                channels_to_crawl = sorted([c for c in channels if c[2] is not None], key=lambda x: x[2], reverse=True)[:10]
                print(f"DEBUG: Starting spider crawl of similar channels for: {[c[1] for c in channels_to_crawl]}")
                for title, username, members in channels_to_crawl:
                    similar = None
                    try:
                        similar = await userbot.get_chat_recommendations(username)
                    except Exception:
                        try:
                            similar = await userbot.get_similar_channels(username)
                        except Exception:
                            pass

                    try:
                        if similar:
                            for sim_channel in similar:
                                sim_username = getattr(sim_channel, 'username', None)
                                if sim_username and sim_username.lower() not in seen_usernames:
                                    seen_usernames.add(sim_username.lower())
                                    sim_title = getattr(sim_channel, 'title', "بدون عنوان")
                                    sim_members = getattr(sim_channel, 'participants_count', None) or getattr(sim_channel, 'members_count', None)
                                    channels.append((sim_title, sim_username, sim_members))
                    except Exception as sim_err:
                        print(f"DEBUG: Processing similar channels failed for {username}: {sim_err}")

                if not channels:
                    await safe_edit_message(owner_id, msg, f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
                    return

                # Format page 1 results (50 items per page)
                import math
                page_size = 50
                total_items = len(channels)
                total_pages = max(1, math.ceil(total_items / page_size))
                page_channels = channels[:page_size]

                page_text = f"🎯 *نتایج جستجوی عمیق تلگرام برای «{query}»*\n"
                page_text += f"📊 *شمارش کل دیتابیس: {total_items:,} کانال عمومی یافت شد (در قالب {total_pages} صفحه ۵۰تایی)*\n"
                page_text += f"📍 *نمایش صفحه ۱ از {total_pages} (کانال‌های ۱ تا {len(page_channels)}):*\n\n"

                for i, (title, username, members) in enumerate(page_channels, 1):
                    members_str = f" ({members:,} عضو)" if members is not None else ""
                    page_text += f"{i}. 📣 *{title}*\n   🔗 شناسه: @{username}{members_str}\n   👉 [ورود به کانال](https://t.me/{username})\n\n"

                await safe_edit_message(owner_id, msg, page_text, disable_web_page_preview=True)

                if total_pages > 1:
                    info_msg = (
                        f"💡 *رئیس بزرگ، تعداد کل کانال‌های یافت‌شده {total_items:,} عدد در {total_pages} صفحه ۵۰تایی است.*\n"
                        f"برای مرور زنده و استفاده از دکمه‌های شیشه‌ای «صفحه بعدی ⏩»، می‌توانید سرور ربات را روشن نگه داشته یا دستور `/search {query}` را مستقیم در چت ربات بزنید! 💎"
                    )
                    await safe_send_message(owner_id, info_msg)

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
