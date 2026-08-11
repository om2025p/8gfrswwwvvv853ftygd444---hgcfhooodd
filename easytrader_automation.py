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


def wait_for_telegram_otp(start_time_epoch):
    """
    Polls Telegram getUpdates API for up to 3 minutes (180 seconds) for a message
    from the target TELEGRAM_CHAT_ID containing a 5-6 digit verification code.
    Only messages sent AFTER start_time_epoch are considered.
    """
    print("[+] Starting live Telegram polling for OTP verification code...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    timeout_seconds = 180
    poll_interval = 5
    elapsed = 0
    offset = 0

    while elapsed < timeout_seconds:
        try:
            query_url = url
            if offset > 0:
                query_url += f"?offset={offset}"

            req = urllib.request.Request(query_url)
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode('utf-8'))
                if data.get("ok") and "result" in data:
                    updates = data["result"]
                    for upd in updates:
                        upd_id = upd.get("update_id")
                        if upd_id >= offset:
                            offset = upd_id + 1

                        # Extract message object from channel or user message
                        msg_obj = None
                        if "message" in upd:
                            msg_obj = upd["message"]
                        elif "channel_post" in upd:
                            msg_obj = upd["channel_post"]
                        elif "edited_message" in upd:
                            msg_obj = upd["edited_message"]
                        elif "edited_channel_post" in upd:
                            msg_obj = upd["edited_channel_post"]

                        if not msg_obj:
                            continue

                        chat_obj = msg_obj.get("chat", {})
                        chat_id = str(chat_obj.get("id", ""))

                        # Match destination chat ID
                        if chat_id != str(TELEGRAM_CHAT_ID):
                            continue

                        # Verify message date is fresh
                        msg_date = msg_obj.get("date", 0)
                        if msg_date < start_time_epoch - 15:  # Allow small leeway
                            continue

                        text = msg_obj.get("text", "")
                        if not text:
                            continue

                        # Normalize Persian digits to English digits
                        norm_text = convert_persian_to_english_numbers(text)

                        # Find 5 or 6 digit verification code patterns
                        codes = re.findall(r'\b\d{5,6}\b', norm_text)
                        if codes:
                            detected_code = codes[0]
                            print(f"[+] Successfully intercepted live OTP code: {detected_code} from chat {chat_id}!")
                            return detected_code

        except Exception as e:
            print(f"[i] Warning during live Telegram polling: {e}")

        time.sleep(poll_interval)
        elapsed += poll_interval
        if elapsed % 30 == 0:
            print(f"[+] Still waiting for live Telegram OTP... ({elapsed}/{timeout_seconds}s elapsed)")

    print("[-] Timeout: Did not receive any valid OTP code from Telegram in 3 minutes.")
    return None


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

        # Modern Chrome Mobile User Agent to bypass blocking modals warning about old Safari/iOS versions
        chrome_mobile_ua = "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

        # Use mobile view and restore state if it exists
        if session_exists:
            print(f"[+] Restoring existing browser session state from: {session_file_path}")
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent=chrome_mobile_ua,
                storage_state=session_file_path
            )
        else:
            print("[i] No browser session state found. Starting a fresh context...")
            context = browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent=chrome_mobile_ua
            )

        page = context.new_page()
        page.set_default_timeout(45000)

        try:
            is_logged_in = False

            # Try direct navigation to portfolio if session exists
            if session_exists:
                print("[+] Navigating directly to portfolio with active session...")
                try:
                    page.goto("https://m.easytrader.ir/portfolio-fill", wait_until="load", timeout=30000)
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
                page.goto("https://m.easytrader.ir/", wait_until="load")
                time.sleep(3)

                # Check if we are redirected to login.emofid.com
                current_url = page.url
                print(f"[+] Current URL: {current_url}")

                # If not already on login, try directly navigating to emofid login
                if "login.emofid.com" not in current_url:
                    print("[i] Directing browser to emofid SSO login page...")
                    page.goto("https://login.emofid.com/Login", wait_until="load")
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

                    # 1. Check if we already have it in environment variables (for testing/bypass)
                    otp_code = os.environ.get("OTP_CODE")

                    # 2. If not, trigger interactive live Telegram Polling
                    if not otp_code or otp_code.strip() == "":
                        print("[+] Triggering interactive live Telegram polling...")
                        start_time = int(time.time())

                        otp_prompt = (
                            f"<b>🔑 درخواست کد تأیید ورود (OTP)</b>\n\n"
                            f"رئیس عزیز! من پشت در ورودی مفید ایستاده‌ام و منتظر زنگ پیامک هستم.\n"
                            f"لطفاً کد ۵ یا ۶ رقمی پیامک شده را <b>به صورت معمولی یا ریپلای</b> در همین چت برای من ارسال کنید تا سریعاً وارد شوم! 📱⏱️\n\n"
                            f"⏳ <b>مهلت زمان ارسال شما:</b> ۳ دقیقه (۱۸۰ ثانیه)"
                        )
                        send_telegram_message(otp_prompt)

                        otp_code = wait_for_telegram_otp(start_time)

                    if otp_code:
                        print(f"[+] Attempting to fill OTP code: {otp_code}")

                        # Dynamic / Self-healing OTP input selector
                        otp_input = None

                        # 1. Try standard/probable selectors first
                        standard_selectors = [
                            "input[name='Token']",
                            "input#Token",
                            "input[name='token']",
                            "input#token",
                            "input[type='tel']",
                            "input[type='number']",
                            "input[inputmode='numeric']",
                            "input[placeholder*='کد']",
                            "input[placeholder*='code']",
                            "input[name*='code']",
                            "input[name*='Code']",
                            "input[type='text']"
                        ]

                        print("[+] Searching for OTP input element...")
                        for sel in standard_selectors:
                            try:
                                element = page.locator(sel).first
                                if element.is_visible():
                                    otp_input = element
                                    print(f"[+] Found OTP input using selector: {sel}")
                                    break
                            except Exception:
                                continue

                        # 2. Self-healing fallback: scan all visible inputs
                        if not otp_input:
                            print("[i] Standard OTP selectors failed or not visible yet. Waiting 5s then running self-healing scan...")
                            time.sleep(5)
                            try:
                                all_inputs = page.locator("input").all()
                                visible_inputs = [inp for inp in all_inputs if inp.is_visible()]

                                print(f"[i] Found {len(visible_inputs)} visible input(s) on the page.")

                                if len(visible_inputs) == 1:
                                    otp_input = visible_inputs[0]
                                    print("[+] Self-healing: Found exactly one visible input, assuming it is the OTP field.")
                                else:
                                    # Filter by likely attributes
                                    for inp in visible_inputs:
                                        html = inp.evaluate("el => el.outerHTML").lower()
                                        if any(k in html for k in ["token", "code", "otp", "tel", "numeric", "کد", "تایید"]):
                                            otp_input = inp
                                            print(f"[+] Self-healing: Found likely OTP input matching attributes in HTML: {html}")
                                            break

                                    # Last resort: use the first visible input
                                    if not otp_input and visible_inputs:
                                        otp_input = visible_inputs[0]
                                        print("[+] Self-healing last resort: Using the first visible input field on the page.")
                            except Exception as scan_err:
                                print(f"[-] Self-healing input scan failed: {scan_err}")

                        if not otp_input:
                            print("[!] Could not locate visible OTP input element. Attempting fallback wait for general input...")
                            try:
                                page.wait_for_selector("input", timeout=5000)
                                otp_input = page.locator("input").first
                            except Exception as final_wait_err:
                                raise Exception(f"Failed to find any visible OTP input field: {final_wait_err}")

                        # Fill the OTP code
                        otp_input.fill(otp_code)
                        print("[+] OTP code filled successfully.")

                        # Try to click the "تایید دو مرحله برای این سیستم لازم نیست." (Trust this device) checkbox
                        try:
                            print("[+] Checking for 'Trust Device' checkbox on OTP page...")
                            checkbox_selectors = [
                                "input[type='checkbox']",
                                "input#TrustDevice",
                                "input[name*='TrustDevice']",
                                "input[name*='trust']",
                                "text='تایید دو مرحله برای این سیستم لازم نیست.'",
                                "label:has-text('تایید دو مرحله')",
                                ".custom-checkbox",
                                "span:has-text('تایید دو مرحله')"
                            ]

                            ticked = False
                            for sel in checkbox_selectors:
                                checkbox = page.locator(sel).first
                                if checkbox.is_visible():
                                    if sel.startswith("input[type='checkbox']"):
                                        checkbox.check(force=True)
                                    else:
                                        checkbox.click(force=True)
                                    print(f"[+] Successfully ticked 'Trust Device' checkbox using selector: {sel}")
                                    ticked = True
                                    break
                            if not ticked:
                                print("[i] Non-blocking: Could not find any visible 'Trust Device' checkbox.")
                        except Exception as cb_err:
                            print(f"[i] Non-blocking warning: Failed to check 'Trust Device' checkbox: {cb_err}")

                        page.screenshot(path="otp_filled.png")

                        # Try to click the submit button with self-healing fallback
                        clicked_submit = False
                        submit_selectors = [
                            "button[type='submit']",
                            "button#verifyBtn",
                            "button.btn-primary",
                            "button:has-text('ادامه')",
                            "button:has-text('ورود')",
                            "button:has-text('تایید')",
                            "input[type='submit']",
                            "button"
                        ]

                        for sel in submit_selectors:
                            try:
                                btn = page.locator(sel).first
                                if btn.is_visible():
                                    btn.click()
                                    print(f"[+] Successfully clicked OTP submit button using: {sel}")
                                    clicked_submit = True
                                    break
                            except Exception:
                                continue

                        if not clicked_submit:
                            print("[i] Self-healing button click failed via locator. Attempting keyboard Enter key...")
                            try:
                                page.keyboard.press("Enter")
                                print("[+] Pressed Enter key as fallback.")
                            except Exception as key_err:
                                print(f"[-] Keyboard fallback failed: {key_err}")

                        time.sleep(6)
                        current_url = page.url
                        print(f"[+] URL after OTP submission: {current_url}")
                    else:
                        failure_instructions = (
                            f"<b>❌ مهلت ارسال کد تایید به پایان رسید</b>\n\n"
                            f"رئیس جان! متاسفانه بعد از ۳ دقیقه کدی از شما دریافت نکردم و عملیات متوقف شد.\n"
                            f"هر زمان مایل بودید می‌توانید مجدداً جریان کار را در گیت‌هاب اکشنز اجرا کنید."
                        )
                        send_telegram_message(failure_instructions)
                        raise Exception("OTP verification required but no valid code was provided via Telegram in 3 minutes.")

                # 3. Direct navigation to portfolio
                portfolio_url = "https://m.easytrader.ir/portfolio-fill"
                print(f"[+] Navigating directly to portfolio page: {portfolio_url}")
                page.goto(portfolio_url, wait_until="load")
                time.sleep(5)

                # Active dialog / modal overlay dismissal check
                try:
                    print("[+] Checking for any block overlays, system update modals, or alerts to dismiss...")
                    modal_dismiss_selectors = [
                        "button:has-text('✕')",
                        "span:has-text('✕')",
                        "div[class*='close']",
                        "button[class*='close']",
                        "i[class*='close']",
                        "svg[class*='close']",
                        "button:has-text('بستن')",
                        "button:has-text('انصراف')"
                    ]
                    for sel in modal_dismiss_selectors:
                        closer = page.locator(sel).first
                        if closer.is_visible():
                            closer.click(force=True)
                            print(f"[+] Dismissed popup overlay using selector: {sel}")
                            time.sleep(2)
                except Exception as ex_dismiss:
                    print(f"[i] Non-blocking: Modal dismiss scanner had an exception: {ex_dismiss}")

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

            # Additional modal dismissal sweep before scanning portfolio numbers
            try:
                modal_dismiss_selectors = [
                    "button:has-text('✕')",
                    "span:has-text('✕')",
                    "div[class*='close']",
                    "button[class*='close']",
                    "button:has-text('بستن')",
                    "button:has-text('انصراف')"
                ]
                for sel in modal_dismiss_selectors:
                    closer = page.locator(sel).first
                    if closer.is_visible():
                        closer.click(force=True)
                        print(f"[+] Late-stage sweep: Dismissed popup overlay using selector: {sel}")
                        time.sleep(2)
            except Exception:
                pass

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

            print("[+] Found 'سینرژی' row. Dynamically traversing up to locate the exact Synergy card container...")

            card_container = None
            parent = synergy_element

            # Dynamically traverse up to 10 levels of parents to locate the correct card
            for level in range(1, 11):
                parent = parent.locator("xpath=..")
                parent_text = parent.inner_text()

                # Check if we have the word 'سینرژی', but haven't climbed so high that we include 'همسنگ' (the next card)
                if "سینرژی" in parent_text and "همسنگ" not in parent_text:
                    normalized_parent_text = convert_persian_to_english_numbers(parent_text)
                    numbers = re.findall(r'[\d,]+', normalized_parent_text)
                    clean_digits = [num.replace(",", "") for num in numbers if num.replace(",", "").isdigit()]
                    large_numbers = [digit for digit in clean_digits if len(digit) >= 6]

                    # If this level contains the 'سینرژی' label and at least one 6+ digit asset number, it's our optimal card container!
                    if large_numbers:
                        card_container = parent
                        print(f"[+] Successfully detected optimal Synergy card container at parent level {level}!")
                        break

            # Safe fallback if dynamic traversal did not resolve a perfect match
            if not card_container:
                print("[w] Warning: Dynamic parent search did not resolve a perfect match. Falling back to fixed 4-level parent traversal.")
                card_container = synergy_element
                for _ in range(4):
                    card_container = card_container.locator("xpath=..")

            print("[+] Polling Synergy card container for numbers to load completely...")
            clean_numbers = []
            row_text = ""

            # Poll up to 20 seconds for the numbers to load/hydrate on the page
            for attempt in range(20):
                row_text = card_container.inner_text()
                normalized_row = convert_persian_to_english_numbers(row_text)

                # Extract all digit sequences with commas
                numbers_with_commas = re.findall(r'[\d,]+', normalized_row)
                candidates = []
                for num_str in numbers_with_commas:
                    clean_str = num_str.replace(",", "")
                    if clean_str.isdigit() and len(clean_str) >= 6:  # Large numbers (e.g., total asset value >= 100,000 Rials)
                        candidates.append(int(clean_str))

                if candidates:
                    clean_numbers = candidates
                    print(f"[+] Synergy row numbers loaded successfully on attempt {attempt+1}!")
                    break

                print(f"[i] Waiting for numbers to hydrate (attempt {attempt+1}/20)... Row text: {row_text.replace(chr(10), ' | ')}")
                time.sleep(1)

            # Fallback if no large numbers loaded: look for any valid numbers at all
            if not clean_numbers:
                print("[w] Warning: No large numbers loaded. Scanning for any numbers as fallback...")
                normalized_row = convert_persian_to_english_numbers(row_text)
                numbers_with_commas = re.findall(r'[\d,]+', normalized_row)
                for num_str in numbers_with_commas:
                    clean_str = num_str.replace(",", "")
                    if clean_str.isdigit():
                        clean_numbers.append(int(clean_str))

            print(f"[+] Extracted candidate numbers: {clean_numbers}")

            if not clean_numbers:
                raise Exception(f"Could not extract any valid numerical values from Synergy row container. Raw text: {row_text}")

            # The total asset value is always the maximum number in the row (e.g. 100,983,803 vs 1,893 or 53,410)
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
