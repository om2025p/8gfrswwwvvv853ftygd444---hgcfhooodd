# Download a single link and send it to the owner
import sys
import os
import asyncio
import time
import tempfile
import shutil
import yt_dlp
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

class SimpleMsg:
    def __init__(self, mid):
        self.id = mid

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
                resp_data = json.loads(resp.read().decode('utf-8'))
                if resp_data.get('ok') and 'result' in resp_data:
                    msg_id_val = resp_data['result'].get('message_id', 0)
                    return SimpleMsg(msg_id_val)
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
    if not msg_obj or isinstance(msg_obj, bool) or not hasattr(msg_obj, 'id') or getattr(msg_obj, 'id', None) is None:
        return await safe_send_message(owner_id, text, disable_web_page_preview)

    is_telethon = hasattr(msg_obj, 'client') or hasattr(msg_obj, 'respond')
    if is_telethon:
        try:
            res = await msg_obj.edit(text, link_preview=not disable_web_page_preview)
            if res and not isinstance(res, bool) and hasattr(res, 'id'):
                return res
            return msg_obj
        except Exception as e:
            print(f"DEBUG: Telethon edit failed ({e}). Sending new message...")
            return await safe_send_message(owner_id, text, disable_web_page_preview)
    else:
        try:
            res = await msg_obj.edit_text(text, disable_web_page_preview=disable_web_page_preview)
            if res and not isinstance(res, bool) and hasattr(res, 'id'):
                return res
            return msg_obj
        except Exception as e:
            print(f"DEBUG: Pyrogram edit_text failed ({e}). Trying Bot.edit_message_text...")
            try:
                res = await Bot.edit_message_text(owner_id, msg_obj.id, text, disable_web_page_preview=disable_web_page_preview)
                if res and not isinstance(res, bool) and hasattr(res, 'id'):
                    return res
                return msg_obj
            except Exception as e2:
                print(f"DEBUG: Pyrogram Bot.edit_message_text failed ({e2}). Trying userbot edit...")
                try:
                    res = await userbot.edit_message_text(owner_id, msg_obj.id, text, disable_web_page_preview=disable_web_page_preview)
                    if res and not isinstance(res, bool) and hasattr(res, 'id'):
                        return res
                    return msg_obj
                except Exception as e3:
                    print(f"DEBUG: All edits failed. Sending new message...")
                    return await safe_send_message(owner_id, text, disable_web_page_preview)

