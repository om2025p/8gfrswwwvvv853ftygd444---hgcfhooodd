# Project: 8gfrswwwvvv853ftygd444---hgcfhooodd

- This project is a personal activity tracker.
- Deployment is targeted at Netlify (https://netlify.app).
- All UI text must avoid sensitive keywords like "gym" or "varzesh" (ورزش) in titles or metadata.
- Repository is Public to allow Netlify builds.

---

## 📜 قانون اساسی افزودن ابزار جدید و سیستم پشتیبان‌گیری (The PWA Development Constitution)

هر زمان که ابزار جدیدی به پروژه اضافه می‌شود یا ابزارهای موجود ارتقا می‌یابند، رعایت قوانین زیر الزامی است:

### ۱. سیستم پشتیبان‌گیری دوگانه (Dual-Backup System)
هر اپلیکیشن که دارای بخش دانلود بکاپ یا خروجی داده (JSON/Export) و بازیابی (Import/Restore) است، باید مجهز به پشتیبان‌گیری دوگانه باشد:
- **پشتیبان محلی (آفلاین/همیشگی):** دانلود فایل JSON روی حافظه دستگاه کاربر.
- **پشتیبان ابری گیت‌هاب (هیبریدی/در صورت آنلاین بودن):** آپلود مستقیم فایل به مخزن گیت‌هاب شخصی کاربر از طریق API گیت‌هاب.

### ۲. امنیت اطلاعات گیت‌هاب (Security First)
به هیچ وجه نباید توکن یا مشخصات گیت‌هاب کاربر درون کدهای پروژه نوشته (Hardcode) شود.
- اطلاعات ورود گیت‌هاب باید از طریق یک پنجره تنظیمات (Settings Modal) شیک با زدن دکمه چرخ‌دنده ⚙️ از کاربر دریافت شده و **فقط و فقط** در `localStorage` شخصی مرورگر خود کاربر با کلیدهای زیر ذخیره شود:
  - `github_backup_token`
  - `github_backup_repo`
  - `github_backup_branch`
  - `github_backup_filepath`

### ۳. الگوی کد جاوااسکریپت برای آپلود در گیت‌هاب
تمام اپلیکیشن‌ها باید از تابع استاندارد زیر برای آپلود استفاده کنند تا هماهنگی کامل حفظ شود:

```javascript
async function uploadToGitHub(contentString, fileName) {
    const token = localStorage.getItem("github_backup_token");
    const repo = localStorage.getItem("github_backup_repo");
    const branch = localStorage.getItem("github_backup_branch") || "main";
    let filePath = localStorage.getItem("github_backup_filepath");

    if (!token || !repo) return { success: false, message: "تنظیمات گیت‌هاب کامل نیست." };

    if (!filePath) {
        filePath = `backups/${fileName}`;
    } else if (filePath.endsWith("/")) {
        filePath += fileName;
    }

    const url = `https://api.github.com/repos/${repo}/contents/${filePath}`;
    const headers = {
        "Authorization": `token ${token}`,
        "Accept": "application/vnd.github.v3+json"
    };

    try {
        let sha = null;
        try {
            const checkRes = await fetch(`${url}?ref=${branch}`, { headers });
            if (checkRes.status === 200) {
                const fileData = await checkRes.json();
                sha = fileData.sha;
            }
        } catch (e) {}

        const base64Content = btoa(unescape(encodeURIComponent(contentString)));
        const body = {
            message: `بکاپ خودکار برنامه - ${new Date().toLocaleString('fa-IR')}`,
            content: base64Content,
            branch: branch
        };
        if (sha) body.sha = sha;

        const putRes = await fetch(url, {
            method: "PUT",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        return putRes.ok ? { success: true } : { success: false, message: "خطا در آپلود" };
    } catch (err) {
        return { success: false, message: err.message };
    }
}
```

### ۴. قوانین بعد از بازیابی اطلاعات
- بلافاصله پس از پارس موفقیت‌آمیز داده‌های دریافتی، حتماً متد `saveData()` صدا زده شود تا داده‌ها فوراً در `localStorage` ثبت و دائم شوند.
- مقدار فایل اینپوت (`event.target.value = '';`) ریست شود تا امکان آپلود مجدد همان فایل بدون تداخل فراهم باشد.
- در صورت وجود سیستم `cloud-sync.js` در برنامه، متد `window.EmaratCloudSync.push()` صدا زده شود تا آخرین داده‌ی بازیابی شده روی ابر هم همگام‌سازی شود.
