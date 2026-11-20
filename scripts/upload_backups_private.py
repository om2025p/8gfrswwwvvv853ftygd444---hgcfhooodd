#!/usr/bin/env python3
"""آپلود بکاپ‌های اتوماسیون به مخزن خصوصی با ساختار شمسی سلسله‌مراتبی.

مخزن عمومی سایت هرگز نباید بکاپ یا نشست بگیرد. این اسکریپت همان مسیری را
می‌سازد که backup-path.js در فرانت‌اند می‌سازد:
    <app>/<YYYY>/<MM>/week-<NN>/<YYYY.MM.DD>/<name>.json

متغیرهای محیطی:
    PRIVATE_REPO_TOKEN  توکن گیت‌هاب با دسترسی نوشتن به مخزن خصوصی
    PRIVATE_REPO        مالک/مخزن، مثل om2025p/comp-bkp-
    PRIVATE_REPO_BRANCH اختیاری، پیش‌فرض main

اگر توکن یا مخزن تنظیم نشده باشد، اسکریپت با کد ۰ خارج می‌شود (اتوماسیون نباید
به خاطر نبود بکاپ شکست بخورد) ولی هشدار چاپ می‌کند.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta



def gregorian_to_jalali(gy, gm, gd):
    """تبدیل میلادی به شمسی — همان الگوریتم easytrader_automation.py (بدون وابستگی)."""
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


BACKUPS = [
    ("gold5", "gold5/gold5_backup.json"),
    ("gold4", "gold4/gold4_backup.json"),
]

SECRET_SUFFIXES = ("_session.json", "storage_state.json", "cookies.json")


def day_folder(app_id, now):
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    week = min(5, (jd - 1) // 7 + 1)
    return f"{app_id}/{jy:04d}/{jm:02d}/week-{week:02d}/{jy:04d}.{jm:02d}.{jd:02d}"


def api(path, token, method="GET", payload=None):
    url = f"https://api.github.com/repos/{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as res:
        body = res.read().decode()
        return res.status, (json.loads(body) if body else {})


def put_file(repo, token, branch, rel_path, content, message):
    full = f"{repo}/contents/{rel_path}"
    sha = None
    try:
        status, data = api(f"{full}?ref={branch}", token)
        if status == 200:
            sha = data.get("sha")
    except urllib.error.HTTPError as err:
        if err.code not in (404,):
            raise

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    status, _ = api(full, token, method="PUT", payload=payload)
    return status in (200, 201)


def main():
    token = (os.environ.get("PRIVATE_REPO_TOKEN") or "").strip()
    repo = (os.environ.get("PRIVATE_REPO") or "").strip()
    branch = (os.environ.get("PRIVATE_REPO_BRANCH") or "main").strip()

    if not token or not repo:
        print("⚠️ PRIVATE_REPO_TOKEN/PRIVATE_REPO تنظیم نشده — آپلود انجام نشد.")
        return 0

    now = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    stamp = now.strftime("%Y-%m-%d %H:%M")

    uploaded, skipped = [], []
    for app_id, path in BACKUPS:
        if not os.path.exists(path):
            skipped.append(f"{path} (وجود ندارد)")
            continue
        if path.endswith(SECRET_SUFFIXES):
            skipped.append(f"{path} (محرمانه)")
            continue

        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        if not content.strip():
            skipped.append(f"{path} (خالی)")
            continue

        name = os.path.basename(path).replace(".json", "")
        rel = f"{day_folder(app_id, now)}/{name}.json"
        try:
            ok = put_file(repo, token, branch, rel, content,
                          f"بکاپ خودکار {app_id} - {stamp}")
            (uploaded if ok else skipped).append(rel if ok else f"{rel} (خطا)")
        except Exception as err:  # noqa: BLE001
            skipped.append(f"{rel} ({err})")

    print("✅ آپلود‌شده:", *uploaded, sep="\n  ")
    if skipped:
        print("⏭️ رد‌شده:", *skipped, sep="\n  ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
