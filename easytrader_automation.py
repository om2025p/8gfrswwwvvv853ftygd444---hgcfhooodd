#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Emarat EasyTrader Automation Script
===================================
This script automates logging into login.emofid.com, navigating to EasyTrader portfolio,
extracting the total value of the "سینرژی" (Synergy) fund, calculating the daily percent change,
updating local and cloud states, and reporting the result to Telegram.

All credentials and tokens are retrieved strictly from Environment Variables/Secrets.

Author: Jules
"""

import os
import sys
import json
import time
import re
from datetime import datetime
import urllib.request
import urllib.parse

# Try importing Playwright
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


# --- Read Configuration from Environment Variables ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
EASYTRADER_USER = os.environ.get("EASYTRADER_USER")
EASYTRADER_PASS = os.environ.get("EASYTRADER_PASS")
MANTLE_FINGERPRINT = os.environ.get("MANTLE_FINGERPRINT")  # Optional fingerprint for cloud sync

BACKUP_FILE_PATH = "gold5/gold5_backup.json"


def validate_environment():
    """Checks that all required secrets are provided via environment variables."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if not EASYTRADER_USER:
        missing.append("EASYTRADER_USER")
    if not EASYTRADER_PASS:
        missing.append("EASYTRADER_PASS")

    if missing:
        print(f"[-] Critical Error: Missing required environment variables: {', '.join(missing)}")
        print("[-] Please configure these as secrets in your GitHub repository settings.")
        sys.exit(1)


