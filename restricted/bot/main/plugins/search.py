# Search plugin for Telegram deep search directly from bot chat
import os
import asyncio
import time
import math
from .. import bot as Drone
from .. import userbot, Bot, AUTH
from telethon import events, Button
from pyrogram.raw.functions.contacts import Search
from pyrogram.tl.types import InputPeerUser

# Global search cache for pagination
SEARCH_CACHE = {}

def clean_expired_search_cache(max_age_seconds=3600):
    now = time.time()
    expired_keys = [k for k, v in SEARCH_CACHE.items() if now - v.get('time', now) > max_age_seconds]
    for k in expired_keys:
        SEARCH_CACHE.pop(k, None)

def format_search_page(query, channels, page=1, page_size=20):
    total_items = len(channels)
    total_pages = max(1, math.ceil(total_items / page_size))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    page_channels = channels[start_idx:end_idx]

    text = f"🎯 *نتایج جستجوی تلگرام برای «{query}»*\n"
    text += f"📊 *شمارش کل دیتابیس: {total_items:,} کانال عمومی (صفحه {page} از {total_pages}):*\n\n"

    for i, (title, username, members) in enumerate(page_channels, start_idx + 1):
        members_str = f" ({members:,} عضو)" if members is not None else ""
        line = f"{i}. 📣 *{title}*\n   🔗 شناسه: @{username}{members_str}\n   👉 [ورود به کانال](https://t.me/{username})\n\n"
        if len(text) + len(line) > 3800:
            break
        text += line

    return text, total_pages, page

def get_search_buttons(search_id, current_page, total_pages):
    if total_pages <= 1:
        return None

    buttons = []
    if current_page > 1:
        buttons.append(Button.inline("⏪ صفحه قبلی", data=f"sp:{search_id}:{current_page - 1}".encode()))

    buttons.append(Button.inline(f"📄 {current_page}/{total_pages}", data=b"noop"))

    if current_page < total_pages:
        buttons.append(Button.inline("صفحه بعدی ⏩", data=f"sp:{search_id}:{current_page + 1}".encode()))

    return [buttons]

def expand_persian_query(query):
    queries = [query]

    # Character normalization variations (ی/ي, ک/ك)
    q_norm1 = query.replace("ی", "ي").replace("ک", "ك")
    q_norm2 = query.replace("ي", "ی").replace("ك", "ک")
    queries.extend([q_norm1, q_norm2])

    # Common Persian prefixes/suffixes for deep channel discovery
    prefixes = ["کانال ", "دانلود ", "مرجع ", "پست ", "گروه "]
    suffixes = [" ", " رسمى", " رسمی", " جدید", " بروز"]

    for p in prefixes:
        queries.append(f"{p}{query}")
    for s in suffixes:
        queries.append(f"{query}{s}")

    # Standard Persian suffix handling (هام, ام, هایم, های من)
    if query.endswith("هام") and len(query) > 3:
        base = query[:-3]
        queries.extend([f"{base} هام", f"{base}هایم", f"{base} هایم", f"{base}های من", f"{base}ام"])
    elif query.endswith("ام") and len(query) > 2 and not query.endswith("هام"):
        base = query[:-2]
        queries.extend([f"{base} ام", f"{base}هام", f"{base} هام", f"{base}هایم", f"{base}های من"])
    elif query.endswith("هایم") and len(query) > 4:
        base = query[:-4]
        queries.extend([f"{base} هایم", f"{base}هام", f"{base} هام", f"{base}های من", f"{base}ام"])

    # Transliterations and synonyms
    finglish_map = {
        "عکس": ["aks", "ax"],
        "عکسام": ["aksam", "axam"],
        "عکسهام": ["aksham", "axham"],
        "فیلم": ["film"],
        "آهنگ": ["ahang", "music"],
        "موزیک": ["music", "muzik"],
        "مدارک": ["madarek", "madarekam"],
        "مدارکم": ["madarekam", "madarek"]
    }

    synonym_map = {
        "خاطرات": ["خاطره", "خاطرات من"],
        "فیلم": ["سینما", "سریال"],
        "آهنگ": ["موزیک", "ترانه"],
        "کتاب": ["رمان", "داستان"],
        "بورس": ["سهام", "ارز دیجیتال"]
    }

    for k, v in finglish_map.items():
        if k in query or query in k:
            queries.extend(v)

    for k, v in synonym_map.items():
        if k in query or query in k:
            queries.extend(v)

    # Clean up duplicates
    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            unique_queries.append(q_clean)

    return unique_queries[:15]