async def process_social_media_download(link, owner_id, msg_obj=None):
    from main import Bot, bot, userbot

    status_text = f"🎬 *در حال استخراج و دانلود از اینستاگرام / تیک‌تاک / واتساپ:*\n`{link}`\n\n🕒 لطفاً کمی صبور باشید..."
    if msg_obj:
        msg_obj = await safe_edit_message(owner_id, msg_obj, status_text)
    else:
        msg_obj = await safe_send_message(owner_id, status_text)

    temp_dir = tempfile.mkdtemp(prefix="emarat_social_")
    caption = ""

    try:
        # Robust user-agents and headers for Instagram / TikTok / Social media
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Sec-Fetch-Mode': 'navigate',
        }

        def run_ytdlp():
            ydl_opts = {
                'outtmpl': os.path.join(temp_dir, '%(title).30s_%(id)s.%(ext)s'),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'http_headers': headers,
                'extractor_args': {
                    'youtube': ['player_client=android,web'],
                    'tiktok': ['app_version=30.0.0'],
                },
                'retries': 3,
                'fragment_retries': 3,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                return info

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, run_ytdlp)

        # Multi-layer Fallback Service if yt-dlp extracted no media
        def scan_files():
            files_list = []
            for r, _, fs in os.walk(temp_dir):
                for f in fs:
                    if not f.endswith(('.description', '.json', '.part', '.ytdl', '.txt', '.info')):
                        files_list.append(os.path.join(r, f))
            return files_list

        if not scan_files():
            print("DEBUG: yt-dlp produced no files. Attempting fallback extraction layers...")
            # Layer 1: Try Instagram alternative URL wrappers (e.g., ddinstagram / vxinstagram embed parsing)
            if 'instagram.com' in link or 'instagr.am' in link:
                try:
                    import urllib.parse, urllib.request, re
                    match = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', link)
                    if match:
                        shortcode = match.group(1)
                        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
                        req = urllib.request.Request(embed_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            html_text = resp.read().decode('utf-8', errors='ignore')
                            video_urls = re.findall(r'\"video_url\":\"(https:[^\"]+)\"', html_text)
                            display_urls = re.findall(r'\"display_url\":\"(https:[^\"]+)\"', html_text)

                            media_urls = [v.replace('\\u0026', '&').replace('\\/', '/') for v in video_urls]
                            if not media_urls:
                                media_urls = [d.replace('\\u0026', '&').replace('\\/', '/') for d in display_urls]

                            if media_urls:
                                target_url = media_urls[0]
                                ext = '.mp4' if 'video' in target_url or len(video_urls) > 0 else '.jpg'
                                out_path = os.path.join(temp_dir, f"instagram_{shortcode}{ext}")
                                dl_req = urllib.request.Request(target_url, headers=headers)
                                with urllib.request.urlopen(dl_req, timeout=15) as dl_resp, open(out_path, 'wb') as out_file:
                                    out_file.write(dl_resp.read())
                                print(f"DEBUG: Instagram Embed fallback successfully saved media to {out_path}")
                except Exception as ex_ig:
                    print(f"DEBUG: Instagram fallback layer failed: {ex_ig}")

            # Layer 2: Try TikTok API fallback services (e.g., SSSTik / TikWM / Cobalt)
            if 'tiktok.com' in link and not scan_files():
                try:
                    import urllib.parse, urllib.request, json
                    # TikWM API Request
                    req_data = urllib.parse.urlencode({'url': link, 'hd': 1}).encode('utf-8')
                    api_req = urllib.request.Request('https://www.tikwm.com/api/', data=req_data, headers={
                        'User-Agent': headers['User-Agent'],
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                    })
                    with urllib.request.urlopen(api_req, timeout=10) as api_resp:
                        res = json.loads(api_resp.read().decode('utf-8'))
                        if res.get('code') == 0 and res.get('data'):
                            data_obj = res['data']
                            v_url = data_obj.get('hdplay') or data_obj.get('play')
                            if v_url:
                                out_path = os.path.join(temp_dir, f"tiktok_{data_obj.get('id', 'video')}.mp4")
                                dl_req = urllib.request.Request(v_url, headers=headers)
                                with urllib.request.urlopen(dl_req, timeout=20) as dl_resp, open(out_path, 'wb') as out_file:
                                    out_file.write(dl_resp.read())
                                if not caption and data_obj.get('title'):
                                    caption = data_obj.get('title')
                                print(f"DEBUG: TikTok TikWM fallback successfully saved video to {out_path}")
                except Exception as ex_tt:
                    print(f"DEBUG: TikTok fallback layer failed: {ex_tt}")

        # Retrieve caption / description
        if info:
            if isinstance(info, dict):
                caption = info.get('description') or info.get('title') or ""
                if not caption and 'entries' in info and info['entries']:
                    first_entry = info['entries'][0]
                    if isinstance(first_entry, dict):
                        caption = first_entry.get('description') or first_entry.get('title') or ""

            if len(caption) > 1000:
                caption = caption[:995] + "..."

        # Scan for downloaded media files
        downloaded_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if not file.endswith(('.description', '.json', '.part', '.ytdl', '.txt', '.info')):
                    downloaded_files.append(os.path.join(root, file))

        # Sort files to maintain order
        downloaded_files.sort()

        if not downloaded_files:
            await safe_edit_message(owner_id, msg_obj, f"❌ *خطا در دانلود از شبکه اجتماعی:*\n`هیچ فایل ویدیویی یا تصویری قابل دانلودی در این لینک یافت نشد یا محتوا خصوصی (Private) است.`")
            return

        await safe_edit_message(owner_id, msg_obj, f"⬆️ *دانلود با موفقیت انجام شد! در حال آپلود به تلگرام ({len(downloaded_files)} فایل)...*")

        for idx, filepath in enumerate(downloaded_files):
            file_caption = caption if idx == 0 else None
            ext = os.path.splitext(filepath)[1].lower()

            sent = False
            # 1. Try Pyrogram Bot
            try:
                if getattr(Bot, 'is_connected', False):
                    if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                        await Bot.send_video(chat_id=owner_id, video=filepath, caption=file_caption)
                        sent = True
                    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await Bot.send_photo(chat_id=owner_id, photo=filepath, caption=file_caption)
                        sent = True
                    else:
                        await Bot.send_document(chat_id=owner_id, document=filepath, caption=file_caption)
                        sent = True
            except Exception as e_pbot:
                print(f"DEBUG: Pyrogram Bot social send failed ({e_pbot}). Trying Telethon...")

            # 2. Try Telethon Bot
            if not sent:
                try:
                    if bot.is_connected():
                        await bot.send_file(owner_id, filepath, caption=file_caption)
                        sent = True
                except Exception as e_tbot:
                    print(f"DEBUG: Telethon Bot social send failed ({e_tbot}). Trying Userbot...")

            # 3. Try Pyrogram Userbot
            if not sent:
                try:
                    if getattr(userbot, 'is_connected', False):
                        if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                            await userbot.send_video(chat_id=owner_id, video=filepath, caption=file_caption)
                        elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                            await userbot.send_photo(chat_id=owner_id, photo=filepath, caption=file_caption)
                        else:
                            await userbot.send_document(chat_id=owner_id, document=filepath, caption=file_caption)
                        sent = True
                except Exception as e_ubot:
                    print(f"DEBUG: Pyrogram Userbot social send failed ({e_ubot})")

        await safe_send_message(owner_id, "✅ *دانلود و ارسال محتوای اینستاگرام / تیک‌تاک / واتساپ با موفقیت کامل انجام شد!*")

    except Exception as e:
        print(f"DEBUG: Error in process_social_media_download: {e}")
        await safe_edit_message(owner_id, msg_obj, f"❌ *خطا در پردازش لینک شبکه اجتماعی:*\n`{str(e)}`")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

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

    # Stemming suffixes
    words = query.split()
    for w in words:
        if len(w) > 1:
            queries.append(w)
            w_stem = re.sub(r'(های|هامون|هاتون|هاشون|هام|هات|هاش|ها|ام|ات|اش)$', '', w)
            if len(w_stem) > 1 and w_stem != w:
                queries.append(w_stem)

    # Finglish / Transliteration dictionary
    finglish_map = {
        'عکس': ['aks', 'aksam', 'pic', 'photo', 'picture'],
        'عکسهام': ['aks', 'aksam', 'pic', 'photo'],
        'عکسها': ['aks', 'aksam', 'pic', 'photo'],
        'فیلم': ['film', 'movie', 'video'],
        'آهنگ': ['ahang', 'music', 'mp3', 'song'],
        'موزیک': ['music', 'ahang', 'mp3'],
        'خبر': ['khabar', 'news'],
        'بورس': ['bourse', 'stock']
    }
    for q_word in list(queries):
        if q_word in finglish_map:
            queries.extend(finglish_map[q_word])

    # Suffixes & Prefixes
    keywords = [
        'کانال', 'گروه', 'رسمی', 'اصلی', 'جدید', 'بزرگ', 'ایران', 'آنلاین',
        'دانلود', 'منبع', 'خاص', 'channel', 'official', 'group', 'iran', 'plus', 'vip', '1', '2'
    ]
    base_terms = list(queries)
    for term in base_terms:
        for kw in keywords:
            queries.append(f"{term} {kw}")
            queries.append(f"{kw} {term}")

    # Alphabet expansion for deep sub-queries
    alphabet = ['ا', 'ب', 'پ', 'ت', 'ث', 'ج', 'چ', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'ژ', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ک', 'گ', 'ل', 'م', 'ن', 'و', 'ه', 'ی', 'a', 'b', 'c', 'd', 'e', 'f', 'm', 's', '1', '2']
    for term in base_terms[:5]:
        for char in alphabet:
            queries.append(f"{term} {char}")
            queries.append(f"{term}_{char}")

    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            unique_queries.append(q_clean)

    return unique_queries[:250]

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

        # Check if link is social media / web link (Instagram, TikTok, WhatsApp, YouTube, Twitter, etc.)
        link_str = str(link).strip()
        link_lower = link_str.lower()
        from urllib.parse import urlparse
        parsed_domain = urlparse(link_lower).netloc
        is_telegram_link = 't.me' in parsed_domain or 'telegram.me' in parsed_domain

        is_social = any(domain in link_lower for domain in [
            'instagram.com', 'instagr.am', 'tiktok.com', 'vt.tiktok.com', 'vm.tiktok.com',
            'whatsapp.com', 'chat.whatsapp.com', 'wa.me', 'youtube.com', 'youtu.be', 'twitter.com', 'x.com'
        ]) or (link_lower.startswith(('http://', 'https://')) and not is_telegram_link)

        if is_social and not link_lower.startswith("search:"):
            print(f"Starting social media download for: {link_str} to owner: {owner_id}")
            msg = await safe_send_message(owner_id, f"🎬 *تشخیص لینک شبکه اجتماعی (اینستاگرام / تیک‌تاک / واتساپ):*\n`{link_str}`\n\n🕒 لطفا صبور باشید...")
            await process_social_media_download(link_str, owner_id, msg)
            return

        # Check if this is a deep Telegram search request
        if isinstance(link, str) and link.startswith("search:"):
            query = link[7:].strip()
            print(f"Starting deep Telegram search for: {query} for owner: {owner_id}")

            # Send starting message to owner
            msg = await safe_send_message(owner_id, f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای رسمی تلگرام...*\n\n🕒 لطفا صبور باشید...")

            try:
                from pyrogram.raw.functions.contacts import Search
                from main.plugins.seen_db import mark_channels_as_seen, get_all_seen_usernames

                # Get expanded queries
                expanded_queries = expand_persian_query(query)
                print(f"DEBUG: Expanded search queries for execution: {expanded_queries}")

                send_channel_notice(f"🔎 *شروع لاگ زنده جستجوی عمیق تلگرام برای:* «{query}»\n📌 تعداد انشعاب‌های الفبایی و کلمه‌ای: {len(expanded_queries)} عبارت")

                db_seen_usernames = get_all_seen_usernames()
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
                                if username and is_valid_channel(username, chat):
                                    u_lower = username.lower().strip()
                                    if u_lower not in seen_usernames and u_lower not in db_seen_usernames:
                                        title = clean_channel_title(chat, username)
                                        if is_query_in_channel(title, username, query):
                                            seen_usernames.add(u_lower)
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
                                    if username and is_valid_channel(username, message.chat):
                                        u_lower = username.lower().strip()
                                        if u_lower not in seen_usernames and u_lower not in db_seen_usernames:
                                            title = clean_channel_title(message.chat, username)
                                            if is_query_in_channel(title, username, query):
                                                seen_usernames.add(u_lower)
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

                # RECURSIVE SPIDER CRAWL with Extended Depth (Top 30 channels)
                send_channel_notice(f"🕷️ *شروع خزش عنکبوتی عمیق و خسته‌ناپذیر برای کشف شبکه‌های مشابه...*")
                crawl_targets = sorted([c for c in channels if c[2] is not None], key=lambda x: x[2], reverse=True)[:30]
                if not crawl_targets:
                    crawl_targets = channels[:30]

                for title, username, members in crawl_targets:
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
                    await safe_edit_message(owner_id, msg, f"❌ *رئیس بزرگ، هیچ کانال عمومی *جدیدی* برای عبارت «{query}» در تلگرام یافت نشد! (تمامی موارد قبلاً دیده‌شده‌اند)*")
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

                # Keep listening for 5 minutes (300 seconds) with registered Telethon callback handler so inline pagination works
                if total_pages > 1 and bot.is_connected():
                    print("DEBUG: Registering inline pagination handler and serving callbacks for 300s...")
                    from telethon import events
                    from main.plugins.search import format_search_page, get_search_buttons

                    async def on_single_download_callback(event):
                        try:
                            await event.answer()
                        except Exception:
                            pass
                        s_id_raw = event.pattern_match.group(1)
                        s_id = s_id_raw.decode('utf-8') if isinstance(s_id_raw, bytes) else str(s_id_raw)
                        if s_id != search_id:
                            return

                        target_page = int(event.pattern_match.group(2))
                        p_text, t_pages, c_page = format_search_page(query, channels, page=target_page, page_size=10)
                        btns = get_search_buttons(s_id, c_page, t_pages)
                        try:
                            await event.edit(p_text, buttons=btns, link_preview=False)
                        except Exception as e_edit:
                            print(f"DEBUG: Single download callback edit error: {e_edit}")

                    callback_handler = bot.add_event_handler(on_single_download_callback, events.CallbackQuery(pattern=r'^sp:(.+):(\d+)$'))
                    try:
                        await asyncio.sleep(300)
                    finally:
                        try:
                            bot.remove_event_handler(callback_handler)
                        except Exception:
                            pass

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
        edit_id = msg.id if (msg and hasattr(msg, 'id')) else 0

        from main.plugins.pyroplug import get_msg
        from main.plugins.helpers import get_link, join

        try:
            if 't.me/+' in link or 't.me/joinchat/' in link:
                # Join channel
                res = await join(userbot, link)
                await safe_edit_message(owner_id, msg, f"🔑 *نتیجه ورود به کانال خصوصی:*\n{res}")
            elif not is_telegram_link:
                # Direct social media download
                await process_social_media_download(link, owner_id, msg)
            else:
                # Telegram link download
                await get_msg(userbot, Bot, bot, owner_id, edit_id, link, 0)
                await safe_send_message(owner_id, "✅ *دانلود و ارسال با موفقیت پایان یافت!*")
        except Exception as e:
            print(f"Error during execution: {e}")
            try:
                await safe_send_message(owner_id, f"❌ *خطا در پردازش لینک:*\n`{str(e)}`")
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
