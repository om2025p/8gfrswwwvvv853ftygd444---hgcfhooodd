import os
import sys
import asyncio
import glob
import math
import subprocess
import urllib.request
import urllib.parse
import json

# Full list of all 24 apps in Emarat Digital with real UI paths and step-by-step instructions
REAL_UI_TUTORIALS = [
    {
        "id": "gym",
        "title": "Activity (مربی هوشمند ورزشی)",
        "url_path": "gym/index.html",
        "accent": "#38bdf8",
        "steps": [
            {
                "bubble_title": "💡 معرفی رابط کاربری برنامه",
                "bubble_text": "این صفحه اصلی برنامه Activity است! تمام ست‌های تمرینی، کارت حرکات و تایمرهای شما در یک محیط شیک قرار دارند.",
                "arrow_top": 80,
                "arrow_left": 500,
                "arrow_icon": "⬇️",
                "bubble_top": 180,
                "bubble_right": 80
            },
            {
                "bubble_title": "🏋️‍♂️ انتخاب تمرینات روزانه",
                "bubble_text": "حرکت تمرینی مورد نظر خود را انتخاب کرده و تعداد ست‌ها، رپ‌ها و وزنه مورد نظر را تنظیم کنید.",
                "arrow_top": 300,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 400,
                "bubble_right": 80
            },
            {
                "bubble_title": "⏱️ ثبت ست‌ها و تایمر هوشمند",
                "bubble_text": "با زدن تیک هر ست تمرینی، تایمر استراحت صوتی بلافاصله فعال می‌شود تا زمان استراحت دقیقاً رعایت شود!",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🤖 تحلیل مربی هوشمند Gemini",
                "bubble_text": "با زدن دکمه مربی هوشمند، سیستم با بررسی رکوردهای شما، تحلیل تخصصی و توصیه‌های ورزشی کاربردی ارائه می‌دهد!",
                "arrow_top": 750,
                "arrow_left": 500,
                "arrow_icon": "🎯",
                "bubble_top": 600,
                "bubble_right": 80
            },
            {
                "bubble_title": "📊 نمودارهای صعودی DNA پیشرفت",
                "bubble_text": "روند پیشرفت جلسات و میزان وزنه در نمودارهای DNA نمایش داده شده تا انگیزه شما حفظ گردد.",
                "arrow_top": 900,
                "arrow_left": 450,
                "arrow_icon": "📈",
                "bubble_top": 780,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔒 تایمر قفل استراحت ۴۸ ساعته",
                "bubble_text": "پس از پایان جلسه، تایمر استراحت ۴۸ ساعته جهت ریکاوری عضلانی شروع به کار می‌کند.",
                "arrow_top": 1100,
                "arrow_left": 500,
                "arrow_icon": "⏳",
                "bubble_top": 980,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold1",
        "title": "صندوق ثبت درصد ۱ (طلا)",
        "url_path": "gold/index.html",
        "accent": "#f59e0b",
        "steps": [
            {
                "bubble_title": "📈 محیط واقعی ثبت درصد ۱",
                "bubble_text": "در این صفحه می‌توانید درصد بازدهی یا قیمت جدید ابطال صندوق ۱ را وارد کنید.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "⬇️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔢 ورود قیمت جدید ابطال",
                "bubble_text": "عدد قیمت جدید را تایپ کرده و دکمه محاسبه سود را فشار دهید.",
                "arrow_top": 320,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 420,
                "bubble_right": 80
            },
            {
                "bubble_title": "💰 محاسبه سود تومانی صاف",
                "bubble_text": "سود خالص تومانی حاصل از تغییر قیمت به طور خودکار محاسبه و نمایش داده می‌شود.",
                "arrow_top": 520,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 450,
                "bubble_right": 100
            },
            {
                "bubble_title": "🚀 رصد نقطه اوج (Peak)",
                "bubble_text": "در صورت عبور از سقف قبلی سود، آیکون اوج جدید و رنگ سبز نمایان می‌گردد.",
                "arrow_top": 700,
                "arrow_left": 450,
                "arrow_icon": "🏆",
                "bubble_top": 600,
                "bubble_right": 80
            },
            {
                "bubble_title": "📜 تاریخچه و تقویم شمسی",
                "bubble_text": "تمام سودهای قبلی با تاریخ دقیق شمسی در جدول تاریخچه ثبت می‌شوند.",
                "arrow_top": 900,
                "arrow_left": 500,
                "arrow_icon": "📅",
                "bubble_top": 780,
                "bubble_right": 80
            },
            {
                "bubble_title": "☁️ همگام‌سازی ابری GitHub",
                "bubble_text": "اطلاعات بلافاصله در مخزن گیت‌هاب و دیتابیس ابری همگام‌سازی می‌شوند.",
                "arrow_top": 1100,
                "arrow_left": 480,
                "arrow_icon": "☁️",
                "bubble_top": 980,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold2",
        "title": "صندوق ثبت درصد ۲",
        "url_path": "gold2/index.html",
        "accent": "#eab308",
        "steps": [
            {
                "bubble_title": "📊 محیط ثبت درصد صندوق ۲",
                "bubble_text": "مدیریت و ثبت درصد بازدهی اختصاصی برای دومین صندوق سرمایه‌گذاری شما.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "⬇️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✏️ فرم ثبت درصد روزانه",
                "bubble_text": "وارد کردن درصد سود یا زیان امروز و کسر اتوماتیک کارمزدها.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "💵 محاسبه سود خالص تومانی",
                "bubble_text": "تبدیل فوری درصد به سود تومانی با حذف ۴ صفر و گردکردن هوشمند.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📈 نمودار روند بازدهی",
                "bubble_text": "مشاهده منحنی رشد دارایی‌ها بر اساس سودهای ثبت شده قبلی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "📉",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📂 بازیابی و بکاپگیری",
                "bubble_text": "امکان دانلود بکاپ JSON یا بازیابی اطلاعات در صورت نیاز.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "💾",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔄 همگام با دیدبان",
                "bubble_text": "اتصال مستقیم آمار این صندوق به دیدبان درصدها و محاسبه‌گر سود.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🔗",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold3",
        "title": "صندوق ثبت درصد ۳",
        "url_path": "gold3/index.html",
        "accent": "#10b981",
        "steps": [
            {
                "bubble_title": "📊 محیط اختصاصی صندوق ۳",
                "bubble_text": "مدیریت و ثبت بازدهی روزانه صندوق سوم با تم سبز زمردی.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "⬇️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "🏷️ محاسبه قیمت ابطال",
                "bubble_text": "قابلیت محاسبه درصد بر اساس قیمت ابطال جدید واحدها.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📅 تقویم شمسی نقطه‌ای",
                "bubble_text": "افزایش روزانه تاریخ شمسی با فرمول دقیق Jalali.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "📅",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🏆 ثبت رکورد جدید اوج",
                "bubble_text": "نمایش نشانگر اوج سود در صورت جابجایی سقف تاریخی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🔥",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📋 ویرایش رکوردهای گذشته",
                "bubble_text": "امکان اصطلاح و ویرایش تاریخچه‌ها با کلیک روی کارت‌ها.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "✏️",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🌐 ذخیره ابری و محلی",
                "bubble_text": "ذخیره‌سازی همزمان محلی و ابری با بالاترین امنیت.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "☁️",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold4",
        "title": "صندوق ثبت درصد ۴ (مفید آتیه)",
        "url_path": "gold4/index.html",
        "accent": "#0d6efd",
        "steps": [
            {
                "bubble_title": "🤖 ربات اتوماسیون EasyTrader",
                "bubble_text": "این صندوق متصل به ربات Playwright ایزی‌تریدر جهت ثبت اتوماتیک است!",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🤖",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "📊 تب ثبت درصد و محاسبه تغییرات",
                "bubble_text": "دارای ۲ تب مجزا جهت ثبت درصد و محاسبه تغییرات قیمت.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "🏷️ نشانگر اتوماتیک ربات",
                "bubble_text": "رکوردهای ثبت شده توسط ربات با نشانگر 🤖 متمایز می‌شوند.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "💵 محاسبه سود خالص تومانی",
                "bubble_text": "محاسبه دقیق سود تومانی حاصل از تغییر ارزش دارایی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "💰",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔄 همگام‌سازی دوطرفه",
                "bubble_text": "همگام‌سازی مستقیم با کلیدهای pension_history و MantleDB.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🔄",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🏆 پایش اوج سود",
                "bubble_text": "محاسبه سودهای خالص بالاتر از اوج قبلی سرمایه.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🏆",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold5",
        "title": "صندوق ثبت درصد ۵ (سینرژی)",
        "url_path": "gold5/index.html",
        "accent": "#8b5cf6",
        "bg_gradient": "linear-gradient(135deg, #1e1b4b 0%, #4c1d95 50%, #2e1065 100%)",
        "steps": [
            {
                "bubble_title": "⚡ ثبت درصد صندوق ۵",
                "bubble_text": "برنامه تخصصی صندوق سینرژی متصل به استخراج اتوماتیک NAV.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "⬇️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✏️ ورود اطلاعات قیمت ابطال",
                "bubble_text": "محاسبه دقیق درصد بر اساس فرمول NAV جدید.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "💰 محاسبه سود تومانی صاف",
                "bubble_text": "محاسبه سود صاف و گرد شده تومانی در لحظه.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📜 تاریخچه با تاریخ شمسی",
                "bubble_text": "ثبت رکوردهای سود در جدول منظم شمسی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "📅",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "☁️ بکاپ خودکار ابری",
                "bubble_text": "ارسال اتوماتیک بکاپ به فایل gold5_backup.json.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "☁️",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📊 نمایش در دیدبان درصدها",
                "bubble_text": "نمایش داده‌ها روی کارت اختصاصی ۵ در دیدبان درصدها.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📊",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold6",
        "title": "صندوق ثبت درصد ۶",
        "url_path": "gold6/index.html",
        "accent": "#ec4899",
        "steps": [
            {
                "bubble_title": "🌸 محیط ثبت درصد ۶",
                "bubble_text": "صفحه اختصاصی مدیریت سود ششمین صندوق سرمایه‌گذاری.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "⬇️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✏️ فرم ورود درصد روزانه",
                "bubble_text": "ثبت درصد بازدهی روزانه با کیبورد فارسی یا انگلیسی.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "💵 سود تومانی خالص",
                "bubble_text": "محاسبه فوری میزان سود تومانی تولیدی.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🚀 شناساگر اوج سود",
                "bubble_text": "نمایش وضعیت عبور از نقطه اوج قبلی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🚀",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📂 خروجی و ورودی JSON",
                "bubble_text": "دانلود بکاپ و بازیابی اطلاعات صندوق.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "💾",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔗 یکپارچه در داشبورد",
                "bubble_text": "اتصال به محاسبات کل در داشبورد عمارت.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🔗",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "gold7",
        "title": "صندوق ثبت درصد ۷ (آهنگ سهام کیان)",
        "url_path": "gold7/index.html",
        "accent": "#f43f5e",
        "steps": [
            {
                "bubble_title": "🌈 صندوق آهنگ سهام کیان",
                "bubble_text": "هفتمین صندوق با تم جذاب رنگین‌کمانی جهت مدیریت سود سهام کیان.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🌈",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✏️ فرم اختصاصی قیمت ابطال",
                "bubble_text": "ورود قیمت جدید ابطال واحدها بر اساس اعلام رسمی صندوق.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "💰 سود تومانی و درصد دقیق",
                "bubble_text": "محاسبه خودکار درصد و سود تومانی صاف در حافظه ahang_kian_percents.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📅 تقویم و روزشمار شمسی",
                "bubble_text": "ثبت متوالی روزهای شمسی بر اساس طول ماه‌های خورشیدی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "📅",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📊 اتصال به محاسبه‌گر سود",
                "bubble_text": "اتصال مستقیم آمار این صندوق به calc2 در محاسبه‌گر سود.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📊",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🏆 پایش اوج در دیدبان",
                "bubble_text": "نمایش زنده در دیدبان درصدها به عنوان پیشتاز ماه.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🏆",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "monitor",
        "title": "دیدبان درصدها",
        "url_path": "monitor/index.html",
        "accent": "#60a5fa",
        "steps": [
            {
                "bubble_title": "📊 مرکز کنترل و دیدبان زنده",
                "bubble_text": "دیدبان درصدها وضعیت بازدهی تمام ۷ صندوق مالی شما را به صورت یکپارچه و زنده در کارت‌های هوشمند نمایش می‌دهد.",
                "arrow_top": 100,
                "arrow_left": 500,
                "arrow_icon": "⬇️",
                "bubble_top": 200,
                "bubble_right": 80
            },
            {
                "bubble_title": "💳 کارت‌های زنده ۷ صندوق",
                "bubble_text": "مشاهده درصد سود روزانه، مجموع سود تومانی و روزشمار واریز ماهانه روی کارت‌ها.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📈 نمودارهای رشد طلایی",
                "bubble_text": "رسم نمودار رشد انباشته، سودهای مثبت و روند صوتی بازدهی دارایی‌ها.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "📈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🧾 صورت مالی ماهانه با مهر رسمی",
                "bubble_text": "در تب صورت مالی می‌توانید خروجی ماهانه حسابداری صندوق‌ها را با جدول تفکیکی، سود روزانه و مهر رسمی چاپ کنید!",
                "arrow_top": 750,
                "arrow_left": 400,
                "arrow_icon": "🎯",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📌 یادداشت‌های مهم و جستجو",
                "bubble_text": "امکان ثبت یادداشت‌های مهم با تاریخ شمسی و جستجوی پیشرفته در منو.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📌",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "💾 بکاپ کامل JSON سیستم",
                "bubble_text": "دانلود خروجی کامل تمام استوریج‌های ۷ صندوق با ۱ کلیک.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "💾",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "profit",
        "title": "محاسبه‌گر سود",
        "url_path": "profit-calculator/index.html",
        "accent": "#2dd4bf",
        "steps": [
            {
                "bubble_title": "💵 محیط محاسبه‌گر سود",
                "bubble_text": "برنامه‌ای دارای ۳ بخش پیشرفته شامل سود مرکب، سود روزانه و دخل و خرج.",
                "arrow_top": 100,
                "arrow_left": 500,
                "arrow_icon": "⬇️",
                "bubble_top": 200,
                "bubble_right": 80
            },
            {
                "bubble_title": "📈 تب ۱: محاسبه سود مرکب",
                "bubble_text": "پیش‌بینی رشد سرمایه بر اساس نرخ سود ماهانه و مدت زمان.",
                "arrow_top": 320,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 420,
                "bubble_right": 80
            },
            {
                "bubble_title": "📊 تب ۲: میانگین سود روزانه",
                "bubble_text": "محاسبه میانگین سود روزانه صندوق‌ها و قفل کردن نرخ‌های دستی.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "💳 تب ۳: دخل و مصارف",
                "bubble_text": "مدیریت کامل درآمدهای ماهانه، هزینه‌ها و محاسبه باقی‌مانده صاف.",
                "arrow_top": 750,
                "arrow_left": 400,
                "arrow_icon": "💰",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🌙 تم تاریک و فونت پررنگ",
                "bubble_text": "امکان فعال‌سازی تم تاریک شیک به همراه فونت‌های بسیار خوانا.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🌙",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "💾 ذخیره‌سازی خودکار",
                "bubble_text": "حفظ تمامی ورودی‌ها در حافظه مرورگر بدون پریدن داده‌ها.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "💾",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "restricted",
        "title": "سپر دانلود",
        "url_path": "restricted/index.html",
        "accent": "#c084fc",
        "steps": [
            {
                "bubble_title": "🛡️ محیط زنده سپر دانلود",
                "bubble_text": "کافیست لینک ویدیو از اینستاگرام یا یوتیوب را اینجا بچسبانید تا موتورهای چندلایه yt-dlp و Gemini AI فیلم را استخراج کنند.",
                "arrow_top": 150,
                "arrow_left": 500,
                "arrow_icon": "⬇️",
                "bubble_top": 250,
                "bubble_right": 80
            },
            {
                "bubble_title": "📋 چسباندن و دانلود سریع",
                "bubble_text": "امکان ورود لینک‌های چندخطی و استخراج خودکار تمام لینک‌ها.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📜 تاریخچه زنده دانلودها",
                "bubble_text": "رصد وضعیت اجرای دانلود (در حال پردازش / موفق / خطا) در کارت زنده.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🔔 نوتیفیکیشن‌های پایدار",
                "bubble_text": "امکان دانلود مستقیم از نوار اعلان‌های اندروید با ۱ کلیک.",
                "arrow_top": 750,
                "arrow_left": 400,
                "arrow_icon": "🔔",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🚀 تحویل مستقیم در تلگرام",
                "bubble_text": "ارسال خودکار فایل ویدیویی به کانال و ربات تلگرام.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🚀",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🐞 گزارش خطای هوشمند",
                "bubble_text": "امکان کپی سورس DOM و گزارش خطا جهت بررسی AI.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🐞",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "ai-chat",
        "title": "چت هوشمند",
        "url_path": "ai-chat/index.html",
        "accent": "#38bdf8",
        "steps": [
            {
                "bubble_title": "🤖 محیط گفتگوگر Gemini",
                "bubble_text": "دستیار هوشمند قدرتمند برای پاسخ به سوالات، تحلیل کد و تولید محتوا.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "⬇️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "💬 کادر ورودی پیام",
                "bubble_text": "سوال یا درخواست خود را به هر زبانی تایپ کنید.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "⚡ پاسخ‌دهی سریع با پروکسی",
                "bubble_text": "پاسخ‌دهی زیر ۳ ثانیه با زیرساخت اختصاصی Cloudflare.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📝 کپی و رندر کدها",
                "bubble_text": "نمایش کدهای برنامه‌نویسی با فرمت شیک و دکمه کپی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "💻",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🧠 حفظ حافظه گفتگو",
                "bubble_text": "حفظ تاریخچه گفتگوها برای پیگیری مباحث قبلی.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🧠",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 کارکرد PWA آفلاین",
                "bubble_text": "قابل نصب و اجرا روی تمامی گوشی‌ها و دسکتاپ.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "simple-chat",
        "title": "چت فرمان‌بردار",
        "url_path": "simple-chat/index.html",
        "accent": "#a1a1aa",
        "steps": [
            {
                "bubble_title": "🙇‍♂️ هوش مصنوعی مطیع عمارت",
                "bubble_text": "دستیاری باادب که با لحن اختصاصی «اطاعت» تمام دستورات را اجرا می‌کند.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🙇‍♂️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✨ تم گلاسمورفیک خلوت",
                "bubble_text": "طراحی خلوت و ۱۰۰٪ شفاف جهت بیشترین تمرکز روی متن.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "💬 ورود دستورات اجرایی",
                "bubble_text": "ورود سریع دستور خلاصه‌سازی، اصلاح یا تولید متن.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "👈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "👑 احترام کلامی کامل",
                "bubble_text": "شروع پاسخ با عبارت «اطاعت» و بدون هرگونه مخالفتی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "👑",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "⚡ سرعت لود فوق‌العاده",
                "bubble_text": "سبک‌ترین و سریع‌ترین برنامه گفتگوی متنی.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "⚡",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 بدون حاشیه و تبلیغ",
                "bubble_text": "تمرکز ۱۰۰٪ روی انجام دقیق دستورات کاربر.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "clipboard",
        "title": "کلیپ بورد هوشمند",
        "url_path": "clipboard/index.html",
        "accent": "#fb923c",
        "steps": [
            {
                "bubble_title": "📋 مدیریت پیشرفته متون",
                "bubble_text": "ذخیره، پین، دسته‌بندی و خواندن خودکار کلیپ‌بورد سیستم.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "📋",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "📋 کارت Auto-Paste",
                "bubble_text": "شناسایی هوشمند متون کپی‌شده در حافظه گوشی.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📌 پین‌کردن یادداشت‌های مهم",
                "bubble_text": "سنجاق کردن متون پرکاربرد در بالای لیست.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "📌",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📁 فولدرهای سفارشی",
                "bubble_text": "ساخت پوشه‌های رنگی با آیکون دلخواه.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "📁",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 اشتراک‌گذاری سریع",
                "bubble_text": "دکمه‌های کپی کوچک و ارسال با Web Share API.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📱",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "💾 بکاپگیری کامل JSON",
                "bubble_text": "ذخیره خروجی پشتیبان با تاریخ دقیق شمسی.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "💾",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "html-viewer",
        "title": "نمایشگر کد HTML",
        "url_path": "html-viewer/index.html",
        "accent": "#38bdf8",
        "steps": [
            {
                "bubble_title": "💻 اجرای زنده وب و ابزار متن",
                "bubble_text": "پیش‌نمایش وب HTML/JS به همراه ابزار متن ساده.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "💻",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "🖥️ تب ۱: پیش‌نمایش HTML",
                "bubble_text": "رندر کامل کدهای وب با قابلیت Canvas و WebGL.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📄 تب ۲: ابزار متن ساده",
                "bubble_text": "ویرایش، پاکسازی و دانلود متون ساده.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "📄",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🤖 عنوان‌نویسی هوشمند AI",
                "bubble_text": "تولید عنوان فایل توسط Gemini به همراه تاریخ شمسی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🤖",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🐞 کنسول گزارش دیباگ",
                "bubble_text": "بررسی و کپی لاگ‌های عیب‌یابی برنامه.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🐞",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔢 سیستم عدم شمارش تکراری",
                "bubble_text": "محاسبه هش محتوا جهت جلوگیری از شمارش دانلودهای تکراری.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🔢",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "skincare",
        "title": "مراقبت پوستی",
        "url_path": "skincare/index.html",
        "accent": "#a3e635",
        "steps": [
            {
                "bubble_title": "🌿 برنامه‌ریزی روتین پوستی",
                "bubble_text": "ثبت منظم محصولات و روتین‌های روزانه مراقبت پوستی.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🌿",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✨ علامت‌زدن محصولات مصرفی",
                "bubble_text": "انتخاب شستشو، آبرسان و ضدآفتاب مصرفی امروز.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔒 تایمر قفل ۷۲ ساعته استراحت",
                "bubble_text": "تایمر استراحت هوشمند از بامداد روز بعد شروع به کار می‌کند.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "🔒",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "⏳ نمایش معکوس زمان",
                "bubble_text": "نمایش دقیق ساعت و ثانیه باقی‌مانده تا روتین بعدی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "⏳",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📜 ثبت سوابق پوستی",
                "bubble_text": "ذخیره منظم روتین‌های انجام شده در استوریج.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📜",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 برنامه PWA آفلاین",
                "bubble_text": "بدون نیاز به اینترنت و همیشه آماده استفاده.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "vault",
        "title": "رمز راز",
        "url_path": "vault/index.html",
        "accent": "#f87171",
        "steps": [
            {
                "bubble_title": "🔐 گاوصندوق امنیتی محرمانه",
                "bubble_text": "نگهداری رمزنگاری‌شده کلمات عبور و یادداشت‌های خصوصی.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🔐",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔑 ثبت اکانت جدید",
                "bubble_text": "ورود عنوان، نام کاربر و کلمه عبور با امنیت بالا.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "🛡️ رمزنگاری محلی داده‌ها",
                "bubble_text": "ذخیره داده‌ها فقط و فقط در مرورگر دستگاه شما.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "🛡️",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📋 کپی سریع رمزها",
                "bubble_text": "کپی آسان کلمه عبور بدون نمایش متنی به دیگران.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "📋",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔍 جستجوی اکانت‌ها",
                "bubble_text": "یافتن فوری رمز کارت‌ها و اکانت‌ها در گاوصندوق.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🔍",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔒 قفل محرمانه ۱۰۰٪",
                "bubble_text": "عدم خروج کوچک‌ترین اطلاعات به سرورهای خارجی.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🔒",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "funds",
        "title": "WWW.com (وب‌سایت صندوق‌ها)",
        "url_path": "funds/index.html",
        "accent": "#60a5fa",
        "steps": [
            {
                "bubble_title": "🌐 سامانه وب‌ویو صندوق‌ها",
                "bubble_text": "دسترسی مستقیم به سامانه‌های مالی و صرافی‌ها.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🌐",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "🏛️ تب ۱: صرافی فارابی",
                "bubble_text": "ورود مستقیم به سامانه energy.irfarabi.ir.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📈 تب ۲: صندوق بازنشستگی",
                "bubble_text": "ورود مستقیم به سامانه kianfunds4.ir.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "📈",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "📊 تب ۳: روند NAV کیان",
                "bubble_text": "نمایش زنده نمودار روند قیمت ابطال واحدها.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "📊",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🚀 بازکردن مستقیم پنجره",
                "bubble_text": "دکمه‌های بازکردن مستقیم جهت دور زدن محدودیت فریم.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🚀",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 آیکون‌های برجسته ۳D",
                "bubble_text": "طراحی آیکون‌های برجسته سه بعدی بر روی تم نیلی.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "yandex",
        "title": "جستجوگر عکس",
        "url_path": "yandex/index.html",
        "accent": "#fca5a5",
        "steps": [
            {
                "bubble_title": "🖼️ موتور جستجوی بصری",
                "bubble_text": "یافتن تصاویر باکیفیت و عکس‌های مشابه.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🖼️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "📤 آپلود فایل یا لینک",
                "bubble_text": "آپلود عکس یا ورود لینک مستقیم جهت آنالیز.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔍 پردازش با Yandex Vision",
                "bubble_text": "جستجوی هوشمند در بزرگترین دیتابیس تصاویر.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "🔍",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "✨ نتایج ۴K Ultra HD",
                "bubble_text": "یافتن نسخه‌های شفاف‌تر و بالاترین کیفیت عکس.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "✨",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📥 دانلود مستقیم",
                "bubble_text": "ذخیره تصاویر یافت‌شده در گالری گوشی.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📥",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 سرعت و سهولت",
                "bubble_text": "رابط کاربری ساده و سریع برای تمام کاربران.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "tabdeal",
        "title": "کیف پول تبدیل",
        "url_path": "tabdeal/index.html",
        "accent": "#4ade80",
        "steps": [
            {
                "bubble_title": "🪙 مدیریت کریپتو و دارایی",
                "bubble_text": "رصد موجودی کیف پول صرافی تبدیل.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🪙",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "💵 محاسبه قیمت‌ها به تومان",
                "bubble_text": "نمایش ارزش کل دارایی‌ها به تومان و تتر.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "📊 تغییرات ۲۴ ساعت اخیر",
                "bubble_text": "نمایش سود یا زیان روزانه ارزهای دیجیتال.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "📊",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🟢 تفکیک ارزهای برتر",
                "bubble_text": "پایش بیت‌کوین، اتریوم و تتر موجود.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🟢",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔒 امنیت اتصال",
                "bubble_text": "اتصال مستقیم و امن بدون واسطه.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🔒",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 PWA مالی عمارت",
                "bubble_text": "دسترسی همیشگی از داشبورد اصلی.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "detective",
        "title": "کارآگاه داده‌ها",
        "url_path": "detective/index.html",
        "accent": "#818cf8",
        "steps": [
            {
                "bubble_title": "🔍 آنالیز و ردیابی آماری",
                "bubble_text": "تحلیل رفتار داده‌ها و کشف تغییرات آماری.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🔍",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "📥 ورودی داده‌های خام",
                "bubble_text": "ورود اطلاعات متنی یا اعداد برای تحلیل.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "⚡ پردازش الگوی داده",
                "bubble_text": "شناسایی همبستگی و نوسانات الگوها.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "⚡",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🎯 پیش‌بینی نتایج",
                "bubble_text": "ارائه گزارش دقیق با درصد اطمینان بالا.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🎯",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📜 خروجی نموداری",
                "bubble_text": "رسم نمودارهای بصری جهت تحلیل سریع‌تر.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📜",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 ابزار آنالیز عمارت",
                "bubble_text": "یکپارچه در مجموعه ابزارهای هوشمند.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "family",
        "title": "شجره‌نامه",
        "url_path": "family/index.html",
        "accent": "#34d399",
        "steps": [
            {
                "bubble_title": "🌳 درخت خانوادگی و شجره‌نامه",
                "bubble_text": "ثبت اعضا، ارتباطات فامیلی و رویدادها.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🌳",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "👤 افزودن عضو جدید",
                "bubble_text": "ورود مشخصات، نسبت فامیلی و عکس.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔗 رسم ارتباطات نسلی",
                "bubble_text": "رسم خودکار شاخه‌های درخت خانوادگی.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "🔗",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🎉 یادآوری سالگردها",
                "bubble_text": "ثبت تاریخ تولد و رویدادهای مهم فامیلی.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🎉",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "📸 تصویر گرافیکی کامل",
                "bubble_text": "خروجی تصویر از شجره‌نامه کامل.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "📸",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔒 حفظ خاطرات فامیلی",
                "bubble_text": "ذخیره امن داده‌ها در دستگاه.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "🔒",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "monthly-deposit",
        "title": "واریز ماهیانه",
        "url_path": "monthly-deposit/index.html",
        "accent": "#f0abfc",
        "steps": [
            {
                "bubble_title": "🗓️ مدیریت واریزی‌های ماهانه",
                "bubble_text": "ثبت موعد و مبلغ واریز صندوق‌ها.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🗓️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "💵 ثبت مبلغ واریزی",
                "bubble_text": "ورود مبلغ و انتخاب صندوق مقصد.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "⏱️ نشانگر روزشمار زنده",
                "bubble_text": "نمایش زمان گذشته از آخر واریزی.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "⏱️",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🔴 نشانگر وضعیت قرمز/سبز",
                "bubble_text": "هشدار زنده در صورت عقب افتادن واریز.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🔴",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔄 همگام با دیدبان درصدها",
                "bubble_text": "نمایش مستقیم روی کارت‌های دیدبان.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🔄",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 نظم مالی ماهانه",
                "bubble_text": "بهترین روش برای انضباط سرمایه‌گذاری.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    },
    {
        "id": "peace",
        "title": "ثبت آرامش",
        "url_path": "peace/index.html",
        "accent": "#5eead4",
        "steps": [
            {
                "bubble_title": "🕊️ دفترچه ثبت حس خوب",
                "bubble_text": "ذخیره لحظات آرامش‌بخش و شکرگزاری.",
                "arrow_top": 120,
                "arrow_left": 480,
                "arrow_icon": "🕊️",
                "bubble_top": 220,
                "bubble_right": 80
            },
            {
                "bubble_title": "✏️ ثبت یادداشت مثبت",
                "bubble_text": "تایپ تجربیات آرامش‌بخش روزانه.",
                "arrow_top": 350,
                "arrow_left": 400,
                "arrow_icon": "⬇️",
                "bubble_top": 450,
                "bubble_right": 80
            },
            {
                "bubble_title": "✨ ثبت تاریخ و زمان شمسی",
                "bubble_text": "ثبت دقیق زمان ایجاد حس خوب.",
                "arrow_top": 550,
                "arrow_left": 350,
                "arrow_icon": "✨",
                "bubble_top": 480,
                "bubble_right": 100
            },
            {
                "bubble_title": "🌿 مرور یادداشت‌های گذشته",
                "bubble_text": "ایجاد انگیزه و ارتقای روحیه با مرور خاطرات.",
                "arrow_top": 750,
                "arrow_left": 450,
                "arrow_icon": "🌿",
                "bubble_top": 650,
                "bubble_right": 80
            },
            {
                "bubble_title": "🔒 حریم خصوصی ۱۰۰٪",
                "bubble_text": "ذخیره محرمانه فقط روی دستگاه.",
                "arrow_top": 950,
                "arrow_left": 500,
                "arrow_icon": "🔒",
                "bubble_top": 850,
                "bubble_right": 80
            },
            {
                "bubble_title": "📱 حال خوب با عمارت",
                "bubble_text": "همراه همیشگی لحظات مثبت شما.",
                "arrow_top": 1150,
                "arrow_left": 480,
                "arrow_icon": "📱",
                "bubble_top": 1020,
                "bubble_right": 80
            }
        ]
    }
]

def inject_overlay_script(step_data, accent_color):
    b_title = step_data['bubble_title']
    b_text = step_data['bubble_text']
    b_top = step_data['bubble_top']
    b_right = step_data['bubble_right']
    a_top = step_data['arrow_top']
    a_left = step_data['arrow_left']
    a_icon = step_data['arrow_icon']

    js_code = f"""
    (function() {{
        const existing = document.getElementById('tutorial-overlay-container');
        if (existing) existing.remove();

        const container = document.createElement('div');
        container.id = 'tutorial-overlay-container';
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100vw';
        container.style.height = '100vh';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '999999';
        container.style.fontFamily = 'Vazirmatn, Tahoma, sans-serif';

        container.innerHTML = `
            <!-- Thought / Speech Bubble -->
            <div style="position: absolute; top: {b_top}px; right: {b_right}px; background: rgba(15, 23, 42, 0.94); color: #ffffff; padding: 28px 36px; border-radius: 32px; border: 3px solid {accent_color}; box-shadow: 0 25px 60px rgba(0,0,0,0.7); max-width: 650px; text-align: right; direction: rtl; backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);">
                <div style="font-size: 32px; font-weight: 800; color: {accent_color}; margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                    {b_title}
                </div>
                <div style="font-size: 26px; font-weight: 500; color: #e2e8f0; line-height: 1.7;">
                    {b_text}
                </div>
                <div style="position: absolute; bottom: -20px; right: 80px; width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 20px solid {accent_color};"></div>
            </div>

            <!-- Pointing Arrow Indicator -->
            <div style="position: absolute; top: {a_top}px; left: {a_left}px; font-size: 90px; line-height: 1; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.8)); text-align: center;">
                {a_icon}
            </div>
        `;

        document.body.appendChild(container);
    }})();
    """
    return js_code

async def capture_real_ui_tutorial_video(app_info, root_dir):
    from playwright.async_api import async_playwright

    app_id = app_info['id']
    print(f"\n=======================================================")
    print(f"🎬 Rendering REAL UI Tutorial for: {app_info['title']}")

    output_dir = os.path.join(root_dir, f"real_ui_frames_{app_id}")
    os.makedirs(output_dir, exist_ok=True)

    abs_html_path = os.path.abspath(os.path.join(root_dir, app_info['url_path']))
    file_url = f"file://{abs_html_path}"

    slide_images = []
    # 6 steps * 15 seconds per step = 90 seconds (1.5 minutes minimum duration constraint)
    slide_duration = 15.0

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1920})

        if os.path.exists(abs_html_path):
            await page.goto(file_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(0.5)

        for idx, step in enumerate(app_info['steps']):
            overlay_js = inject_overlay_script(step, app_info['accent'])
            await page.evaluate(overlay_js)
            await asyncio.sleep(0.4)

            img_path = os.path.join(output_dir, f"step_{idx:02d}.png")
            await page.screenshot(path=img_path, full_page=False)
            slide_images.append(img_path)
            print(f"  [+] Captured Real UI Step {idx+1}/{len(app_info['steps'])}: {step['bubble_title']}")

        await browser.close()

    # Generate MP4 via FFmpeg
    concat_txt = os.path.join(output_dir, "concat.txt")
    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in slide_images:
            f.write(f"file '{os.path.basename(s)}'\n")
            f.write(f"duration {slide_duration}\n")
        if slide_images:
            f.write(f"file '{os.path.basename(slide_images[-1])}'\n")

    output_mp4 = os.path.abspath(f"real_ui_tutorial_{app_id}.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-vf", "scale=1080:1920,fps=30,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        output_mp4
    ]

    subprocess.run(cmd, check=True, cwd=output_dir)
    print(f"✅ Real UI Video Generated: {output_mp4} (Duration: 90s / 1.5min)")
    return output_mp4, output_dir

def send_video_to_telegram(video_path, caption, bot_token, chat_id):
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

    print(f'Sending Real UI video {os.path.basename(video_path)} to Telegram...')
    with urllib.request.urlopen(req, timeout=180) as response:
        res_body = response.read().decode('utf-8')
        res_json = json.loads(res_body)
        if res_json.get('ok'):
            print('✅ SUCCESSFULLY SENT REAL UI VIDEO TO TELEGRAM CHANNEL!')
            return res_json
        else:
            print('❌ TELEGRAM RETURNED ERROR:', res_json)
            raise RuntimeError(f'Telegram upload failed: {res_json}')

async def main():
    root_dir = os.getcwd()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    print(f"Total Real UI tutorial configurations defined: {len(REAL_UI_TUTORIALS)}")

    for app in REAL_UI_TUTORIALS:
        output_mp4, output_dir = await capture_real_ui_tutorial_video(app, root_dir)

        caption = f'''💬 **آموزش زنده روی رابط کاربری واقعی: {app['title']}**

⏱️ **مدت زمان:** ۱.۵ دقیقه (۹۰ ثانیه) آموزش زنده UI

ویدئوی آموزشی با رندر زنده محیط واقعی برنامه، حباب فکری راهنما و فلش‌های نشانه:
▫️ معرفی دکمه‌ها و المان‌های واقعی UI
▫️ راهنمای ورود داده‌ها با حباب‌های فکری راهنما
▫️ نشانگرهای هوشمند روی بخش‌های مختلف برنامه

✨ *ارائه شده در سامانه جامع «عمارت دیجیتال» | کانال دنیا های قشنگ* ❤️'''

        if bot_token and chat_id:
            send_video_to_telegram(output_mp4, caption, bot_token, chat_id)

        # Cleanup generated video and frames to prevent git repository bloat
        if os.path.exists(output_mp4):
            os.remove(output_mp4)
        if os.path.exists(output_dir):
            for f in glob.glob(os.path.join(output_dir, "*")):
                os.remove(f)
            os.rmdir(output_dir)

if __name__ == "__main__":
    asyncio.run(main())
