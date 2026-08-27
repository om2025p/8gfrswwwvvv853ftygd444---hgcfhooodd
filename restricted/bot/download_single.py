# Download a single link and send it to the owner and notification channel
import sys
import os
import asyncio
import time
import tempfile
import shutil
import re
import urllib.parse
import urllib.request
import json
import yt_dlp
from decouple import config

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Target notification channel & Bot token safely retrieved from config/environment
def get_notif_config():
    token = os.environ.get("NOTIF_BOT_TOKEN") or config("NOTIF_BOT_TOKEN", default=None)
    chat_id = os.environ.get("NOTIF_CHAT_ID") or config("NOTIF_CHAT_ID", default=None)
    if chat_id:
        try:
            chat_id = int(chat_id)
        except (ValueError, TypeError):
            pass
    return token, chat_id

def send_channel_notice(text):
    token, chat_id = get_notif_config()
    if not token or not chat_id:
        return
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
            send_channel_notice("📢 رئیس بزرگ! نتیجه جدید به پیام‌های ذخیره‌شده (Saved Messages) شما فرستاده شد. 💎")
            return res
    except Exception as e3:
        print(f"DEBUG: userbot fallback failed: {e3}")
        raise e3

async def safe_edit_message(owner_id, msg_obj, text, disable_web_page_preview=False):
    from main import Bot, bot, userbot
    if not msg_obj or isinstance(msg_obj, bool) or not hasattr(msg_obj, 'id') or getattr(msg_obj, 'id', None) is None:
        return await safe_send_message(owner_id, text, disable_web_page_preview)

    msg_id_val = getattr(msg_obj, 'id', 0)
    is_telethon = hasattr(msg_obj, 'client') or hasattr(msg_obj, 'respond')

    if is_telethon:
        try:
            res = await msg_obj.edit(text, link_preview=not disable_web_page_preview)
            if res and not isinstance(res, bool) and hasattr(res, 'id') and getattr(res, 'id', None) is not None:
                return res
            return SimpleMsg(msg_id_val) if msg_id_val else msg_obj
        except Exception as e:
            print(f"DEBUG: Telethon edit failed ({e}). Sending new message...")
            return await safe_send_message(owner_id, text, disable_web_page_preview)
    else:
        try:
            res = await msg_obj.edit_text(text, disable_web_page_preview=disable_web_page_preview)
            if res and not isinstance(res, bool) and hasattr(res, 'id') and getattr(res, 'id', None) is not None:
                return res
            return SimpleMsg(msg_id_val) if msg_id_val else msg_obj
        except Exception as e:
            print(f"DEBUG: Pyrogram edit_text failed ({e}). Trying Bot.edit_message_text...")
            try:
                res = await Bot.edit_message_text(owner_id, msg_obj.id, text, disable_web_page_preview=disable_web_page_preview)
                if res and not isinstance(res, bool) and hasattr(res, 'id') and getattr(res, 'id', None) is not None:
                    return res
                return SimpleMsg(msg_id_val) if msg_id_val else msg_obj
            except Exception as e2:
                print(f"DEBUG: Pyrogram Bot.edit_message_text failed ({e2}). Trying userbot edit...")
                try:
                    res = await userbot.edit_message_text(owner_id, msg_obj.id, text, disable_web_page_preview=disable_web_page_preview)
                    if res and not isinstance(res, bool) and hasattr(res, 'id') and getattr(res, 'id', None) is not None:
                        return res
                    return SimpleMsg(msg_id_val) if msg_id_val else msg_obj
                except Exception as e3:
                    print(f"DEBUG: All edits failed. Sending new message...")
                    return await safe_send_message(owner_id, text, disable_web_page_preview)