@Drone.on(events.NewMessage(incoming=True, pattern=r'/search(?:\s+(.+))?'))
async def telegram_search(event):
    if not event.is_private:
        return

    # Check authorization if AUTH is set
    if AUTH and event.sender_id != AUTH:
        return await event.reply("⚠️ شما مجاز به استفاده از این ربات نیستید! 🛡️")

    query = event.pattern_match.group(1)
    if not query:
        return await event.reply("⚠️ لطفاً کلمه مورد نظر برای جستجو را وارد کنید.\nمثال: `/search عکس`")

    query = query.strip()
    msg = await event.reply(f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای تلگرام...*\n\n🕒 لطفا صبور باشید...")

    try:
        # Ensure userbot is connected
        if not getattr(userbot, 'is_connected', False):
            print("Starting userbot inside direct search plugin...")
            res = userbot.start()
            import inspect
            if inspect.iscoroutine(res):
                await res

        expanded_queries = expand_persian_query(query)
        channels = []
        seen_usernames = set()

        for q_term in expanded_queries:
            try:
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
                print(f"Search variation '{q_term}' contacts.Search failed: {e_search}")

            try:
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
                print(f"Search variation '{q_term}' search_global failed: {e_msg_search}")

            await asyncio.sleep(0.5)

        # RECURSIVE SPIDER CRAWL (2 Levels deep): Expand Telegram's similar channel graph!
        level1_crawl = sorted([c for c in channels if c[2] is not None], key=lambda x: x[2], reverse=True)[:10]
        new_discovered = []
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
                    if sim_username and sim_username.lower() not in seen_usernames:
                        seen_usernames.add(sim_username.lower())
                        sim_title = getattr(sim_channel, 'title', "بدون عنوان")
                        sim_members = getattr(sim_channel, 'participants_count', None) or getattr(sim_channel, 'members_count', None)
                        item = (sim_title, sim_username, sim_members)
                        channels.append(item)
                        new_discovered.append(item)

        # LEVEL 2 SPIDER CRAWL for newly discovered channels
        level2_crawl = sorted([c for c in new_discovered if c[2] is not None], key=lambda x: x[2], reverse=True)[:5]
        for title, username, members in level2_crawl:
            try:
                similar2 = await userbot.get_chat_recommendations(username)
                if similar2:
                    for sim_channel in similar2:
                        sim_username = getattr(sim_channel, 'username', None)
                        if sim_username and sim_username.lower() not in seen_usernames:
                            seen_usernames.add(sim_username.lower())
                            sim_title = getattr(sim_channel, 'title', "بدون عنوان")
                            sim_members = getattr(sim_channel, 'participants_count', None) or getattr(sim_channel, 'members_count', None)
                            channels.append((sim_title, sim_username, sim_members))
            except Exception:
                pass

        # Sort all discovered channels by member count in descending order
        channels.sort(key=lambda x: (x[2] if x[2] is not None else 0), reverse=True)

        if not channels:
            await msg.edit(f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
            return

        # Store in search cache for live pagination
        clean_expired_search_cache()
        search_id = str(int(time.time()))
        cache_key = f"{event.sender_id}_{search_id}"
        SEARCH_CACHE[cache_key] = {
            'query': query,
            'channels': channels,
            'id': search_id,
            'time': time.time()
        }

        page_text, total_pages, current_page = format_search_page(query, channels, page=1, page_size=20)
        buttons = get_search_buttons(search_id, current_page, total_pages)

        await msg.edit(page_text, buttons=buttons, link_preview=False)
        await event.reply("✅ *جستجوی عمیق تلگرام با موفقیت کامل شد!*")

    except Exception as e:
        print(f"Error during execution of direct search: {e}")
        try:
            await msg.edit(f"❌ *خطا در اجرای جستجوی عمیق تلگرام:*\n`{str(e)}`")
        except:
            pass

@Drone.on(events.CallbackQuery(pattern=r'^sp:(.+):(\d+)$'))
async def on_search_page_callback(event):
    sender_id = event.sender_id
    search_id_raw = event.pattern_match.group(1)
    search_id = search_id_raw.decode('utf-8') if isinstance(search_id_raw, bytes) else str(search_id_raw)
    target_page = int(event.pattern_match.group(2))

    cache_key = f"{sender_id}_{search_id}"
    cache = SEARCH_CACHE.get(cache_key)

    if not cache:
        return await event.answer("⚠️ اطلاعات این جستجو منقضی شده است. لطفاً مجدداً جستجو فرمایید.", alert=True)

    query = cache['query']
    channels = cache['channels']

    page_text, total_pages, current_page = format_search_page(query, channels, page=target_page, page_size=20)
    buttons = get_search_buttons(search_id, current_page, total_pages)

    try:
        await event.edit(page_text, buttons=buttons, link_preview=False)
    except Exception as e:
        print(f"DEBUG: Callback edit error: {e}")

    await event.answer()
