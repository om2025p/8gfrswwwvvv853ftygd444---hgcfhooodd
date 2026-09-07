import os
import sys
import asyncio
import glob
import math
import base64
import subprocess
import urllib.request
import urllib.parse
import json

# Full list of apps with icons, descriptions, and mock data/previews
SLIDES = [
    {
        "id": "intro",
        "badge": "🏛️ درگاه جامع",
        "title": "عمارت دیجیتال",
        "subtitle": "سامانه ۲۴ ابزار هوشمند، مالی و شخصی",
        "desc": "خوش آمدید به هاب ابزارهای مدرن عمارت. تمام برنامه‌های مورد نیاز شما در یک محیط یکپارچه، آفلاین و سریع.",
        "icon": "🏛️",
        "is_emoji": True,
        "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%)",
        "accent": "#fbbf24",
        "mock_type": "dashboard",
        "mock_title": "نمای کلی داشبورد عمارت",
        "mock_items": [
            {"label": "تعداد ابزارهای فعال", "val": "۲۴ ابزار", "color": "#fbbf24"},
            {"label": "وضعیت سرویس‌ورکر", "val": "فعال (آفلاین)", "color": "#34d399"},
            {"label": "همگام‌سازی ابری", "val": "متصل به GitHub / MantleDB", "color": "#60a5fa"},
            {"label": "امنیت و پایداری", "val": "تضمین ۱۰۰٪ داده‌ها", "color": "#f0abfc"}
        ]
    },
    {
        "id": "gym",
        "badge": "🏋️‍♂️ سلامتی و ورزش",
        "title": "Activity (مربی هوشمند)",
        "subtitle": "برنامه‌ریزی، تایمر صوتی و تحلیل ورزشی",
        "desc": "ثبت ست‌های تمرینی، تایمرهای فول‌اسکرین با هشدار صوتی، نمودارهای DNA روند پیشرفت و تحلیل هوشمند توسط Gemini AI.",
        "icon": "gym/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #064e3b 50%, #022c22 100%)",
        "accent": "#34d399",
        "mock_type": "gym_preview",
        "mock_title": "خلاصه تمرین امروز و آنالیز مربی",
        "mock_items": [
            {"label": "حرکت تمرینی", "val": "پرس سینه ۳ ست ۱۰ تایی", "color": "#34d399"},
            {"label": "تایمر استراحت", "val": "۰۰:۹۰ ثانیه (صوتی)", "color": "#fbbf24"},
            {"label": "تفسیر مربی هوشمند", "val": "«عالی بود رفیق! روند پیشرفتت ۱۵٪ رشد داشته.»", "color": "#60a5fa"}
        ]
    },
    {
        "id": "gold1",
        "badge": "📈 سرمایه‌گذاری و بورس",
        "title": "صندوق‌های ثبت درصد ۱ تا ۷",
        "subtitle": "مدیریت و ثبت دقیق بازدهی روزانه",
        "desc": "ثبت روزانه سود، محاسبه اتوماتیک نقطه اوج، فرمول قیمت ابطال، همگام‌سازی ابری خودکار و محاسبه سود تومانی.",
        "icon": "gold/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1035 100%)",
        "accent": "#f59e0b",
        "mock_type": "fund_preview",
        "mock_title": "نمونه داده‌های ثبت درصد صندوق‌ها",
        "mock_items": [
            {"label": "ثبت درصد امروز (۱۴۰۴/۰۶/۱۷)", "val": "+۱.۴۵٪", "color": "#34d399"},
            {"label": "نقطه اوج (Peak)", "val": "+۴۲.۸۰٪", "color": "#fbbf24"},
            {"label": "سود تومانی امروز", "val": "+۳,۴۵۰,۰۰۰ تومان", "color": "#60a5fa"},
            {"label": "وضعیت رکورد", "val": "عبور از اوج جدید 🔥", "color": "#f43f5e"}
        ]
    },
    {
        "id": "monitor",
        "badge": "📊 مرکز کنترل و پایش",
        "title": "دیدبان درصدها",
        "subtitle": "پایش جامع ۷ صندوق و صورت مالی",
        "desc": "نمایش بازدهی لحظه‌ای، گزارشات صورت مالی ماهانه با مهر رسمی، نمودارهای رشد طلایی و خروجی فاکتور بانک.",
        "icon": "monitor/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)",
        "accent": "#60a5fa",
        "mock_type": "monitor_preview",
        "mock_title": "گزارش دیدبان درصدها",
        "mock_items": [
            {"label": "مجموع سود کل تومانی", "val": "+۱۲۸,۵۰۰,۰۰۰ تومان", "color": "#34d399"},
            {"label": "میانگین درصد روزانه", "val": "+۰.۸۲٪ در روز", "color": "#60a5fa"},
            {"label": "صندوق پیشتاز ماه", "val": "صندوق آهنگ سهام کیان (۷)", "color": "#f0abfc"},
            {"label": "صورت مالی ماهانه", "val": "آماده دانلود PDF / HTML 📄", "color": "#fbbf24"}
        ]
    },
    {
        "id": "profit",
        "badge": "💵 محاسبات مالی",
        "title": "محاسبه‌گر سود",
        "subtitle": "سود مرکب، سود روزانه و دخل‌ومصارف",
        "desc": "محاسبه دقیق سود مرکب، رصد میانگین سود روزانه صندوق‌ها و مدیریت دخل و خرج با تم تاریک شیک.",
        "icon": "profit-calculator/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #1e293b 0%, #0f766e 50%, #115e59 100%)",
        "accent": "#2dd4bf",
        "mock_type": "profit_preview",
        "mock_title": "محاسبه سود مرکب و دخل و خرج",
        "mock_items": [
            {"label": "سرمایه اولیه", "val": "۱۰۰,۰۰۰,۰۰۰ تومان", "color": "#2dd4bf"},
            {"label": "نرخ سود ماهانه", "val": "۲.۵٪ مرکب", "color": "#fbbf24"},
            {"label": "پیش‌بینی ۱ ساله", "val": "۱۳۴,۴۸۸,۸۲۴ تومان", "color": "#34d399"},
            {"label": "بخش دخل و خرج", "val": "مدیریت هزینه‌های ماهانه", "color": "#a7f3d0"}
        ]
    },
    {
        "id": "restricted",
        "badge": "🛡️ دانلودر هوشمند",
        "title": "سپر دانلود",
        "subtitle": "استخراج چندلایه ویدیو و ارسال به تلگرام",
        "desc": "استخراج ویدیو از اینستاگرام، یوتیوب و وب با موتورهای چندلایه yt-dlp و Gemini AI و ارسال خودکار به تلگرام.",
        "icon": "restricted/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #1e1b4b 0%, #4c1d95 50%, #2e1065 100%)",
        "accent": "#c084fc",
        "mock_type": "download_preview",
        "mock_title": "وضعیت زنده دانلودها",
        "mock_items": [
            {"label": "لینک ورودی", "val": "instagram.com/p/C...", "color": "#c084fc"},
            {"label": "موتور استخراج", "val": "Gemini AI + yt-dlp (لایه ۲)", "color": "#38bdf8"},
            {"label": "کیفیت فایل", "val": "1080p MP4 (کاهش حجم هوشمند)", "color": "#34d399"},
            {"label": "ارسال به تلگرام", "val": "تکمیل شده ✅ (کانال مقصد)", "color": "#fbbf24"}
        ]
    },
    {
        "id": "ai-chat",
        "badge": "🤖 هوش مصنوعی",
        "title": "چت هوشمند",
        "subtitle": "دستیار گفتگوگر قدرتمند Gemini",
        "desc": "پاسخگویی به سوالات، تحلیل متون و کد، مشاوره تخصصی و تولید محتوا با آخرین مدل‌های هوش مصنوعی.",
        "icon": "ai-chat/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #172554 100%)",
        "accent": "#38bdf8",
        "mock_type": "ai_preview",
        "mock_title": "نمونه گفتگوی هوش مصنوعی",
        "mock_items": [
            {"label": "کاربر", "val": "بهترین روش برنامه‌ریزی مالی چیه؟", "color": "#93c5fd"},
            {"label": "هوش مصنوعی Gemini", "val": "«تفکیک ۵۰/۳۰/۲۰ سرمایه و ثبت روزانه سود در صندوق‌ها...»", "color": "#38bdf8"}
        ]
    },
    {
        "id": "simple-chat",
        "badge": "🙇‍♂️ دستیار مطیع",
        "title": "چت فرمان‌بردار",
        "subtitle": "هوش مصنوعی مطیع با لحن «اطاعت»",
        "desc": "پاسخگویی بسیار سریع و باادب به دستورات شما بدون هیچ‌گونه پاسخ منفی یا محدودیت.",
        "icon": "simple-chat/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #18181b 0%, #27272a 50%, #09090b 100%)",
        "accent": "#a1a1aa",
        "mock_type": "simple_preview",
        "mock_title": "دستورات و پاسخ‌های هوش مصنوعی",
        "mock_items": [
            {"label": "دستور کاربر", "val": "این متن رو خلاصه کن", "color": "#e4e4e7"},
            {"label": "پاسخ مدل", "val": "«اطاعت سرورم! متن با دقت خلاصه گردید...»", "color": "#fbbf24"}
        ]
    },
    {
        "id": "clipboard",
        "badge": "📋 مدیریت متون",
        "title": "کلیپ بورد هوشمند",
        "subtitle": "ذخیره، پین و دسته‌بندی متن‌ها",
        "desc": "خواندن خودکار کلیپ‌بورد، پین‌کردن یادداشت‌های مهم، فولدرهای رنگی سفارشی و تاریخ دقیق شمسی.",
        "icon": "clipboard/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #1c1917 0%, #451a03 50%, #292524 100%)",
        "accent": "#fb923c",
        "mock_type": "clip_preview",
        "mock_title": "لیست یادداشت‌های کلیپ بورد",
        "mock_items": [
            {"label": "📌 یادداشت پین شده", "val": "شماره حساب و کارت‌های بانکی", "color": "#fb923c"},
            {"label": "📁 فولدر کدهای روزانه", "val": "۵ متن ذخیره شده (خودکار)", "color": "#fcd34d"},
            {"label": "تاریخ ثبت", "val": "۱۴۰۴/۰۶/۱۷ - ۱۸:۴۵:۱۰", "color": "#a1a1aa"}
        ]
    },
    {
        "id": "html-viewer",
        "badge": "💻 توسعه و کد",
        "title": "نمایشگر کد HTML",
        "subtitle": "اجرای زنده وب و ابزار متن ساده",
        "desc": "پیش‌نمایش وب با قابلیت Canvas/WebGL، دانلود سورس کدها با عناوین هوشمند Gemini AI و تاریخ شمسی.",
        "icon": "html-viewer/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #0f172a 0%, #0369a1 50%, #0c4a6e 100%)",
        "accent": "#38bdf8",
        "mock_type": "html_preview",
        "mock_title": "پیش‌نمایش زنده کد HTML",
        "mock_items": [
            {"label": "وضعیت رندر", "val": "اجرای زنده JS / CSS / HTML5", "color": "#38bdf8"},
            {"label": "عنوان‌نویسی هوشمند", "val": "Gemini Smart Title Generator", "color": "#34d399"},
            {"label": "دانلود سورس", "val": "نام‌گذاری خودکار با تاریخ شمسی", "color": "#fef08a"}
        ]
    },
    {
        "id": "skincare",
        "badge": "🌿 سلامتی و زیبایی",
        "title": "مراقبت پوستی",
        "subtitle": "روتین پوستی و تایمر استراحت",
        "desc": "ثبت منظم روتین‌های روزانه، تایمر استراحت ۷۲ ساعته هوشمند تا بامداد روز بعد و یادآوری منظم.",
        "icon": "skincare/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #1a2e05 0%, #3f6212 50%, #14532d 100%)",
        "accent": "#a3e635",
        "mock_type": "skin_preview",
        "mock_title": "وضعیت روتین پوستی",
        "mock_items": [
            {"label": "روتین امروز", "val": "شستشو + آبرسان + ضدآفتاب", "color": "#a3e635"},
            {"label": "تایمر قفل ۷۲ ساعته", "val": "۴۸ ساعت و ۱۲ دقیقه باقی‌مانده", "color": "#fef08a"},
            {"label": "شروع تایمر", "val": "بامداد روز بعد (۱۲:۰۰ AM)", "color": "#86efac"}
        ]
    },
    {
        "id": "vault",
        "badge": "🔐 امنیت داده‌ها",
        "title": "رمز راز",
        "subtitle": "صندوقچه امن و رمزنگاری‌شده",
        "desc": "نگهداری محرمانه کلمات عبور، اطلاعات خصوصی و یادداشت‌های رمزنگاری شده با امنیت بالاو قفل محرمانه.",
        "icon": "vault/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #1f2937 0%, #111827 50%, #030712 100%)",
        "accent": "#f87171",
        "mock_type": "vault_preview",
        "mock_title": "صندوقچه رمز راز",
        "mock_items": [
            {"label": "سطح رمزنگاری", "val": "AES-256 Local Encryption", "color": "#f87171"},
            {"label": "تعداد گاوصندوق‌ها", "val": "۱۲ کلمه عبور و کلید امنیتی", "color": "#fca5a5"},
            {"label": "دسترسی آفلاین", "val": "بدون اتصال به سرور (محرمانه)", "color": "#34d399"}
        ]
    },
    {
        "id": "funds",
        "badge": "🌐 سامانه وب‌ویو",
        "title": "WWW.com (وب‌سایت صندوق‌ها)",
        "subtitle": "دسترسی مستقیم به سامانه‌های مالی",
        "desc": "مشاهده مستقیم نمودارهای NAV صندوق‌ها، صرافی فارابی و کیان بدون نیاز به خروج از برنامه.",
        "icon": "funds/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #172554 0%, #1e40af 50%, #1e3a8a 100%)",
        "accent": "#60a5fa",
        "mock_type": "funds_preview",
        "mock_title": "سامانه وب‌ویو صندوق‌ها",
        "mock_items": [
            {"label": "تب ۱: صرافی فارابی", "val": "energy.irfarabi.ir", "color": "#60a5fa"},
            {"label": "تب ۲: صندوق بازنشستگی", "val": "kianfunds4.ir", "color": "#93c5fd"},
            {"label": "تب ۳: روند NAV کیان", "val": "نمودار زنده NAV صندوق", "color": "#34d399"}
        ]
    },
    {
        "id": "yandex",
        "badge": "🖼️ جستجوی بصری",
        "title": "جستجوگر عکس",
        "subtitle": "موتور هوشمند یافتن تصاویر مشابه",
        "desc": "یافتن تصاویر با کیفیت بالا، نسخه‌های با وضوح بهتر و عکس‌های مشابه براساس آپلود فایل یا لینک.",
        "icon": "yandex/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #450a0a 0%, #7f1d1d 50%, #3f0712 100%)",
        "accent": "#fca5a5",
        "mock_type": "yandex_preview",
        "mock_title": "نتایج جستجوی تصویری",
        "mock_items": [
            {"label": "تصویر ورودی", "val": "فایل عکس / URL", "color": "#fca5a5"},
            {"label": "کیفیت یافت‌شده", "val": "4K Ultra HD (مشابه)", "color": "#f87171"},
            {"label": "موتور جستجو", "val": "Yandex Vision API", "color": "#fbbf24"}
        ]
    },
    {
        "id": "tabdeal",
        "badge": "🪙 ارز دیجیتال",
        "title": "کیف پول تبدیل",
        "subtitle": "مدیریت دارایی‌های صرافی تبدیل",
        "desc": "رصد لحظه‌ای موجودی کریپتو، محاسبه قیمت‌ها و مدیریت کیف پول دیجیتال.",
        "icon": "tabdeal/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #14532d 0%, #166534 50%, #052e16 100%)",
        "accent": "#4ade80",
        "mock_type": "tabdeal_preview",
        "mock_title": "موجودی کیف پول تبدیل",
        "mock_items": [
            {"label": "موجودی کل (تومان)", "val": "۸۵,۴۰۰,۰۰۰ تومان", "color": "#4ade80"},
            {"label": "ارزهای برتر", "val": "USDT, BTC, ETH", "color": "#86efac"},
            {"label": "سود ۲۴ ساعت گذشته", "val": "+۳.۲٪ 🟢", "color": "#34d399"}
        ]
    },
    {
        "id": "detective",
        "badge": "🔍 آنالیز و آمار",
        "title": "کارآگاه داده‌ها",
        "subtitle": "ردیابی و تحلیل رفتار آماری",
        "desc": "بررسی هوشمند الگوهای داده، کشف تغییرات و آنالیز دقیق اطلاعات ورودی.",
        "icon": "detective/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #312e81 0%, #3730a3 50%, #1e1b4b 100%)",
        "accent": "#818cf8",
        "mock_type": "detective_preview",
        "mock_title": "تحلیل آنالیز کارآگاه داده‌ها",
        "mock_items": [
            {"label": "حجم داده ورودی", "val": "۱,۲۴۰ رکورد آماری", "color": "#818cf8"},
            {"label": "الگوی کشف‌شده", "val": "روند صعودی همبستگی داده‌ها", "color": "#a5b4fc"},
            {"label": "پیش‌بینی نهایی", "val": "دقت ۹۸.۴٪", "color": "#34d399"}
        ]
    },
    {
        "id": "family",
        "badge": "🌳 شجره‌نامه خانوادگی",
        "title": "شجره‌نامه",
        "subtitle": "مدیریت و رسم درخت خانوادگی",
        "desc": "ثبت اعضای خانواده، ارتباطات فامیلی، تاریخ رویدادهای مهم و رسم شجره‌نامه تصویری.",
        "icon": "family/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #064e3b 0%, #047857 50%, #022c22 100%)",
        "accent": "#34d399",
        "mock_type": "family_preview",
        "mock_title": "نمودار شجره‌نامه خانوادگی",
        "mock_items": [
            {"label": "تعداد اعضا", "val": "۲۸ نفر ثبت شده", "color": "#34d399"},
            {"label": "نسل‌های فعال", "val": "۴ نسل خانوادگی", "color": "#a7f3d0"},
            {"label": "رویدادهای پیش‌رو", "val": "تولدها و سالگردها", "color": "#fbbf24"}
        ]
    },
    {
        "id": "monthly-deposit",
        "badge": "🗓️ برنامه‌ریزی مالی",
        "title": "واریز ماهیانه",
        "subtitle": "زمان‌بندی و ثبت موعد واریزی‌ها",
        "desc": "ثبت واریزهای ماهانه، نشانگر روزشمار زنده، و همگام‌سازی مستقیم با کارت‌های دیدبان درصدها.",
        "icon": "monthly-deposit/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #701a75 0%, #86198f 50%, #4a044e 100%)",
        "accent": "#f0abfc",
        "mock_type": "deposit_preview",
        "mock_title": "روزشمار واریز ماهیانه",
        "mock_items": [
            {"label": "واریزی ماه جاری", "val": "۱۰,۰۰۰,۰۰۰ تومان", "color": "#f0abfc"},
            {"label": "زمان گذشته", "val": "۵ روز گذشته 🔴", "color": "#f43f5e"},
            {"label": "همگام‌سازی", "val": "نمایش روی کارت‌های دیدبان", "color": "#34d399"}
        ]
    },
    {
        "id": "peace",
        "badge": "🕊️ حس خوب و آرامش",
        "title": "ثبت آرامش",
        "subtitle": "ثبت لحظات و تجربیات مثبت",
        "desc": "دفترچه یادداشت اختصاصی برای ذخیره لحظات آرامش‌بخش، شکرگزاری و ارتقای روحیه.",
        "icon": "peace/icon-192.png",
        "is_emoji": False,
        "bg_gradient": "linear-gradient(135deg, #0f766e 0%, #115e59 50%, #134e4a 100%)",
        "accent": "#5eead4",
        "mock_type": "peace_preview",
        "mock_title": "یادداشت‌های ثبت آرامش",
        "mock_items": [
            {"label": "احساس امروز", "val": "آرامش عالی و حس شکرگزاری ✨", "color": "#5eead4"},
            {"label": "لحظه ثبت‌شده", "val": "پیاده‌روی غروب در هوای عالی", "color": "#99f6e4"},
            {"label": "تعداد یادداشت‌ها", "val": "۴۲ حس خوب ثبت شده", "color": "#fbbf24"}
        ]
    },
    {
        "id": "outro",
        "badge": "🏛️ پایان معرفی",
        "title": "عمارت دیجیتال",
        "subtitle": "یکپارچه، سریع، آفلاین و هوشمند",
        "desc": "طراحی شده برای بیشترین کارایی و سهولت استفاده. تمامی ابزارها آماده استفاده شما هستند.",
        "icon": "🏛️",
        "is_emoji": True,
        "bg_gradient": "linear-gradient(135deg, #020617 0%, #1e1b4b 50%, #0f172a 100%)",
        "accent": "#fbbf24",
        "mock_type": "outro",
        "mock_title": "ویژگی‌های برجسته عمارت",
        "mock_items": [
            {"label": "دسترسی ۱۰۰٪ آفلاین", "val": "پشتیبانی کامل PWA / Service Worker", "color": "#34d399"},
            {"label": "امنیت و بکاپگیری", "val": "دانلود بکاپ کامل JSON و GitHub Sync", "color": "#60a5fa"},
            {"label": "تقدیم به", "val": "همراهان گرامی کانال «دنیا های قشنگ» ❤️", "color": "#f0abfc"}
        ]
    }
]

