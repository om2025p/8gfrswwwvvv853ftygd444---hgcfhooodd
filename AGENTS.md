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

---

## 🦾 قانون اساسی طراحی و توسعه اتوماسیون‌های آینده (The Automation Constitution)

وقتی قرار است یک اتوماسیون خودکارساز جدید برای سایر برنامه‌ها (مانند صندوق‌های ثبت درصد ۱ تا ۶ در کارگزاری مفید یا سایر کارگزاری‌ها نظیر آگاه، فارابی و...) پیاده‌سازی شود، برای پیشگیری کامل از خطاهای پلتفرمی گیت‌هاب و گرفتن بهترین نتیجه، رعایت قوانین طلایی زیر الزامی است:

### ۱. عبور ایمن از خطاهای کلاسیک و تجربیات گران‌بهای صندوق ۵:
- **تغییر از حالت Wait Networkidle به Load:** کارگزاری‌ها از سوکت‌های قیمت‌گذاری زنده (WebSocket) و ترکرهای تبلیغاتی مداوم استفاده می‌کنند که ترافیک شبکه را هرگز صفر نمی‌کنند. پس همواره برای دستور ناوبری <code>wait_until</code> به جای <code>networkidle</code> از مقدار <code>load</code> استفاده کنید تا سرور گیت‌هاب اکشنز معطل نمانده و تایم‌اوت ۴۵ ثانیه‌ای نخورد.
- **تغییر User Agent به مرورگر مدرن موبایل:** برای پیشگیری از باز شدن پاپ‌آپ‌ها و کادرهای اخطار مسدودکننده‌ای چون «سیستم عامل شما قدیمی است و به Safari 15 نیاز دارد»، همواره User Agent کانتکست Playwright را بر روی گوگل کروم موبایل مدرن (مانند نسخه ۱۲۴ روی اندروید ۱۳) تنظیم کنید.
- **بافر زمانی بارگذاری (Hydration Buffer):** در فریم‌ورک‌های وب مدرن، تگ‌های صفحه ابتدا لود شده و چند ثانیه بعد اعداد واقعی از سرور خوانده شده و تزریق می‌شوند. همواره قبل از شروع به خواندن اعداد، یک تاخیر ۸ الی ۱۰ ثانیه‌ای (<code>time.sleep(8)</code>) اعمال کنید.
- **موتور استخراج داده دوگانه‌سوز (Dual-Strategy Extraction):** هرگز فقط به پیمایش لایه‌های ثابت درختی DOM تکیه نکنید، زیرا با تغییرات جزئی ظاهر سایت مفید خراب می‌شوند. همواره استراتژی اول خود را بر روی اسکن مستقیم رشته متنی نمایان صفحه (Viewport Text Stream Reader) بر اساس کلمه کلیدی نماد و نماد بعدی قرار دهید و استراتژی دوم را به عنوان پشتیبان لایه‌ای DOM بگذارید.
- **تیک زدن خودکار دکمه Trust Device:** همواره قبل از ارسال فرم حاوی کد تایید ورود (OTP)، چک‌باکس مربوط به «تایید دو مرحله برای این سیستم لازم نیست» را بیابید و تیک بزنید تا سشن ذخیره شده دائمی شود.

### ۲. سیستم ادغام دوطرفه امن (Resilient Two-Way Merge Engine):
در اتصال خودکار بکاپ گیت‌هاب به فرانت‌اند PWA، هرگز دیتابیس لوکال گوشی کاربر را به طور کامل جایگزین (اوروایت) نکنید، زیرا این کار باعث پاک شدن تاریخچه‌های ارزشمندی می‌شود که پیش‌تر کاربر دستی وارد کرده است. همواره فرآیند ادغام را به صورت دوطرفه بر اساس برچسب زمانی (Timestamp) دقیق ثانیه‌ای بنویسید تا فقط رکوردهای جدید ربات به رکوردهای قدیمی گوشی اضافه شوند و تکراری‌ها فیلتر شوند.

### ۳. مکانیزم OTP تعاملی تلگرام:
برای بخش‌هایی از اتوماسیون که ورود دو مرحله‌ای فعال است، یک سیستم شنود زنده ۳ دقیقه‌ای از طریق متد رسمی <code>getUpdates</code> تلگرام بنویسید تا کاربر بتواند در صدم ثانیه با ریپلای کد تایید، ربات را عبور دهد.

### ۴. ساختار گزارش‌دهی پیروزی و خطا:
همواره اسکرین‌شات‌ها را در فایل <code>.gitignore</code> فیلتر کنید تا حجم مخزن زیاد نشود. در تلگرام، گزارش‌ها را به صورت زیبا همراه با ایموجی‌های مناسب (📊، 💰، 🤖)، مقایسه درصدها و اعلام وضعیت همگام‌سازی ابری و محلی ارسال کنید.
