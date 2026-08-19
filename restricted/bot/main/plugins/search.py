# Search plugin for Telegram deep search directly from bot chat
import os
import asyncio
import time
import math
from decouple import config
from .. import bot as Drone
from .. import userbot, Bot, AUTH
from telethon import events, Button
from pyrogram.raw.functions.contacts import Search
from .seen_db import is_channel_seen, mark_channels_as_seen, get_all_seen_usernames, clear_seen_channels

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

# Global search cache for pagination
SEARCH_CACHE = {}

def clean_expired_search_cache(max_age_seconds=3600):
    now = time.time()
    expired_keys = [k for k, v in SEARCH_CACHE.items() if now - v.get('time', now) > max_age_seconds]
    for k in expired_keys:
        SEARCH_CACHE.pop(k, None)

def generate_green_progress_bar(current, total, length=10):
    if total <= 0:
        percent = 0.0
    else:
        percent = min(1.0, max(0.0, current / total))
    filled = int(round(length * percent))
    bar = "█" * filled + "░" * (length - filled)
    return f"🟢 `[{bar}] {int(percent * 100)}%`"

def format_search_page(query, channels, page=1, page_size=10):
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

import re

def normalize_persian(text):
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    replacements = {
        'ي': 'ی', 'ك': 'ک', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ۀ': 'ه',
        '\u200c': ' '
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[\-_.:;!?,()\[\]{\}\'\"]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_query_in_channel(title, username, query):
    q_norm = normalize_persian(query)
    if not q_norm:
        return True
    t_norm = normalize_persian(title)
    u_norm = normalize_persian(username)

    if q_norm in t_norm or q_norm in u_norm:
        return True

    q_words = [w.replace('ها', '').replace('های', '') for w in q_norm.split() if len(w) > 1]
    if not q_words:
        return True

    # High recall matching: if any primary query word matches in title or username, keep channel
    matched_count = sum(1 for w in q_words if w in t_norm or w in u_norm)
    if matched_count >= 1:
        return True

    return False

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
    query = query.strip()
    queries = [query]

    # Add individual words of query (e.g. 'عکسها خودمون' -> 'عکسها', 'خودمون', 'عکس')
    words = query.split()
    for w in words:
        if len(w) > 1:
            queries.append(w)
            w_stem = w.replace('ها', '').replace('های', '')
            if len(w_stem) > 1 and w_stem != w:
                queries.append(w_stem)

    # Persian/English suffixes & common Telegram prefixes
    keywords = [
        'کانال', 'گروه', 'رسمی', 'اصلی', 'جدید', 'بزرگ', 'ایران', 'آنلاین',
        'channel', 'official', 'group', 'iran', 'plus', 'vip', '1', '2', '01'
    ]
    for kw in keywords:
        queries.append(f"{query} {kw}")
        queries.append(f"{kw} {query}")

    # Persian & English Alphabetical Sub-Query Expansion
    alphabet = ['ا', 'ب', 'پ', 'ت', 'ث', 'ج', 'چ', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'ژ', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'گ', 'ل', 'م', 'ن', 'و', 'ه', 'ی', 'a', 'b', 'c', 'd', 'e', 'f', 'm', 's', '1', '2']
    for char in alphabet:
        queries.append(f"{query} {char}")
        queries.append(f"{query}_{char}")

    # Clean up duplicates
    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            unique_queries.append(q_clean)

    return unique_queries[:120]

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
        send_channel_notice(f"🔎 *شروع لاگ زنده جستجوی عمیق تلگرام برای:* «{query}»\n📌 تعداد انشعاب‌های الفبایی و کلمه‌ای: {len(expanded_queries)} عبارت")

        db_seen_usernames = get_all_seen_usernames()
        channels = []
        seen_usernames = set()

        total_steps = len(expanded_queries)
        for idx, q_term in enumerate(expanded_queries, 1):
            try:
                found = await userbot.invoke(Search(q=q_term, limit=1000))
                # Only iterate over chats (and ignore my_results/user dialogs)
                if found and hasattr(found, 'chats'):
                    for chat in found.chats:
                        username = getattr(chat, 'username', None)
                        if username and is_valid_channel(username, chat):
                            u_lower = username.lower().strip()
                            if u_lower not in seen_usernames and u_lower not in db_seen_usernames:
                                title = clean_channel_title(chat, username)
                                if is_query_in_channel(title, username, query):
                                    seen_usernames.add(u_lower)
                                    members = getattr(chat, 'participants_count', None) or getattr(chat, 'members_count', None)
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
                            if username and is_valid_channel(username, message.chat):
                                u_lower = username.lower().strip()
                                if u_lower not in seen_usernames and u_lower not in db_seen_usernames:
                                    title = clean_channel_title(message.chat, username)
                                    if is_query_in_channel(title, username, query):
                                        seen_usernames.add(u_lower)
                                        members = getattr(message.chat, 'participants_count', None) or getattr(message.chat, 'members_count', None)
                                        channels.append((title, username, members))
            except Exception as e_msg_search:
                print(f"Search variation '{q_term}' search_global failed: {e_msg_search}")

            if idx % 5 == 0 or idx == total_steps:
                progress_bar = generate_green_progress_bar(idx, total_steps)
                progress_msg = (
                    f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای تلگرام...*\n\n"
                    f"{progress_bar}\n"
                    f"⚡ گام {idx} از {total_steps} (عبارت: `{q_term}`)\n"
                    f"🟢 مجموع کانال‌های کشف‌شده تا این لحظه: *{len(channels):,} کانال*"
                )
                try:
                    await msg.edit(progress_msg)
                except Exception:
                    pass
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
                    if sim_username and is_valid_channel(sim_username, sim_channel):
                        u_lower = sim_username.lower().strip()
                        if u_lower not in seen_usernames and u_lower not in db_seen_usernames:
                            sim_title = clean_channel_title(sim_channel, sim_username)
                            if is_query_in_channel(sim_title, sim_username, query):
                                seen_usernames.add(u_lower)
                                sim_members = getattr(sim_channel, 'participants_count', None) or getattr(sim_channel, 'members_count', None)
                                channels.append((sim_title, sim_username, sim_members))

        # Deduplicate strictly by lowercase username
        unique_dict = {}
        for title, username, members in channels:
            u_key = str(username or '').lower().strip()
            if u_key and u_key not in unique_dict:
                unique_dict[u_key] = (title, username, members)
        channels = list(unique_dict.values())

        # Filter strictly again and sort by Relevance Score
        channels = [c for c in channels if is_query_in_channel(c[0], c[1], query)]
        channels.sort(key=lambda c: calculate_relevance_score(c[0], c[1], c[2], query), reverse=True)
        send_channel_notice(f"📊 *پایان لاگ زنده جستجو!*\n🎯 کل کانال‌های عمومی یافت‌شده: {len(channels):,} کانال\n⭐ الگوریتم رتبه‌بندی بر اساس ارتباط کلمه‌ای و اعضا اعمال گردید.")

        if not channels:
            await msg.edit(f"❌ *رئیس بزرگ، هیچ کانال عمومی *جدیدی* برای عبارت «{query}» در تلگرام یافت نشد! (تمامی موارد قبلاً دیده‌شده‌اند)*")
            return

        # Mark all new channels as seen in SQLite database
        mark_channels_as_seen(channels)

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

        page_text, total_pages, current_page = format_search_page(query, channels, page=1, page_size=10)
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
    try:
        await event.answer()
    except Exception:
        pass

    sender_id = event.sender_id
    search_id_raw = event.pattern_match.group(1)
    search_id = search_id_raw.decode('utf-8') if isinstance(search_id_raw, bytes) else str(search_id_raw)
    target_page = int(event.pattern_match.group(2))

    cache_key = f"{sender_id}_{search_id}"
    cache = SEARCH_CACHE.get(cache_key)

    if not cache:
        # Fallback to search_results.json if SEARCH_CACHE is empty
        channels = []
        query = ""
        for json_path in ['search_results.json', '../search_results.json', 'restricted/search_results.json']:
            if os.path.exists(json_path):
                try:
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        query = data.get('query', '')
                        for c in data.get('channels', []):
                            channels.append((c.get('title', ''), c.get('username', ''), c.get('members', 0)))
                    break
                except Exception:
                    pass
        if not channels:
            try:
                return await event.answer("⚠️ اطلاعات این جستجو منقضی شده است. لطفاً مجدداً دستور /search را وارد فرمایید.", alert=True)
            except Exception:
                return
    else:
        query = cache['query']
        channels = cache['channels']

    page_text, total_pages, current_page = format_search_page(query, channels, page=target_page, page_size=10)
    buttons = get_search_buttons(search_id, current_page, total_pages)

    try:
        await event.edit(page_text, buttons=buttons, link_preview=False)
    except Exception as e:
        print(f"DEBUG: Callback edit error: {e}")
