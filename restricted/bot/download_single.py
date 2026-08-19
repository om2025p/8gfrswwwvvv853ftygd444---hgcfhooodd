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
    payload = {'chat_id': chat_id, 'text': text, 'disable_web_page_preview': True}
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

def is_valid_channel(username, chat=None):
    if not username or not isinstance(username, str):
        return False
    u_lower = username.lower().strip()
    if u_lower.endswith('bot') or u_lower.endswith('_bot') or u_lower.startswith('bot_'):
        return False
    if chat and getattr(chat, 'is_bot', False):
        return False
    return True

def clean_channel_title(chat, username):
    title = getattr(chat, 'title', None)
    if not title:
        first_name = getattr(chat, 'first_name', '') or ''
        last_name = getattr(chat, 'last_name', '') or ''
        title = f"{first_name} {last_name}".strip()
    if not title or str(title).strip().lower() in ["none", "null", ""]:
        title = f"@{username}"
    return str(title).strip()

def is_query_in_channel(title, username, query):
    q_clean = query.lower().strip()
    t_clean = str(title or '').lower().strip()
    u_clean = str(username or '').lower().strip()
    return q_clean in t_clean or q_clean in u_clean

def calculate_relevance_score(title, username, members, query):
    score = 0
    q_clean = query.lower().strip()
    t_clean = str(title).lower().strip()
    u_clean = str(username).lower().strip()

    # Exact full query match in title or username -> HUGE BOOST
    if q_clean in t_clean or q_clean in u_clean:
        score += 10000

    # Member count boost (logarithmic scale)
    m_val = members if members is not None else 0
    import math
    if m_val > 0:
        score += math.log10(m_val) * 100

    return score

def generate_green_progress_bar(current, total, length=10):
    if total <= 0:
        percent = 0.0
    else:
        percent = min(1.0, max(0.0, current / total))
    filled = int(round(length * percent))
    bar = "█" * filled + "░" * (length - filled)
    return f"🟢 `[{bar}] {int(percent * 100)}%`"

