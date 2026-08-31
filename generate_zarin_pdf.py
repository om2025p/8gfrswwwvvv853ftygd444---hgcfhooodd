import asyncio
import datetime
import json
import os
import sys
import urllib.request
from playwright.async_api import async_playwright

JALALI_MONTH_NAMES = [
    "فروردین", "اردیبهشت", "خرداد",
    "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر",
    "دی", "بهمن", "اسفند"
]

def jalali_to_gregorian(jy, jm, jd):
    jy += 1595
    days = -355668 + (365 * jy) + (jy // 33 * 8) + ((jy % 33 + 3) // 4) + jd + ((jm - 1) * 31 if jm < 7 else ((jm - 7) * 30) + 186)
    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    sal_a = [0, 31, 29 if (gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and days >= sal_a[gm]:
        days -= sal_a[gm]
        gm += 1
    gd = days + 1
    return gy, gm, gd

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy if gm > 2 else gy - 1
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

def build_pdf_html(year, month_idx, history_records, total_month_toman):
    month_name = JALALI_MONTH_NAMES[month_idx - 1]

    # Build day blocks
    day_blocks_html = ""
    if not history_records:
        day_blocks_html = """
        <div style="text-align: center; padding: 40px; color: #64748b; font-size: 13px; border: 1px dashed #cbd5e1; border-radius: 12px;">
            📭 هیچ سود مثبتی برای این ماه ثبت نشده است.
        </div>
        """
    else:
        for idx, rec in enumerate(history_records, start=1):
            day_str = rec.get("date_str", "")
            time_str = rec.get("time_str", "")
            day_total_toman = rec.get("day_total_toman", 0)
            positive_items = rec.get("positive_items", [])

            rows_html = ""
            for item_idx, item in enumerate(positive_items):
                bg_class = "yellow-bg" if item_idx % 2 == 0 else "white-bg"
                f_title = item.get("title", "")
                f_percent = item.get("percent", 0.0)
                f_toman = item.get("toman", 0)
                rows_html += f"""
                <div class="fund-row {bg_class}">
                    <span class="fund-name">{f_title}</span>
                    <span class="fund-val pos">+{f_percent:.2f}% (+{f_toman:,} تومان)</span>
                </div>
                """

            day_blocks_html += f"""
            <div class="day-block">
                <div class="day-block-header">
                    <span>📅 تاریخ: {day_str} · ساعت ثبت: {time_str}</span>
                    <span class="day-total-badge">💰 مجموع روز: +{day_total_toman:,} تومان</span>
                </div>
                {rows_html}
            </div>
            """

    html_content = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
    @page {{ size: A4; margin: 12mm; }}
    body {{
        font-family: 'Tahoma', 'Segoe UI', sans-serif;
        background: #ffffff;
        color: #0f172a;
        margin: 0;
        padding: 15px;
        direction: rtl;
        -webkit-print-color-adjust: exact;
    }}
    .header-bank-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
        border: 2px solid #1e3a8a;
        border-radius: 8px;
        overflow: hidden;
    }}
    .header-bank-table td {{
        padding: 12px 15px;
        vertical-align: middle;
    }}
    .header-title-cell {{
        background: #1e3a8a;
        color: #ffffff;
        text-align: center;
    }}
    .header-title {{ font-size: 18px; font-weight: bold; margin: 0; }}
    .header-sub {{ font-size: 11px; opacity: 0.9; margin-top: 4px; }}

    .info-grid {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
    }}
    .info-grid td {{
        padding: 8px 12px;
        font-size: 11px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .info-label {{ font-weight: bold; color: #475569; width: 20%; }}
    .info-val {{ font-weight: bold; color: #0f172a; width: 30%; }}
    .badge-green {{ color: #16a34a; font-weight: bold; }}

    .day-block {{
        border: 2px solid #1e3a8a;
        border-radius: 10px;
        margin-bottom: 18px;
        overflow: hidden;
        background: #ffffff;
    }}
    .day-block-header {{
        background: #1e3a8a;
        color: #ffffff;
        padding: 10px 15px;
        font-size: 13px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .day-total-badge {{
        background: #fef08a;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: bold;
    }}

    .fund-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 15px;
        font-size: 11px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .fund-row:last-child {{
        border-bottom: none;
    }}
    .fund-row.yellow-bg {{
        background-color: #fef9c3;
    }}
    .fund-row.white-bg {{
        background-color: #ffffff;
    }}

    .fund-name {{
        font-weight: bold;
        color: #1e293b;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .fund-val {{
        font-weight: 800;
        direction: ltr;
        font-size: 12px;
    }}
    .fund-val.pos {{ color: #16a34a; }}

    .footer-stamp {{
        margin-top: 25px;
        border-top: 2px dashed #94a3b8;
        padding-top: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 10px;
        color: #64748b;
    }}
    .stamp-box {{
        border: 2px double #1e3a8a;
        color: #1e3a8a;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: bold;
        text-align: center;
        font-size: 10px;
    }}
</style>
</head>
<body>

<table class="header-bank-table">
    <tr>
        <td class="header-title-cell">
            <div class="header-title">🏛️ بانک متمرکز عمارت دیجیتال</div>
            <div class="header-sub">صورت‌حساب رسمی بانکی · گردش روزانه تاریخچه زرین سودهای مثبت</div>
        </td>
    </tr>
</table>

<table class="info-grid">
    <tr>
        <td class="info-label">📅 دوره گزارش:</td>
        <td class="info-val">{month_name} ماه {year}</td>
        <td class="info-label">👤 دارنده حساب:</td>
        <td class="info-val">مدیریت محترم عمارت</td>
    </tr>
    <tr>
        <td class="info-label">🏷️ نوع صورت‌حساب:</td>
        <td class="info-val">تاریخچه زرین (فقط سودهای مثبت)</td>
        <td class="info-label">🏷️ کد پیگیری:</td>
        <td class="info-val">EMR-{year}-{month_idx:02d}-ZARIN</td>
    </tr>
    <tr>
        <td class="info-label">💰 مجموع سود ماه:</td>
        <td class="info-val badge-green">+{total_month_toman:,} تومان</td>
        <td class="info-label">🟢 وضعیت گزارش:</td>
        <td class="info-val badge-green">ماه تکمیل‌شده (رسمی)</td>
    </tr>
</table>

<h4 style="margin-bottom: 10px; color: #1e3a8a;">📋 ریز صورت‌حساب سودهای مثبت ماه (زیر هم در کادرهای زرد و سفید):</h4>

{day_blocks_html}

<div class="footer-stamp">
    <div>
        📌 این سند به صورت الکترونیکی و خودکار توسط سرور ابری عمارت دیجیتال صادر شده است.<br>
        اصالت سند: معتبر و تأییدشده در سیستم مرکزی دیدبان درصدها.
    </div>
    <div class="stamp-box">
        تأییدشده و رسمی<br>
        🏛️ EMARAT DIGITAL
    </div>
</div>

</body>
</html>
"""
    return html_content

def send_telegram_doc(bot_token, chat_id, file_path, caption):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    filename = os.path.basename(file_path)

    body = []
    body.append(f"--{boundary}".encode())
    body.append('Content-Disposition: form-data; name="chat_id"'.encode())
    body.append(b"")
    body.append(chat_id.encode())

    body.append(f"--{boundary}".encode())
    body.append('Content-Disposition: form-data; name="caption"'.encode())
    body.append(b"")
    body.append(caption.encode())

    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode())
    body.append(b'Content-Type: application/pdf')
    body.append(b"")
    body.append(file_bytes)

    body.append(f"--{boundary}--".encode())
    body.append(b"")

    payload = b"\r\n".join(body)
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    res = urllib.request.urlopen(req)
    print("Telegram upload result:", res.read().decode('utf-8'))

async def generate_pdf():
    # Read environment variables
    year = int(os.environ.get("JALALI_YEAR", "1405"))
    month = int(os.environ.get("JALALI_MONTH", "5"))
    bot_token = os.environ.get("BOT_TOKEN", "")
    chat_id = os.environ.get("CHAT_ID", "")
    data_json_raw = os.environ.get("DATA_JSON", "{}")

    data = {}
    try:
        data = json.loads(data_json_raw)
    except Exception as e:
        print("JSON parse error:", e)

    # Process history and filter for requested Jalali year & month and positive items (>0)
    # data format: list of day objects [{ date_str, time_str, timestamp, positive_items, day_total_toman, ... }]
    raw_history = data.get("history", [])

    filtered_history = []
    total_month_toman = 0

    for day_item in raw_history:
        ts = day_item.get("timestamp")
        if not ts:
            continue
        # Convert timestamp to Jalali using Tehran timezone (UTC+3:30)
        tehran_tz = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
        d = datetime.datetime.fromtimestamp(ts / 1000.0, tz=tehran_tz)
        jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)

        if jy == year and jm == month:
            pos_items = day_item.get("positive_items", [])
            if pos_items:
                day_pos_toman = sum(it.get("toman", 0) for it in pos_items)
                total_month_toman += day_pos_toman
                filtered_history.append({
                    "date_str": f"{jy}/{jm:02d}/{jd:02d}",
                    "time_str": d.strftime("%H:%M:%S"),
                    "day_total_toman": day_pos_toman,
                    "positive_items": pos_items
                })

    html_content = build_pdf_html(year, month, filtered_history, total_month_toman)

    pdf_filename = f"zarin_report_{year}_{month:02d}.pdf"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content)
        await page.pdf(path=pdf_filename, format="A4")
        await browser.close()

    print(f"PDF generated: {pdf_filename}")

    if bot_token and chat_id:
        month_name = JALALI_MONTH_NAMES[month - 1]
        caption = f"🏛️ **صورت‌حساب رسمی تاریخچه زرین ({month_name} {year})**\n💰 مجموع سود ماه: +{total_month_toman:,} تومان\n📄 صادر شده توسط سامانه دیدبان درصدها"
        send_telegram_doc(bot_token, chat_id, pdf_filename, caption)

if __name__ == "__main__":
    asyncio.run(generate_pdf())
