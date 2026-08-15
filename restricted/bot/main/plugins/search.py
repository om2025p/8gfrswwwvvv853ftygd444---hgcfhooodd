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

def format_search_page(query, channels, page=1, page_size=50):
    total_items = len(channels)
    total_pages = max(1, math.ceil(total_items / page_size))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    page_channels = channels[start_idx:end_idx]

    text = f"🎯 *نتایج جستجوی عمیق تلگرام برای «{query}»*\n"
    text += f"📊 *شمارش کل دیتابیس: {total_items:,} کانال عمومی یافت شد (در قالب {total_pages} صفحه ۵۰تایی)*\n"
    text += f"📍 *نمایش صفحه {page} از {total_pages} (کانال‌های {start_idx + 1} تا {end_idx}):*\n\n"

    for i, (title, username, members) in enumerate(page_channels, start_idx + 1):
        members_str = f" ({members:,} عضو)" if members is not None else ""
        text += f"{i}. 📣 *{title}*\n   🔗 شناسه: @{username}{members_str}\n   👉 [ورود به کانال](https://t.me/{username})\n\n"

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
            await msg.edit(f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
            return

        # Store in search cache for live pagination
        search_id = str(int(time.time()))
        cache_key = f"{event.sender_id}_{search_id}"
        SEARCH_CACHE[cache_key] = {
            'query': query,
            'channels': channels,
            'id': search_id
        }

        page_text, total_pages, current_page = format_search_page(query, channels, page=1, page_size=50)
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

    page_text, total_pages, current_page = format_search_page(query, channels, page=target_page, page_size=50)
    buttons = get_search_buttons(search_id, current_page, total_pages)

    try:
        await event.edit(page_text, buttons=buttons, link_preview=False)
    except Exception as e:
        print(f"DEBUG: Callback edit error: {e}")

    await event.answer()