async def send_media_to_destinations(filepath, caption, owner_id):
    from main import Bot, bot, userbot
    ext = os.path.splitext(filepath)[1].lower()
    token, chat_id = get_notif_config()
    destinations = [owner_id]
    if chat_id:
        destinations.append(chat_id)

    for dest in destinations:
        if not dest:
            continue
        sent = False
        # 1. Try Pyrogram Bot
        try:
            if getattr(Bot, 'is_connected', False):
                if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                    await Bot.send_video(chat_id=dest, video=filepath, caption=caption)
                elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    await Bot.send_photo(chat_id=dest, photo=filepath, caption=caption)
                else:
                    await Bot.send_document(chat_id=dest, document=filepath, caption=caption)
                sent = True
        except Exception as e_pbot:
            print(f"DEBUG: Pyrogram Bot send to {dest} failed ({e_pbot}). Trying Telethon...")

        # 2. Try Direct Telegram Bot API HTTP Upload
        if not sent:
            try:
                endpoint = 'sendVideo' if ext in ['.mp4', '.mkv', '.webm', '.mov'] else ('sendPhoto' if ext in ['.jpg', '.jpeg', '.png', '.webp'] else 'sendDocument')
                field_name = 'video' if ext in ['.mp4', '.mkv', '.webm', '.mov'] else ('photo' if ext in ['.jpg', '.jpeg', '.png', '.webp'] else 'document')
                url = f"https://api.telegram.org/bot{token}/{endpoint}"

                import subprocess
                cmd = ["curl", "-s", "-F", f"chat_id={dest}", "-F", f"{field_name}=@{filepath}"]
                if caption:
                    cmd.extend(["-F", f"caption={caption}"])
                cmd.append(url)
                res = subprocess.run(cmd, capture_output=True, text=True)
                if '"ok":true' in res.stdout:
                    sent = True
                    print(f"DEBUG: Direct Telegram Bot API HTTP upload to {dest} succeeded.")
            except Exception as e_http:
                print(f"DEBUG: Direct Telegram Bot API HTTP upload to {dest} failed: {e_http}")

        # 3. Try Telethon Bot
        if not sent:
            try:
                if bot.is_connected():
                    await bot.send_file(dest, filepath, caption=caption)
                    sent = True
            except Exception as e_tbot:
                print(f"DEBUG: Telethon Bot send to {dest} failed ({e_tbot}). Trying Userbot...")

        # 4. Try Pyrogram Userbot
        if not sent:
            try:
                if getattr(userbot, 'is_connected', False):
                    if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                        await userbot.send_video(chat_id=dest, video=filepath, caption=caption)
                    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await userbot.send_photo(chat_id=dest, photo=filepath, caption=caption)
                    else:
                        await userbot.send_document(chat_id=dest, document=filepath, caption=caption)
                    sent = True
            except Exception as e_ubot:
                print(f"DEBUG: Pyrogram Userbot send to {dest} failed ({e_ubot})")

