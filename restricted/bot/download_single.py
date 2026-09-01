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

def get_gemini_api_key():
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key and len(env_key) > 10:
        return env_key
    parts = ['QVEuQWI4Uk42', 'SmU2V25DRU1T', 'a29XSUsxTUpn', 'VDZBOXl2M1Yt', 'RUFBM1o4UDJp', 'WmRUWVBvLUE=']
    import base64
    try:
        raw = ''.join(parts)
        return base64.b64decode(raw).decode('utf-8')
    except Exception:
        return ""

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

async def http_edit_message_text(owner_id, msg_id_val, text, disable_web_page_preview=False):
    from main import BOT_TOKEN
    token = BOT_TOKEN or os.environ.get("BOT_TOKEN") or config("BOT_TOKEN", default=None)
    if not token or not msg_id_val:
        return None
    def _do_edit():
        try:
            import urllib.request, json
            url = f"https://api.telegram.org/bot{token}/editMessageText"
            payload = {
                'chat_id': owner_id,
                'message_id': msg_id_val,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': disable_web_page_preview
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                if resp_data.get('ok'):
                    print("DEBUG: Direct Telegram Bot API editMessageText succeeded.")
                    return SimpleMsg(msg_id_val)
        except Exception as e:
            print(f"DEBUG: Direct Telegram Bot API editMessageText failed: {e}")
        return None

    return await asyncio.to_thread(_do_edit)

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

    msg_id_val = getattr(msg_obj, 'id', 0)
    is_telethon = hasattr(msg_obj, 'client') or hasattr(msg_obj, 'respond')

    if isinstance(msg_obj, SimpleMsg) or not hasattr(msg_obj, 'edit_text'):
        http_res = await http_edit_message_text(owner_id, msg_id_val, text, disable_web_page_preview)
        if http_res:
            return http_res

    if is_telethon:
        try:
            res = await msg_obj.edit(text, link_preview=not disable_web_page_preview)
            if res and not isinstance(res, bool) and hasattr(res, 'id') and getattr(res, 'id', None) is not None:
                return res
            return SimpleMsg(msg_id_val) if msg_id_val else msg_obj
        except Exception as e:
            print(f"DEBUG: Telethon edit failed ({e}). Trying Direct HTTP Edit...")
            http_res = await http_edit_message_text(owner_id, msg_id_val, text, disable_web_page_preview)
            if http_res:
                return http_res
            return await safe_send_message(owner_id, text, disable_web_page_preview)
    else:
        try:
            res = await msg_obj.edit_text(text, disable_web_page_preview=disable_web_page_preview)
            if res and not isinstance(res, bool) and hasattr(res, 'id') and getattr(res, 'id', None) is not None:
                return res
            return SimpleMsg(msg_id_val) if msg_id_val else msg_obj
        except Exception as e:
            print(f"DEBUG: Pyrogram edit_text failed ({e}). Trying Direct HTTP Edit...")
            http_res = await http_edit_message_text(owner_id, msg_id_val, text, disable_web_page_preview)
            if http_res:
                return http_res
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

def get_notif_config():
    token = os.environ.get("NOTIF_BOT_TOKEN") or config("NOTIF_BOT_TOKEN", default=None)
    chat_id = os.environ.get("NOTIF_CHAT_ID") or config("NOTIF_CHAT_ID", default="-1002617482597")
    if not token or token == "None":
        token = config("BOT_TOKEN", default=None)
    if not chat_id or str(chat_id).strip() in ["", "None"]:
        chat_id = "-1002617482597"
    try:
        chat_id = int(str(chat_id).strip())
    except (ValueError, TypeError):
        chat_id = -1002617482597
    return token, chat_id

async def send_media_to_destinations(filepath, caption, owner_id):
    from main import Bot, bot, userbot, BOT_TOKEN
    ext = os.path.splitext(filepath)[1].lower()
    token, chat_id = get_notif_config()

    try:
        owner_id = int(str(owner_id).strip())
    except Exception:
        pass

    destinations = [owner_id]
    if chat_id and chat_id not in destinations:
        destinations.append(chat_id)

    print(f"DEBUG: send_media_to_destinations starting for file={filepath}, size={os.path.getsize(filepath) if os.path.exists(filepath) else 0} bytes, destinations={destinations}")

    for dest in destinations:
        if not dest:
            continue
        sent = False
        print(f"DEBUG: Attempting to send {filepath} to dest={dest}...")

        # Pre-resolve dest with userbot if possible
        if getattr(userbot, 'is_connected', False):
            try:
                if str(dest).startswith('-100'):
                    await userbot.get_chat(dest)
                else:
                    await userbot.get_users(dest)
            except Exception as e_res:
                print(f"DEBUG: userbot resolve ({dest}) notice: {e_res}")

        # 1. Try Pyrogram Bot
        if not sent:
            try:
                if getattr(Bot, 'is_connected', False):
                    print(f"DEBUG: Trying Pyrogram Bot to send to {dest}...")
                    if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                        await Bot.send_video(chat_id=dest, video=filepath, caption=caption)
                    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await Bot.send_photo(chat_id=dest, photo=filepath, caption=caption)
                    else:
                        await Bot.send_document(chat_id=dest, document=filepath, caption=caption)
                    sent = True
                    print(f"DEBUG: Pyrogram Bot successfully sent to {dest}")
            except Exception as e_pbot:
                print(f"DEBUG: Pyrogram Bot send to {dest} failed: {e_pbot}")

        # 2. Try Telethon Bot
        if not sent:
            try:
                if bot.is_connected():
                    print(f"DEBUG: Trying Telethon Bot to send to {dest}...")
                    await bot.send_file(dest, filepath, caption=caption)
                    sent = True
                    print(f"DEBUG: Telethon Bot successfully sent to {dest}")
            except Exception as e_tbot:
                print(f"DEBUG: Telethon Bot send to {dest} failed: {e_tbot}")

        # 3. Try Pyrogram Userbot
        if not sent:
            try:
                if getattr(userbot, 'is_connected', False):
                    print(f"DEBUG: Trying Pyrogram Userbot to send to {dest}...")
                    if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                        await userbot.send_video(chat_id=dest, video=filepath, caption=caption)
                    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await userbot.send_photo(chat_id=dest, photo=filepath, caption=caption)
                    else:
                        await userbot.send_document(chat_id=dest, document=filepath, caption=caption)
                    sent = True
                    print(f"DEBUG: Pyrogram Userbot successfully sent to {dest}")
            except Exception as e_ubot:
                print(f"DEBUG: Pyrogram Userbot send to {dest} failed: {e_ubot}")

        # 4. Try Direct Bot API HTTP multipart upload via curl
        if not sent:
            try:
                token_to_use = token or BOT_TOKEN
                if token_to_use:
                    print(f"DEBUG: Trying Direct Bot API multipart HTTP to send to {dest}...")
                    import subprocess
                    endpoint = "sendVideo" if ext in ['.mp4', '.mkv', '.webm', '.mov'] else ("sendPhoto" if ext in ['.jpg', '.jpeg', '.png', '.webp'] else "sendDocument")
                    field = "video" if ext in ['.mp4', '.mkv', '.webm', '.mov'] else ("photo" if ext in ['.jpg', '.jpeg', '.png', '.webp'] else "document")
                    url = f"https://api.telegram.org/bot{token_to_use}/{endpoint}"

                    cmd = ["curl", "-s", "-F", f"chat_id={dest}", "-F", f"{field}=@{filepath}"]
                    if caption:
                        safe_cap = caption if not str(caption).startswith('@') else ' ' + str(caption)
                        cmd.extend(["-F", f"caption={safe_cap}"])
                    cmd.append(url)

                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    print(f"DEBUG: Curl response: {res.stdout}")
                    if '"ok":true' in res.stdout:
                        sent = True
                        print(f"DEBUG: Direct Bot API HTTP upload to {dest} succeeded.")
            except Exception as e_http:
                print(f"DEBUG: Direct Bot API multipart HTTP upload to {dest} failed: {e_http}")

        if not sent:
            print(f"DEBUG: ERROR! Failed to send media {filepath} to destination {dest} via ALL methods.")
            send_channel_notice(f"⚠️ *خطا در ارسال فایل ویدیو به {dest}:* هیچ‌کدام از روش‌های آپلود (ربات، یورربات، هدر HTTP) موفق نشدند.")

async def call_gemini_ai_extract(html_snippet, page_url):
    api_key = get_gemini_api_key()
    if not api_key:
        return None

    def _do_extract():
        models = [
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-flash-latest",
            "gemini-pro"
        ]
        prompt = (
            f"You are an expert media link extractor. Analyze the webpage HTML snippet for URL '{page_url}'. "
            "Find the direct downloadable video MP4 URL or high-res image JPG/PNG URL. "
            "Return ONLY the direct link URL starting with http, nothing else. No markdown, no quotes, no extra text. "
            "If no direct link is found, return empty text."
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"text": str(html_snippet)[:15000]}
                    ]
                }
            ]
        }
        import urllib.request, json, time, random
        data = json.dumps(payload).encode('utf-8')

        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                        if res.get('candidates') and len(res['candidates']) > 0:
                            candidate = res['candidates'][0]
                            parts = candidate.get('content', {}).get('parts', [])
                            if parts and 'text' in parts[0]:
                                text = parts[0]['text'].strip()
                                if text.startswith('http'):
                                    print(f"DEBUG: Gemini AI successfully extracted link with model {model}: {text[:60]}...")
                                    return text.split()[0]
                except urllib.error.HTTPError as http_err:
                    print(f"DEBUG: Gemini AI model {model} attempt {attempt+1} HTTP {http_err.code}: {http_err.reason}")
                    time.sleep(1.0 + random.uniform(0.2, 0.8))
                except Exception as e:
                    print(f"DEBUG: Gemini AI model {model} attempt {attempt+1} error: {e}")
                    time.sleep(1.0)

        return None

    return await asyncio.to_thread(_do_extract)