def get_base64_icon(icon_relative_path, root_dir):
    abs_path = os.path.abspath(os.path.join(root_dir, icon_relative_path))
    if os.path.exists(abs_path):
        with open(abs_path, 'rb') as f:
            return 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')
    return ''

def generate_html_slide(slide_data, root_dir):
    icon_html = ""
    if slide_data['is_emoji']:
        icon_html = f"<span class='emoji-icon'>{slide_data['icon']}</span>"
    else:
        b64 = get_base64_icon(slide_data['icon'], root_dir)
        icon_html = f"<img src='{b64}' alt='icon' />"

    mock_items_html = ""
    for item in slide_data.get('mock_items', []):
        mock_items_html += f"""
        <div class="mock-row">
            <span class="mock-label">{item['label']}</span>
            <span class="mock-val" style="color: {item['color']};">{item['val']}</span>
        </div>
        """

    mock_box_html = f"""
    <div class="mock-box">
        <div class="mock-header">
            <div class="mock-dots">
                <span class="dot red"></span>
                <span class="dot yellow"></span>
                <span class="dot green"></span>
            </div>
            <div class="mock-title">{slide_data.get('mock_title', 'پیش‌نمایش داده‌ها')}</div>
        </div>
        <div class="mock-body">
            {mock_items_html}
        </div>
    </div>
    """

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        width: 1080px;
        height: 1920px;
        font-family: 'Vazirmatn', sans-serif;
        background: {slide_data['bg_gradient']};
        color: #ffffff;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        padding: 100px 70px 110px 70px;
        position: relative;
        overflow: hidden;
    }}

    .orb-1 {{
        position: absolute;
        top: -120px;
        right: -120px;
        width: 650px;
        height: 650px;
        background: {slide_data['accent']};
        opacity: 0.18;
        filter: blur(150px);
        border-radius: 50%;
    }}
    .orb-2 {{
        position: absolute;
        bottom: -120px;
        left: -120px;
        width: 750px;
        height: 750px;
        background: {slide_data['accent']};
        opacity: 0.15;
        filter: blur(170px);
        border-radius: 50%;
    }}

    .header-badge {{
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(25px);
        border: 1.5px solid rgba(255, 255, 255, 0.25);
        padding: 16px 45px;
        border-radius: 50px;
        font-size: 32px;
        font-weight: 700;
        color: {slide_data['accent']};
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 2;
    }}

    .main-card {{
        width: 100%;
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(40px);
        -webkit-backdrop-filter: blur(40px);
        border: 2px solid rgba(255, 255, 255, 0.18);
        border-radius: 44px;
        padding: 55px 50px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.5);
        z-index: 2;
    }}

    .icon-wrapper {{
        width: 190px;
        height: 190px;
        background: #ffffff;
        border-radius: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 20px 50px rgba(0,0,0,0.4);
        margin-bottom: 35px;
        border: 4px solid rgba(255,255,255,0.5);
    }}

    .icon-wrapper img {{
        width: 140px;
        height: 140px;
        object-fit: contain;
    }}

    .emoji-icon {{
        font-size: 110px;
        line-height: 1;
    }}

    .app-title {{
        font-size: 52px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 15px;
        text-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}

    .app-subtitle {{
        font-size: 30px;
        font-weight: 600;
        color: {slide_data['accent']};
        margin-bottom: 25px;
        line-height: 1.4;
    }}

    .divider {{
        width: 120px;
        height: 5px;
        background: {slide_data['accent']};
        border-radius: 3px;
        margin-bottom: 30px;
        opacity: 0.8;
    }}

    .app-desc {{
        font-size: 28px;
        font-weight: 400;
        color: #e2e8f0;
        line-height: 1.7;
        margin-bottom: 40px;
        max-width: 860px;
    }}

    .mock-box {{
        width: 100%;
        background: rgba(15, 23, 42, 0.75);
        border: 1.5px solid rgba(255, 255, 255, 0.2);
        border-radius: 28px;
        overflow: hidden;
        text-align: right;
        box-shadow: 0 15px 40px rgba(0,0,0,0.4);
    }}

    .mock-header {{
        background: rgba(255, 255, 255, 0.08);
        padding: 16px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }}

    .mock-dots {{
        display: flex;
        gap: 8px;
    }}

    .dot {{
        width: 14px;
        height: 14px;
        border-radius: 50%;
    }}
    .dot.red {{ background: #f87171; }}
    .dot.yellow {{ background: #fbbf24; }}
    .dot.green {{ background: #34d399; }}

    .mock-title {{
        font-size: 24px;
        font-weight: 600;
        color: #cbd5e1;
    }}

    .mock-body {{
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }}

    .mock-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.05);
        padding: 16px 22px;
        border-radius: 18px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .mock-label {{
        font-size: 24px;
        font-weight: 500;
        color: #94a3b8;
    }}

    .mock-val {{
        font-size: 26px;
        font-weight: 700;
    }}

    .footer-brand {{
        display: flex;
        align-items: center;
        gap: 20px;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 18px 40px;
        border-radius: 40px;
        font-size: 26px;
        font-weight: 500;
        color: #cbd5e1;
        z-index: 2;
    }}

    .footer-brand span {{
        color: #fbbf24;
        font-weight: 700;
    }}
</style>
</head>
<body>
    <div class="orb-1"></div>
    <div class="orb-2"></div>

    <div class="header-badge">{slide_data['badge']}</div>

    <div class="main-card">
        <div class="icon-wrapper">
            {icon_html}
        </div>
        <div class="app-title">{slide_data['title']}</div>
        <div class="app-subtitle">{slide_data['subtitle']}</div>
        <div class="divider"></div>
        <div class="app-desc">{slide_data['desc']}</div>

        {mock_box_html}
    </div>

    <div class="footer-brand">
        سامانه جامع <span>عمارت دیجیتال</span> 🏛️ | دنیا های قشنگ
    </div>
</body>
</html>
"""
    return html

async def generate_all_slide_images():
    from playwright.async_api import async_playwright

    root_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(root_dir, "slide_frames")
    os.makedirs(output_dir, exist_ok=True)

    print("Generating high-resolution slides with Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1920})

        image_paths = []
        for index, slide in enumerate(SLIDES):
            html_code = generate_html_slide(slide, root_dir)
            await page.set_content(html_code)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(0.3)

            img_path = os.path.join(output_dir, f"slide_{index:02d}.png")
            await page.screenshot(path=img_path, full_page=True)
            image_paths.append(img_path)
            print(f"  [+] Slide {index+1}/{len(SLIDES)} rendered: {slide['title']}")

        await browser.close()
    return image_paths

def generate_video_via_ffmpeg(slide_frames_dir, output_mp4, duration_per_slide=3.0):
    print("Building video with FFmpeg CLI...")
    concat_txt = os.path.join(slide_frames_dir, "concat.txt")
    slide_files = sorted(glob.glob(os.path.join(slide_frames_dir, "slide_*.png")))

    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in slide_files:
            f.write(f"file '{os.path.basename(s)}'\n")
            f.write(f"duration {duration_per_slide}\n")
        if slide_files:
            f.write(f"file '{os.path.basename(slide_files[-1])}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-vf", "fps=30,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        output_mp4
    ]

    subprocess.run(cmd, check=True, cwd=slide_frames_dir)
    print("Video rendered successfully with FFmpeg!")

def send_video_to_telegram(video_path, bot_token, chat_id):
    caption = '''🏛️ **کلیپ معرفی کامل تمام ابزارهای عمارت دیجیتال**

معرفی نسخه جدید با نمایش آیکون‌های شفاف و پیش‌نمایش زنده داده‌های ساختگی ۲۴ ابزار هوشمند، مالی و کاربردی:

▫️ **Activity (مربی هوشمند):** ثبت ست‌های ورزشی، تایمر صوتی و تحلیل ورزشی
▫️ **صندوق‌های ثبت درصد ۱ تا ۷:** مدیریت سودهای روزانه، نقطه اوج و همگام‌سازی ابری
▫️ **دیدبان درصدها:** مرکز کنترل، گزارشات مالی ماهانه با مهر رسمی و خروجی فاکتور
▫️ **محاسبه‌گر سود:** سود مرکب، سود روزانه و مدیریت دخل‌ومصارف
▫️ **سپر دانلود:** دانلودر هوشمند چندلایه شبکه‌های اجتماعی و وب
▫️ **چت هوشمند و چت فرمان‌بردار:** دستیارهای گفتگوگر هوش مصنوعی Gemini
▫️ **کلیپ بورد هوشمند:** ذخیره و دسته‌بندی پیشرفته متون با خوانش خودکار
▫️ **نمایشگر کد HTML:** اجرای زنده وب و ابزار متن ساده
▫️ **مراقبت پوستی، رمز راز، WWW.com، جستجوگر عکس، کیف پول تبدیل، کارآگاه داده‌ها، شجره‌نامه، واریز ماهیانه و ثبت آرامش**

✨ *تقدیم به همراهان گرامی کانال «دنیا های قشنگ»* ❤️'''

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

    def encode_multipart_formdata(fields, files):
        body = bytearray()
        for key, value in fields.items():
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode('utf-8'))
            body.extend(f'{value}\r\n'.encode('utf-8'))
        for key, filename, content, content_type in files:
            body.extend(f'--{boundary}\r\n'.encode('utf-8'))
            body.extend(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode('utf-8'))
            body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
            body.extend(content)
            body.extend(b'\r\n')
        body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
        return body

    with open(video_path, 'rb') as f:
        video_bytes = f.read()

    fields = {
        'chat_id': chat_id,
        'caption': caption,
        'parse_mode': 'Markdown',
        'supports_streaming': 'true'
    }
    files = [('video', os.path.basename(video_path), video_bytes, 'video/mp4')]

    data = encode_multipart_formdata(fields, files)

    url = f'https://api.telegram.org/bot{bot_token}/sendVideo'
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

    print('Sending video to Telegram...')
    with urllib.request.urlopen(req, timeout=180) as response:
        res_body = response.read().decode('utf-8')
        res_json = json.loads(res_body)
        if res_json.get('ok'):
            print('SUCCESSFULLY SENT VIDEO TO TELEGRAM CHANNEL!')
            return res_json
        else:
            print('TELEGRAM RETURNED ERROR:', res_json)
            raise RuntimeError(f'Telegram upload failed: {res_json}')

async def main():
    image_paths = await generate_all_slide_images()
    slide_dir = os.path.dirname(image_paths[0])
    output_mp4 = os.path.abspath("emarat_showcase_video.mp4")
    generate_video_via_ffmpeg(slide_dir, output_mp4, duration_per_slide=3.0)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if bot_token and chat_id:
        send_video_to_telegram(output_mp4, bot_token, chat_id)
    else:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable not set. Skipping upload.")

    # Clean up temporary video file and frames to prevent git repository bloat
    if os.path.exists(output_mp4):
        os.remove(output_mp4)
    if os.path.exists(slide_dir):
        for f in glob.glob(os.path.join(slide_dir, "*")):
            os.remove(f)
        os.rmdir(slide_dir)

if __name__ == "__main__":
    asyncio.run(main())