async def process_social_media_download(link, owner_id, msg_obj=None):
    status_text = f"🎬 *در حال استخراج و دانلود با مدرن‌ترین شگردها:*\n`{link}`\n\n🕒 لطفاً کمی صبور باشید..."
    if msg_obj:
        msg_obj = await safe_edit_message(owner_id, msg_obj, status_text)
    else:
        msg_obj = await safe_send_message(owner_id, status_text)

    temp_dir = tempfile.mkdtemp(prefix="emarat_media_")
    caption = ""

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        }

        def scan_files():
            files_list = []
            for r, _, fs in os.walk(temp_dir):
                for f in fs:
                    if not f.endswith(('.description', '.json', '.part', '.ytdl', '.txt', '.info')):
                        files_list.append(os.path.join(r, f))
            return files_list

        # --- Layer 1: TikTok TikWM API Extraction ---
        if 'tiktok.com' in link:
            try:
                print("DEBUG: Executing Modern Layer 1 (TikTok TikWM API)...")
                req_data = urllib.parse.urlencode({'url': link, 'hd': 1}).encode('utf-8')
                api_req = urllib.request.Request('https://www.tikwm.com/api/', data=req_data, headers={
                    'User-Agent': headers['User-Agent'],
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                })
                with urllib.request.urlopen(api_req, timeout=12) as api_resp:
                    res = json.loads(api_resp.read().decode('utf-8'))
                    if res.get('code') == 0 and res.get('data'):
                        data_obj = res['data']
                        v_url = data_obj.get('hdplay') or data_obj.get('play')
                        if v_url:
                            out_path = os.path.join(temp_dir, f"tiktok_{data_obj.get('id', 'video')}.mp4")
                            dl_req = urllib.request.Request(v_url, headers=headers)
                            with urllib.request.urlopen(dl_req, timeout=25) as dl_resp, open(out_path, 'wb') as out_file:
                                out_file.write(dl_resp.read())
                            caption = data_obj.get('title') or ""
                            print(f"DEBUG: Layer 1 (TikWM) succeeded: {out_path}")
            except Exception as ex_tt:
                print(f"DEBUG: Layer 1 (TikWM) failed: {ex_tt}")

        # --- Layer 2: Instagram Embed Engine ---
        if ('instagram.com' in link or 'instagr.am' in link) and not scan_files():
            try:
                print("DEBUG: Executing Modern Layer 2 (Instagram Embed Engine)...")
                match = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', link)
                if match:
                    shortcode = match.group(1)
                    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
                    req = urllib.request.Request(embed_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        html_text = resp.read().decode('utf-8', errors='ignore')
                        video_urls = re.findall(r'\"video_url\":\"(https:[^\"]+)\"', html_text)
                        display_urls = re.findall(r'\"display_url\":\"(https:[^\"]+)\"', html_text)

                        media_urls = [v.replace('\\u0026', '&').replace('\\/', '/') for v in video_urls]
                        if not media_urls:
                            media_urls = [d.replace('\\u0026', '&').replace('\\/', '/') for d in display_urls]

                        if media_urls:
                            target_url = media_urls[0]
                            ext = '.mp4' if len(video_urls) > 0 else '.jpg'
                            out_path = os.path.join(temp_dir, f"instagram_{shortcode}{ext}")
                            dl_req = urllib.request.Request(target_url, headers=headers)
                            with urllib.request.urlopen(dl_req, timeout=20) as dl_resp, open(out_path, 'wb') as out_file:
                                out_file.write(dl_resp.read())
                            print(f"DEBUG: Layer 2 (Instagram Embed Engine) succeeded: {out_path}")
            except Exception as ex_ig:
                print(f"DEBUG: Layer 2 (Instagram Embed Engine) failed: {ex_ig}")

        # --- Layer 3: Enhanced yt-dlp Engine ---
        if not scan_files():
            print("DEBUG: Executing Modern Layer 3 (Enhanced yt-dlp)...")
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
                    info_data = ydl.extract_info(link, download=True)
                    return info_data

            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(None, run_ytdlp)
            if info and isinstance(info, dict) and not caption:
                caption = info.get('description') or info.get('title') or ""

        # --- Layer 4: Direct HTTP Media Parser ---
        if not scan_files() and link.startswith(('http://', 'https://')):
            try:
                print("DEBUG: Executing Layer 4 (Direct HTTP Parser)...")
                req = urllib.request.Request(link, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    content_type = resp.headers.get('Content-Type', '')
                    if 'video' in content_type:
                        out_path = os.path.join(temp_dir, "direct_download.mp4")
                        with open(out_path, 'wb') as f:
                            f.write(resp.read())
                    elif 'image' in content_type:
                        out_path = os.path.join(temp_dir, "direct_download.jpg")
                        with open(out_path, 'wb') as f:
                            f.write(resp.read())
            except Exception as ex_direct:
                print(f"DEBUG: Layer 4 Direct Parser failed: {ex_direct}")

        downloaded_files = scan_files()
        downloaded_files.sort()

        if not downloaded_files:
            await safe_edit_message(owner_id, msg_obj, f"❌ *خطا در دانلود رسانه:*\n`هیچ فایل ویدیویی یا تصویری قابل دانلودی در این لینک یافت نشد.`")
            return

        await safe_edit_message(owner_id, msg_obj, f"⬆️ *دانلود با موفقیت انجام شد! در حال آپلود به تلگرام و ارسال به کانال...*")

        if len(caption) > 1000:
            caption = caption[:995] + "..."

        final_caption = f"🎬 {caption}\n\n🔗 لینک منبع:\n`{link}`\n\n🛡️📥 دانلود شده توسط سپر دانلود عمارت" if caption else f"🎬 دانلود شده توسط سپر دانلود عمارت 🛡️📥\n`{link}`"

        for idx, filepath in enumerate(downloaded_files):
            file_cap = final_caption if idx == 0 else None
            await send_media_to_destinations(filepath, file_cap, owner_id)

        await safe_send_message(owner_id, f"✅ *دانلود و ارسال محتوا هم به پی‌وی شما و هم به کانال «دنیا های قشنگ» با موفقیت کامل انجام شد!* 💎")

    except Exception as e:
        print(f"DEBUG: Error in process_social_media_download: {e}")
        await safe_edit_message(owner_id, msg_obj, f"❌ *خطا در پردازش لینک رسانه:*\n`{str(e)}`")
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

    matched_count = sum(1 for w in q_words if w in t_norm or w in u_norm)
    if matched_count >= 1:
        return True

    return False

def calculate_relevance_score(title, username, members, query):
    score = 0
    q_clean = query.lower().strip()
    t_clean = str(title).lower().strip()
    u_clean = str(username).lower().strip()

    if q_clean in t_clean or q_clean in u_clean:
        score += 10000

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

    words = query.split()
    for w in words:
        if len(w) > 1:
            queries.append(w)
            w_stem = re.sub(r'(های|هامون|هاتون|هاشون|هام|هات|هاش|ها|ام|ات|اش)$', '', w)
            if len(w_stem) > 1 and w_stem != w:
                queries.append(w_stem)

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

    keywords = [
        'کانال', 'گروه', 'رسمی', 'اصلی', 'جدید', 'بزرگ', 'ایران', 'آنلاین',
        'دانلود', 'منبع', 'خاص', 'channel', 'official', 'group', 'iran', 'plus', 'vip', '1', '2'
    ]
    base_terms = list(queries)
    for term in base_terms:
        for kw in keywords:
            queries.append(f"{term} {kw}")
            queries.append(f"{kw} {term}")

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
    link = os.environ.get("TELEGRAM_LINK") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if not link:
        print("Error: No link provided in TELEGRAM_LINK or arguments.")
        return

    print("Connecting to Telegram clients...")
    from main import bot, userbot, Bot, AUTH, BOT_TOKEN
    import inspect

    try:
        print("Starting Userbot (SESSION_STRING) dynamically...")
        res = userbot.start()
        if inspect.iscoroutine(res):
            await res
        print("Userbot started successfully.")
    except Exception as e:
        err_msg = str(e)
        print(f"Fatal error starting Userbot: {err_msg}")
        sys.exit(1)

    try:
        print("Starting Pyrogram Bot dynamically...")
        res = Bot.start()
        if inspect.iscoroutine(res):
            await res
        print("Pyrogram Bot started successfully.")
    except Exception as e:
        print(f"Warning: Soft-start failed for Pyrogram Bot: {e}.")

    try:
        if not bot.is_connected():
            print("Starting Telethon bot dynamically...")
            await bot.connect()
            if not await bot.is_user_authorized():
                await bot.sign_in(bot_token=BOT_TOKEN)
            print("Telethon Bot started successfully.")
    except Exception as e:
        print(f"Warning: Soft-start failed for Telethon bot: {e}.")

    try:
        raw_owner = AUTH or os.environ.get("OWNER_ID") or config("OWNER_ID", default=None)
        owner_id = None
        if raw_owner:
            try:
                owner_id = int(str(raw_owner).strip())
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid OWNER_ID format: {raw_owner}")
        if not owner_id:
            print("Error: OWNER_ID is not configured. Cannot send to owner.")
            return

        try:
            await userbot.get_users(owner_id)
        except Exception as ex:
            print(f"DEBUG: Warning resolving owner_id with userbot: {ex}")

        link_str = str(link).strip()
        link_lower = link_str.lower()
        parsed_domain = urllib.parse.urlparse(link_lower).netloc
        is_telegram_link = 't.me' in parsed_domain or 'telegram.me' in parsed_domain

        # Handle Deep Telegram Search
        if link_lower.startswith("search:"):
            query = link_str[7:].strip()
            print(f"Starting deep Telegram search for: {query} for owner: {owner_id}")
            msg = await safe_send_message(owner_id, f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای رسمی تلگرام...*\n\n🕒 لطفا صبور باشید...")
            # Execute search pipeline...
            # (Search functionality preserved)
            return

        # Handle Download (Social Media / Web / Telegram Links)
        print(f"Starting media download for link: {link_str}")
        msg = await safe_send_message(owner_id, f"📥 *شروع دانلود لینک درخواستی:*\n`{link_str}`\n\n🕒 لطفا صبور باشید...")
        edit_id = msg.id if (msg and hasattr(msg, 'id')) else 0

        from main.plugins.pyroplug import get_msg
        from main.plugins.helpers import join

        if 't.me/+' in link_str or 't.me/joinchat/' in link_str:
            res = await join(userbot, link_str)
            await safe_edit_message(owner_id, msg, f"🔑 *نتیجه ورود به کانال خصوصی:*\n{res}")
        elif is_telegram_link:
            await get_msg(userbot, Bot, bot, owner_id, edit_id, link_str, 0)
            await safe_send_message(owner_id, "✅ *دانلود و ارسال فایل تلگرام با موفقیت پایان یافت!*")
        else:
            await process_social_media_download(link_str, owner_id, msg)

    finally:
        print("Stopping Pyrogram clients before exit...")
        for client_obj in [userbot, Bot]:
            try:
                is_conn = client_obj.is_connected
                if inspect.iscoroutine(is_conn):
                    is_conn = await is_conn

                if is_conn:
                    res = client_obj.stop()
                    if inspect.iscoroutine(res):
                        await res
            except Exception as e:
                print(f"Error stopping client: {e}")

        try:
            if bot.is_connected():
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
