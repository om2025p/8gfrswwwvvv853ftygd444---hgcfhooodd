# 🚀 راهنمای میزبانی وب‌سایت عمارت روی کلودفلر (Cloudflare Pages)

این راهنما شامل آدرس‌های زنده دپلوی‌شده وب‌سایت **عمارت دیجیتال** روی پروژه **`emarat-percent-imana`** در کلودفلر و نحوه بازیابی بکاپ **دیدبان درصدها** می‌باشد.

---

## 🌐 آدرس‌های زنده وب‌سایت در کلودفلر:

* **آدرس اصلی و پرسرعت وب‌سایت:** [https://emarat-percent-imana.pages.dev](https://emarat-percent-imana.pages.dev)
* **آدرس اختصاصی شاخه ۱۵۶:** [https://156.emarat-percent-imana.pages.dev](https://156.emarat-percent-imana.pages.dev)
* **ورود مستقیم به دیدبان درصدها جهت بارگذاری بکاپ:** [https://emarat-percent-imana.pages.dev/monitor/index.html](https://emarat-percent-imana.pages.dev/monitor/index.html)

---

## ⚡ نحوه آپلود و به‌روزرسانی مستقیم دستی با Wrangler CLI

جهت انتشار جدیدترین کدها روی کلودفلر از ترمینال:

```bash
npx wrangler pages deploy . --project-name=emarat-percent-imana --branch=156
```

---

## 📂 نحوه بازیابی کامل اطلاعات و بکاپ «دیدبان درصدها» روی کلودفلر

1. وارد آدرس **[https://emarat-percent-imana.pages.dev/monitor/index.html](https://emarat-percent-imana.pages.dev/monitor/index.html)** شوید.
2. منوی همبرگری بالا را باز کنید.
3. روی گزینه **📂 بازیابی اطلاعات (بارگذاری بکاپ)** کلیک کرده و فایل JSON بکاپ قبلی خود (`emarat_full_backup_...json`) را بارگذاری بفرمایید.
4. یا روی دکمه **☁️ بازیابی از بکاپ ابری کلودفلر** کلیک کنید.

تمامی ۷ صندوق، تاریخچه‌ها و درصدها بلافاصله روی دامنه کلودفلر بازیابی و فعال می‌شوند! 🎉💎