def gregorian_to_jalali(gy, gm, gd):
    """Converts Gregorian date to Jalali date. Pure Python, zero dependencies."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 335]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621

    gy2 = gy + 1 if gm > 2 else gy
    g_day_no = 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400 - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (g_day_no // 12053)
    g_day_no %= 12053
    jy += 4 * (g_day_no // 1461)
    g_day_no %= 1461

    if g_day_no > 365:
        jy += (g_day_no - 1) // 365
        g_day_no = (g_day_no - 1) % 365

    if g_day_no < 186:
        jm = 1 + g_day_no // 31
        jd = 1 + g_day_no % 31
    else:
        jm = 7 + (g_day_no - 186) // 30
        jd = 1 + (g_day_no - 186) % 30

    return jy, jm, jd


def get_current_persian_datetime():
    """Returns formatted Persian date and time string."""
    now = datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"


def convert_persian_to_english_numbers(text):
    """Converts Persian/Arabic numerals in a string to English digits."""
    if not text:
        return ""
    persian_arabic = "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩"
    english = "01234567890123456789"
    translation_table = str.maketrans(persian_arabic, english)
    return text.translate(translation_table)


def send_telegram_message(message, photo_path=None):
    """Sends a markdown message to the Telegram channel, optionally with a photo."""
    print(f"[+] Sending Telegram message: {message[:100]}...")
    try:
        if photo_path and os.path.exists(photo_path):
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            parts = []
            parts.append(f'--{boundary}')
            parts.append(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{TELEGRAM_CHAT_ID}')
            parts.append(f'--{boundary}')
            parts.append(f'Content-Disposition: form-data; name="parse_mode"\r\n\r\nHTML')
            parts.append(f'--{boundary}')
            parts.append(f'Content-Disposition: form-data; name="caption"\r\n\r\n{message}')
            parts.append(f'--{boundary}')

            with open(photo_path, 'rb') as f:
                img_data = f.read()

            parts.append(f'Content-Disposition: form-data; name="photo"; filename="{os.path.basename(photo_path)}"\r\nContent-Type: image/png\r\n\r\n')

            body = b''
            for p in parts[:-1]:
                body += p.encode('utf-8') + b'\r\n'
            body += parts[-1].encode('utf-8') + img_data + b'\r\n'
            body += f'--{boundary}--\r\n'.encode('utf-8')

            req = urllib.request.Request(url, data=body)
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

            with urllib.request.urlopen(req) as response:
                res_data = response.read()
                print("[+] Photo sent successfully to Telegram.")
                return json.loads(res_data)
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }).encode("utf-8")

            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req) as response:
                res_data = response.read()
                print("[+] Message sent successfully to Telegram.")
                return json.loads(res_data)

    except Exception as e:
        print(f"[-] Failed to send Telegram notification: {e}")
        return None


def sync_with_mantledb(new_val, percent_val, base_val):
    """Syncs the new records to MantleDB to automatically sync user's PWAs."""
    if not MANTLE_FINGERPRINT:
        print("[i] MANTLE_FINGERPRINT not provided, skipping cloud synchronization.")
        return False

    namespace = "emarat-pwa-backup-v2"
    url = f"https://mantledb.sh/v2/{namespace}/{MANTLE_FINGERPRINT}"

    print(f"[+] Syncing with MantleDB at URL: {url}")
    try:
        # 1. Fetch current data from MantleDB
        req = urllib.request.Request(url)
        current_cloud = {}
        try:
            with urllib.request.urlopen(req) as res:
                if res.status == 200:
                    current_cloud = json.loads(res.read().decode('utf-8'))
        except Exception as e:
            print(f"[i] No existing cloud record or unable to fetch. Will start fresh. Error: {e}")

        cloud_data = current_cloud.get("data", {})

        # Parse energy_fund_synergy
        synergy_str = cloud_data.get("energy_fund_synergy", "{}")
        try:
            synergy_obj = json.loads(synergy_str)
        except Exception:
            synergy_obj = {}

        percents = synergy_obj.get("percents", [])
        trash = synergy_obj.get("trash", [])
        goal = synergy_obj.get("goal", None)
        highlightedStates = synergy_obj.get("highlightedStates", {})
        periodTarget = synergy_obj.get("periodTarget", None)
        achievedPeriods = synergy_obj.get("achievedPeriods", [])
        notes = synergy_obj.get("notes", [])

        # Append new percent record
        timestamp_ms = int(time.time() * 1000)
        percents.append({
            "value": float(percent_val),
            "timestamp": timestamp_ms
        })
        percents.sort(key=lambda x: x["timestamp"])

        # Re-save energy_fund_synergy object
        updated_synergy_obj = {
            "percents": percents,
            "trash": trash,
            "goal": goal,
            "highlightedStates": highlightedStates,
            "periodTarget": periodTarget,
            "achievedPeriods": achievedPeriods,
            "notes": notes
        }
        cloud_data["energy_fund_synergy"] = json.dumps(updated_synergy_obj)

        # Update sinergy_baseNumber
        formatted_new_val = f"{new_val:,}"
        cloud_data["sinergy_baseNumber"] = formatted_new_val

        # Update sinergy_history
        history_str = cloud_data.get("sinergy_history", "[]")
        try:
            history_list = json.loads(history_str)
        except Exception:
            history_list = []

        # Get true Persian date string for history
        persian_date_str = get_current_persian_datetime()

        diff_type = "neutral"
        if percent_val > 0:
            diff_type = "increase"
        elif percent_val < 0:
            diff_type = "decrease"

        history_list.insert(0, {
            "id": timestamp_ms,
            "base": f"{base_val:,}",
            "new": formatted_new_val,
            "percent": f"{percent_val:.2f}",
            "type": diff_type,
            "rawBase": float(base_val),
            "rawNew": float(new_val),
            "timestamp": datetime.now().isoformat() + "Z",
            "persianDate": persian_date_str
        })
        if len(history_list) > 60:
            history_list = history_list[:60]

        cloud_data["sinergy_history"] = json.dumps(history_list)

        # Set last modified
        cloud_data["emarat_last_modified"] = str(timestamp_ms)

        # Construct payload
        payload = {
            "timestamp": timestamp_ms,
            "data": cloud_data
        }

        # Send POST request to update MantleDB
        data_bytes = json.dumps(payload).encode('utf-8')
        req_post = urllib.request.Request(
            url,
            data=data_bytes,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req_post) as res_post:
            if res_post.status in [200, 201]:
                print("[+] Successfully synchronized state with MantleDB cloud backup!")
                return True

    except Exception as e:
        print(f"[-] Error syncing with MantleDB: {e}")

    return False


