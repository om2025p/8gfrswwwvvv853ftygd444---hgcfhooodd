# Zip/Rar/7z Compressed File Extractor & Categorized Folder Telegram Dispatcher
import sys
import os
import asyncio
import time
import json
import re
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from decouple import config

# Add current directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Persistent Tracking Files
SENT_ZIP_FILES_DB = "restricted_zip_sent.json"
ZIP_STATS_DB = "restricted_zip_stats.json"

MAX_BATCH_BYTES = 2 * 1024 * 1024 * 1024 # 2 GB limit per execution cycle

def log_print(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    prefix = {
        "INFO": "ℹ️ [INFO]",
        "SUCCESS": "✅ [SUCCESS]",
        "WARNING": "⚠️ [WARNING]",
        "ERROR": "❌ [ERROR]",
        "DEBUG": "🔍 [DEBUG]",
        "PROGRESS": "⚡ [PROGRESS]"
    }.get(level, "ℹ️ [LOG]")
    formatted = f"[{timestamp}] {prefix} {msg}"
    print(formatted, flush=True)

def get_db_paths(filename):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return [
        os.path.join(os.path.dirname(__file__), filename), # restricted/bot/
        os.path.join(base_dir, filename),                  # restricted/
        os.path.join(base_dir, "bot", filename)            # restricted/bot/
    ]

def load_sent_files_db():
    for p in get_db_paths(SENT_ZIP_FILES_DB):
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        log_print(f"Loaded {len(data)} sent file keys from persistent DB: {p}", "DEBUG")
                        return set(data)
            except Exception as e:
                log_print(f"Error loading sent files DB from {p}: {e}", "WARNING")
    return set()

def save_sent_files_db(sent_set):
    data = sorted(list(sent_set))
    for p in get_db_paths(SENT_ZIP_FILES_DB):
        try:
            parent = os.path.dirname(p)
            if parent and not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_print(f"Saved {len(data)} sent file keys to {p}", "DEBUG")
        except Exception as e:
            log_print(f"Error saving sent files DB to {p}: {e}", "WARNING")

def update_zip_stats(total_files, sent_files, total_bytes_sent, current_folder, status_text):
    try:
        stats = {
            "total_files": total_files,
            "sent_files": sent_files,
            "total_bytes_sent": total_bytes_sent,
            "total_mb_sent": round(total_bytes_sent / (1024 * 1024), 2),
            "current_folder": current_folder,
            "status_text": status_text,
            "last_updated": time.time(),
            "last_updated_jalali": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        for p in get_db_paths(ZIP_STATS_DB):
            try:
                parent = os.path.dirname(p)
                if parent and not os.path.exists(parent):
                    os.makedirs(parent, exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(stats, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
    except Exception as e:
        log_print(f"Error updating zip stats: {e}", "WARNING")

def resolve_direct_download_link(url):
    log_print(f"Resolving direct download link for input URL: {url}", "INFO")
    url_clean = url.strip()

    # Check if page is an anonfiles/anonfilesnew or similar file host page
    if "anonfiles" in url_clean or "filechan" in url_clean or "bayfiles" in url_clean or "openload" in url_clean or "pixeldrain" in url_clean:
        log_print("Detected file hosting page (anonfiles/anonfilesnew). Parsing HTML DOM for direct download link...", "INFO")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        try:
            import requests
            resp = requests.get(url_clean, headers=headers, timeout=20)
            log_print(f"HTML fetch response status: {resp.status_code}, length: {len(resp.text)} bytes", "DEBUG")
            if resp.status_code == 200:
                html = resp.text
                # Look for direct download link in href or download buttons
                download_matches = re.findall(r'href=[\"\'](https?://[^\s\"\'<>]+(?:/download/|/cdn/|/get/|\.zip|\.rar|\.7z|\.tar|\.gz)[^\s\"\'<>]*)[\"\']', html, re.I)
                if not download_matches:
                    download_matches = re.findall(r'id=[\"\']download-url[\"\'][^>]*href=[\"\']([^\"\']+)[\"\']', html, re.I)
                if not download_matches:
                    download_matches = re.findall(r'class=[\"\'][^\"\']*btn-primary[^\"\']*[\"\'][^>]*href=[\"\']([^\"\']+)[\"\']', html, re.I)
                if not download_matches:
                    download_matches = re.findall(r'href=[\"\'](https?://[^\s\"\'<>]+)[\"\']', html, re.I)

                for match in download_matches:
                    if any(ext in match.lower() for ext in ['.zip', '.rar', '.7z', '.tar', '.gz', 'download', 'cdn']):
                        log_print(f"Direct download link extracted successfully: {match}", "SUCCESS")
                        return match

                log_print("No explicit direct link regex match found in HTML. Using raw input URL.", "WARNING")
        except Exception as e:
            log_print(f"Error fetching page HTML for direct link extraction: {e}", "WARNING")

    return url_clean

def download_compressed_file(download_url, dest_dir):
    log_print(f"Initiating download of compressed file from: {download_url}", "INFO")
    dest_file = os.path.join(dest_dir, "downloaded_archive.tmp")

    # Layer 1: aria2c (High speed multi-connection downloader)
    log_print("Attempting download using aria2c engine...", "DEBUG")
    cmd_aria2 = [
        "aria2c", "-x", "16", "-s", "16", "-k", "1M",
        "--out=downloaded_archive.tmp",
        "--dir=" + dest_dir,
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36",
        download_url
    ]
    try:
        res = subprocess.run(cmd_aria2, capture_output=True, text=True, timeout=1800) # 30 min timeout for download
        log_print(f"aria2c exit code: {res.returncode}", "DEBUG")
        if res.returncode == 0 and os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
            size_mb = os.path.getsize(dest_file) / (1024 * 1024)
            log_print(f"aria2c download completed! Archive size: {size_mb:.2f} MB ({size_mb/1024:.2f} GB)", "SUCCESS")
            return dest_file
    except Exception as e:
        log_print(f"aria2c engine notice: {e}", "WARNING")

    # Layer 2: curl engine with redirect follow and stealth headers
    log_print("Attempting download using curl engine...", "DEBUG")
    cmd_curl = [
        "curl", "-L", "-C", "-",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36",
        "-o", dest_file,
        download_url
    ]
    try:
        res_curl = subprocess.run(cmd_curl, capture_output=True, text=True, timeout=1800)
        log_print(f"curl exit code: {res_curl.returncode}", "DEBUG")
        if os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
            size_mb = os.path.getsize(dest_file) / (1024 * 1024)
            log_print(f"curl download completed! Archive size: {size_mb:.2f} MB ({size_mb/1024:.2f} GB)", "SUCCESS")
            return dest_file
    except Exception as e:
        log_print(f"curl engine notice: {e}", "WARNING")

    # Layer 3: wget fallback
    log_print("Attempting download using wget engine...", "DEBUG")
    cmd_wget = [
        "wget", "-c",
        "-U", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36",
        "-O", dest_file,
        download_url
    ]
    try:
        res_wget = subprocess.run(cmd_wget, capture_output=True, text=True, timeout=1800)
        if os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
            size_mb = os.path.getsize(dest_file) / (1024 * 1024)
            log_print(f"wget download completed! Archive size: {size_mb:.2f} MB ({size_mb/1024:.2f} GB)", "SUCCESS")
            return dest_file
    except Exception as e:
        log_print(f"wget engine notice: {e}", "WARNING")

    if os.path.exists(dest_file) and os.path.getsize(dest_file) > 1000:
        return dest_file

    log_print("All download methods failed to retrieve compressed file archive.", "ERROR")
    return None

def extract_archive(archive_path, extract_to):
    log_print(f"Extracting compressed archive file: {archive_path} into: {extract_to}", "INFO")

    # Layer 1: 7z command line (handles .zip, .rar, .7z, .tar, .gz, .iso, etc.)
    cmd_7z = ["7z", "x", "-y", f"-o{extract_to}", archive_path]
    try:
        log_print("Attempting extraction with 7z tool...", "DEBUG")
        res = subprocess.run(cmd_7z, capture_output=True, text=True, timeout=1200) # 20 min extraction timeout
        log_print(f"7z exit code: {res.returncode}", "DEBUG")
        if res.returncode == 0:
            log_print("7z extraction completed successfully!", "SUCCESS")
            return True
        else:
            log_print(f"7z output: {res.stdout[:300]} | error: {res.stderr[:300]}", "WARNING")
    except Exception as e:
        log_print(f"7z extraction error: {e}", "WARNING")

    # Layer 2: unrar
    cmd_unrar = ["unrar", "x", "-o+", archive_path, extract_to]
    try:
        log_print("Attempting extraction with unrar tool...", "DEBUG")
        res = subprocess.run(cmd_unrar, capture_output=True, text=True, timeout=1200)
        if res.returncode == 0:
            log_print("unrar extraction completed successfully!", "SUCCESS")
            return True
    except Exception as e:
        log_print(f"unrar extraction error: {e}", "WARNING")

    # Layer 3: Python zipfile module
    try:
        import zipfile
        if zipfile.is_zipfile(archive_path):
            log_print("Extracting using Python zipfile module...", "DEBUG")
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(extract_to)
            log_print("Python zipfile extraction completed successfully!", "SUCCESS")
            return True
    except Exception as e:
        log_print(f"Python zipfile extraction error: {e}", "WARNING")

    # Layer 4: py7zr
    try:
        import py7zr
        if py7zr.is_7zfile(archive_path):
            log_print("Extracting using py7zr module...", "DEBUG")
            with py7zr.SevenZipFile(archive_path, mode='r') as z:
                z.extractall(path=extract_to)
            log_print("py7zr extraction completed successfully!", "SUCCESS")
            return True
    except Exception as e:
        log_print(f"py7zr extraction error: {e}", "WARNING")

    # Check if any files were extracted regardless of exit codes
    extracted_items = os.listdir(extract_to)
    if extracted_items:
        log_print(f"Extraction directory contains {len(extracted_items)} items.", "SUCCESS")
        return True

    log_print("Failed to extract compressed archive file using all engines.", "ERROR")
    return False

async def main():
    log_print("==================================================================", "INFO")
    log_print("🚀 STARTING COMPRESSED FILE EXTRACTOR & TELEGRAM DISPATCHER", "INFO")
    log_print("==================================================================", "INFO")

    zip_url = os.environ.get("ZIP_URL") or os.environ.get("TELEGRAM_LINK") or (sys.argv[1] if len(sys.argv) > 1 else "")
    target_channel_raw = os.environ.get("TARGET_CHANNEL") or "-1004498823531"
    owner_id_raw = os.environ.get("OWNER_ID") or os.environ.get("AUTH") or ""

    if not zip_url or not zip_url.strip():
        log_print("No ZIP_URL provided. Exiting.", "ERROR")
        return

    try:
        target_channel = int(str(target_channel_raw).strip())
    except ValueError:
        target_channel = -1004498823531

    try:
        owner_id = int(str(owner_id_raw).strip())
    except ValueError:
        owner_id = 0

    log_print(f"Target Channel ID: {target_channel}", "INFO")
    log_print(f"Owner Chat ID: {owner_id}", "INFO")
    log_print(f"Input Compressed File URL: {zip_url}", "INFO")

    # Connect Pyrogram clients
    from main import userbot, Bot, BOT_TOKEN

    userbot_connected = False
    try:
        log_print("Connecting Pyrogram Userbot (SESSION_STRING)...", "INFO")
        import inspect
        res = userbot.start()
        if inspect.iscoroutine(res):
            await res
        log_print("Pyrogram Userbot connected successfully!", "SUCCESS")
        userbot_connected = True
    except Exception as e:
        log_print(f"Userbot connection notice: {e}", "WARNING")

    bot_connected = False
    try:
        log_print("Connecting Pyrogram Bot...", "INFO")
        import inspect
        res = Bot.start()
        if inspect.iscoroutine(res):
            await res
        log_print("Pyrogram Bot connected successfully!", "SUCCESS")
        bot_connected = True
    except Exception as e:
        log_print(f"Pyrogram Bot connection notice: {e}", "WARNING")

    async def send_tg_notice(text):
        if userbot_connected:
            try:
                await userbot.send_message(target_channel, text)
                return
            except Exception as e:
                log_print(f"Userbot send_notice error: {e}", "WARNING")
        if bot_connected:
            try:
                await Bot.send_message(target_channel, text)
                return
            except Exception as e:
                log_print(f"Bot send_notice error: {e}", "WARNING")

    temp_work_dir = tempfile.mkdtemp(prefix="zip_extractor_")
    download_dir = os.path.join(temp_work_dir, "dl")
    extract_dir = os.path.join(temp_work_dir, "extracted")
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)

    sent_db = load_sent_files_db()

    start_notice = (
        f"📦 <b>شروع فرآیند استخراج و ارسال پوشه‌ای فایل فشرده:</b>\n"
        f"🔗 <b>لینک:</b> <code>{zip_url[:70]}...</code>\n"
        f"🎯 <b>کانال مقصد:</b> <code>{target_channel}</code>\n"
        f"🕒 در حال دانلود فایل فشرده ۱۰ گیگابایتی و استخراج پوشه‌ها..."
    )
    await send_tg_notice(start_notice)
    if owner_id:
        try:
            if userbot_connected: await userbot.send_message(owner_id, start_notice)
        except Exception: pass

    # Step 1: Resolve Direct Link
    direct_link = resolve_direct_download_link(zip_url)

    # Step 2: Download Archive
    archive_path = download_compressed_file(direct_link, download_dir)
    if not archive_path:
        err_msg = f"❌ <b>خطا در دانلود فایل فشرده:</b> عدم امکان دریافت فایل از لینک <code>{zip_url[:60]}</code>."
        await send_tg_notice(err_msg)
        update_zip_stats(0, 0, 0, "نامشخص", "خطا در دانلود فایل فشرده")
        shutil.rmtree(temp_work_dir, ignore_errors=True)
        return

    archive_size_bytes = os.path.getsize(archive_path)
    archive_size_mb = archive_size_bytes / (1024 * 1024)
    archive_size_gb = archive_size_mb / 1024
    log_print(f"Archive file downloaded successfully. Size: {archive_size_mb:.2f} MB ({archive_size_gb:.2f} GB)", "SUCCESS")

    dl_success_notice = (
        f"✅ <b>دانلود فایل فشرده با موفقیت انجام شد!</b>\n"
        f"📦 <b>حجم فایل فشرده:</b> {archive_size_mb:,.1f} MB ({archive_size_gb:.2f} GB)\n"
        f"⚡ در حال خارج کردن از حالت فشرده (Extract) و آنالیز ساختار پوشه‌ها..."
    )
    await send_tg_notice(dl_success_notice)

    # Step 3: Extract Archive
    extract_ok = extract_archive(archive_path, extract_dir)
    if not extract_ok:
        err_msg = f"❌ <b>خطا در استخراج (Extract) فایل فشرده:</b> ساختار فایل آسیب دیده یا رمزنگاری شده است."
        await send_tg_notice(err_msg)
        update_zip_stats(0, 0, 0, "نامشخص", "خطا در آنزیپ فایل")
        shutil.rmtree(temp_work_dir, ignore_errors=True)
        return

    log_print("Archive extracted successfully! Indexing directory structure...", "SUCCESS")

    # Step 4: Catalog folders and files
    # Traverse extracted directory
    folder_map = {} # relative_folder_path -> list of (file_abs_path, file_rel_path, size_bytes)
    total_file_count = 0
    total_extracted_bytes = 0

    for root, dirs, files in os.walk(extract_dir):
        # Sort dirs and files
        dirs.sort()
        files.sort()

        rel_folder = os.path.relpath(root, extract_dir)
        if rel_folder == ".":
            rel_folder = "ریشه فایل‌های فشرده (Main Root)"

        file_entry_list = []
        for fname in files:
            abs_fp = os.path.join(root, fname)
            rel_fp = os.path.relpath(abs_fp, extract_dir)
            f_size = os.path.getsize(abs_fp)

            file_entry_list.append((abs_fp, rel_fp, f_size))
            total_file_count += 1
            total_extracted_bytes += f_size

        if file_entry_list:
            folder_map[rel_folder] = file_entry_list

    total_extracted_gb = total_extracted_bytes / (1024 * 1024 * 1024)
    log_print(f"Cataloging completed: {len(folder_map)} folders, {total_file_count} total files, {total_extracted_gb:.2f} GB total content.", "SUCCESS")

    indexed_notice = (
        f"📂 <b>ساختار پوشه‌ها و فایل‌ها شناسایی شد:</b>\n"
        f"📁 <b>تعداد کل پوشه‌ها:</b> {len(folder_map)}\n"
        f"📄 <b>تعداد کل فایل‌ها:</b> {total_file_count}\n"
        f"📊 <b>مجموع حجم استخراج‌شده:</b> {total_extracted_bytes/(1024*1024):,.1f} MB ({total_extracted_gb:.2f} GB)\n"
        f"🚀 شروع ارسال مرحله‌ای تا سقف ۲ گیگابایت به کانال اختصاصی..."
    )
    await send_tg_notice(indexed_notice)

    # Step 5: Send Folder Headers & Files with 2GB Cumulative Batch Enforcement
    cumulative_bytes_this_run = 0
    files_sent_this_run = 0
    already_sent_count = 0

    # Ensure client is active
    active_client = userbot if userbot_connected else (Bot if bot_connected else None)
    if not active_client:
        log_print("No connected Telegram client available to send files!", "ERROR")
        return

    for folder_name, file_list in folder_map.items():
        # Check if all files in this folder are already sent
        unsent_in_folder = [f for f in file_list if f"{f[1]}_{f[2]}" not in sent_db]

        if not unsent_in_folder:
            already_sent_count += len(file_list)
            log_print(f"Folder '{folder_name}' - All {len(file_list)} files already sent. Skipping.", "DEBUG")
            continue

        log_print(f"------------------------------------------------------------------", "INFO")
        log_print(f"📁 Processing Folder: '{folder_name}' ({len(unsent_in_folder)} unsent files)", "INFO")
        log_print(f"------------------------------------------------------------------", "INFO")

        # 1. Dispatch Folder Header Announcement First!
        folder_header_msg = (
            f"📌 <b>📁 پوشه:</b> <code>{folder_name}</code>\n"
            f"📊 تعداد فایل‌های این پوشه: {len(file_list)} عدد | مانده: {len(unsent_in_folder)} عدد"
        )
        try:
            await active_client.send_message(target_channel, folder_header_msg)
            log_print(f"Dispatched Folder Announcement Header for: {folder_name}", "SUCCESS")
            await asyncio.sleep(1.5)
        except Exception as e_hdr:
            log_print(f"Error sending folder header announcement: {e_hdr}", "WARNING")

        # 2. Send Files of this folder
        for abs_fp, rel_fp, f_size in file_list:
            tracking_key = f"{rel_fp}_{f_size}"
            if tracking_key in sent_db:
                continue

            # Check 2GB batch limit check
            if cumulative_bytes_this_run > 0 and (cumulative_bytes_this_run + f_size) > MAX_BATCH_BYTES:
                log_print(f"🛑 Batch size limit (2 GB) reached for this run ({cumulative_bytes_this_run/(1024*1024):.1f} MB sent). Stopping execution cleanly.", "WARNING")
                limit_notice = (
                    f"⚡ <b>سقف نوبت ارسال این مرحله (۲ گیگابایت) تکمیل شد!</b>\n"
                    f"📊 <b>حجم ارسال شده در این سرفصل:</b> {cumulative_bytes_this_run/(1024*1024):,.1f} MB ({cumulative_bytes_this_run/(1024*1024*1024):.2f} GB)\n"
                    f"📄 <b>تعداد فایل‌های ارسال‌شده:</b> {files_sent_this_run} عدد\n"
                    f"💾 وضعیت ذخیره گردید. نوبت بعدی برای فایل‌های باقی‌مانده آغاز خواهد شد. 💎"
                )
                await send_tg_notice(limit_notice)
                update_zip_stats(total_file_count, len(sent_db), cumulative_bytes_this_run, folder_name, "تکمیل پارت ۲ گیگابایتی - آماده پارت بعدی")
                shutil.rmtree(temp_work_dir, ignore_errors=True)
                return

            fname = os.path.basename(abs_fp)
            f_size_mb = f_size / (1024 * 1024)
            log_print(f"Uploading file [{files_sent_this_run+1}]: '{fname}' ({f_size_mb:.2f} MB) to channel {target_channel}...", "PROGRESS")

            caption = (
                f"📄 <b>فایل:</b> <code>{fname}</code>\n"
                f"📁 <b>پوشه:</b> <code>{folder_name}</code>\n"
                f"📊 <b>حجم:</b> {f_size_mb:.2f} MB\n"
                f"🛡️📥 استخراج‌شده توسط سپر دانلود عمارت"
            )

            upload_success = False
            for attempt in range(3):
                try:
                    await active_client.send_document(
                        chat_id=target_channel,
                        document=abs_fp,
                        caption=caption
                    )
                    upload_success = True
                    log_print(f"File uploaded successfully: {fname}", "SUCCESS")
                    break
                except Exception as e_up:
                    log_print(f"Attempt {attempt+1} upload error for {fname}: {e_up}", "WARNING")
                    await asyncio.sleep(3)

            if upload_success:
                cumulative_bytes_this_run += f_size
                files_sent_this_run += 1
                sent_db.add(tracking_key)
                save_sent_files_db(sent_db)
                update_zip_stats(total_file_count, len(sent_db), cumulative_bytes_this_run, folder_name, f"در حال ارسال (فایل {len(sent_db)} از {total_file_count})")
                await asyncio.sleep(1.2) # Avoid hitting Telegram flood limits
            else:
                log_print(f"Failed to upload file after 3 attempts: {fname}", "ERROR")

    # Final summary notice when all files across all folders are sent
    final_summary = (
        f"🎉 <b>انتقال کامل فایل‌های فشرده به پایان رسید!</b>\n"
        f"📁 <b>تعداد کل پوشه‌ها:</b> {len(folder_map)}\n"
        f"📄 <b>تعداد کل فایل‌های فرستاده‌شده:</b> {len(sent_db)} از {total_file_count}\n"
        f"📊 <b>مجموع حجم کل:</b> {total_extracted_bytes/(1024*1024):,.1f} MB ({total_extracted_gb:.2f} GB)\n"
        f"🎯 <b>کانال مقصد:</b> <code>{target_channel}</code>"
    )
    await send_tg_notice(final_summary)
    update_zip_stats(total_file_count, len(sent_db), total_extracted_bytes, "تکمیل شده", "پایان استخراج و انتقال کامل 💎")
    log_print("==================================================================", "SUCCESS")
    log_print("🎉 ALL COMPRESSED FILE CONTENTS TRANSFERRED SUCCESSFULLY!", "SUCCESS")
    log_print("==================================================================", "SUCCESS")

    shutil.rmtree(temp_work_dir, ignore_errors=True)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(main())