def expand_persian_query(query):
    query = query.strip()
    queries = [query]

    # Persian & English Alphabetical Sub-Query Expansion using EXACT base query
    alphabet = ['ا', 'ب', 'پ', 'ت', 'ث', 'ج', 'چ', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'ژ', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'گ', 'ل', 'م', 'ن', 'و', 'ه', 'ی', 'a', 'b', 'c', 'd', 'e', 'f', 'm', 's']
    for char in alphabet:
        queries.append(f"{query} {char}")

    # Clean up duplicates
    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            unique_queries.append(q_clean)

    return unique_queries[:40]

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

                send_channel_notice(f"🔎 *شروع لاگ زنده جستجوی عمیق تلگرام برای:* «{query}»\n📌 تعداد انشعاب‌های الفبایی و کلمه‌ای: {len(expanded_queries)} عبارت")

                channels = []
                seen_usernames = set()

                total_steps = len(expanded_queries)
                for idx, q_term in enumerate(expanded_queries, 1):
                    print(f"DEBUG: Executing search for term variation: {q_term}")
                    try:
                        # Invoke raw global search with a limit of 1000
                        found = await userbot.invoke(Search(q=q_term, limit=1000))
                        if found and hasattr(found, 'chats'):
                            for chat in found.chats:
                                username = getattr(chat, 'username', None)
                                if username and is_valid_channel(username, chat) and username.lower() not in seen_usernames:
                                    title = clean_channel_title(chat, username)
                                    # Strict filtering: Title or Username MUST contain the exact base search query
                                    if is_query_in_channel(title, username, query):
                                        seen_usernames.add(username.lower())
                                        members = getattr(chat, 'participants_count', None) or getattr(chat, 'members_count', None)
                                        channels.append((title, username, members))
                    except Exception as e_search:
                        print(f"DEBUG: Search variation '{q_term}' contacts.Search failed: {e_search}")

                    try:
                        # Global message search for variation
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
                                    if username and is_valid_channel(username, message.chat) and username.lower() not in seen_usernames:
                                        title = clean_channel_title(message.chat, username)
                                        # Strict filtering: Title or Username MUST contain the exact base search query
                                        if is_query_in_channel(title, username, query):
                                            seen_usernames.add(username.lower())
                                            members = getattr(message.chat, 'participants_count', None) or getattr(message.chat, 'members_count', None)
                                            channels.append((title, username, members))
                    except Exception as e_msg_search:
                        print(f"DEBUG: Search variation '{q_term}' search_global failed: {e_msg_search}")

                    # Real-time update in Telegram chat with green progress bar
                    if idx % 5 == 0 or idx == total_steps:
                        progress_bar = generate_green_progress_bar(idx, total_steps)
                        progress_msg = (
                            f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای تلگرام...*\n\n"
                            f"{progress_bar}\n"
                            f"⚡ گام {idx} از {total_steps} (عبارت: `{q_term}`)\n"
                            f"🟢 مجموع کانال‌های کشف‌شده تا این لحظه: *{len(channels):,} کانال*"
                        )
                        await safe_edit_message(owner_id, msg, progress_msg)
                        send_channel_notice(f"⚡ [گام {idx}/{total_steps}] عبارت «{q_term}» -> تاکنون مجموعاً {len(channels):,} کانال عمومی مطابقت‌دار کشف شد.")

                    await asyncio.sleep(0.3)

                # RECURSIVE SPIDER CRAWL with Strict Matching
                send_channel_notice(f"🕷️ *شروع خزش عنکبوتی برای کشف کانال‌های مشابه با نام دقیق...*")
                level1_crawl = sorted([c for c in channels if c[2] is not None], key=lambda x: x[2], reverse=True)[:10]
                for title, username, members in level1_crawl:
                    similar = None
                    try:
                        similar = await userbot.get_chat_recommendations(username)
                    except Exception:
                        try:
                            similar = await userbot.get_similar_channels(username)
                        except Exception:
                            pass

                    if similar:
                        for sim_channel in similar:
                            sim_username = getattr(sim_channel, 'username', None)
                            if sim_username and is_valid_channel(sim_username, sim_channel) and sim_username.lower() not in seen_usernames:
                                sim_title = clean_channel_title(sim_channel, sim_username)
                                if is_query_in_channel(sim_title, sim_username, query):
                                    seen_usernames.add(sim_username.lower())
                                    sim_members = getattr(sim_channel, 'participants_count', None) or getattr(sim_channel, 'members_count', None)
                                    channels.append((sim_title, sim_username, sim_members))

                # Filter strictly again and sort by Relevance Score
                channels = [c for c in channels if is_query_in_channel(c[0], c[1], query)]
                channels.sort(key=lambda c: calculate_relevance_score(c[0], c[1], c[2], query), reverse=True)
                send_channel_notice(f"📊 *پایان لاگ زنده جستجو!*\n🎯 کل کانال‌های عمومی یافت‌شده: {len(channels):,} کانال\n⭐ الگوریتم رتبه‌بندی بر اساس ارتباط کلمه‌ای و اعضا اعمال گردید.")

                if not channels:
                    await safe_edit_message(owner_id, msg, f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
                    return

                # Save search results to search_results.json for web platform display
                import json
                search_results_payload = {
                    'query': query,
                    'total_count': len(channels),
                    'timestamp': time.time(),
                    'channels': [
                        {
                            'title': title,
                            'username': username,
                            'members': members if members is not None else 0,
                            'link': f"https://t.me/{username}"
                        }
                        for title, username, members in channels
                    ]
                }
                for json_path in ['search_results.json', '../search_results.json', 'restricted/search_results.json']:
                    try:
                        with open(json_path, 'w', encoding='utf-8') as f_json:
                            json.dump(search_results_payload, f_json, ensure_ascii=False, indent=2)
                    except Exception:
                        pass

                # Populate SEARCH_CACHE and format page 1 using 10 items per page for Telegram
                from main.plugins.search import SEARCH_CACHE, format_search_page, get_search_buttons
                import math

                search_id = str(int(time.time()))
                cache_key = f"{owner_id}_{search_id}"
                SEARCH_CACHE[cache_key] = {
                    'query': query,
                    'channels': channels,
                    'id': search_id,
                    'time': time.time()
                }

                page_text, total_pages, current_page = format_search_page(query, channels, page=1, page_size=10)
                buttons = get_search_buttons(search_id, current_page, total_pages)

                # Send using telethon bot directly if connected to retain inline glass buttons
                sent_with_buttons = False
                try:
                    if bot.is_connected():
                        await bot.send_message(owner_id, page_text, buttons=buttons, link_preview=False)
                        sent_with_buttons = True
                except Exception as e_btn:
                    print(f"DEBUG: Sending message with inline buttons via Telethon failed: {e_btn}")

                if not sent_with_buttons:
                    await safe_edit_message(owner_id, msg, page_text, disable_web_page_preview=True)

                if total_pages > 1:
                    info_msg = (
                        f"💡 *رئیس بزرگ، تعداد کل کانال‌های یافت‌شده {len(channels):,} عدد در {total_pages} صفحه ۱۰تایی است.*\n"
                        f"برای مرور زنده و استفاده از دکمه‌های شیشه‌ای «صفحه بعدی ⏩»، سرور ربات تا چند دقیقه آینده شنود می‌کند یا می‌توانید دستور `/search {query}` را مستقیم در چت ربات بزنید! 💎"
                    )
                    await safe_send_message(owner_id, info_msg)

                await safe_send_message(owner_id, "✅ *جستجوی عمیق تلگرام با موفقیت کامل شد!*")

                # Keep listening for 5 minutes (300 seconds) so inline callback buttons work seamlessly
                if total_pages > 1 and bot.is_connected():
                    print("DEBUG: Keeping bot listener active for 300s to serve inline pagination callbacks...")
                    await asyncio.sleep(300)

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