def run_automation():
    if not HAS_PLAYWRIGHT:
        print("[-] Playwright library is not installed. Cannot run browser automation.")
        return False

    validate_environment()

    # Read or initialize local state backup
    local_state = {
        "percents": [],
        "trash": [],
        "goal": None,
        "highlightedStates": {},
        "periodTarget": None,
        "achievedPeriods": [],
        "notes": [],
        "baseNumber": 100983803, # Fallback initial base
        "history": []
    }

    if os.path.exists(BACKUP_FILE_PATH):
        try:
            with open(BACKUP_FILE_PATH, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
                print(f"[+] Loaded existing backup file. Current base value: {local_state.get('baseNumber')}")
        except Exception as e:
            print(f"[-] Warning: Failed to parse backup file, using defaults: {e}")

    base_val = local_state.get("baseNumber", 100983803)
    history_list = local_state.get("history", [])

    session_file_path = "gold5/easytrader_session.json"
    session_exists = os.path.exists(session_file_path)

    print("[+] Launching Playwright browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-blink-features=AutomationControlled'
            ]
        )

        # Use mobile view and restore state if it exists
        if session_exists:
            print(f"[+] Restoring existing browser session state from: {session_file_path}")
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                storage_state=session_file_path
            )
        else:
            print("[i] No browser session state found. Starting a fresh context...")
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            )

        page = context.new_page()
        page.set_default_timeout(45000)

        try:
            is_logged_in = False

            # Try direct navigation to portfolio if session exists
            if session_exists:
                print("[+] Navigating directly to portfolio with active session...")
                try:
                    page.goto("https://m.easytrader.ir/portfolio-fill", wait_until="networkidle", timeout=30000)
                    time.sleep(5)
                    current_url = page.url
                    body_text = page.locator("body").inner_text()

                    if "login.emofid.com" not in current_url and "ورود" not in body_text:
                        print("[+] Active session resumed successfully!")
                        page.screenshot(path="portfolio_loaded.png")
                        is_logged_in = True
                    else:
                        print("[i] Session state expired or logged out. Re-authentication required.")
                except Exception as e:
                    print(f"[i] Direct portfolio navigation failed/timed out: {e}. Falling back to normal login...")

            if not is_logged_in:
                # 1. Open EasyTrader Main/Login redirects
                print("[+] Navigating to EasyTrader login sequence...")
                page.goto("https://m.easytrader.ir/", wait_until="networkidle")
                time.sleep(3)

                # Check if we are redirected to login.emofid.com
                current_url = page.url
                print(f"[+] Current URL: {current_url}")

                # If not already on login, try directly navigating to emofid login
                if "login.emofid.com" not in current_url:
                    print("[i] Directing browser to emofid SSO login page...")
                    page.goto("https://login.emofid.com/Login", wait_until="networkidle")
                    time.sleep(3)

                # Take screenshot of login page for debug
                page.screenshot(path="login_page.png")
                print("[+] Saved login page screenshot to login_page.png")

                # 2. Fill login credentials
                print("[+] Filling credentials...")

                # Locate input fields (username and password)
                username_selector = "input[name='Username'], input#Username, input[type='text']"
                password_selector = "input[name='Password'], input#Password, input[type='password']"
                submit_selector = "button[type='submit'], button#loginBtn"

                # Wait for fields
                page.wait_for_selector(username_selector, timeout=15000)
                page.fill(username_selector, EASYTRADER_USER)

                page.wait_for_selector(password_selector, timeout=15000)
                page.fill(password_selector, EASYTRADER_PASS)

                # Screenshot before submit
                page.screenshot(path="credentials_filled.png")

                print("[+] Submitting login form...")
                page.click(submit_selector)
                time.sleep(5)

                # Check URL and handle possible security or redirect states
                current_url = page.url
                print(f"[+] Current URL after login: {current_url}")
                page.screenshot(path="after_login.png")

                # Handle verification/OTP screen
                if "Verify" in current_url or "verify" in current_url.lower():
                    print("[!] OTP Verification screen detected!")
                    otp_code = os.environ.get("OTP_CODE")
                    if otp_code:
                        print(f"[+] Attempting to fill manual OTP code: {otp_code}")
                        otp_input_selector = "input[name='Token'], input#Token, input[type='text'], input[placeholder*='کد']"
                        page.wait_for_selector(otp_input_selector, timeout=15000)
                        page.fill(otp_input_selector, otp_code)
                        page.screenshot(path="otp_filled.png")

                        verify_submit_btn = "button[type='submit'], button#verifyBtn, button.btn-primary"
                        page.click(verify_submit_btn)
                        time.sleep(6)
                        print(f"[+] URL after OTP submission: {page.url}")
                    else:
                        print("[-] No OTP_CODE found in environment variables! Notifying user on Telegram...")
                        otp_instructions = (
                            f"<b>⚠️ نیاز به تأیید هویت دو مرحله‌ای (OTP) برای صندوق سینرژی</b>\n\n"
                            f"رئیس عزیز! کارت دعوت طلایی منقضی شده یا اولین ورود شماست.\n"
                            f"لطفاً مراحل زیر را برای ورود انجام دهید:\n\n"
                            f"1️⃣ به تب <b>Actions</b> در گیت‌هاب بروید.\n"
                            f"2️⃣ جریان کار <b>Daily EasyTrader 5 Sync (Synergy)</b> را انتخاب کنید.\n"
                            f"3️⃣ روی دکمه <b>Run workflow</b> کلیک کرده و کد پیامک‌شده را در کادر بنویسید.\n"
                            f"4️⃣ دکمه سبز رنگ را بزنید تا کار تمام شود و کارت دعوت دائمی برای بارهای بعدی ساخته شود! 🚀"
                        )
                        send_telegram_message(otp_instructions)
                        raise Exception("OTP verification required but no OTP_CODE environment variable was provided.")

                # 3. Direct navigation to portfolio
                portfolio_url = "https://m.easytrader.ir/portfolio-fill"
                print(f"[+] Navigating directly to portfolio page: {portfolio_url}")
                page.goto(portfolio_url, wait_until="networkidle")
                time.sleep(5)

                page.screenshot(path="portfolio_loaded.png")
                print("[+] Portfolio page screenshot saved to portfolio_loaded.png")

                # Validate we are not still prompted to login
                body_text = page.locator("body").inner_text()
                if "ورود" in body_text or "رمز" in body_text or "login.emofid.com" in page.url:
                    raise Exception("Still on login/verification page or authentication failed.")

                # Save the new storage state/session cookie file
                os.makedirs(os.path.dirname(session_file_path), exist_ok=True)
                context.storage_state(path=session_file_path)
                print(f"[+] Successfully logged in and saved browser storage state to: {session_file_path}")

            # 4. Extract "سینرژی" value
            print("[+] Extracting total asset value for 'سینرژی'...")

            body_text = page.locator("body").inner_text()
            synergy_element = page.locator("text='سینرژی'").first
            if not synergy_element.is_visible():
                print("[-] Could not find element with text 'سینرژی' via direct locator.")
                print("--- Visible Text ---")
                print(body_text[:1000])
                print("--------------------")

                if "ورود" in body_text or "رمز" in body_text:
                    raise Exception("Still on login/verification page or authentication failed.")
                raise Exception("Synergy ('سینرژی') row not found in portfolio view.")

            print("[+] Found 'سینرژی' row. Attempting to traverse and find value...")

            # Traverse up and locate row container with numbers
            parent = synergy_element
            row_text = ""
            for i in range(5):
                parent = parent.locator("xpath=..")
                row_text = parent.inner_text()
                if any(char.isdigit() or char in "۰۱۲۳۴۵۶۷۸۹" for char in row_text):
                    print(f"[+] Found row container at level {i+1} with text: {row_text.replace(chr(10), ' | ')}")
                    break

            normalized_row = convert_persian_to_english_numbers(row_text)
            print(f"[+] Normalized row text: {normalized_row.replace(chr(10), ' | ')}")

            numbers_with_commas = re.findall(r'[\d,]+', row_text)
            clean_numbers = []
            for num_str in numbers_with_commas:
                english_num_str = convert_persian_to_english_numbers(num_str).replace(",", "")
                if english_num_str.isdigit():
                    clean_numbers.append(int(english_num_str))

            print(f"[+] Extracted candidate numbers: {clean_numbers}")

            if not clean_numbers:
                raise Exception("Could not extract any valid numerical values from Synergy row container.")

            new_val = max(clean_numbers)
            print(f"[+] Identified Synergy total asset value: {new_val:,} Rials")

            # 5. Calculation
            diff = new_val - base_val
            percent_change = (diff / base_val) * 100

            print(f"[+] Base Value: {base_val:,}")
            print(f"[+] New Value: {new_val:,}")
            print(f"[+] Percent Change: {percent_change:+.4f}%")

            # Save new percent in local state list
            timestamp_ms = int(time.time() * 1000)

            local_state["percents"].append({
                "value": float(round(percent_change, 2)),
                "timestamp": timestamp_ms
            })
            local_state["percents"].sort(key=lambda x: x["timestamp"])

            # Update history list in local state as well
            persian_date_str = get_current_persian_datetime()
            diff_type = "neutral"
            if percent_change > 0:
                diff_type = "increase"
            elif percent_change < 0:
                diff_type = "decrease"

            formatted_new_val = f"{new_val:,}"
            history_list.insert(0, {
                "id": timestamp_ms,
                "base": f"{base_val:,}",
                "new": formatted_new_val,
                "percent": f"{percent_change:.2f}",
                "type": diff_type,
                "rawBase": float(base_val),
                "rawNew": float(new_val),
                "timestamp": datetime.now().isoformat() + "Z",
                "persianDate": persian_date_str
            })
            if len(history_list) > 60:
                history_list = history_list[:60]

            local_state["history"] = history_list

            # Update base number for tomorrow
            local_state["baseNumber"] = new_val

            # Write updated local state back to JSON file
            os.makedirs(os.path.dirname(BACKUP_FILE_PATH), exist_ok=True)
            with open(BACKUP_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(local_state, f, ensure_ascii=False, indent=2)
            print(f"[+] Successfully wrote updated local backup to {BACKUP_FILE_PATH}")

            # 6. Synchronization with MantleDB (Cloud sync)
            sync_ok = sync_with_mantledb(new_val, round(percent_change, 2), base_val)

            # 7. Send Telegram Notification
            emoji = "📈" if percent_change > 0 else ("📉" if percent_change < 0 else "⚖️")
            persian_time_report = get_current_persian_datetime()

            telegram_report = (
                f"<b>🤖 عملیات خودکار ثبت درصد ۵ (صندوق سینرژی) با موفقیت انجام شد!</b>\n\n"
                f"📅 <b>تاریخ و زمان:</b> {persian_time_report}\n"
                f"💵 <b>دارایی قبلی (پایه):</b> {base_val:,} ریال\n"
                f"💰 <b>دارایی جدید استخراج‌شده:</b> {new_val:,} ریال\n"
                f"📊 <b>تغییرات درصد امروز:</b> <code>{percent_change:+.2f}%</code> {emoji}\n\n"
                f"🔄 <b>سینک ابری MantleDB:</b> {'✅ انجام شد' if sync_ok else '❌ انجام نشد (تنظیم نشده یا خطا)'}\n"
                f"💾 <b>فایل پشتیبان محلی:</b> ✅ بروزرسانی و در گیت‌هاب ذخیره شد\n\n"
                f"🌹 فردا هم راس ساعت ۱۰ شب همینجا منتظر من باشید! شب خوش."
            )

            send_telegram_message(telegram_report, photo_path="portfolio_loaded.png")

            context.close()
            browser.close()
            return True

        except Exception as err:
            print(f"[-] Error during Playwright execution: {err}")
            try:
                page.screenshot(path="error_emergency.png")
                print("[-] Emergency screenshot saved to error_emergency.png")
            except Exception:
                pass

            persian_time_report = get_current_persian_datetime()
            failure_report = (
                f"<b>⚠️ خطا در اجرای اتوماسیون ثبت درصد ۵ (صندوق سینرژی)</b>\n\n"
                f"📅 <b>تاریخ:</b> {persian_time_report}\n"
                f"❌ <b>جزئیات خطا:</b> <code>{str(err)[:500]}</code>\n\n"
                f"🛠️ لطفا وضعیت و لاگ‌های گیت‌هاب اکشنز را بررسی کنید تا ریشه مشکل مشخص شود."
            )
            send_telegram_message(failure_report, photo_path="error_emergency.png" if os.path.exists("error_emergency.png") else None)

            context.close()
            browser.close()
            raise err


if __name__ == "__main__":
    print("[+] Starting EasyTrader Automation Script...")
    success = run_automation()
    if success:
        print("[+] Automation execution finished successfully.")
        sys.exit(0)
    else:
        print("[-] Automation execution failed.")
        sys.exit(1)