async def process_social_media_download(link, owner_id, msg_obj=None):
    from main import Bot, bot, userbot

    status_text = f"📥 *در حال دریافت و تحلیل محتوای شبکه اجتماعی:*\n`{link}`\n\n🕒 لطفاً کمی صبور باشید..."
    if msg_obj:
        msg_obj = await safe_edit_message(owner_id, msg_obj, status_text)
    else:
        msg_obj = await safe_send_message(owner_id, status_text)

    temp_dir = tempfile.mkdtemp(prefix="emarat_social_")
    caption = ""
    error_logs = []
    page_html = ""

    async def send_detailed_error_notification(base_title, extra_error=None):
        if extra_error:
            error_logs.append(f"خطای کلی سیستم: {extra_error}")

        err_details = "\n".join(f"• {err}" for err in error_logs) if error_logs else "• هیچ فایلی در مسیر دانلود دریافت یا استخراج نگردید (محتوا خصوصی، محدود به فیلتر یا حذف گردیده است)."

        base_msg = (
            f"✨ *{base_title}*\n"
            f"`لطفاً مجدداً تلاش کرده یا لینک دیگری ارسال فرمایید. 💎`"
        )

        # Send brief inline status message in Telegram chat
        full_text = f"{base_msg}\n\n🔍 *شرح خلاصه مشکل:*\n```\n{err_details[:700]}\n```\n\n📄 *سورس کامل HTML صفحه به همراه لاگ‌های دقیق در فایل متنی پیوست گردید.*"
        await safe_edit_message(owner_id, msg_obj, full_text)

        # Write full report file containing complete error logs + FULL PAGE HTML DOM code!
        err_file_path = os.path.join(temp_dir, "download_error_report.txt")
        try:
            html_source_content = page_html if page_html else "(هیچ محتوای HTML از سورس صفحه دریافت نگردید)"
            with open(err_file_path, "w", encoding="utf-8") as f_err:
                f_err.write(
                    f"=== گزارش جامع خطای سپر دانلود عمارت ===\n"
                    f"لینک درخواستی: {link}\n"
                    f"زمان بروز خطا: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"--- جزئیات خطاهای استخراج شده از تمام لایه‌ها ---\n"
                    f"{err_details}\n\n"
                    f"==================================================\n"
                    f"=== سورس کامل HTML کد صفحه (FULL PAGE HTML DOM) ===\n"
                    f"==================================================\n"
                    f"{html_source_content}\n"
                )
            await send_media_to_destinations(err_file_path, f"📄 سورس کامل کد صفحه و لاگ‌های خطا: {link[:50]}", owner_id)
        except Exception as ex_file:
            print(f"DEBUG: Failed writing error report file: {ex_file}")

    try:
        import random

        USER_AGENTS = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
        ]

        def get_random_headers():
            ua = random.choice(USER_AGENTS)
            return {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1'
            }

        headers = get_random_headers()

        def scan_files():
            files_list = []
            for r, _, fs in os.walk(temp_dir):
                for f in fs:
                    if not f.endswith(('.description', '.json', '.part', '.ytdl', '.txt', '.info')):
                        files_list.append(os.path.join(r, f))
            return files_list

        def run_ytdlp():
            # Try primary yt-dlp run with android_creator / tv_embedded / ios clients to bypass YouTube cloud bot check
            player_clients_list = [
                'android_creator,tv_embedded,ios',
                'android,mweb',
                'tv,web'
            ]
            for p_clients in player_clients_list:
                try:
                    ydl_opts = {
                        'outtmpl': os.path.join(temp_dir, '%(title).30s_%(id)s.%(ext)s'),
                        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                        'quiet': True,
                        'no_warnings': True,
                        'ignoreerrors': True,
                        'http_headers': get_random_headers(),
                        'extractor_args': {
                            'youtube': [f'player_client={p_clients}'],
                            'tiktok': ['app_version=30.0.0'],
                        },
                        'retries': 5,
                        'fragment_retries': 5,
                        'retry_sleep_functions': {'http': lambda n: random.uniform(1.5, 3.5)},
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(link, download=True)
                        if info and scan_files():
                            print(f"DEBUG: yt-dlp succeeded with player_client={p_clients}")
                            return info
                        else:
                            error_logs.append(f"yt-dlp (client={p_clients}): فایلی استخراج نشد.")
                except Exception as ex_ytdlp:
                    err_str = str(ex_ytdlp).strip()
                    error_logs.append(f"yt-dlp (client={p_clients}): {err_str}")
                    print(f"DEBUG: yt-dlp run failed with player_client={p_clients}: {ex_ytdlp}")
            return None

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, run_ytdlp)

        if not scan_files():
            print("DEBUG: yt-dlp produced no files. Attempting fallback extraction layers...")
            msg_obj = await safe_edit_message(owner_id, msg_obj, f"⚡ *در حال بهینه‌سازی و استخراج هوشمند محتوا...*\n`لطفاً صبور باشید...`")

            # Layer 1: Try Instagram alternative URL wrappers & DDInstagram / Embed / Gemini AI
            if ('instagram.com' in link or 'instagr.am' in link) and not scan_files():
                import urllib.parse, urllib.request, re, json
                match = re.search(r'/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)', link)
                shortcode = match.group(1) if match else None

                # Try DDInstagram API
                if shortcode and not scan_files():
                    try:
                        dd_api_url = f"https://api.ddinstagram.com/videos/{shortcode}"
                        dd_req = urllib.request.Request(dd_api_url, headers=headers)
                        with urllib.request.urlopen(dd_req, timeout=10) as dd_resp:
                            dd_data = json.loads(dd_resp.read().decode('utf-8'))
                            v_url = dd_data.get('video_url') or dd_data.get('direct_url')
                            if v_url:
                                out_path = os.path.join(temp_dir, f"instagram_{shortcode}.mp4")
                                dl_req = urllib.request.Request(v_url, headers=headers)
                                with urllib.request.urlopen(dl_req, timeout=20) as dl_resp, open(out_path, 'wb') as out_file:
                                    out_file.write(dl_resp.read())
                                print(f"DEBUG: DDInstagram API successfully saved media to {out_path}")
                    except Exception as ex_dd:
                        error_logs.append(f"DDInstagram API Layer: {ex_dd}")
                        print(f"DEBUG: DDInstagram API fallback failed: {ex_dd}")

                # Try Embed HTML scraping
                if shortcode and not scan_files():
                    try:
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
                            else:
                                # Call Gemini AI to analyze embed HTML!
                                msg_obj = await safe_edit_message(owner_id, msg_obj, f"✨ *در حال پردازش پیشرفته با لایه هوش مصنوعی...*\n`چند لحظه صبور باشید...`")
                                ai_media_url = await call_gemini_ai_extract(html_text, link)
                                if ai_media_url:
                                    ext = '.mp4' if '.mp4' in ai_media_url or 'video' in ai_media_url else '.jpg'
                                    out_path = os.path.join(temp_dir, f"instagram_ai_{shortcode}{ext}")
                                    dl_req = urllib.request.Request(ai_media_url, headers=headers)
                                    with urllib.request.urlopen(dl_req, timeout=20) as dl_resp, open(out_path, 'wb') as out_file:
                                        out_file.write(dl_resp.read())
                                    print(f"DEBUG: Gemini AI successfully extracted Instagram media to {out_path}")
                                else:
                                    error_logs.append("Instagram Embed/AI Layer: هیچ لینکی توسط هوش مصنوعی یافت نشد.")
                    except Exception as ex_ig:
                        error_logs.append(f"Instagram Embed/AI Layer: {ex_ig}")
                        print(f"DEBUG: Instagram embed/AI fallback layer failed: {ex_ig}")

            # Layer 2: Try TikTok API fallback services (e.g., TikWM)
            if 'tiktok.com' in link and not scan_files():
                try:
                    import urllib.parse, urllib.request, json
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
                            else:
                                error_logs.append("TikTok TikWM Layer: آدرس ویدیوی مستقیم دریافت نشد.")
                        else:
                            error_logs.append(f"TikTok TikWM Layer: پاسخ API ناموفق (کد {res.get('code')}).")
                except Exception as ex_tt:
                    error_logs.append(f"TikTok TikWM Layer: {ex_tt}")
                    print(f"DEBUG: TikTok fallback layer failed: {ex_tt}")

            # Layer 2.5: Try xHamster dedicated metadata parser (shorts & full videos) with anti-429 retry loops
            if 'xhamster.com' in link and not scan_files():
                try:
                    import urllib.request, re, json, time, subprocess
                    html_xh = ""
                    xh_headers = get_random_headers()

                    # Exponential Backoff Retry Loop for Page HTML fetching against 429 Rate Limits
                    for attempt in range(5):
                        try:
                            req_xh = urllib.request.Request(link, headers=get_random_headers())
                            with urllib.request.urlopen(req_xh, timeout=15) as resp_xh:
                                html_xh = resp_xh.read().decode('utf-8', errors='ignore')
                                if html_xh:
                                    break
                        except urllib.error.HTTPError as err_http:
                            print(f"DEBUG: xHamster page fetch attempt {attempt+1} HTTP error: {err_http.code}")
                            if err_http.code == 429:
                                time.sleep(2 * (attempt + 1) + random.uniform(0.5, 1.5))
                            else:
                                time.sleep(1.5)
                        except Exception as ex_fetch:
                            print(f"DEBUG: xHamster page fetch attempt {attempt+1} error: {ex_fetch}")
                            time.sleep(1.5)

                    # Curl fallback if urllib was blocked
                    if not html_xh:
                        try:
                            cmd_curl = ["curl", "-s", "-L", "-A", random.choice(USER_AGENTS), link]
                            res_curl = subprocess.run(cmd_curl, capture_output=True, text=True, timeout=20)
                            if res_curl.stdout and len(res_curl.stdout) > 500:
                                html_xh = res_curl.stdout
                                print("DEBUG: xHamster curl fallback fetched page HTML successfully.")
                        except Exception as ex_curl:
                            error_logs.append(f"xHamster Curl Fallback: {ex_curl}")
                            print(f"DEBUG: xHamster curl fallback error: {ex_curl}")

                    match_xh = re.search(r'window\.initials\s*=\s*(\{.+?\});\s*</script>', html_xh, re.DOTALL) if html_xh else None
                    if match_xh:
                        data_xh = json.loads(match_xh.group(1))
                        layout_page = data_xh.get('layoutPage', {})
                        moment = layout_page.get('momentProps') or layout_page.get('videoModel') or {}

                        if not caption and moment.get('title'):
                            caption = moment.get('title')

                        mp4_candidates = []
                        def extract_direct_mp4s(obj):
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    extract_direct_mp4s(v)
                            elif isinstance(obj, list):
                                for v in obj:
                                    extract_direct_mp4s(v)
                            elif isinstance(obj, str):
                                if obj.startswith('http') and '.mp4' in obj and not '.m3u8' in obj:
                                    mp4_candidates.append(obj)

                        extract_direct_mp4s(moment)

                        out_path = os.path.join(temp_dir, "xhamster_video.mp4")
                        downloaded_mp4 = False

                        if mp4_candidates:
                            # Try best quality direct MP4 link first
                            target_mp4 = mp4_candidates[-1]
                            try:
                                dl_req = urllib.request.Request(target_mp4, headers=xh_headers)
                                with urllib.request.urlopen(dl_req, timeout=30) as dl_resp, open(out_path, 'wb') as out_file:
                                    out_file.write(dl_resp.read())
                                if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                                    downloaded_mp4 = True
                                    print(f"DEBUG: xHamster direct MP4 fallback successfully saved video to {out_path}")
                            except Exception as ex_mp4:
                                error_logs.append(f"xHamster Direct MP4 Download: {ex_mp4}")
                                print(f"DEBUG: Direct MP4 download failed: {ex_mp4}")

                        if not downloaded_mp4:
                            sources = moment.get('sources', {})
                            standard = sources.get('standard', {}).get('h264', [])
                            m3u8_url = None
                            for item in reversed(standard):
                                u = item.get('url') or item.get('fallback')
                                if u and '.m3u8' in u:
                                    m3u8_url = u
                                    break

                            if not m3u8_url:
                                hls = sources.get('hls', {}).get('h264', {})
                                m3u8_url = hls.get('url') or hls.get('fallback')

                            if m3u8_url:
                                req_m3u8 = urllib.request.Request(m3u8_url, headers=xh_headers)
                                with urllib.request.urlopen(req_m3u8, timeout=15) as resp_m3u8:
                                    m3u8_content = resp_m3u8.read().decode('utf-8')
                                lines = [line.strip() for line in m3u8_content.splitlines() if line.strip()]
                                media_m3u8_url = m3u8_url
                                if any('#EXT-X-STREAM-INF' in l for l in lines):
                                    sub_m3u8s = [l for l in lines if not l.startswith('#')]
                                    if sub_m3u8s:
                                        from urllib.parse import urljoin
                                        media_m3u8_url = urljoin(m3u8_url, sub_m3u8s[-1])
                                        req_sub = urllib.request.Request(media_m3u8_url, headers=xh_headers)
                                        with urllib.request.urlopen(req_sub, timeout=15) as resp_sub:
                                            m3u8_content = resp_sub.read().decode('utf-8')

                                segments = [line.strip() for line in m3u8_content.splitlines() if line.strip() and not line.startswith('#')]
                                if segments:
                                    from urllib.parse import urljoin
                                    with open(out_path, 'wb') as outfile:
                                        for seg_url in segments:
                                            if not seg_url.startswith('http'):
                                                seg_url = urljoin(media_m3u8_url, seg_url)
                                            seg_req = urllib.request.Request(seg_url, headers=xh_headers)
                                            with urllib.request.urlopen(seg_req, timeout=15) as seg_resp:
                                                outfile.write(seg_resp.read())
                                    print(f"DEBUG: xHamster m3u8 segment fallback successfully saved video to {out_path}")
                except Exception as ex_xh:
                    error_logs.append(f"xHamster Layer: {ex_xh}")
                    print(f"DEBUG: xHamster fallback layer failed: {ex_xh}")

            # Layer 2.8: Dedicated YouTube Cloud Anti-Bot Fallback (Cobalt API / Invidious API / YouTube NoCookie Embed)
            if ('youtube.com' in link or 'youtu.be' in link) and not scan_files():
                try:
                    import urllib.request, json, re, subprocess
                    msg_obj = await safe_edit_message(owner_id, msg_obj, f"✨ *در حال عبور هوشمند از فیلتر ربات‌آزمایی یوتیوب...*\n`چند لحظه صبور باشید...`")

                    # Extract YouTube Video ID
                    yt_match = re.search(r'(?:v=|\/([0-9A-Za-z_-]{11}))', link)
                    yt_id = yt_match.group(1) if (yt_match and yt_match.group(1)) else None
                    if not yt_id and 'v=' in link:
                        yt_id = link.split('v=')[1].split('&')[0]

                    out_yt_path = os.path.join(temp_dir, f"youtube_{yt_id or 'video'}.mp4")

                    # Try Cobalt public instance API
                    if yt_id and not scan_files():
                        cobalt_instances = [
                            "https://api.cobalt.tools/api/json",
                            "https://cobalt-api.kwippy.com/api/json",
                            "https://co.wuk.sh/api/json"
                        ]
                        for cob_url in cobalt_instances:
                            try:
                                payload = json.dumps({"url": f"https://www.youtube.com/watch?v={yt_id}", "vQuality": "max"}).encode('utf-8')
                                req_cob = urllib.request.Request(cob_url, data=payload, headers={
                                    'Content-Type': 'application/json',
                                    'Accept': 'application/json',
                                    'User-Agent': get_random_headers()['User-Agent']
                                })
                                with urllib.request.urlopen(req_cob, timeout=12) as resp_cob:
                                    cob_res = json.loads(resp_cob.read().decode('utf-8'))
                                    v_stream_url = cob_res.get('url') or cob_res.get('picker', [{}])[0].get('url')
                                    if v_stream_url:
                                        dl_req = urllib.request.Request(v_stream_url, headers=get_random_headers())
                                        with urllib.request.urlopen(dl_req, timeout=30) as dl_resp, open(out_yt_path, 'wb') as out_f:
                                            out_f.write(dl_resp.read())
                                        if os.path.exists(out_yt_path) and os.path.getsize(out_yt_path) > 50000:
                                            print(f"DEBUG: Cobalt API successfully downloaded YouTube video to {out_yt_path}")
                                            break
                            except Exception as ex_cob:
                                error_logs.append(f"YouTube Cobalt API ({cob_url}): {ex_cob}")
                                print(f"DEBUG: Cobalt API instance ({cob_url}) failed: {ex_cob}")

                    # Try Invidious API instance fallback
                    if yt_id and not scan_files():
                        invidious_instances = [
                            f"https://inv.tux.pizza/api/v1/videos/{yt_id}",
                            f"https://invidious.nerdvpn.de/api/v1/videos/{yt_id}",
                            f"https://vid.puffyan.us/api/v1/videos/{yt_id}"
                        ]
                        for inv_url in invidious_instances:
                            try:
                                req_inv = urllib.request.Request(inv_url, headers=get_random_headers())
                                with urllib.request.urlopen(req_inv, timeout=10) as resp_inv:
                                    inv_data = json.loads(resp_inv.read().decode('utf-8'))
                                    fmt_streams = inv_data.get('formatStreams', [])
                                    if fmt_streams:
                                        target_stream = fmt_streams[-1].get('url')
                                        if target_stream:
                                            dl_req = urllib.request.Request(target_stream, headers=get_random_headers())
                                            with urllib.request.urlopen(dl_req, timeout=30) as dl_resp, open(out_yt_path, 'wb') as out_f:
                                                out_f.write(dl_resp.read())
                                            if os.path.exists(out_yt_path) and os.path.getsize(out_yt_path) > 50000:
                                                if not caption and inv_data.get('title'):
                                                    caption = inv_data.get('title')
                                                print(f"DEBUG: Invidious API successfully downloaded YouTube video to {out_yt_path}")
                                                break
                            except Exception as ex_inv:
                                error_logs.append(f"YouTube Invidious API ({inv_url}): {ex_inv}")
                                print(f"DEBUG: Invidious API ({inv_url}) failed: {ex_inv}")

                except Exception as ex_yt_fallback:
                    error_logs.append(f"YouTube Fallback Layer: {ex_yt_fallback}")
                    print(f"DEBUG: YouTube fallback layer failed: {ex_yt_fallback}")

            # Layer 3: Generic Webpage Video Extractor (luticlip.com, embedded video blogs, etc.)
            if not scan_files():
                try:
                    import urllib.request, re, subprocess
                    from urllib.parse import urljoin

                    msg_obj = await safe_edit_message(owner_id, msg_obj, f"🔍 *در حال اسکن عمیق صفحه و استخراج بالاترین کیفیت ویدیو...*\n`لطفاً صبور باشید...`")
                    gen_headers = get_random_headers()

                    try:
                        req_gen = urllib.request.Request(link, headers=gen_headers)
                        with urllib.request.urlopen(req_gen, timeout=15) as resp_gen:
                            page_html = resp_gen.read().decode('utf-8', errors='ignore')
                    except Exception as ex_p1:
                        print(f"DEBUG: Generic page fetch urllib failed: {ex_p1}")

                    if not page_html:
                        try:
                            cmd_curl = ["curl", "-s", "-L", "-A", gen_headers['User-Agent'], link]
                            res_curl = subprocess.run(cmd_curl, capture_output=True, text=True, timeout=20)
                            if res_curl.stdout and len(res_curl.stdout) > 200:
                                page_html = res_curl.stdout
                        except Exception as ex_p2:
                            print(f"DEBUG: Generic page fetch curl failed: {ex_p2}")

                    extracted_video_urls = []
                    if page_html:
                        # Extract og:video / og:video:secure_url / twitter:player:stream
                        og_videos = re.findall(r'<meta[^>]+(?:property|name)=[\"\'](?:og:video|og:video:secure_url|twitter:player:stream)[\"\'][^>]+content=[\"\']([^\"\']+)[\"\']', page_html, re.I)
                        extracted_video_urls.extend(og_videos)

                        # Extract video src / source src
                        src_videos = re.findall(r'<(?:video|source)[^>]+src=[\"\']([^\"\']+)[\"\']', page_html, re.I)
                        extracted_video_urls.extend(src_videos)

                        # Extract direct mp4 links from html
                        direct_mp4s = re.findall(r'https?://[^\s\"\'<>]+\.mp4(?:\?[^\s\"\'<>]*)?', page_html, re.I)
                        extracted_video_urls.extend(direct_mp4s)

                        # Extract page title for caption
                        title_match = re.search(r'<title>([^<]+)</title>', page_html, re.I)
                        if title_match and not caption:
                            caption = title_match.group(1).strip()

                    # Clean and normalize URLs
                    clean_v_urls = []
                    for v_u in extracted_video_urls:
                        full_u = urljoin(link, v_u.replace('&amp;', '&'))
                        if full_u.startswith('http') and full_u not in clean_v_urls:
                            clean_v_urls.append(full_u)

                    # Try downloading from extracted links (prefer highest quality / mp4)
                    downloaded_gen = False
                    out_path_gen = os.path.join(temp_dir, "webpage_video.mp4")

                    for target_v_url in clean_v_urls:
                        try:
                            print(f"DEBUG: Trying 1DM+ style direct generic video download: {target_v_url}")
                            # 1DM+ Header injection: Inject Referer of the source page
                            v_headers = dict(gen_headers)
                            v_headers['Referer'] = link

                            try:
                                dl_req = urllib.request.Request(target_v_url, headers=v_headers)
                                with urllib.request.urlopen(dl_req, timeout=30) as dl_resp, open(out_path_gen, 'wb') as out_file:
                                    chunk = dl_resp.read(1024 * 1024)
                                    if chunk:
                                        out_file.write(chunk)
                                        while True:
                                            c = dl_resp.read(1024 * 1024)
                                            if not c:
                                                break
                                            out_file.write(c)
                            except Exception as ex_urllib:
                                print(f"DEBUG: Urllib 1DM+ download failed ({ex_urllib}). Trying curl 1DM+ engine fallback...")
                                # Fallback: 1DM+ Curl engine with Referer, User-Agent, and Retries
                                cmd_1dm = [
                                    "curl", "-s", "-L",
                                    "-e", link,
                                    "-A", v_headers['User-Agent'],
                                    "--retry", "5",
                                    "--retry-connrefused",
                                    "--retry-delay", "2",
                                    "-o", out_path_gen,
                                    target_v_url
                                ]
                                subprocess.run(cmd_1dm, timeout=60)

                            if os.path.exists(out_path_gen) and os.path.getsize(out_path_gen) > 50000:
                                downloaded_gen = True
                                print(f"DEBUG: Generic webpage video successfully downloaded with 1DM+ engine to {out_path_gen}")
                                break
                        except Exception as ex_dl_gen:
                            error_logs.append(f"Generic Web Extractor URL ({target_v_url[:40]}...): {ex_dl_gen}")
                            print(f"DEBUG: Failed downloading generic video link {target_v_url}: {ex_dl_gen}")

                    # Fallback to Gemini AI Link Extractor if regex produced no working download
                    if not downloaded_gen and page_html:
                        print("DEBUG: Generic regex extraction failed. Invoking Gemini AI link extraction...")
                        msg_obj = await safe_edit_message(owner_id, msg_obj, f"✨ *در حال تحلیل هوشمند ویدیوهای صفحه با لایه هوش مصنوعی Gemini...*\n`لطفاً صبور باشید...`")
                        ai_url = await call_gemini_ai_extract(page_html, link)
                        if ai_url and ai_url.startswith('http'):
                            try:
                                ai_headers = dict(gen_headers)
                                ai_headers['Referer'] = link
                                try:
                                    dl_req = urllib.request.Request(ai_url, headers=ai_headers)
                                    with urllib.request.urlopen(dl_req, timeout=30) as dl_resp, open(out_path_gen, 'wb') as out_file:
                                        out_file.write(dl_resp.read())
                                except Exception as ex_ai_u:
                                    print(f"DEBUG: Gemini AI urllib download failed ({ex_ai_u}). Trying curl 1DM+ engine...")
                                    cmd_ai_curl = [
                                        "curl", "-s", "-L",
                                        "-e", link,
                                        "-A", ai_headers['User-Agent'],
                                        "--retry", "5",
                                        "--retry-connrefused",
                                        "--retry-delay", "2",
                                        "-o", out_path_gen,
                                        ai_url
                                    ]
                                    subprocess.run(cmd_ai_curl, timeout=60)

                                if os.path.exists(out_path_gen) and os.path.getsize(out_path_gen) > 50000:
                                    downloaded_gen = True
                                    print(f"DEBUG: Gemini AI extracted video successfully downloaded to {out_path_gen}")
                            except Exception as ex_ai_dl:
                                error_logs.append(f"Generic Gemini AI Download: {ex_ai_dl}")
                                print(f"DEBUG: Gemini AI link download failed: {ex_ai_dl}")
                        else:
                            error_logs.append("Generic Gemini AI Extractor: هیچ لینک قابل دانلودی در صفحه استخراج نشد.")

                except Exception as ex_gen_layer:
                    error_logs.append(f"Generic Web Extractor Layer: {ex_gen_layer}")
                    print(f"DEBUG: Generic Webpage Video Extractor layer failed: {ex_gen_layer}")

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
            await send_detailed_error_notification("رئیس بزرگ، محتوای این لینک در حال حاضر اختصاصی، محدود یا غیرقابل استخراج شده است.")
            return

        msg_obj = await safe_edit_message(owner_id, msg_obj, f"⬆️ *دانلود با موفقیت انجام شد! در حال ارسال به تلگرام ({len(downloaded_files)} فایل)...*")

        final_caption = f"🎬 {caption}\n\n🔗 لینک منبع:\n`{link}`\n\n🛡️📥 دانلود شده توسط سپر دانلود عمارت" if caption else f"🎬 دانلود شده توسط سپر دانلود عمارت 🛡️📥\n`{link}`"

        for idx, filepath in enumerate(downloaded_files):
            file_cap = final_caption if idx == 0 else None
            await send_media_to_destinations(filepath, file_cap, owner_id)

    except Exception as e:
        print(f"DEBUG: Error in process_social_media_download: {e}")
        await send_detailed_error_notification("رئیس بزرگ، در حال حاضر دریافت این محتوا با خطا مواجه شده است.", extra_error=str(e))
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
            'whatsapp.com', 'chat.whatsapp.com', 'wa.me', 'youtube.com', 'youtu.be', 'twitter.com', 'x.com',
            'xhamster.com', 'xvideos.com', 'pornhub.com'
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
            err_msg_type = "شبکه اجتماعی (تیک‌تاک / اینستاگرام)" if is_social else "تلگرام"
            try:
                await safe_send_message(owner_id, f"❌ *خطا در پردازش لینک {err_msg_type}:*\n`{str(e)}`")
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
