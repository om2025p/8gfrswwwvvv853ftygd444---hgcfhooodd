# Project: 8gfrswwwvvv853ftygd444---hgcfhooodd

> ## 🚨 اول این را بخوان — اگر سرور ریست شد
> **`PROJECT-STATE.md`** در ریشهٔ مخزن، وضعیت کامل کار جاری، تصمیم‌های گرفته‌شده،
> باگ‌های رفع‌شده و قدم بعدی را دارد. **قبل از هر کاری آن را بخوان.**
>
> خلاصهٔ ۳۰ ثانیه‌ای: کار جاری **بازطراحی رابط کاربری شجره‌نامه** است.
> `family-lab/index.html` (آزمایشگاه ۵ تب با ویرایش کامل) و
> `tree-samples/m1..m6.html` (۶ مدل رسم درختی) تحویل داده شده و
> **منتظر انتخاب کاربر** هستیم تا مدل برنده در `family/index.html` اصلی پیاده شود.

- This project is a personal activity tracker.
- Deployment is targeted at Netlify (https://netlify.app).
- All UI text must avoid sensitive keywords like "gym" or "varzesh" (ورزش) in titles or metadata.
- Repository is Public to allow Netlify builds.

> 🧭 **قوانین اساسی (به ترتیب اولویت):**
> ۱. [افزودن ابزار جدید و پشتیبان‌گیری دوگانه](#-قانون-اساسی-افزودن-ابزار-جدید-و-سیستم-پشتیبانگیری-the-pwa-development-constitution)
> ۲. [اتوماسیون‌های آینده](#-قانون-اساسی-طراحی-و-توسعه-اتوماسیونهای-آینده-the-automation-constitution)
> ۳. [کارکرد آفلاین واقعی](#-قانون-کارکرد-آفلاین-واقعی-true-offline--no-vpn-rule)
> ۴. [**دکمهٔ به‌روزرسانی — الزامی برای هر اپ جدید**](#-قانون-اساسی-دکمهٔ-بهروزرسانی-سراسری-the-refresh-button-constitution)
> ۵. [**کارایی اسکرول — ممنوعیت‌های انیمیشن و تایمر**](#-قانون-کارایی-اسکرول-scroll-performance-rule)

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

### ۵. همگام‌سازی خودکار و آنی فرانت‌اند با گیت‌هاب (Real-time Background GitHub Auto-Sync):
در تمامی برنامه‌های ثبت درصد و اتوماسیون‌ها، هر زمان کاربر اقدامی انجام داد که منجر به تغییر داده‌ها گردید (مانند افزودن درصد جدید، حذف، بازیابی، تغییر هدف یا یادداشت)، حتماً تابع ذخیره‌سازی (`saveData`) باید به یک مکانیزم ارسال هوشمند با تاخیر کنترل‌شده (Debounce) مجهز باشد تا آخرین داده‌های تجمیعی برنامه به صورت خودکار و بی‌سروصدا در پس‌زمینه به فایل بکاپ مربوطه در گیت‌هاب (مثلاً `gold5/gold5_backup.json`) آپلود شوند و نیازی به فشردن دستی دکمه ذخیره نباشد.

---

## 🌐 قانون کارکرد آفلاین واقعی (True Offline / No-VPN Rule)

**مشکل ریشه‌ای:** هر `<link rel="stylesheet">` یا `<script src>` که به یک دامنه‌ی خارجی مسدود در ایران اشاره کند (مثل `cdnjs.cloudflare.com`، `fonts.googleapis.com`، `fonts.gstatic.com`، `ajax.googleapis.com`، `unpkg.com`، `jsdelivr.net`)، یک منبع **Render-Blocking** است. بدون VPN، مرورگر تا ۳۰+ ثانیه روی اتصال Hang می‌کند و صفحه **سفید** می‌ماند. Service Worker هم نمی‌تواند نجات دهد چون فقط منابع هم‌دامنه (`same-origin`) را کش می‌کند.

**قانون طلایی:** هیچ صفحه‌ای نباید هیچ وابستگی خارجی برای رندر داشته باشد. همه‌ی کتابخانه‌ها باید در پوشه‌ی `vendor/` میزبانی شوند و مسیرها **نسبی** باشند.

**ساختار استاندارد vendor:**
```
vendor/fontawesome/css/all.min.css          # + webfonts/*.woff2 (فقط woff2، ارجاع ttf حذف شود)
vendor/jszip/jszip.min.js
vendor/inter/inter.css                       # + fonts/*.woff2 (فقط latin/latin-ext)
```
مسیر استفاده از هر زیرپوشه: `../vendor/...`

**چک‌لیست پس از هر تغییر:**
1. `grep -rnE '<(link|script)[^>]*(href|src)="https?://(cdnjs|fonts\.googleapis|fonts\.gstatic|unpkg|jsdelivr)' --include=*.html .` باید **صفر** نتیجه بدهد.
2. منابع جدید `vendor/` باید به آرایه‌ی `ASSETS` در `sw.js` اضافه شوند.
3. `CACHE_NAME` در `sw.js` باید bump شود (مثلاً `v56` → `v57`) تا کش قدیمی پاک شود.
4. `preconnect`/`dns-prefetch` بی‌خطرند (Render-Blocking نیستند) ولی برای پاکیزگی حذف شوند.
5. تست واقعی: سرور محلی را بالا بیاور، صفحه را باز کن، سرور را **خاموش** کن و رفرش کن — باید از کش بیاید.

**هشدار داده:** تغییر مسیر CSS/JS هیچ تأثیری روی `localStorage`/`IndexedDB`/`cloud-sync` ندارد و داده‌های کاربر دست‌نخورده می‌مانند.

### ⚠️ باگ خطرناک سرویس‌ورکر: ترتیب `install` و `activate`
در `sw.js` فعلی، `activate` **همه‌ی کش‌های قدیمی را حذف می‌کند** و `install` هم با `Promise.allSettled` خطای تک‌فایل را نادیده می‌گیرد. اگر شبکه نیمه‌کاره قطع شود، ممکن است کش جدید **ناقص** بماند و کش قدیمی هم پاک شده باشد → **صفحه سفید تا اتصال بعدی**.

**قانون:** تا وقتی شمارش موفق `cache.add` در `install` به حد آستانه نرسیده، کش قدیمی پاک نشود؛ یا حداقل `./index.html` و `./sw.js` تضمین شوند.

**نکته مهم:** هیچ‌کدام از اپ‌های زیرمجموعه (`gold/`، `gym/`، `profit-calculator/`) نباید `sw.js` مستقل داشته باشند؛ فقط سرویس‌ورکر ریشه (`/sw.js`) مجاز است. سرویس‌ورکر تکراری در زیرپوشه، دامنه‌ی کش را می‌شکند و آفلاین را غیرقابل‌پیش‌بینی می‌کند.

### 🖥️ میزبانی فعلی: GitHub Pages (علت نیاز به VPN)
- سایت روی `https://om2025p.github.io/8gfrswwwvvv853ftygd444---hgcfhooodd/` سرو می‌شود (تأییدشده با Pages API: `status=built`، `cname=None`).
- **دامنه `github.io` در ایران فیلتر است**؛ به همین دلیل بدون VPN حتی با کش سالم، **بار اول** صفحه بالا نمی‌آید.
- `AGENTS.md` می‌گوید هدف Netlify است، ولی هیچ `netlify.toml` یا ورک‌فلوی Netlify در مخزن نیست و سایت قدیمی `emarat-digital.netlify.app` هم `404` می‌دهد.
- **راه‌حل بدون VPN:** انتقال میزبانی به یک دامنه‌ی غیرفیلتر (Netlify/Cloudflare Pages). چون مسیرها نسبی‌اند، فقط کافی است مخزن به آن سرویس وصل شود؛ **داده‌های کاربر روی دامنه‌ی جدید از صفر شروع می‌شود** (چون `localStorage` به دامنه گره خورده) — پس باید از کاربر بکاپ JSON گرفته شود.

---

## 🔄 قانون اساسی دکمهٔ «به‌روزرسانی» سراسری (The Refresh-Button Constitution)

### قانون ۱ — هر اپ جدید باید این دکمه را داشته باشد
**هر صفحهٔ HTML جدید** که به این مخزن اضافه می‌شود (چه اپ کامل، چه صفحهٔ فرعی مثل `price.html` یا `total.html`) **باید** یک تگ زیر را داشته باشد، دقیقاً **یک بار** و بلافاصله قبل از `</body>`:

```html
<script src="../refresh-button.js"></script>
```

- برای صفحات **ریشه** (مثل `index.html` پورتال): `src="refresh-button.js"` **بدون** `../`
- برای صفحات داخل زیرپوشه: `src="../refresh-button.js"`
- **هرگز** دو بار تزریق نکن (`grep -c "refresh-button.js" <page>` باید دقیقاً **۱** باشد). تزریق با `rfind('</body>')` انجام می‌شود، نه `replace`.

### قانون ۲ — رفتار اجباری: «از زیر لبهٔ صفحه بیرون می‌آید»
دکمه **نباید** شناور و نیمه‌پیدا باشد. رفتار استاندارد و **غیرقابل‌تغییر** این است:

| ویژگی | مقدار الزامی |
|---|---|
| موقعیت | `position: fixed` — با اسکرول **جابه‌جا نمی‌شود** |
| حالت پیش‌فرض | **کاملاً پنهان** زیر لبه: `transform: translate3d(0,110%,0)` |
| شرط بیرون آمدن | فقط **اسکرول اضافه رو به پایین** وقتی کاربر در **کف صفحه** است |
| آستانه | **۲ برخورد متوالی** `wheel`/`touchmove` در کف (شمارنده `bottomHits`) |
| بازگشت خودکار | **۵ ثانیه** (`REVEAL_MS`) بعد از نمایش |
| انیمیشن | `transform .32s cubic-bezier(.22,.9,.3,1)` |
| `z-index` | `2147483000` |

**منطق تشخیص کف صفحه:**
- `wheel` با `deltaY > 0` → اگر `scrollTop + clientHeight >= scrollHeight - 3` بود، `bottomHits++`
- `touchmove` با `dy = touchY - clientY > 0` → همان منطق
- اسکرول **رو به بالا** شمارنده را صفر می‌کند و دکمه را باز **نمی‌کند**
- صفحه‌ای که **اصلاً اسکرول ندارد** (کوتاه‌تر از viewport): هر اسکرول رو به پایین دکمه را باز می‌کند

### قانون ۳ — پشتیبانی اجباری از iframeهای هم‌دامنه
**تلهٔ گران‌بها:** بعضی اپ‌ها (مثل `gold9/`) صفحهٔ بیرونی‌شان **اسکرول ندارد**؛ همهٔ اسکرول داخل `iframe` رخ می‌دهد و رویداد `wheel` به پنجرهٔ والد **نمی‌رسد**. بدون هوک، دکمه هرگز بیرون نمی‌آید.

**الزام:** `refresh-button.js` باید تابع `bindFrames()` داشته باشد که:
1. یک هوک کوچک داخل هر `iframe` **هم‌دامنه** تزریق می‌کند (`window.__emrRbHook` به‌عنوان نگهبان تک‌بار).
2. هوک همان منطق «۲ اسکرول اضافه در کف» را اجرا می‌کند.
3. با `parent.postMessage({__emrRb:1}, '*')` به والد خبر می‌دهد.
4. والد با `message` listener دکمه را باز می‌کند.
5. تزریق در سه زمان + یک `setInterval` هر ۴ ثانیه انجام می‌شود (چون تب‌ها با `display` عوض می‌شوند و iframe تازه لود می‌شود).
6. iframeهای **cross-origin** بی‌صدا رد می‌شوند (`try/catch`).

### قانون ۴ — غیرفعال داخل iframe
`refresh-button.js` در خط اول باید `if (window.top !== window.self) return;` داشته باشد تا داخل iframeهای دیگر اپ‌ها دکمهٔ **تکراری** ساخته نشود.

### قانون ۵ — جریان دو مرحله‌ای (ضد کلیک اتفاقی)
1. کلیک اول → `⚠️ مطمئنی؟ دوباره بزن` (۳٫۵ ثانیه مهلت، بعد خودکار لغو)
2. کلیک دوم → پاک‌سازی `caches` + `unregister` سرویس‌ورکر + `location.replace` با پارامتر `_r=<timestamp>`
3. اگر `navigator.onLine === false` → پیام `📡 اینترنت قطع است` و **هیچ کشی پاک نمی‌شود** (تا کاربر صفحه سفید نبیند)

### قانون ۶ — 🚨 داده‌ها هرگز دست نمی‌خورند
فقط `caches` و `ServiceWorkerRegistration` پاک می‌شوند. **`localStorage`، `IndexedDB`، کوکی و `cloud-sync` هیچ تغییری نمی‌کنند.**
این قانون **مطلق** است: هر تغییری که دادهٔ کاربر را تهدید کند، رد می‌شود.

### قانون ۷ — نمایش نسخهٔ کش
متن دکمه باید شمارهٔ نسخهٔ کش را نشان دهد: `🔄 به‌روزرسانی · v90`
نسخه از `CACHE_NAME` در `sw.js` خوانده می‌شود (`fetch(SW_URL, {cache:'no-store'})`). پس **هر بامپ `CACHE_NAME` خودکار در دکمه دیده می‌شود**.

### قانون ۸ — بازرس خودکار (اجرای قانون، نه فقط توصیه)
یک اسکریپت بازرس در `scripts/check-refresh-button.py` هست که **همهٔ** صفحات HTML را می‌گردد و اگر صفحه‌ای دکمه نداشته باشد یا دو بار داشته باشد، با کد خروجی **۱** شکست می‌خورد:

```bash
python3 scripts/check-refresh-button.py
# ✅ همهٔ صفحات دقیقاً یک دکمهٔ به‌روزرسانی دارند.
# یا
# ❌ بدون دکمه: __newapp/index.html
# 1 صفحه قانون اساسی را نقض می‌کند.   (exit=1)
```

**قانون:** هر اپ جدید **پیش از کامیت** باید این اسکریپت را پاس کند. پوشه‌های مستثنی (`vendor`, `node_modules`, `fund-automation-android`, `restricted`) در خود اسکریپت تعریف شده‌اند.

**بازرس دوم — رفتار واقعی در مرورگر** (`scripts/verify-refresh-behavior.js`):
```bash
node scripts/verify-refresh-behavior.js http://127.0.0.1:12099
# ✅ index.html  (top=710)
# ✅ monitor/index.html  (top=710)
# ✅ gold9/index.html  (top=710)
# ✅ رفتار دکمه در همهٔ صفحات مطابق قانون است.
```
این بازرس سه چیز را می‌سنجد: **پیش‌فرض پنهان بودن**، **باز شدن فقط با ۲ اسکرول اضافه در کف**، و **ثابت ماندن هنگام اسکرول**. اگر صفحه‌ای این‌ها را نقض کند، با کد خروجی **۱** شکست می‌خورد. `puppeteer-core` لازم دارد.

### قانون ۸.۱ — چک‌لیست دستی تکمیلی
```bash
# ۱) دقیقاً یک تگ در هر صفحه
grep -c "refresh-button.js" <page>        # باید 1 باشد

# ۲) هیچ وابستگی خارجی برای رندر نباشد
grep -rnE '<(link|script)[^>]*(href|src)="https?://(cdnjs|fonts\.googleapis|fonts\.gstatic|unpkg|jsdelivr)' --include=*.html .

# ۳) بامپ نسخهٔ کش
grep -n "CACHE_NAME" sw.js                # v90 → v91 → ...

# ۴) آینهٔ اندروید همگام شود
cp refresh-button.js fund-automation-android/app/src/main/assets/webapp/refresh-button.js
```

**تست Puppeteer الزامی:**
```js
// دکمه باید پیش‌فرض پنهان باشد
btn.getBoundingClientRect().top >= window.innerHeight   // true
// بعد از ۲ اسکرول اضافه در کف باید باز شود
root.classList.contains('open')                          // true
// با اسکرول به بالا نباید جابه‌جا شود
beforeTop === afterTop                                   // true
```

### قانون ۹ — دام `sw.js`
هر بار `refresh-button.js` تغییر کرد، `CACHE_NAME` در `sw.js` **باید** بامپ شود. وگرنه کاربر نسخهٔ کهنهٔ دکمه را از کش می‌گیرد و فکر می‌کند تغییرات اعمال نشده.

---

---

## ⚡ قانون کارایی اسکرول (Scroll Performance Rule)

### علائم
«گیر ریز» هنگام اسکرول که بعد از چند ثانیه خودش رفع می‌شود (۲ تا ۱۷ ثانیه).

### چهار مقصر واقعی که در دیدبان و ردپای من پیدا و رفع شدند

| # | مقصر | چرا کند است | درمان |
|---|---|---|---|
| ۱ | **`setInterval(renderMonitor, 30000)`** | `renderMonitor()` کل `innerHTML` را پاک و بازسازی می‌کند: **۲۲۲ms روی CPU ۶ برابر کندتر**. اگر وسط اسکرول بیفتد، گیر محسوس می‌دهد | فقط وقتی `visibilityState === 'visible'` و فقط اگر **امضای داده** عوض شده باشد |
| ۲ | **انیمیشن بی‌نهایت روی `box-shadow`** (`pulseGlowGold`) | `box-shadow` در هر فریم paint می‌شود؛ همراه با `backdrop-filter` فاجعه است. **۵۸۳ms → ۹۲ms** | `box-shadow` را روی شبه‌عنصر `::after` ببر و فقط `opacity` را انیمیت کن (فقط کامپوزیتور) |
| ۳ | **`backdrop-filter` روی پس‌زمینهٔ کدر** | کارت `#000` کدر بود، پس بلور هیچ چیزی بلور نمی‌کرد؛ فقط هزینهٔ ترکیب‌بندی داشت | حذف `backdrop-filter` از کارت‌هایی که پس‌زمینهٔ کدر دارند |
| ۴ | **`animation` روی ظرف بسیار بلند** (`fadeIn` با `transform` روی المان ۲۳۰۰px) | `transform` کل ظرف را به یک لایهٔ ترکیب‌بندی دائمی تبدیل می‌کند | فقط `opacity` را انیمیت کن، `transform` را حذف کن |

### ⚠️ `background-attachment: fixed` ممنوع
در `usage/index.html` وجود داشت و هر فریم کل ویوپورت را دوباره رنگ می‌زد.
**درمان:** گرادیان پایه روی `body` و هاله‌های رنگی روی `body::before` با `position: fixed`.

### 🧪 روش تشخیص (ترتیب کار)
1. **اول اندازه بگیر، حدس نزن.** با Puppeteer + `Performance.getMetrics()` مقدار `TaskDuration` را قبل/بعد از یک اسکرول کامل بگیر.
2. **CPU را ۶ برابر کند کن** (`Emulation.setCPUThrottlingRate {rate:6}`) — چون گوشی واقعی از headless کندتر است و بدون throttle همه‌چیز «سالم» به‌نظر می‌رسد.
3. **مقصر را با حذف تکی پیدا کن** (`addStyleTag` با `!important`) — هر ویژگی را جدا خاموش کن و دوباره اندازه بگیر.
4. **انیمیشن‌های در حال اجرا را ببین:** `document.getAnimations().filter(a => a.playState === 'running')`.
5. **میانهٔ ۵ تا ۷ اجرا** را بگیر، نه یک اجرا (نویز زیاد است).

### ✅ قواعد اجباری برای هر اپ جدید
- هیچ `setInterval` که DOM را کامل بازسازی می‌کند، بدون گارد `visibilityState` نباشد.
- هیچ انیمیشن بی‌نهایت روی `box-shadow`، `width`، `height`، `top`، `left` نباشد — فقط `opacity` و `transform`.
- هیچ `backdrop-filter` روی عنصری که پس‌زمینهٔ آن کدر است نباشد.
- هیچ `animation` روی ظرف‌های بلند (بیش از ۱۰۰۰px) نباشد؛ یا فقط `opacity`.
- `background-attachment: fixed` ممنوع؛ از `body::before { position: fixed }` استفاده کن.
- هر انیمیشن باید `@media (prefers-reduced-motion: reduce)` داشته باشد.

---

## 📱 اپ اندروید بومی «نمایشگر کد» (Native Android App)

### مشخصات فنی
- **پکیج (applicationId):** `ir.omarat.codeviewer` — عمداً از `com.emarat.*` جدا شد تا با هیچ اپ دیگری تداخل نکند.
- **نام نمایشی:** «نمایشگر کد» (بدون کلمات حساس).
- **نسخه:** 1.1.0 (versionCode 2).
- **آیکون:** دقیقاً از `html-viewer/icon-512.png` ساخته می‌شود (adaptive + همه چگالی‌ها).

### 🔐 قاعده طلایی: جداسازی کامل شناسه‌های ذخیره‌سازی
هر اپ اندرویدی جدید **باید** شناسه‌های ذخیره‌سازی یکتا داشته باشد تا در کنار سایر اپ‌ها بدون تداخل نصب شود:

| مورد | مقدار (نمایشگر کد) | مقدار (اپ دیگر: سپر دانلود) |
|---|---|---|
| applicationId | `ir.omarat.codeviewer` | `com.emarat.downloadshield` |
| SharedPreferences | `omarat_code_viewer_prefs` | `restricted_bot_prefs` |
| دیتابیس SQLite | `omarat_code_viewer.db` | — |
| پوشه دانلود | `Downloads/CodeViewer/` | — |

**نکته:** اندروید هر اپ را در sandbox جدا نگه می‌دارد، ولی برای اطمینان مضاعف:
1. applicationId نباید زیرمجموعه‌ی اپ دیگری باشد.
2. نام دیتابیس و SharedPreferences باید پیشوند اختصاصی داشته باشد.
3. خروجی دانلود باید در **زیرپوشه‌ی اختصاصی** ذخیره شود تا فایل‌ها بازنویسی نشوند.

### 🎨 ساخت آیکون از وب‌اپ
آیکون اندروید باید **عیناً** از `html-viewer/icon-512.png` تولید شود:
- همه چگالی‌ها: mdpi(48) hdpi(72) xhdpi(96) xxhdpi(144) xxxhdpi(192)
- Adaptive icon (اندروید ۸+): `mipmap-anydpi-v26/ic_launcher.xml` + `ic_launcher_foreground.png` با حاشیه امن (~۶۲٪)
- اعتبارسنجی: مقایسه‌ی aHash آیکون اپ با آیکون وب‌اپ باید **۱۰۰٪** باشد.

### 🏗️ بیلد
```bash
export JAVA_HOME=/opt/tools/jdk17
export ANDROID_HOME=/opt/tools/android-sdk
export PATH=/opt/tools/gradle/bin:$JAVA_HOME/bin:$PATH
gradle assembleRelease assembleDebug --no-daemon
```
خروجی: `app/build/outputs/apk/{release,debug}/`

### 🛡️ اپ اندروید «سپر دانلود» (restricted/android)
- **applicationId:** `com.emarat.downloadshield` | **SharedPreferences:** `restricted_bot_prefs` | minSdk 24 / targetSdk 34.
- WebView داخلی `file:///android_asset/restricted/index.html` را لود می‌کند؛ assets باید همگام بمانند.
- **دام بزرگ (درس گران‌بها):** الگوی `*.png` در `.gitignore` آیکون‌های `mipmap-*` را نادیده می‌گرفت؛ در نتیجه هیچ clone‌ای آیکون نداشت و بیلد با خطای `AAPT: resource mipmap/ic_launcher not found` می‌شکست. **راه‌حل:** استثنای صریح در `.gitignore`:
  ```
  !restricted/android/app/src/main/res/mipmap-*/ic_launcher*.png
  ```
  پس از هر تغییر در `.gitignore`، با `git check-ignore -v <path>` تأیید کنید که فایل‌های حیاتی ردیابی می‌شوند.
- آیکون‌ها از `restricted/icon-512.png` ساخته می‌شوند (۵ چگالی + `_round`). اگر پوشه نبود:
  `python3 -c` با Pillow و `Image.LANCZOS` (نمونه در `.github/workflows/build_android_apk.yml`).
- امضا: `keystore.properties` (فیلترشده در git) با کلیدهای `storeFile/storePassword/keyAlias/keyPassword`. اگر فایل نباشد، بیلد release بدون امضا انجام می‌شود.
- `app/proguard-rules.pro` باید وجود داشته باشد (حتی خالی) چون `build.gradle` به آن ارجاع می‌دهد.
- بیلد خودکار: `.github/workflows/build_android_apk.yml` (workflow_dispatch + آپلود artifact + ارسال اختیاری به تلگرام).

#### 🐛 باگ «دکمه چسباندن اعلان فقط یک بار کار می‌کند» — علت و درمان
سه علت هم‌زمان داشت و هر سه باید رفع شوند:
1. **`onNewIntent` پیاده‌سازی نشده بود.** اکتیویتی `TransparentPasteActivity` با `noHistory` و `CLEAR_TOP` باز می‌شد؛ اینتنت دوم به `onNewIntent` تحویل داده می‌شد و چون آن متد وجود نداشت، اینتنت **دور ریخته می‌شد**. باید `onNewIntent` را override و منطق را به متد مشترک (`tryPaste`) منتقل کرد.
2. **خواندن کلیپ‌بورد پیش از گرفتن فوکوس (اندروید ۱۰+).** خواندن در `onCreate` خالی برمی‌گردد. باید در `onWindowFocusChanged` و با چند تلاش مجدد (مثلاً ۶ بار × ۲۵۰ms) خوانده شود.
3. **`PendingIntent` بدون `SINGLE_TOP`.** باید اکشن اختصاصی (`ACTION_PASTE`) + `FLAG_ACTIVITY_SINGLE_TOP` داشته باشد تا همیشه به نمونه زندهٔ اکتیویتی برسد؛ و `launchMode="singleTop"` در مانیفست.

**درس کلی:** هر اکتیویتی شفاف/موقتی که از اعلان باز می‌شود، **باید** `onNewIntent` داشته باشد؛ وگرنه فقط بار اول کار می‌کند.

### 🎬 زیرنویس‌سازی ویدیو (فارسی)
ابزار: `yt-dlp` (دانلود) + `ffmpeg` (صدا/burn-in) + `faster-whisper` (تشخیص گفتار) + فونت **وزیرمتن**.
- ffmpeg باید با `libass + libfribidi + libharfbuzz` کامپایل شده باشد تا فارسی درست شکل بگیرد.
- برای burn-in: `ffmpeg -i in.mp4 -vf "ass=sub.ass:fontsdir=fontsonly" -c:v libx264 ...`
- اعتبارسنجی رندر فارسی با OCR (`tesseract -l fas`).

### ☁️ سرور اختصاصی سپر دانلود (restricted/bot)
اپ «سپر دانلود» به یک سرور FastAPI نیاز دارد که کلاینت تلگرام (Pyrogram) را ۲۴ ساعته زنده نگه دارد.
- کد: `restricted/bot/server.py` (FastAPI + CORSMiddleware)، `Dockerfile` روی پورت 8080.
- میزبانی: Railway (پلن trial با ۵ دلار اعتبار یک‌باره — تمدید ماهانه ندارد). مصرف واقعی ~۱ دلار/ماه.
- متغیرهای محیطی لازم: `AUTH`, `API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`, `SERVER_TOKEN`, `SESSION`, `PORT=8080`.
- احراز هویت: هدر `X-Auth-Token` باید برابر `SERVER_TOKEN` باشد.
- **CORS الزامی است:** بدون `CORSMiddleware` مرورگر درخواست‌ها را بلاک می‌کند و پیام «عدم اتصال به سرور» نمایش داده می‌شود (curl کار می‌کند ولی مرورگر نه).
- در فرانت‌اند، آدرس سرور در `DEFAULT_SRV_URL` داخل `restricted/index.html` و توکن در `localStorage` با کلید `restricted_bot_srvToken` نگه‌داری می‌شود.
- **محدودیت تلگرام:** دو نمونه سرور همزمان با یک `SESSION` باعث خطای `AUTH_KEY_DUPLICATED` می‌شود؛ قبل از راه‌اندازی سرور جدید، قدیمی را خاموش کنید.
- تعویض میزبان: فقط پروژه Railway جدید + همان متغیرها + به‌روزرسانی `DEFAULT_SRV_URL` کافی است.

#### 🎬 باگ «فقط عکس اول + ویدیوی صفر ثانیه» — علت و درمان
سه باگ هم‌زمان باعث می‌شدند لینک‌هایی مثل `luticlip.com` به‌جای ویدیو، پوستر بفرستند:
1. **`curl` در ایمیج داکر نصب نبود.** `Dockerfile` فقط `git ffmpeg gcc python3-dev` داشت؛ پس هر مسیر پشتیبان دانلود با `[Errno 2] No such file or directory: 'curl'` می‌مُرد. **درمان:** `curl` به `apt-get install` اضافه شد.
2. **بعضی CDNها (مثل `luti2425.takcdn.com`) بدون هدر `Range` اتصال را `Connection reset` می‌کنند.** **درمان:** `download_url_robust()` اول بدون Range، بعد با `Range: bytes=0-` و در نهایت با `curl --range` تلاش می‌کند.
3. **هر فایلی با پسوند شبیه ویدیو کورکورانه با `send_video` ارسال می‌شد؛** پس پوستر (og:image) که با اسم `webpage_video.mp4` ذخیره شده بود، به‌عنوان ویدیوی ۰ ثانیه به تلگرام می‌رفت. **درمان:** `sniff_media_kind()` نوع واقعی فایل را از **magic bytes** تشخیص می‌دهد و گارد پایانی قبل از ارسال، HTML/خالی/پوستر را رد می‌کند و پسوند را با محتوای واقعی هم‌راستا می‌کند.

- توابع کلیدی در `restricted/bot/download_single.py`: `sniff_media_kind()`, `is_usable_media()`, `download_url_robust()`, `download_hls_with_ffmpeg()`.
- **ترتیب لایه‌ها مهم است:** استخراج‌گر سامسونگ (`Layer 2.9`) باید **قبل از** لایهٔ عمومی اجرا شود، وگرنه پوستر دانلود شده و نوبت به فایل واقعی نمی‌رسد.
- **Samsung Quick Share:** لینک فایل واقعی داخل `sharedatacontents = JSON.parse('[...]')` در صفحه است (فیلد `original`). برای همهٔ سایت‌های ناشناس، پرامپت Gemini هم اصلاح شد تا اولویت را روی ویدیو بگذارد، نه پوستر.
- **HLS:** اگر لینک `.m3u8` بود یا محتوای دانلودشده پلی‌لیست بود، با `ffmpeg` به mp4 رمکس می‌شود (ffmpeg از قبل در ایمیج هست).
- **مهم برای دیپلوی:** این کد روی **Railway** اجرا می‌شود، نه GitHub Pages. پس بعد از هر تغییر، سرویس Railway باید مجدداً بیلد/دیپلوی شود تا فیکس به کاربر برسد.

### 🤖 استاد هوشمند اپ ورزشی (gym/index.html)
- فراخوانی AI در `callGeminiAiCoach()` انجام می‌شود؛ کلید از `getGeminiTokenForWorkout()` می‌آید (اول `localStorage.custom_gemini_api_key`، وگرنه کلید پیش‌فرض تکه‌تکه Base64).
- **مدل‌ها بازنشسته می‌شوند:** `gemini-flash-latest` و `gemini-2.5-flash` دیگر کار نمی‌کنند (503/NOT_FOUND). زنجیرهٔ فعلی: `AI_MODEL_CHAIN = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]`. برای یافتن مدل‌های زنده: `GET https://generativelanguage.googleapis.com/v1beta/models?key=...`.
- استراتژی «مسابقه» با برندهٔ واحد: همهٔ مسیرها (هر مدل × پروکسی/مستقیم) هم‌زمان فرستاده می‌شوند، اما فقط **اولین** مسیری که واقعاً متن تولید کند برنده می‌شود و بقیه فوراً `abort` می‌شوند. (نسخهٔ قبلی از `Promise.any` استفاده می‌کرد و با اولین تکه برمی‌گشت → پاسخ ناقص ذخیره می‌شد؛ ضمناً چون همهٔ مسیرها `onDelta` را صدا می‌زدند، متن تکراری رندر می‌شد.)
- **استریم زنده (SSE):** درخواست با `:streamGenerateContent?alt=sse` فرستاده می‌شود و متن کلمه‌به‌کلمه با `aiRenderRich()` رندر می‌شود تا کاربر لحظهٔ تایپ استاد را ببیند. پارسر SSE با بافر + شمارش آکولاد، آبجکت‌های JSON را از تکه‌های نصفه‌بین‌دو‌chunk جدا می‌کند.
- مهلت `AI_TIMEOUT_MS = 30 * 60 * 1000` (۳۰ دقیقه). تایمر تا **پایان کامل خواندن بدنه** زنده می‌ماند (قبلاً بلافاصله بعد از رسیدن هدرها `clearTimeout` می‌شد و اگر بدنه قفل می‌کرد، اسپینر تا بی‌نهایت می‌چرخید). حلقهٔ خواندن با سیگنال `abort` مسابقه داده می‌شود تا مهلت/لغو همیشه آن را بشکند.
- **دکمهٔ توقف:** `stopAiGeneration()` → `aiAbortActiveCoach()`؛ همهٔ کنترلرهای موازی را `abort` می‌کند و متن جزئیِ تا همان لحظه را نگه می‌دارد. در حین تولید، دکمهٔ ارسال (`⚡`) پنهان و دکمهٔ توقف (`⏹`) نمایان می‌شود (`aiSetGenerating`). بستن مودال هم استریم را آزاد می‌کند.
- آخرین خطا در `localStorage.workout_ai_last_diagnostic` ذخیره می‌شود (برای عیب‌یابی روی گوشی کاربر).
- **مهم — کدام سرویس‌ورکر فعال است:** پورتال (`/sw.js`) همهٔ سرویس‌ورکرهای زیرپوشه‌ها را `unregister` می‌کند، پس `gym/sw.js` **بی‌اثر** است. برای رسیدن تغییرات به کاربر، فقط `CACHE_NAME` در `sw.js` ریشه را بالا ببرید (الان `emarat-portal-v62`).
- فرانت‌اند با استراتژی Stale-While-Revalidate کش می‌شود؛ بعد از تغییر، کاربر یک‌بار رفرش کند.

### 🎨 قالب‌بندی پاسخ استاد + ارسال به تلگرام (gym/index.html)
- **موتور رندر داخلی:** `aiRenderMarkdown()` → HTML. پشتیبانی: تیتر `##`، پررنگ `**`، مورب `*`، زیرخط `__`، هایلایت `==`، رنگ `{red:متن}` (پالت `AI_SAFE_COLORS`)، لیست `-`/`1.`، جعبهٔ نکته `>`، جدول `| ... |`. بدون کتابخانه خارجی (آفلاین). همهٔ ورودی‌ها با `aiEscapeHtml()` امن می‌شوند.
- **رندر:** `aiRenderRich(container, text)` و `aiBuildAnswerBlock(text, {telegram})` که متن + دکمه‌های «📋 کپی با قالب» و «📤 ارسال به تلگرام» را می‌سازد. `renderAiAnalysis()` و `renderAiChat()` از همین استفاده می‌کنند.
- **پرامپت استاد:** ابزارهای قالب‌بندی **اختیاری** معرفی شده‌اند («هر وقت لازم دیدی استفاده کن»)، نه اجباری.
- **تلگرام:** `aiToTelegramHtml()` خروجی را به HTML مجاز تلگرام تبدیل می‌کند (جدول → `<pre>`، رنگ/هایلایت حذف). `aiSplitForTelegram()` پیام بلند را زیر ۴۰۹۶ کاراکتر می‌شکند. در صورت خطای HTML، بدون قالب (`plain`) دوباره می‌فرستد.
- **تنظیمات:** توکن و Chat ID فقط در `localStorage` کاربر با کلیدهای `ai_tg_bot_token` و `ai_tg_chat_id` (بدون hardcode). پنل با دکمهٔ ⚙️ در هدر مودال استاد: `openAiSettingsModal()`, `saveAiSettings()`, `clearAiSettings()`, `aiTestTelegramConnection()`.
- **نکته:** `innerText` در jsdom پشتیبانی نمی‌شود؛ از `aiElementText()` (innerText با fallback به textContent) استفاده کنید.

### 🎛️ کنترل اجزای محاسبه در صفحه «مجموع کل» (profit-calculator/total.html)
- دکمهٔ «📊 مشاهده مجموع کل در صفحه مجزا» در `calc2.html` فایل `total.html` را باز می‌کند (فقط وقتی ≥۲ تب علامت‌خورده وجود دارد).
- تابع محاسبه: `runCompoundingCalculation(data, targetYears, options)` — آرگومان سوم (`options`) فیلترهای کنترل کاربر است:
  - `includeInitial`, `includeMonthly`, `includeAnnualIncrease`, `includeBimonthly`, `includeProfit`, `manualDailyRate`.
- **نرخ دستی** همیشه «میانگین سود روزانه به درصد» است و با `×365` به نرخ سالانه تبدیل می‌شود (منطبق بر `calc2.html`).
- **نرخ سراسری** (`#global-daily-rate`) پیش‌فرض همهٔ صندوق‌هاست؛ اگر کادر نرخ همان صندوق (`.fund-rate-input[data-tab-id]`) پُر باشد، همان غالب می‌شود.
- تیک «احتساب سود» با صفر کردن نرخ پیاده می‌شود → خروجی می‌شود «اصل پول + واریزی‌ها بدون رشد».
- **مهم:** این کنترلها فقط شبیه‌سازِ محلی هستند؛ **هیچ‌چیز در `localStorage` ذخیره نمی‌شود** و **هیچ اثری روی دادهٔ تب‌های صندوق (`calculatorTab_*`) ندارند**. تنها کلید ذخیره‌شده `totalSumYears` است.
- رندر مجدد کارت‌ها مقادیر نرخ دستی را از `manualRateCache` بازیابی و فوکوس/مکان‌نما را حفظ می‌کند (`focusTabId`)؛ ورودی نرخ با debounce (۴۰۰ms) و نرخ سراسری با ۲۵۰ms محاسبه می‌شود.
- `total.html` باید در `ASSETS` فایل `sw.js` ریشه باشد و `CACHE_NAME` بامپ شود (الان `emarat-portal-v72`).
- باکس کنترل (`#control-toggle-btn` / `#control-content`) به‌صورت آکاردئون و **پیش‌فرض بسته** است (فقط تیتر + فلش ▼) تا صفحه خلوت بماند.

### 🗑️ تأیید دو مرحله‌ای حذف تب (profit-calculator/calc2.html)
- دکمهٔ ضربدر تب (`.close-tab`) دیگر فوراً `closeTab()` را صدا نمی‌زند؛ ابتدا `requestDeleteTabConfirmation(tabId, onConfirmed)` اجرا می‌شود.
- مودال سفارشی `#confirmDeleteModal` دو مرحله دارد: مرحلهٔ ۱ «ادامه»، مرحلهٔ ۲ «🗑️ بله، پاک کن» (دکمهٔ قرمز `.confirm-danger-btn`).
- انصراف، کلید `Escape` و کلیک روی پس‌زمینه (`onBackdrop`) مودال را می‌بندند؛ listenerها در `cleanup()` حذف می‌شوند تا نشتی نداشته باشیم.
- نشانگر مرحله با دو نقطه (`.confirm-dot`) و نمایش نام دلخواه تب (`tabCustomName_*`) در متن پیام.
- اگر تب تنها تب موجود باشد، همان `alert` قبلی نمایش داده می‌شود و مودال باز نمی‌شود.
- مودال با `display:flex` و `align-items/justify-content:center` **وسط صفحه** باز می‌شود (نه بالا)؛ `max-height:85vh` + `overflow-y:auto` برای صفحه‌های کوچک.

### 🌾 اپ «ثبت درصد ۹» — سهم غبهار (gold9/)
- **پوشه:** `gold9/` (کلون از `gold8`) | **نام آیکون/PWA:** «ثبت درصد 9» (لاتین، هم‌راستا با gold4..gold8) | **عنوان داخل اپ:** «سهم غبهار» + زیرعنوان «کشت وصنعت بهاران گلبهار خراسان».
- **تفکیک مهم:** `manifest.name/short_name` و `<title>` = «ثبت درصد 9»، ولی `brand-title` داخل صفحه = «سهم غبهار». `apple-mobile-web-app-title` هم «ثبت درصد 9» است (نام هوم‌اسکرین iOS).
- **پالت:** زیتونی–گندمی (`#5b7c2d`, `#a3b544`, `#d4af37`؛ پس‌زمینه `#1b2410`، کارت `#24301a`).
- **پیشوند کلیدهای ذخیره‌سازی: `baharan_`** — `baharan_percents` (شیء یکپارچه: `{percents, trash, goal, notes, periodTarget, achievedPeriods, highlightedStates}`)، `baharan_history`، `baharan_peakNumber`، `baharan_baseNumber`، `baharan_prices_v1`.
- **پس‌زمینه:** `gold9/baharan_bg.webp` + فالبک `baharan_bg.jpg` با `background-size: cover` (هنوز جای تصویر کاربر، قابل تعویض).
- **آیکون:** آسمان آبی + خورشید طلایی + چمن سبز (بدون متن).
- **اتصالات اکوسیستم (همه انجام شد):**
  - پورتال `index.html` → `DEFAULT_APPS` با `{ id: 'gold9', title: 'ثبت درصد 9' }` + `path.includes('/gold9/')` در لیست مسیرهای مجاز iframe.
  - `sw.js` → `CACHE_NAME` = `emarat-portal-v84` + ۱۴ فایل gold9 در `ASSETS`.
  - `monitor/index.html` → `MONITOR_HISTORY_KEYS[9] = "baharan_history"`، `peakKeys[9] = "baharan_peakNumber"`، `getAppPercentData()` id 9، و همهٔ حلقه‌های `appId <= 9`؛ کلیدهای بکاپ/یادداشت: `['baharan_percents','baharan_notes']`.
  - `profit-calculator/calc2.html` و `total.html` → گزینهٔ `baharan_percents` در منبع دیدبان.
  - `monthly-deposit/index.html` → `APP_PERCENT_LABELS[9]` + نام صندوق + حلقه‌های `appId <= 9`.
- **⚠️ نکتهٔ `getAppPercentData`:** برای اپ‌های شیء‌محور (gold5..gold9) داده از `parsed.percents` خوانده می‌شود، نه از ریشه. اگر آرایهٔ خام در ریشه ذخیره شود، فهرست خالی می‌ماند.
- **بعد از تغییر:** `CACHE_NAME` در `sw.js` بامپ شود (الان `emarat-portal-v85`).

### 📦 ارسال فایل بزرگ (تا ۲GB) به تلگرام بدون سشن کاربر — ترفند کلیدی
- **مشکل ۱:** `sendDocument` روی HTTP API بات (`api.telegram.org`) سقفش **۵۰ مگابایت** است.
- **مشکل ۲:** سشن کاربر ممکن است جای دیگر فعال باشد → خطای `AUTH_KEY_DUPLICATED` (همان چیزی که سرور Railway سپر دانلود باعثش می‌شود؛ چون `main.py` سرور، `userbot` را با همان `SESSION` بالا می‌آورد).
- **راه‌حل:** بات را با **Pyrogram + MTProto** وصل کن (`bot_token=...`)؛ سقف آپلود بات در MTProto می‌شود **۲ گیگابایت** و به سشن کاربر نیازی نیست.
- **🪄 ترفند حیاتی (Peer cache):** قبل از `send_document`، حتماً یک `sendMessage` ساده به همان `chat_id` بزن و ~۳ ثانیه صبر کن. بدون این کار خطای `Peer id invalid: -100...` می‌گیری، چون بات هیچ‌وقت کانال را «ندیده» و `access_hash` آن را ندارد.
  ```python
  requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
               params={"chat_id": CHAT, "text": "🔔 شروع ارسال..."}, timeout=15)
  time.sleep(3)
  app.send_document(CHAT, FILE, force_document=True, progress=cb)
  ```
- `app.get_dialogs()` برای بات ممنوع است (`BOT_METHOD_INVALID`).
- **محدودیت‌ها:** آپلود بات ۲GB / دانلود ۴GB. فایل‌های گیت از قبل فشرده‌اند؛ `xz -9e` فقط چند درصد کم می‌کند (۳۵۱MB → ۳۲۴MB).
- **بک‌آپ کامل همه مخزن‌ها:** `git clone --mirror` برای هر مخزن (۳۵ مخزن، ~۳۵۴MB)، سپس `tar` + `xz -9e -T0`.
- **توجه:** توکنی که در `restricted/index.html` و سرور استفاده می‌شود، `SERVER_TOKEN` سرور (هدر `X-Auth-Token`) است، نه توکن Railway. برای خاموش کردن سرویس باید از پنل Railway اقدام شود (توکن API آن جداگانه است).

### 📈 باگ «نمودار سفید و کج» در دیدبان درصدها (monitor/index.html)
سه ریشهٔ هم‌زمان باعث می‌شد نمودار بخش «📜 تاریخچه کامل سودها» دیده نشود:
1. **`!important` روی کانواس:** `canvas.growth-canvas { width: 100% !important; }` عرض اینلاین JS (`canvas.style.width = calcWidth + 'px'`) را بی‌اثر می‌کرد و کانواس بزرگ را در عرض ظرف (~۳۲۸px) له می‌کرد → «کج». **درمان:** `!important` حذف شد؛ عرض/ارتفاع فقط از JS (اینلاین) می‌آید.
2. **سقف سخت ابعاد کانواس:** مرورگر کانواس با عرض > ~۶۵۵۳۵px (یا مساحت خیلی بزرگ) را **بی‌صدا سفید** می‌کند. با فاصلهٔ ۴۵px و dpr=3، فقط ~۵۰۰ روز کافی بود تا نمودار سفید شود. **درمان:** در `renderGrowthChart` سقف `MAX_CANVAS_DIM = 32767` و `MAX_CANVAS_AREA = 16MP` و `dpr = min(devicePixelRatio, 2)` اعمال شد؛ اگر از سقف عرض رد شویم، نقاط با نمونه‌برداری یکنواخت (بازهٔ پویا) فشرده می‌شوند تا کاربر افقی اسکرول کند.
3. **تایم‌استمپ خراب (ثانیه‌ای/صفر):** یک رکورد با `timestamp` ثانیه‌ای یا `0` (از بکاپ/ایمپورت قدیمی) حلقهٔ `calculateDailyHistory` را تا سقف ۳۶۵۰ روز می‌برد → کانواس ۱۶۴ هزار پیکسلی → **۱۰۰٪ سفید**. **درمان:** تابع `normalizeTimestamp()` (ثانیه→میلی‌ثانیه + رد مقادیر خارج از بازهٔ ۲۰۰۰..۲۱۰۰) در `calculateDailyHistory`، `initializeTomanProfitCache` و `getGregorianDayString` استفاده شد.
- **اسکرول:** ظرف `.chart-canvas-wrapper` با `overflow: auto; touch-action: pan-x pan-y; height: 200px` هم اسکرول افقی و هم عمودی می‌دهد (RTL هم پشتیبانی می‌شود).
- **برچسب تاریخ:** حداکثر ~۱۲ برچسب (پویا بر اساس تعداد نقاط) تا تاریخ‌ها روی هم نیفتند.
- **نکته تست:** با Puppeteer/Chromium می‌توان با `canvas.drawImage` روی یک کانواس کوچک و `getImageData`، «سفید بودن» را کمی سنجید؛ `getImageData` مستقیم روی کانواس چند‌ده‌هزار‌پیکسلی ممکن است تایم‌اوت کند.
- **بعد از تغییر:** `CACHE_NAME` در `sw.js` بامپ شود (الان `emarat-portal-v74`).

### 💥 باگ بحرانی «صفر شدن کل تاریخچه سودهای مثبت» (رگرسیون v73)
پس از استقرار v73، **تمام تاریخچهٔ سود مثبت صفر** نمایش داده شد. علت یک رگرسیون در `normalizeTimestamp()` بود:
- **ریشه:** اپ‌های `calc` (مثل `gold/calculator.html`، `gold3`..`gold7`) تایم‌استمپ را با `now.toISOString()` ذخیره می‌کنند (رشتهٔ ISO مثل `"2026-11-16T10:12:19.000Z"`)، ولی اپ‌های `percent` عدد میلی‌ثانیه می‌گذارند. نسخهٔ v73 ابتدا `Number(rawTs)` می‌زد؛ برای رشتهٔ ISO نتیجه `NaN` می‌شد → `normalizeTimestamp` مقدار `null` برمی‌گرداند → **هر رکورد بی‌صدا حذف** و نمودار/سود صفر می‌شد.
- **نکته حیاتی:** داده‌ها **پاک نشده بودند**؛ فقط خواندنشان خراب بود. هیچ‌کدام از این کلیدها (`gold_history`، `percents`، ...) توسط `monitor/index.html` نوشته نمی‌شوند (فقط خوانده می‌شوند)، پس خطر از‌دست‌رفتن دائمی وجود نداشت.
- **درمان:** `normalizeTimestamp()` ابتدا نوع را چک می‌کند: رشتهٔ عددی خالص → عدد؛ در غیر این صورت `Date.parse()` (برای ISO). اعداد فارسی هم با `normalizeToEnglishDigits()` تبدیل می‌شوند. ثانیه‌ای → میلی‌ثانیه و بازهٔ مجاز ۲۰۰۰..۲۱۰۰ حفظ شد.
- **درس کلی:** هر تابع «نرمال‌سازی» که روی دادهٔ چند‌اپلیکیشنی کار می‌کند، باید **همهٔ فرمت‌های واقعی** (ISO string، ms number، sec number، رشتهٔ عددی، ارقام فارسی) را پوشش دهد؛ وگرنه `null` بی‌صدا داده را حذف می‌کند.
- **تست رگرسیون:** با Puppeteer + `file://` می‌توان `gold_history` را با رشتهٔ ISO و `percents` را با عدد میلی‌ثانیه seed کرد و سپس `calculateDailyHistory().length` و `Object.keys(dailyTomanProfitMap).length` را سنجید؛ هر دو باید برابر تعداد روزهای داده باشند.

### 📊 نمودار ستونی روزانه/تجمعی + خط سرمایه واریزی + فیلترها (monitor/index.html)
- **حالت‌ها:** سوییچ `📈 تجمعی` / `📉 روزانه` در هدر مودال (`#chartModeSwitch`, `#chartModeCumBtn`, `#chartModeDayBtn`). پیش‌فرض **تجمعی**. انتخاب در `localStorage.monitor_chart_view_mode` ذخیره می‌شود.
- **معنای داده:** `history[i].value` = مجموع انباشته تا آن روز (تجمعی)؛ `history[i].dailyValue` = سطح خام همان روز. **حالت روزانه = تفاضل سطح روز جاری و روز قبل** (`dailyDelta`)، نه خود سطح. اگر از سطح خام استفاده شود، میله‌های قرمز هرگز ظاهر نمی‌شوند (اشتباه رایجی که یک‌بار رخ داد).
- **حالت 🔁 زرین (سودهای مثبت):** همچنان **نمودار خطی سبز** است و سوییچ حالت پنهان می‌شود (`openLargeChartModal` مقدار `display:none` می‌دهد).
- **خط سرمایه واریزی:** `getCumulativeDepositByDay()` از `fundManagerV10` (`monthlyAmounts` + `payments` + `history` با تایم‌استمپ شمسی) می‌سازد؛ در نبود آن به `monthly_deposit_sync` fallback می‌کند. خط پله‌ای نارنجی روی محور راست (تومان)، برچسب‌ها با `formatCompactToman()`.
- **فیلترها:** سه چیپ `رشد`/`کاهش`/`سرمایه واریزی` (`toggleChartFilter`) که در `localStorage.monitor_chart_filters` ذخیره می‌شوند (پیش‌فرض همه روشن). `chartFilters.growth===false` میله‌های صعودی و `chartFilters.drop===false` میله‌های نزولی را حذف می‌کند؛ `chartFilters.capital===false` خط نارنجی را حذف می‌کند.
- **چیدمان:** نمودار به **کف مودال** چسبیده (`justify-content: flex-end` روی بدنه). فاصله‌ی تاریخ‌ها با `minLabelGap = 86` (large) / `66` (کوچک) تعیین می‌شود تا تاریخ‌ها کامل و خوانا بمانند.
- **تست:** با Puppeteer روی `file://` می‌توان با `canvas.drawImage` روی کانواس کوچک + `getImageData` تعداد پیکسل سبز/قرمز/نارنجی را شمرد؛ با داده‌ی نوسانی قوی (مثلاً مقادیر یک‌درمیان ۵ و ۱) باید هم سبز و هم قرمز ظاهر شود.
- **بعد از تغییر:** `CACHE_NAME` در `sw.js` بامپ شود (الان `emarat-portal-v75`).

### 💰 واریز دوگانه در اپ «واریز ماهیانه» (monthly-deposit/index.html)
- **مدل داده نسخه ۳:** `payments[fi][mi]` دیگر بولین نیست؛ **تعداد واریزهای تیک‌خورده** (۰..N) است. آرایه‌ی جدید `depositCounts[fi]` = تعداد واریز در ماه برای هر صندوق (پیش‌فرض **۱**، حداکثر ۶).
- **سازگاری عقب‌رو:** `normalizePayments()` مقادیر قدیمی (`true/1`) را به عدد تبدیل می‌کند و `normalizeDepositCounts()` آرایه‌ی غایب را با پیش‌فرض ۱ می‌سازد؛ پس بکاپ‌های `version:2` بدون تغییر داده لود می‌شوند. کلید ذخیره‌سازی همان `fundManagerV10` است (نسخه‌ی داخلی `version:3`).
- **UI:** ستون `.deposit-col` شامل **دایره‌ی بزرگ بالا** (واریز اول، `slotIndex=0`) و در صورت `depositCounts[fi]>=2` **دایره‌ی کوچک پایین** (واریز دوم، `slotIndex=1`) که با `.deposit-link` به هم وصل‌اند. هر دایره‌ی تیک‌خورده `.done` (سبز + ✔) می‌شود.
- **منطق تیک:** `toggleDeposit(fi, mi, slotIndex)` — اگر روی خانه‌ی خالی بزنی، همه‌ی خانه‌های قبل هم پر می‌شوند (خانه‌های قبل تایم‌استمپ می‌گیرند)؛ اگر روی خانه‌ی تیک‌خورده بزنی، از همان خانه به بعد پاک می‌شود (`hist.length` هم کوتاه می‌شود).
- **جمع:** `getFundMonthCount()` تعداد واقعی را برمی‌گرداند و جمع ماه/کل = `مبلغ واحد × تعداد` (`computeTotalDeposits`/`getMonthTotal`). سینک مانیتور هم `amount = unit × cnt` می‌فرستد.
- **تاریخ‌ها:** روی صفحه‌ی اصلی هیچ تاریخی نمایش داده نمی‌شود؛ فقط در پنجره‌ی 📋 (`showHistoryPopup`). هر واریز یک تایم‌استمپ جدا دارد.
- **تنظیمات:** در `#settingsFundManageRows` هر صندوق یک `<select class="deposit-count-select" data-fund-index="N">` با گزینه‌های «۱ بار»/«۲ بار» دارد؛ با کم کردن تعداد، واریزهای اضافه و تایم‌استمپ‌هایشان کوتاه می‌شوند.
- **مانیتور (`getCumulativeDepositByDay`):** `payments[mi][fi]` را به‌عنوان تعداد می‌خواند و برای هر واریز از `history` تایم‌استمپ می‌گیرد؛ در نبود تاریخ، `unit × cnt` روی همان روز/کل حساب می‌شود.
- **چیدمان تنظیمات:** ردیف مدیریت صندوق **دو خطی** است (خط اول نام کامل صندوق، خط دوم کنترل «واریز/ماه» + دکمه‌های ویرایش/حذف). علت: در حالت یک‌خطی، `overflow:hidden` نام صندوق را روی صفحه گوشی به ~۱۴px له می‌کرد.
- **تم تاریک/روشن:** کل رنگ‌های اپ در `:root` به‌صورت CSS Variable تعریف شده‌اند و بلوک `body.dark-theme` آن‌ها را برای تم تاریک بازنویسی می‌کند (تاریک ملایم `#0f172a`، نه سیاه مطلق). دکمه‌ی چرخشی `#themeToggleBtn` **داخل ⚙️ تنظیمات** است (`toggleTheme()` / `initTheme()` / `applyTheme()`)، انتخاب در `localStorage.monthly_deposit_theme` (`light`/`dark`) ذخیره می‌شود و متاتگ `#metaThemeColor` هم هماهنگ می‌شود. پیش‌فرض روشن.
- **تله‌های تم (درس گران‌بها):**
  1. `body` باید رنگ متن پایه داشته باشد (`color: var(--text-head)`)؛ وگرنه عناصری که رنگ صریح ندارند (مثل `.month-total`) در تم تاریک با **سیاه پیش‌فرض مرورگر** رندر می‌شوند و نامرئی می‌شوند (کنتراست ۱.۶۵).
  2. هرگز `background: white` هاردکد نگذارید (مثل `.toggle-all-btn`)؛ از `var(--card-bg)` استفاده کنید.
  3. پاپ‌آپ‌های بلند باید `max-height: 85vh` + `overflow-y: auto` + تیتر `position: sticky` داشته باشند؛ وگرنه روی موبایل بلندتر از صفحه می‌شوند و **دکمه‌ی بستن بیرون صفحه می‌افتد** (کاربر گیر می‌کند).
  4. اعتبارسنجی کنتراست: با Puppeteer نسبت کنتراست WCAG هر سلکتور را حساب کنید؛ حداقل باید ≥ ۴.۵ (AA) و ترجیحاً ≥ ۶ باشد.
- **بعد از تغییر:** `CACHE_NAME` در `sw.js` بامپ شود (الان `emarat-portal-v79`).

---

## 📱 اپ اندروید اتوماسیون ثبت درصد ۴ و ۵ (fund-automation-android/)

### مشخصات فنی
- **applicationId:** `ir.omarat.fundautomation` (جدا از سایر اپ‌ها، بدون تداخل)
- **SharedPreferences:** `omarat_fund_automation_prefs` (رمزنگاری‌شده با Android Keystore)
- **SharedPreferences وضعیت:** `omarat_fund_automation_state`
- **نسخه:** 1.5.0 (versionCode 6) | minSdk 24 / targetSdk 34
- **آیکون:** از `gold4/icon-512.png` ساخته می‌شود (۵ چگالی + round + adaptive)
- **زبان:** Kotlin + ViewBinding + OkHttp + EncryptedSharedPreferences

### 📌 وضعیت فعلی (آخرین به‌روزرسانی: 1405/08/27)
| بخش | وضعیت |
|---|---|
| ورود به ایزی‌تریدر (SSO + auth-callback) | ✅ **حل شد** (v1.5.0) |
| استخراج سینرژی (صندوق ۵) | ✅ کار می‌کند (لایهٔ هوش مصنوعی) |
| استخراج آتیه مفید (صندوق ۴) | 🔧 **رفع شد** (v1.6.0) — منتظر تأیید روی گوشی |
| ثبت در صفحهٔ وب‌اپ (localStorage) | ✅ کار می‌کند |
| بکاپ گیت‌هاب با ادغام دوطرفه | ✅ **حل شد** (v1.5.0) |
| تست واحد (BackupMerger) | ✅ ۱۱ تست پاس |

**گام بعدی معلق:** رفع باگ ناوبری آتیه — منتظر تأیید کاربر و (در صورت امکان) آدرس دقیق صفحهٔ صندوق آتیه برای ناوبری مستقیم با `loadUrl`.

### 🏛️ معماری Local-First (بدون VPS، بدون سرور، بدون GitHub Actions)
- اپ خودش یک WebView می‌سازد، وارد `login.emofid.com/Login` می‌شود، تیک «این دستگاه را به خاطر بسپار» می‌زند، سپس به `m.easytrader.ir/portfolio-fill` می‌رود.
- **کروم نمی‌تواند اتوماسیون کند** — فقط WebView خودِ اپ.
- درصد در حافظهٔ داخلی اپ ذخیره می‌شود + بکاپ JSON با **GitHub API مستقیم** آپلود می‌شود (نه Actions).

### 🧩 فایل‌های کد
| فایل | مسئولیت |
|---|---|
| `MainActivity.kt` | صفحهٔ اصلی، دکمهٔ اجرا، OTP تعاملی، تنظیمات ⚙️، گزارش |
| `AutomationEngine.kt` | WebView + ورود + استخراج ۴ لایه (network/text/dom/ai) |
| `FundCalculator.kt` | فرمول درصد + منطق قله (INCREASE/RECOVERING/DECREASE/NEUTRAL) |
| `SessionStore.kt` | رمز و کوکی با Keystore (EncryptedSharedPreferences) |
| `BackupManager.kt` | آپلود بکاپ به گیت‌هاب + **خواندن محتوای موجود برای ادغام** |
| `BackupMerger.kt` | **موتور ادغام دوطرفهٔ امن** — حفظ تاریخچه بر اساس id یکتا |
| `WebAppStore.kt` | ساخت payload بکاپ + اسکریپت تزریق localStorage |
| `AiPageReader.kt` | لایهٔ Gemini (زنجیرهٔ مدل‌ها) |
| `JalaliDate.kt` | تبدیل میلادی به شمسی |
| `ReportBuilder.kt` | گزارش فارسی پایان اجرا |
| `WebViewActivity.kt` | نمایش صفحات محلی ثبت درصد |

### 🔄 کانال نمایش در وب‌اپ‌ها (مهم)
اپ بکاپ را در `gold4/gold4_backup.json` و `gold5/gold5_backup.json` آپلود می‌کند و هر دو وب‌اپ خودشان `autoSyncFromBackup` دارند → عدد را می‌بینند.
- `gold5/percent.html` از قبل داشت؛ `gold4/percent.html` هم اضافه شد (ادغام دوطرفه با محترم‌شمردن `trash`).
- `monitor/index.html` فقط می‌خواند (نمی‌نویسد) و از همان بکاپ تغذیه می‌شود.

### 🐛 باگ‌های رفع‌شدهٔ v1.1.0 (درس‌های گران‌بها)

#### ۱. تاریخ شمسی ۳۴۳۰ به‌جای ۱۴۰۵
- **ریشه:** الگوریتم قدیمی `gy - 621` می‌زد و بعد `33 * np` را هم اضافه می‌کرد → سال دو بار جابه‌جا می‌شد.
- **درمان:** الگوریتم استاندارد `jalaali-js`/`jdatetime` (پایهٔ ۳۳سالهٔ ۱۲۰۵۳روزه) در `JalaliDate.toJalali` + منطقهٔ زمانی `Asia/Tehran`.
- **درس:** هر الگوریتم تبدیل تاریخ را با حداقل ۷ تاریخ شناخته‌شده تست کن (نوروز، کبیسه، مرز سال).

#### ۲. استخراج همیشه «ناموفق» (هر چهار لایه)
سه علت هم‌زمان، و هر سه باید رفع شوند:
1. **تب «سایر» کلیک نمی‌شد.** صندوق‌های مفید زیر تب «سایر» هستند، نه تب پیش‌فرض «سهام». `openOtherTab()` اضافه شد (idempotent — اگر «سینرژی» در صفحه باشد، دوباره کلیک نمی‌کند).
2. **`innerText` در WebView اندروید `\n` نمی‌گذارد.** برخلاف Playwright، «سینرژی۲۵۰,۰۰۰,۰۰۰همسنگ ۲۵,۰۰۰,۰۰۰» به‌هم‌چسبیده می‌آید؛ پس پیمایش خط‌به‌خط بی‌فایده است. `scanBodyText` بازنویسی شد: پنجرهٔ ۲۰۰ کاراکتری بعد از کلیدواژه، تا اولین «همسنگ»/«تومان»/«کارگزاری»، سپس بزرگ‌ترین عدد ۶رقمی+.
3. **تاریخ ۳۴۳۰** خودش نشانهٔ باگ ۱ بود و اعتبارسنجی را هم خراب می‌کرد.
- **درس:** هرگز فقط به یک نمایش (Playwright) تکیه نکن؛ با Chromium واقعی و ماکت صفحه تست کن.

#### ۳. بکاپ سینرژی آپلود نمی‌شد
- فقط `gold4` آپلود می‌شد. `buildSynergyBackupPayload()` + آپلود `gold5/gold5_backup.json` اضافه شد.

#### ۴. 🚨 خطرناک‌ترین باگ — نابودی تاریخچهٔ بکاپ گیت‌هاب (v1.5.0)
- **نشانه:** پس از یک اجرای موفق، فایل `gold5/gold5_backup.json` در گیت‌هاب از **۶۰ رکورد به ۱ رکورد** رسید (۱۰۱۵ خط → ۱۲ خط). تاریخچهٔ ماه‌ها کار در یک لحظه رفت.
- **ریشه:** `BackupManager.uploadToGitHub()` فقط `sha` را می‌خواند (برای گرفتن مجوز بازنویسی از گیت‌هاب) ولی **محتوای فایل موجود را هرگز نمی‌خواند**. پس هر آپلود، کل فایل را با payload تازه (که فقط **یک** رکورد دارد) **جایگزین** می‌کرد. این نقض مستقیم قانون «ادغام دوطرفهٔ امن» در AGENTS.md است.
- **بازیابی داده:** نسخهٔ کامل در git history (`git show f51d8d2:gold5/gold5_backup.json`) سالم بود. با `git show` استخراج، رکورد تازهٔ اپ هم ادغام و فایل بازنویسی شد (۶۰ → ۶۱ رکورد). `baseNumber` با `newestRecord.rawNew` هم‌راستا شد.
- **درمان:** کلاس `BackupMerger` ساخته شد و `uploadToGitHub` اکنون **محتوای موجود را می‌خواند و ادغام می‌کند**:
  - `history`/`percents`/`trash` بر اساس **شناسهٔ یکتا** (`id`، وگرنه `timestamp`) ادغام می‌شوند.
  - رکوردهای **تازه برنده‌اند** (override)، رکوردهای قدیمی که در تازه نیستند دست‌نخورده می‌مانند.
  - خروجی بر اساس زمان مرتب می‌شود؛ `baseNumber` از جدیدترین رکورد گرفته می‌شود.
  - فرمت‌های چندگانهٔ زمان (ms عددی، رشتهٔ ISO، ثانیه‌ای، ارقام فارسی) پشتیبانی می‌شوند.
- **⚠️ درس طراحی:** ابتدا پنجرهٔ زمانی ۲ ثانیه‌ای برای تشخیص تکرار گذاشتم؛ تست واحد ثابت کرد این کار دو اندازه‌گیری واقعیِ نزدیک به هم را بی‌گناه حذف می‌کند. دادهٔ واقعی نشان داد هر رکورد `id` یکتا دارد، پس ادغام بر اساس `id` انجام شد. **تست واحد، باگ را قبل از کاربر گرفت.**
- **تست:** ۸ تست واحد در `BackupMergerTest` — از جمله «۶۰ رکورد نابود نمی‌شود»، «رکورد تکراری اضافه نمی‌شود»، «فایل نامعتبر داده را خراب نمی‌کند». (`gradle testDebugUnitTest`)

#### ۵. ⚠️ خطای دروغین «رمز/نام کاربری نادرست است» — ایستگاه auth-callback (v1.5.0)
- **نشانه:** لاگ می‌گفت «فرم ورود پیدا نشد» و بعد «پس از ورود هم به صفحهٔ پرتفوی نرسیدیم» با آدرسی مثل `https://m.easytrader.ir/auth-callback?code=...&state=...`.
- **نشانهٔ طلایی:** وجود `code=...` یعنی **SSO مفید ورود را تأیید کرده**؛ نام کاربری و رمز درست بوده. این خطا هیچ ربطی به رمز ندارد.
- **ریشه ۱:** `isOnPortfolio()` سخت‌گیرانه بود (`باید portfolio در URL باشد`) و `auth-callback` این واژه را ندارد → اپ فکر می‌کرد وارد نشده.
- **ریشه ۲:** اپ به `login.emofid.com/Login` می‌رفت؛ ولی چون نشست SSO فعال بود، مفید **فرمی نشان نمی‌داد** و بی‌درنگ ریدایرکت می‌کرد → «فرم ورود پیدا نشد». این پیام در واقع نشانهٔ ورودِ موفق بود، نه خطا.
- **درمان:**
  1. `isAuthCallback()` اضافه شد (`auth-callback`/`signin-oidc`/`callback?code=`).
  2. `waitForPortfolio()` اضافه شد: هر ۱ ثانیه URL را می‌خواند و به‌محض رسیدن به پرتفوی برمی‌گردد (تا ۴۵ ثانیه) — به‌جای مکث کور.
  3. `fillLoginForm()` اکنون `Boolean` برمی‌گرداند؛ اگر فرمی نبود، پیام «احتمالاً نشست SSO فعال است» ثبت می‌شود و **فرم خالی ارسال نمی‌شود**.
  4. `isStillOnLoginForm()` فقط وقتی «رمز اشتباه» اعلام می‌کند که فرم را واقعاً پر و ارسال کرده باشیم و دوباره فرم ظاهر شود.

#### ۶. ⚠️ «درصد ثبت شد ولی روی صفحهٔ وب‌اپ دیده نشد» — تابع مُرده (v1.4.0)
- **نشانه:** لاگ می‌گفت «📦 پشتیبان سینرژی در گیت‌هاب ذخیره شد» ✅، ولی در صفحهٔ سینرژی رکورد جدید نبود.
- **ریشه ۱ — تابع مُرده:** `WebAppStore.buildInjectScript()` که کارش نوشتن در `localStorage` وب‌اپ است، **هیچ‌جای پروژه صدا زده نمی‌شد** (فقط تعریف بود). کامنت `AutomationEngine` ادعا می‌کرد «نوشتن در localStorage داخل همین WebView انجام می‌شود» ولی چنین کدی وجود نداشت.
- **ریشه ۲ — origin متفاوت:** `localStorage` به **origin** گره خورده است. WebView اتوماسیون روی `https://m.easytrader.ir` است ولی وب‌اپ روی `file:///android_asset/webapp/...`. پس تزریق باید در WebView **جداگانه** با origin وب‌اپ انجام شود، نه در WebView اتوماسیون.
- **درمان:** کلاس `WebAppWriter` ساخته شد: صفحهٔ صندوق را در یک WebView با `allowFileAccess` بارگذاری می‌کند و اسکریپت را همان‌جا اجرا می‌کند. در `MainActivity` بعد از استخراج، برای هر صندوق `write()` صدا زده می‌شود.
- **ریشه ۳ — باگ ظریف `beforeunload` در gold4:** `gold4/percent.html` روی `beforeunload` به `saveData()` وصل است و `saveData` آرایهٔ **درون‌حافظه** را روی `localStorage` بازنویسی می‌کند. اگر فقط `localStorage` تزریق شود، هنگام بستن WebView رکورد **پاک می‌شود**. درمان: در پایان اسکریپت `window.reloadLocalData()` + `window.saveData()` صدا زده می‌شود (gold4 این توابع را گلوبال دارد). gold5 این مشکل را ندارد چون `beforeunload` ندارد.

#### ۷. 🚨 آتیه مفید اصلاً استخراج نمی‌شد — باگ «ALREADY» در ناوبری (رفع‌شده در v1.6.0)
- **نشانه در لاگ (v1.5.0):** ورود موفق ✅، سینرژی از لایهٔ هوش مصنوعی استخراج شد ✅، ولی آتیه از هیچ لایه‌ای نیامد:
  ```
  🗂 تب «سایر» از قبل باز بود.        ← دروغ! هیچ کلیکی رخ نداد
  ℹ️ تب «صندوق‌های مفید» نبود (شاید صندوق‌ها در همین صفحه‌اند).
  ```
- **ریشه:** در `clickTab()` (AutomationEngine.kt) شرط «از قبل باز است» روی **کل متن صفحه** تست می‌شد:
  ```javascript
  var already = /سینرژی|آتیه/.test(document.body.innerText || '');
  if (already) return 'ALREADY';
  ```
  روی صفحهٔ پرتفوی، واژهٔ «سینرژی» **به‌عنوان نام یک نماد سهام** در جدول هست (نه به‌عنوان تب صندوق). پس همیشه `ALREADY` برمی‌گشت و **هرگز روی تب کلیک نمی‌شد** → به تب «صندوق‌های مفید» و صفحهٔ آتیه نمی‌رسیدیم.
- **چرا هوش مصنوعی هم نجات نداد:** داده‌ای که **بارگذاری نشده** است، در متن صفحه نیست. آتیه در صفحهٔ پرتفوی وجود ندارد؛ پس لایهٔ ۴ هم دستش خالی بود. **مشکل، مسیریابی است نه استخراج.**
- **نکتهٔ کلیدی صفحهٔ آتیه:** مقدار ۳۹۷٬۶۱۵٬۸۶۹ ریال در صفحهٔ **جداگانهٔ صندوق** است («دارایی شما» با واحد ریال)، نه در جدول پرتفوی. آن صفحه برچسب «واحد» (۷٬۵۸۱) و «ریال» (۳۹۷٬۶۱۵٬۸۶۹) دارد و دکمه‌های «خرید/فروش/تراکنش‌ها».
- **درمان (v1.6.0):**
  1. شرط «فعال بودن» فقط از وضعیت **خودِ عنصر** خوانده می‌شود (`isActive()`: `aria-selected`/`aria-current`/کلاس فعال در ۴ سطح والد). اگر شک داشتیم، محتاطانه کلیک می‌کنیم — کلیک تکراری بی‌خطر است، ولی کلیک‌نکردن ناوبری را متوقف می‌کند.
  2. `openOtherTab()` → `navigateToFund()`: ناوبری **گام‌به‌گام با تأیید** (سایر → صندوق‌های مفید → خودِ صندوق).
  3. `tryClickLink()`: کلیک روی `a[href]`/`[role=button]`/`[role=tab]` — با **محافظ امنیتی** که هرگز دکمه‌های «خرید/فروش/برداشت/واریز/انتقال/سفارش» را لمس نمی‌کند.
  4. `dumpNavigationDiagnostics()`: اگر در پایان کلیدواژه پیدا نشد، همهٔ لینک‌های صفحه (`href`+متن) و عناصر صندوقی در لاگ ثبت می‌شوند تا **آدرس واقعی صفحه** لو برود.
- **درس:** ناوبری با کلیک شکننده است؛ ناوبری با URL پایدار است. همیشه شرط «وضعیت» را روی عنصر بسنجید، نه روی کل صفحه.

#### ۸. ⚠️ آتیه در پرتفوی پیدا نمی‌شد — کلیک دوم گم‌شده (v1.4.0)
- **نشانه:** در لاگ، فهرست تب‌های پرتفوی «سایر» را نداشت و آتیه هیچ‌جا نبود؛ فقط سینرژی/دارونو/همسنگ دیده می‌شدند.
- **ریشه:** `easytrader_automation.py` **دو کلیک** می‌زند: اول «سایر»، بعد «صندوق‌های مفید». اپ فقط «سایر» را می‌گشت.
- **درمان:** `openOtherTab()` به دو مرحله تقسیم شد: `clickTab(سایر)` سپس `clickTab(صندوق‌های مفید)`. تابع کمکی `clickTab(texts)` اضافه شد و بررسی می‌کند تب دیده‌شدنی باشد و کلیک تکراری نکند.

#### ۹. ⚠️ دروغ «نشست فعال» — صفحهٔ تبلیغاتی به‌جای پرتفوی (v1.3.0)
- **نشانه:** لاگ می‌گفت «✅ نشست فعال است» ولی آدرس بعدی `https://easytrader.ir/` بود و تب‌های پیداشده منوی سایت تبلیغاتی بودند (`پرتفوی | بازدهی | طرح حامی | دانلود اَپ | ...`)، نه تب‌های پرتفوی.
- **ریشه:** `run()` **اول** صفحهٔ ورود را لود می‌کرد و بعد `performLoginIfNeeded` با شرط شل `url.contains("portfolio-fill") || (url.contains("easytrader") && !body.contains("رمز"))` قضاوت می‌کرد. صفحهٔ تبلیغاتی `https://easytrader.ir/` هر دو شرط را رد می‌کرد (شامل «easytrader» و بدون «رمز») → «نشست فعال» دروغین → `return` بدون لود پرتفوی → هر ۴ لایه روی صفحهٔ اشتباه.
- **تفاوت با پایتون:** `easytrader_automation.py` **اول** به `portfolio-fill` می‌رود و **بعد** قضاوت می‌کند (`if "login.emofid.com" not in current_url and "ورود" not in body_text`). اپ برعکس عمل می‌کرد.
- **درمان:** (۱) جریان «پرتفوی-اول»: `run()` مستقیم `PORTFOLIO_URL` را لود می‌کند. (۲) `isOnPortfolio()` سختگیرانه: هاست باید `m.easytrader.ir` + مسیر `portfolio` داشته باشد و صفحهٔ ورود/تأیید نباشد. (۳) `dismissModals()` بستن پاپ‌آپ‌ها. (۴) اگر پس از ورود هم به پرتفوی نرسیدیم → `IllegalStateException` با آدرس واقعی.
- **درس:** تشخیص «وضعیت» را هرگز با شرط شلِ زیررشته‌ای روی دامنه انجام نده؛ دامنهٔ تبلیغاتی و زیردامنهٔ اپ (که زیررشتهٔ هم‌نام دارند) با `contains` از هم تفکیک نمی‌شوند.

#### ۱۰. ⚠️ بحرانی‌ترین باگ — WebView به صفحه اضافه نمی‌شد (v1.2.0)
- **نشانه:** همهٔ چهار لایهٔ استخراج شکست می‌خوردند، در حالی که لاگ می‌گفت «نشست فعال است» و هیچ لاگی از `openOtherTab` نبود.
- **ریشه:** در `MainActivity` کال‌بک این بود `{ /* WebView آماده شد */ }` و **هیچ‌جا `addView(webView)` صدا زده نمی‌شد.** یک WebView وصل‌نشده به پنجره، layout/render ندارد و **`document.body.innerText` رشتهٔ خالی برمی‌گرداند** (`innerText` به رندر نیاز دارد، برخلاف `textContent`). پس هر ۴ لایه روی متن خالی کار می‌کردند.
- **دو مدرک از لاگ:** (۱) «نشست فعال» → یعنی `bodyText()` خالی بود و شرط `!body.contains("رمز")` برقرار شد. (۲) پیام «تب سایر باز شد» غایب بود → `openOtherTab` عنصری ندید.
- **درمان:** ریشهٔ `activity_main.xml` از `ScrollView` به `FrameLayout` تغییر کرد + پنل `automationPanel` شامل `webViewContainer` (و `txtWebStatus`). در `MainActivity.attachAutomationWebView()` نمونهٔ WebView داخل کانتینر قرار می‌گیرد و پنل `VISIBLE` می‌شود؛ در `finally` پنل بسته می‌شود. **درس:** هر WebView اتوماسیون باید واقعاً به سلسله‌مراتب ویو وصل و دیده شود، وگرنه `innerText` همیشه خالی است.

#### ۱۱. باگ ظریف JSON در خواندن خروجی `evaluateJavascript` (v1.2.0)
- `evaluateJavascript` خروجی رشته‌ای را **JSON-encode** می‌کند: `"{\"inner\":\"خط۱\\nخط۲\"}"`.
- نسخهٔ اول `JSONObject(diag)` می‌زد → روی نقل‌قول شکست می‌خورد. `unquote` سادهٔ قبلی هم `\n` را زودتر از موعد به newline واقعی تبدیل می‌کرد و JSON را می‌شکست.
- **درمان:** `decodeJsonString()` با `JSONTokener` (ترتیب درست escapeها) در `bodyText`، `scanDom`، `sniffFromNetwork` و `openOtherTab`.

### 📋 لاک‌گذاری فراوان (v1.2.0 — برای عیب‌یابی از راه دور)
- `BODY_TEXT_PROBE`: طول `innerText` و `textContent`، `attached`، اندازهٔ viewport.
- نمونهٔ ۳۰۰ کاراکتر اول متن صفحه.
- `TAB_PROBE`: فهرست همهٔ متن‌های کوتاه صفحه (تب‌ها) — اگر نام تب عوض شد، سریع معلوم می‌شود.
- نتیجهٔ خام هر لایه (`✖ [لایهٔ N] نتیجه‌ای نداد`) + تعداد برخورد کلیدواژه‌ها در متن.
- URL فعلی صفحه پیش از هر استخراج.
- **درس:** در محیطی که به دستگاه کاربر دسترسی نداری، لاگ باید جای چشم تو را بگیرد.

### 🛰️ تزریق زودهنگام شنود شبکه (v1.2.0)
- `WebViewCompat.addDocumentStartJavaScript(webView, SNIFFER_JS, setOf("*"))` در `onPageStarted` — اسکریپت **پیش از** اسکریپت‌های صفحه اجرا می‌شود، پس `fetch` و `XMLHttpRequest` قبل از اولین درخواست SPA بازنویسی می‌شوند (نسخهٔ قبلی فقط `fetch` و فقط بعد از `onPageFinished`).
- XHR هم پوشش داده می‌شود؛ بعضی SPAها از XHR استفاده می‌کنند.

### 🆕 v1.1.0 — امکانات جدید
- **صفحهٔ انتخاب صندوق** (`assets/webapp/index.html`): دو دکمهٔ آتیه/سینرژی. پیش از این مسیر `gold4` در `WebViewActivity` هاردکد بود و سینرژی هیچ راه دسترسی نداشت. دکمهٔ بازگشت هم `canGoBack()` را رعایت می‌کند.
- **دو فیلد «مقدار پایه» در ⚙️:** بدون آن، اولین اجرا «پایه تنظیم نشده» می‌داد. ورودی ارقام فارسی/عربی را هم می‌پذیرد (`digits()`).
- **`cloud-sync.js` داخل assets = stub بی‌اثر:** اپ Local-First است و طبق طراحی از MantleDB استفاده نمی‌کند؛ این فایل فقط ۴۰۴ را رفع می‌کند و هیچ درخواست شبکه‌ای نمی‌فرستد. **فایل اصلی مخزن دست‌نخورده است.**
- **آیکون جدید:** فلش چرخشی (↻) + علامت درصد (%). تولید با Pillow از `/tmp/iconbuild/make_icon.py`. محتوا داخل ناحیهٔ امن آداپتیو (شعاع ≤۳۱٪) — `ic_launcher_foreground` شفاف + پس‌زمینهٔ گرادیان در `ic_launcher`/`ic_launcher_round`.

### 🛠️ بیلد
```bash
export JAVA_HOME=/tmp/androidbuild/jdk17
export ANDROID_HOME=/tmp/androidbuild/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH=$JAVA_HOME/bin:/tmp/androidbuild/gradle-8.7/bin:$PATH
cd fund-automation-android
gradle testDebugUnitTest assembleDebug assembleRelease --no-daemon
```
خروجی: `app/build/outputs/apk/{release,debug}/`
بیلد خودکار: `.github/workflows/build_fund_apk.yml` (workflow_dispatch + push روی `main`/`S-15`).

#### 🔑 کلید امضای پایدار (Signing Key) — حل باگ «بسته با بستهٔ موجود تداخل دارد»
- **نشانه:** هنگام نصب APK جدید، اندروید می‌گفت «برنامه نصب نشد چون بسته با بستهٔ موجود تداخل دارد».
- **ریشه:** APK قبلی با **debug keystore** امضا شده بود که در `/tmp` بود و **پاک شد**. پس بیلد جدید یک `debug.keystore` **تازه** ساخت (SHA-256 متفاوت) → اندروید نصب را رد کرد. این مشکل **هر بار** تکرار می‌شد چون کلید debug موقتی است.
- **درمان:** یک **کلید release پایدار** ساخته شد (`emarat-fund.keystore`، RSA 2048، اعتبار ۱۰۰۰۰ روز، alias=`emarat-fund`) و APK release با آن امضا می‌شود.
- **فایل‌های حساس (در `.gitignore` — هرگز commit نشوند):**
  - `fund-automation-android/emarat-fund.keystore`
  - `fund-automation-android/keystore.properties`
  - تأیید: `git check-ignore -v <path>` باید هر دو را نشان دهد.
- **بیلد محلی امضاشده:**
  ```bash
  cd fund-automation-android
  gradle assembleRelease --no-daemon
  # خروجی: app/build/outputs/apk/release/app-release.apk
  # تأیید امضا:
  apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk
  ```
- **GitHub Secrets لازم** (تا بیلد Actions هم امضاشده باشد):
  `ANDROID_KEYSTORE_BASE64` (کلید به base64)، `ANDROID_STORE_PASSWORD`، `ANDROID_KEY_ALIAS` (`emarat-fund`)، `ANDROID_KEY_PASSWORD`.
- **⚠️ محدودیت قطعی (غیرقابل دور زدن):** امضا بخشی از **هویت** اپ است. اگر اپ نصب‌شده با کلید A امضا شده باشد، فقط APKی با **همان کلید A** روی آن آپدیت می‌شود. اگر کلید A گم شده باشد، **هیچ راهی** برای آپدیت بدون حذف نصب وجود ندارد — نه با Android Studio، نه با ابزار دیگر. تنها راه: حذف اپ و نصب مجدد (دادهٔ محلی اپ پاک می‌شود؛ تاریخچهٔ صندوق‌ها در بکاپ گیت‌هاب سالم می‌ماند).
- **درس:** کلید امضا را **هرگز** در `/tmp` نگه ندار. از روز اول یک کلید release بساز و در GitHub Secrets ذخیره کن. `debug.keystore` برای انتشار مناسب نیست.

#### ⚠️ درس گران‌بها: محیط بیلد `/tmp` **موقتی** است
در 1405/08/27 پوشهٔ `/tmp/androidbuild` (JDK 17 + Android SDK + Gradle) **به‌کلی پاک شد** — چون `/tmp` موقتی است. **کدها در گیت سالم ماندند** (این ارزش «همه‌چیز در گیت» را ثابت کرد)، ولی بیلد محلی از صفر لازم شد.

**بازسازی سریع محیط (۳ دانلود):**
```bash
mkdir -p /tmp/androidbuild && cd /tmp/androidbuild
# ۱) JDK 17
curl -sL -o jdk.tar.gz "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk"
tar xzf jdk.tar.gz && mv jdk-17* jdk17
# ۲) Gradle 8.7 (unzip نصب نیست → با پایتون استخراج کن)
curl -sL -o gradle.zip "https://services.gradle.org/distributions/gradle-8.7-bin.zip"
python3 -c "import zipfile; zipfile.ZipFile('gradle.zip').extractall('.')"
# ۳) Android cmdline-tools + SDK
curl -sL -o cmdtools.zip "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
python3 -c "import zipfile; zipfile.ZipFile('cmdtools.zip').extractall('android-sdk-tmp')"
mkdir -p android-sdk/cmdline-tools && mv android-sdk-tmp/cmdline-tools android-sdk/cmdline-tools/latest
chmod +x android-sdk/cmdline-tools/latest/bin/*
export JAVA_HOME=/tmp/androidbuild/jdk17; export PATH=$JAVA_HOME/bin:$PATH
yes | android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$PWD/android-sdk \
  "platform-tools" "platforms;android-34" "build-tools;34.0.0"
chmod +x gradle-8.7/bin/gradle
echo "sdk.dir=/tmp/androidbuild/android-sdk" > <repo>/fund-automation-android/local.properties
```
**نکات:** `unzip` در این محیط نصب نیست → از `zipfile` پایتون استفاده کن. `sdkmanager` و `gradle` بدون `chmod +x` خطای Permission denied می‌دهند. `local.properties` در `.gitignore` است و باید دستی ساخته شود.
**راه امن‌تر:** به‌جای بیلد محلی، از **GitHub Actions** استفاده کن — روی سرور گیت‌هاب اجرا می‌شود و به این محیط وابسته نیست.

### 🐛 نکات و تله‌ها
- `local.properties` (شامل `sdk.dir`) باید در `.gitignore` باشد (اینجا هست).
- الگوی `*.png` در `.gitignore` آیکون‌های mipmap را نادیده می‌گرفت → استثنا اضافه شد:
  `!fund-automation-android/app/src/main/res/mipmap-*/ic_launcher*.png`
- در پوشهٔ `drawable` نباید هم `ic_launcher_foreground.png` و هم `.xml` باشد (تعارض AAPT).
- رمز و توکن‌ها **فقط** در `SessionStore` (رمزنگاری‌شده) — هیچ‌گاه hardcode یا در گزارش.

---

## 📱 اپ اندروید اتوماسیون صندوق‌ها (`fund-automation-android/`)

### معماری
- **applicationId:** `ir.omarat.fundautomation` | versionName 1.7.0 (versionCode 8)
- minSdk 24 / targetSdk 34 | Kotlin + WebView + Room-less (SharedPreferences + فایل JSON)
- ورود به ایزی‌تریدر: WebView واقعی + رمز ذخیره‌شده در `EncryptedSharedPreferences` (Android Keystore)
- OTP دستی از کاربر | کوکی نشست در WebView باقی می‌ماند
- فقط دکمهٔ «▶️ شروع اتوماسیون» (بدون زمان‌بندی، طبق تصمیم کاربر)

### 🐛 باگ بحرانی استخراج — جداکنندهٔ هزارگان فارسی (v1.7.0)
- **ریشه:** `toEnglishDigits` فقط ارقام را تبدیل می‌کرد، ولی `٬` (U+066C) و `،` (U+060C) را نه. پس «۲۲۰٬۳۵۱٬۲۶۰» → «220٬351٬260» و regex `[\d,]{6,}` هیچ عددی پیدا نمی‌کرد → **هر چهار لایهٔ استخراج می‌شکست**، حتی وقتی صفحهٔ درست باز بود.
- **درمان:** کلاس خالص `FundTextScanner` (بدون Android) که نرمال‌سازی را انجام می‌دهد: ارقام فارسی/عربی → لاتین، `٬`/`،` → `,`، حذف فاصلهٔ نازک/نیم‌فاصله/کنترل RTL. **نقطهٔ اعشار دست‌نخورده می‌ماند** (تبدیل `.` به `,` باعث عدد غلط در درصدها می‌شد).
- **تست:** `FundTextScannerTest` — ۱۲ تست با دادهٔ واقعی اسکرین‌شات‌های کاربر (۳۹۷٬۶۱۵٬۸۶۹ آتیه و ۲۲۰٬۳۵۱٬۲۶۰ سینرژی).

### 🗺️ ناوبری — دو صندوق در دو صفحهٔ متفاوت
- **سینرژی (۵)** روی **پرتفوی** (`/portfolio-fill`) است، در جدول نمادها. **نباید از پرتفوی خارج شد.** نسخهٔ پیشین همیشه اول به تب «سایر» می‌رفت → سینرژی هرگز خوانده نمی‌شد.
- **آتیه (۴)** روی **صندوق‌های مفید** (`/menu/funds`) است. با `loadUrl` **مستقیم** می‌رود؛ کلیک روی `span` در SPA ناوبری نمی‌کند (درس گران‌بهای v1.6.0).
- **الگوی ستونی:** در پرتفوی، «ارزش فعلی» بزرگ‌ترین عدد ۶رقمی+ پنجره تا نماد بعدی («همسنگ») است. در صندوق‌ها، مرز پنجرهٔ آتیه «ممتاز»/«امید توسعه» است تا اعداد صندوق‌های دیگر قاطی نشوند.

### 🔐 ترتیب طلایی OTP (از `easytrader_automation.py`)
۱. کد را در فیلد بگذار → ۲. تیک «تایید دو مرحله برای این سیستم لازم نیست» را بزن → ۳. **آخر** فرم را ارسال کن.
نسخهٔ پیشین اول submit می‌کرد و بعد تیک می‌زد؛ صفحه عوض می‌شد و تیک هرگز زده نمی‌شد → هر بار OTP دوباره.

### 🚫 جلوگیری از ثبت تکراری
`WebAppReader` درصدهای وب‌اپ را می‌خواند؛ اگر کاربر امروز **دستی** ثبت کرده باشد (`source != "automation"`)، اتوماسیون آن صندوق را دست‌نخورده رها می‌کند. ثبت‌های خودِ اتوماسیون نادیده گرفته می‌شوند تا دوباره‌اجرا در همان روز مسدود نشود.

### 📦 پشتیبان‌گیری و بازیابی داخل اپ
- `LocalBackupManager`: فایل JSON در `filesDir/backups/` با نام `fund-backup-<stamp>-<manual|auto>.json`؛ نگه‌داشت ۲۰ تای آخر.
- `WebAppWriter.readKeys/writeKeys`: خواندن/نوشتن `localStorage` وب‌اپ (origin جداگانه).
- **قبل از هر بازیابی، یک بکاپ ایمنی (`-auto`) از وضعیت فعلی گرفته می‌شود.**
- اشتراک‌گذاری بکاپ با `FileProvider` (`${applicationId}.fileprovider` + `res/xml/file_paths.xml`).
- بازیابی هم قالب خود اپ (`{data:{...}}`) و هم قالب خام بکاپ وب‌اپ‌ها را می‌پذیرد.

### 🎨 استایل اعداد پایه
`txtAtieBase`/`txtSynergyBase` = ۲۱sp سبز پررنگ | `txtAtiePercent`/`txtSynergyPercent` = ۲۶sp سبز پررنگ. برچسب‌های کوچک («مقدار پایه» / «آخرین درصد») بالای اعداد.

### 🏗️ بیلد
```bash
export JAVA_HOME=/tmp/androidbuild/jdk17
export ANDROID_HOME=/tmp/androidbuild/android-sdk
export PATH=/tmp/androidbuild/gradle-8.7/bin:$JAVA_HOME/bin:$PATH
gradle test assembleRelease assembleDebug --no-daemon
```
خروجی: `app/build/outputs/apk/{release,debug}/` | امضا: `emarat-fund.keystore` + `keystore.properties`
- **تست:** ۲۳ تست JVM (دیباگ) / ۴۶ در کل — همه پاس.

### 🐛 باگ «درصد ۰.۰۰٪» و بی‌دقتی گرد کردن (v1.8.0)
سه ریشهٔ هم‌زمان باعث می‌شد درصد واقعی صفر دیده شود:
1. **گرد کردن پیش از ذخیره:** `FundCalculator` درصد را با `roundTo2` گرد می‌کرد. تغییر واقعی سینرژی `+0.003428%` بود (۷٬۵۱۱ ریال روی پایهٔ ۲۱۹ میلیونی) → با ۲ رقم اعشار **صفر** می‌شد و همان صفر در `percents[].value` ذخیره می‌گشت. **درمان:** دقت ۶ رقم حفظ می‌شود؛ گرد کردن فقط هنگام نمایش.
2. **نمایش با دو رقم ثابت:** `%.2f` همان مقدار ریز را «۰.۰۰٪» نشان می‌داد. **درمان:** `PercentFormatter` با **دقت تطبیقی** (۰٫۰۱٪→۴ رقم، ۱٪→۳ رقم، بزرگ‌تر→۲ رقم). «۰٫۰۰٪» دیگر نمایش داده نمی‌شود مگر تغییر واقعاً صفر باشد.
3. **ذخیرهٔ درصد گردشده در وب‌اپ:** فیلد `percents[].value` همان رشتهٔ `%.2f` را می‌گرفت. **درمان:** فیلد جدید `rawPercent` با دقت ۶ رقم در کنار `percent` نمایشی؛ هم در `localStorage` و هم در بکاپ.

**نکتهٔ مهم:** آتیه واقعاً ۰٪ بود، نه باگ — تاریخ «بروز رسانی دارایی» در صفحه `1405/08/25` بود (منبع هنوز عدد تازه نداده). حالا این تاریخ در گزارش می‌آید و اگر پایه=جدید باشد، گزارش صریح می‌گوید «مقدار منبع تغییر نکرده؛ صفر درصد درست است».

### 📚 پایه از تاریخچهٔ وب‌اپ خوانده می‌شود (v1.8.0)
- `WebAppReader.lastHistoryBase()` آخرین مقدار پایه را از آرایهٔ `history` وب‌اپ می‌خواند (منبع حقیقت واحد)، چون کاربر ممکن است داخل خود صفحهٔ وب‌اپ دستی ثبت کرده باشد و اپ بی‌خبر باشد.
- هر دو شکل رکورد پوشش داده می‌شود: `rawNew` (عدد خام اپ‌های `calculator`) و `new` (رشتهٔ جداکننده‌دار اپ‌های `percent`). بزرگ‌ترین تایم‌استمپ برنده است، نه آخرین ایندکس.
- اگر تاریخی نبود، به `prefs` اپ برمی‌گردد (fallback).

### ⏳ انتظار هوشمند هیدریشن (v1.8.0)
- `awaitNumbersReady()` جای تأخیر ثابت ۸ ثانیه را گرفت: تا آمدن **اولین عدد معتبر** صبر می‌کند (سقف ۳۰ ثانیه) و در این فاصله هر ۵ ثانیه مودال‌ها را می‌بندد.
- **علت:** در لاگ واقعی، پرتفوی ساعت ۱۱:۵۰:۲۶ همه‌چیز **صفر** نشان می‌داد و فقط ۱۱:۵۰:۴۰ درست شد. تأخیر ثابت ۸ ثانیه کافی نبود.

### 🪟 مقاوم‌سازی پنجرهٔ استخراج (v1.8.0)
- پنجرهٔ سینرژی دیگر فقط به «همسنگ» تکیه نمی‌کند: مرزهای پایان `همسنگ`/`خرید`/`فروش`/`کل دارایی`/`یادداشت`/`هشدار`/`سود و زیان`.
- پنجرهٔ آتیه هم مرزهای بیشتر: `ممتاز`/`امید توسعه`/`سایر صندوق‌های مفید`/`تاریخ بروز رسانی`.
- **علت:** لایهٔ شنود API در اجرای واقعی هر دو بار شکست خورد (۳۲۷۶ و ۸۹۰۱ کاراکتر بود ولی عدد معتبر نداشت) و فقط اسکن متن نجات داد.

### 🧪 تست‌ها (v1.8.0)
- **۳۷ تست JVM** (دیباگ) — قبلاً ۲۳ بود. فایل‌های جدید: `PercentPrecisionTest` (۷ تست دقت درصد با عدد واقعی ۷٬۵۱۱ ریال) و `FundWindowResilienceTest` (۷ تست پایداری پنجره + تاریخ منبع).

### 💥 باگ بحرانی «هر دو صندوق دست‌نخورده رها شد» + «پایهٔ سینرژی = عدد آتیه» (v1.9.0)
سه ریشهٔ هم‌زمان که با هم لاگ «اتوماسیون هیچ کاری نکرد» را ساختند:
1. **پایهٔ سینرژی، عدد آتیه شد.** صفحات وب‌اپ روی `file://` هستند و در WebView اندروید **همه یک origin مشترک** دارند، پس `localStorage` مشترک است. اسکریپت خواندن مشترک (`READ_SCRIPT`) همیشه اول `mofid_atie_history` را می‌خواند و برای صفحهٔ سینرژی هم همان را برمی‌گرداند. **درمان:** اسکریپت جدا برای هر صندوق (`ATIE_READ_SCRIPT` / `SYNERGY_READ_SCRIPT`) + پارامتر الزامی `fund` در `WebAppReader.manualEntries/lastHistoryBase`.
2. **«امروز دستی ثبت شده» دروغین.** `manualEntries` نامش «دستی» بود ولی فیلتر `manual` را اعمال نمی‌کرد و **همهٔ** رکوردها را برمی‌گرداند؛ پس رکورد خودِ اتوماسیون (`source=automation`) هم «ثبت دستی امروز» شمرده می‌شد و اپ خودش را رد می‌کرد. **درمان:** `.filter { it.manual }`.
3. **استخراج آتیه هرگز اجرا نشد** — نتیجهٔ زنجیره‌ای باگ ۲ (هر دو صندوق `skip` شدند).

**افزوده‌های v1.9.0 (موتور محاسبهٔ خود وب‌اپ):**
- فایل جدید `WebAppCalculator.kt`: صفحهٔ `goldN/calculator.html` را در WebView باز می‌کند، دو عدد را در فیلدهای خودش می‌گذارد و **تابع خودش** (`calculateAndSave(false)`) را صدا می‌زند تا **نوع تغییر** (increase/recovering/decrease) و **قله** عیناً از منطق وب‌اپ بیاید. درصد همچنان با **دقت ۶ رقم از اپ** محاسبه می‌شود (وب‌اپ فقط `toFixed(2)` می‌دهد و همان باگ «۰٫۰۰٪» بود).
- `calculateAndSave(false)` یعنی **تاریخچه را وب‌اپ نمی‌نویسد**؛ نوشتن با اسکریپت اپ انجام می‌شود تا فیلد `source=automation` حفظ شود. اگر مستقیم `addPercent()` صدا زده می‌شد، رکورد **بدون `source`** ذخیره می‌شد و باگ تشخیص تکراری **برمی‌گشت**.
- `WebAppStore.buildInjectScript` پارامتر `peak: Long?` گرفت و قله را در `pension_peakNumber`/`sinergy_peakNumber` می‌نویسد (وگرنه قلهٔ موتور وب‌اپ گم می‌شد).
- نگاشت «کلاس CSS → نوع تغییر» در `WebAppCalculator.typeFromClassName` و در **کاتلین** انجام می‌شود (نه در رشتهٔ JS) تا مستقل از مرورگر و قابل تست باشد.
- `FundOutcome` دو فیلد `engineType` و `enginePeak` گرفت؛ `MainActivity` قلهٔ موتور را در `prefs` و در حافظهٔ وب‌اپ هر دو ذخیره می‌کند.
- **تست‌های جدید:** `ManualEntryFilterTest` (۲ تست) + `EngineTypeMappingTest` (۵ تست) → **جمع ۴۴ تست، ۰ شکست**.
- نسخه: versionCode 9→10، versionName 1.8.0→1.9.0؛ امضای APK پایدار (SHA-256: `4603b639...`).


### 🔁 ثبت خودکار درصد در «تب ثبت درصد» (v1.10.0 وب‌اپ)
**مسئله:** کاربر در تب «🏆 محاسبه تغییرات» عدد جدید را می‌زد و درصد فقط در **تاریخچه** ذخیره می‌شد؛ برای دیدن آن در «📊 ثبت درصد» (تب اول) باید دستی هم وارد می‌کرد.

**راه‌حل (گزینهٔ امن با تشخیص تکراری):** بعد از `addToHistory(...)` در هر `goldN/calculator.html`، تابع `syncPercentToList(percentFixed, Date.now())` صدا زده می‌شود و درصد را در **فهرست تب اول** هم می‌نویسد — **فقط اگر** همان **روز شمسی** با همان مقدار (تلورانس ۰٫۰۰۵) قبلاً ثبت نشده باشد.

- **کلید ذخیره‌سازی هر اپ (مهم!):**

| اپ | فایل | کلید فهرست درصد | شکل داده |
|---|---|---|---|
| gold | `gold/` | `percents` | آرایه |
| gold2 | `gold2/` | `kian_percents` | آرایه |
| gold3 | `gold3/` | `stock____________tas9yl_new_unified` | **شیء** (`percents` داخلش) |
| gold4 | `gold4/` | `mofid_atie_percents` | آرایه |
| gold5 | `gold5/` | `energy_fund_synergy` | **شیء** |
| gold6 | `gold6/` | `cement_factory_percents` | **شیء** |
| gold7 | `gold7/` | `ahang_kian_percents` | **شیء** |
| gold8 | `gold8/` | `pharma_kian_percents` | **شیء** |

- **حفظ دادهٔ شیء‌محور:** `writePercentList` شیء را **merge** می‌کند (فقط `percents` را عوض می‌کند) تا `goal`/`notes`/`trash`/`periodTarget`/`achievedPeriods`/`initialCapital` **دست‌نخورده** بمانند.
- **روز شمسی:** با `Intl.DateTimeFormat('fa-IR', {year,month,day})` — همان تقویمی که کاربر می‌بیند (تصمیم تأییدشدهٔ کاربر).
- **رکورد خودکار** با `source: 'automation'` ذخیره می‌شود → در فهرست با نشان 🤖 نمایش داده می‌شود.
- **پیام‌ها:** موفق → «✅ درصد در تب «ثبت درصد» هم ثبت شد»؛ تکراری → «⚠️ این درصد امروز قبلاً در تب ثبت درصد هست».
- **به‌روزرسانی زنده:** در هر `goldN/percent.html` شنوندهٔ `storage` اضافه شد که با تغییر کلید فهرست، `window.__emaratAutoSync()` را صدا می‌زند و فهرست را بدون رفرش به‌روز می‌کند. (gold4 از قبل شنونده داشت → دست‌نخورده.)
- **عدد پایه عمداً خودکار به‌روز نمی‌شود** (تصمیم کاربر: خودش دستی می‌زند).
- **تست:** ۵۸ تست jsdom روی هر ۸ اپ (ثبت، تکراری، حفظ دادهٔ شیء، به‌روزرسانی زنده) + ۱۱ تست منطق خالص — همه موفق.
- **بامپ:** `CACHE_NAME` → `emarat-portal-v82`؛ `gold4/gold5` در `fund-automation-android/.../assets/webapp/` همگام شد.

### 📱 APK اندروید v1.10.0 (نسخهٔ ثبت خودکار درصد)
- `versionCode 10→11`، `versionName 1.9.0→1.10.0` در `fund-automation-android/app/build.gradle`.
- **دلیل نسخه:** assets وب‌اپ (`gold4`/`gold5`) با قابلیت «ثبت خودکار درصد در تب ثبت درصد» همگام شدند.
- **امضای APK پایدار:** SHA-256 گواهی `4603b639c0ed4480630c6db3598e5112f97b85f4aed6ac55d501b886b94e9585` (بدون تغییر نسبت به v1.9.0) → **نصب درجا روی نسخهٔ قبلی کار می‌کند** و `localStorage` کاربر حفظ می‌شود.
- **بیلد محلی (بدون VPN):** `JAVA_HOME=/tmp/androidbuild/jdk17`, `ANDROID_HOME=/tmp/androidbuild/android-sdk`, `gradle` از `/tmp/androidbuild/gradle-8.7/bin`. خروجی: `app/build/outputs/apk/{release,debug}/`.
- **تأیید محتوا:** با `zipfile` پایتون چک شد که `assets/webapp/gold4|gold5/{calculator,percent}.html` کد جدید (`syncPercentToList`, `__emaratAutoSync`) را دارند.
- **تحویل:** APK در `.gitignore` است (`*.apk`)؛ پس از طریق **GitHub Release** منتشر می‌شود (مثل نسخه‌های قبلی)، نه کامیت.

---

## 🌾 اپ «ثبت درصد ۹» — سهم غبهار (gold9/) — آیکون‌های تصویری اختصاصی

### هویت
- **نام درون‌برنامه:** «سهم غبهار» (`.brand-title`) + زیرعنوان «کشت وصنعت بهاران گلبهار خراسان» (`.brand-subtitle`).
- **`<title>`:** `ثبت درصد 9 · سهم غبهار` | `manifest.name`: `ثبت درصد 9` (بدون کلمهٔ حساس).
- **کلیدهای ذخیره‌سازی:** `baharan_percents` (شیء: percents/trash/goal/notes/…)، `baharan_history`، `baharan_baseNumber`، `baharan_peakNumber`.
- **مانیتور:** از قبل پشتیبانی می‌شود — `MONITOR_HISTORY_KEYS[9] = "baharan_history"` و `localStorage.getItem("baharan_percents")` در `getAllAppsPercentData()`.

### 📦 خط تولید دارایی تصویری (۲۱ خانه از ۲ شیت)
- شیت A (۴×۳ = ۱۲ آیکون کوچک) + شیت B (۳×۳ = ۹ بنر) + ۱ پس‌زمینه.
- **دام بزرگ هاله (halo):** مدل دور هر خانه یک **کارت تیره** کشیده بود؛ آستانهٔ آلفای سست (lo=10) آن را نیمه‌شفاف نگه می‌داشت و روی پس‌زمینهٔ روشن «هاله» می‌شد. آستانهٔ نهایی: **lo=55, hi=105** (رمپ آلفا) + decontamination رنگ لبه. فاصلهٔ رنگی گاتر: p95 ≈ ۴۸.
- **اعتبارسنجی برش با roundtrip** (بازسازی تصویر از روی برش‌ها): خطای ۰.۱–۰.۶ از ۲۵۵، محتوای گم‌شده < ۰.۵٪. **متریک «halo%» گمراه‌کننده بود** (سایهٔ طبیعی اجسام را هم می‌شمرد) — به‌جایش از roundtrip و بازبینی بصری استفاده کن.
- خروجی: `gold9/assets/a01..a12.png` + `aNN@2x.png` + `b01..b09.webp` (۳۳ فایل، ~۷۹۵KB).

### 🎯 نگاشت آیکون → جای UI (تأییدشده با تحلیل ASCII/shape، نه حدس)
| # | محتوا | جای استفاده |
|---|---|---|
| a01 | دفتر/لیست | تب «ثبت درصد» |
| a02 | نمودار ستونی | تب «محاسبه تغییرات» + هدر باکس آمار |
| a03 | برچسب | تب «ثبت ابطال» |
| a04 | نمودار رشد صعودی | تب «مدیریت رشد» |
| a05 | سکه | کارت «سود کل» |
| a06 | ماشین‌حساب | کارت «تعداد معاملات» |
| a07 | مدال | کارت «بهترین معامله» |
| a08 | فلش رو به بالا (زیتونی) | حالت `increase` در تاریخچه |
| a09 | فلش بازگشتی | حالت `neutral` |
| a10 | فلش رو به پایین (نارنجی) | حالت `decrease` |
| a11 | قله/کوه | برچسب «بالاترین عدد ثبت‌شده / قله» |
| a12 | ابر | دکمه‌های بکاپ/گیت‌هاب |

### 🖼️ جای بنرها
- `b01` → empty-state فهرست درصد (بالای پیام «هنوز درصدی ثبت نشده»)
- `b02` → هدر صفحهٔ `calculator.html`
- `b03` → هدر صفحهٔ `price.html`
- `b04` → هدر صفحهٔ `growth.html`
- `b05..b09` فعلاً استفاده نشده (رزرو برای بخش‌های آینده) — ولی در `ASSETS` کش می‌شوند.

### 🎨 کنتراست روی پس‌زمینهٔ روشن (مهم)
- پس‌زمینهٔ هنری **روشن** است: میانگین روشنایی ۱۲۴، اوج ۲۴۶. متن اپ روشن است (`--text-dark: #f6f8e8`).
- **راه‌حل: کارت ۹۲٪ کدر کافی است — overlay لازم نیست.** محاسبهٔ بدترین حالت (پس‌زمینهٔ ۲۴۶ زیر کارت): کنتراست متن **۱۰.۲** (حد AA = ۴.۵). با overlay 0.3 به ۱۱.۲ می‌رسد ولی چون ۱۰.۲ از قبل عالی است، overlay اضافه نشد (تصویر تمیزتر می‌ماند).
- `index.html` (پوستهٔ تب‌ها) پس‌زمینه ندارد چون **iframe کاملاً آن را می‌پوشاند** (تأییدشده: ۳۹۰×۷۴۵ هر دو) و پس‌زمینه از خود iframe می‌آید.

### 🐛 دو کنتراست شکسته که در همین کار رفع شد
| دکمه | قبل | بعد | نسبت |
|---|---|---|---|
| «ذخیره» تنظیمات گیت‌هاب (percent) | `#7fa336` | `#5f7d24` | ۲.۹۲ → **۴.۷۲** |
| حذف تاریخچه (calculator/price) | `#ef4444` | `#c53030` | ۳.۷۶ → **۵.۴۷** |
- **درس:** `#7fa336` و `#ef4444` با متن سفید **زیر استاندارد AA** هستند. برای سبز برند از `#5f7d24` و برای قرمز خطر از `#c53030` استفاده کن.
- **مثبت کاذب در تست کنتراست:** دکمه‌های گرادیانی (`background-image` بدون `background-color`) و دکمه‌های ایموجی‌محور (مثل 💡) را نادیده بگیر.

### ⚠️ دام `.gitignore` (تکرار همان درس اندروید)
الگوی `*.png` در `.gitignore` **همهٔ ۳۳ آیکون را نادیده می‌گرفت**. استثنای صریح اضافه شد:
```
!gold9/assets/*.png
```
**همیشه بعد از افزودن دارایی تصویری:** `git add -An <dir>` بزن و بشمار — اگر تعداد صفر یا کمتر از انتظار بود، استثنا لازم است.

### 🔌 اتصال کامل (تأییدشده)
| مسیر | وضعیت |
|---|---|
| پورتال `index.html` → `{id:'gold9', title:'ثبت درصد 9', url:'gold9/index.html'}` | ✅ از قبل |
| `sw.js` ASSETS + `CACHE_NAME` | ✅ ۳۳ دارایی اضافه، v85 → **v86** |
| `cloud-sync.js` در `gold9/index.html` | ✅ از قبل (`../cloud-sync.js`) |
| بکاپ گیت‌هاب (`triggerAutoGithubSync` با debounce ۱s) | ✅ از قبل، فایل `gold9_backup.json` |
| `autoSyncFromBackup()` از `gold9_backup.json` | ✅ از قبل |
| مانیتور (`monitor/index.html`) | ✅ از قبل (app id 9) |
| شاخهٔ استقرار | `S-17` → merge در `main` → GitHub Pages |

### ✅ چک‌لیست تست این اپ
1. `document.images` → `broken` باید خالی باشد در هر ۵ صفحه.
2. ثبت درصد از UI → `baharan_percents` باید **همهٔ** کلیدها را داشته باشد (`percents, trash, goal, notes, highlightedStates, periodTarget, achievedPeriods`).
3. حذف آخرین درصد → `.empty-state` با بنر `b01.webp` و `naturalWidth > 0`.
4. آفلاین واقعی: سرور را خاموش کن، رفرش کن → عنوان/زیرعنوان/۴ تب باید بیایند.
5. کنتراست: بدترین حالت ≥ ۴.۵ (اینجا ۱۰.۲).

---

## 📥 قابلیت «ورود قیمت ابطال از فایل سایت» (price-import.js)

### دامنهٔ پوشش
فقط اپ‌هایی که **تب «ثبت ابطال»** دارند: `gold3`, `gold5`, `gold6`, `gold7`, `gold8`, `gold9`.
`gold`, `gold2`, `gold4` این تب (و فایل `price.html`) را ندارند → این قابلیت هم ندارند.

### قانون طلایی: کپی محض عدد
عدد دقیقاً همان‌طور که در فایل اکسل است ذخیره می‌شود. **هیچ تقسیم، ضرب، تبدیل ریال↔تومان یا گرد کردن انجام نمی‌شود.**
اگر مقیاس اعداد فایل با دادهٔ موجود خیلی فرق کند (بیش از ۸ برابر)، فقط یک **هشدار** نشان داده می‌شود و کاربر خودش تصمیم می‌گیرد.

### تشخیص ستون قیمت (به ترتیب اولویت)
1. ستونی که هم `قیمت` دارد هم `ابطال` → مثلاً `قیمت ابطال واحد ممتاز` در غبهار (`51938`)
2. ستونی که هم `NAV` دارد هم `ابطال` → مثلاً `NAV ابطال` در دارونو/سیمان
3. هر ستون `ابطال` که `ارزش|تعداد|بازدهی` نباشد
- غلط تایپی رایج سایت `ابظال` (ظ به‌جای ط) هم پذیرفته می‌شود.
- فایل‌هایی که فقط درصد بازدهی دارند (مثل `DailyAssetStructure.xlsx`) → پیام واضح و رد.

### منطق ضدتکرار
- کلید مقایسه: **تاریخ شمسی نرمال‌شده** (`YYYY.MM.DD`، صفر پیشرو اجباری).
- ۴ وضعیت: `new` (🟢 بعد از آخرین تاریخ) / `duplicate` (🟡 همان تاریخ قبلاً ثبت شده) / `old` (🟠 قبل از آخرین تاریخ) / `invalid` (🔴 قیمت نامعتبر).
- فقط `new`ها ثبت می‌شوند؛ هیچ رکوردی بازنویسی یا حذف نمی‌شود.
- رکورد واردشده: `{id, date, timestamp, price, source:'excel-import'}`.
- دکمهٔ ثبت وقتی `new === 0` باشد **غیرفعال** است.

### خواندن فایل بدون CDN
`JSZip` از `vendor/jszip/jszip.min.js` (همان نسخهٔ مخزن) — `xlsx` یک zip است و با `DOMParser` پارس می‌شود. هیچ وابستگی خارجی ندارد.
مسیرها **نسبی** هستند: `../vendor/jszip/jszip.min.js` و `../price-import.js` (فایل در ریشهٔ مخزن است، مشترک بین همهٔ اپ‌ها).

### تم‌دهی
ماژول از CSS Variable استفاده می‌کند: `--pi-accent`, `--pi-accent-fg`, `--pi-border`, `--pi-head-bg`, `--pi-drop-bg`, `--pi-hot-bg`.
هر اپ رنگ خودش را در `mount({accent, accentFg})` می‌دهد:

| اپ | accent | accentFg |
|---|---|---|
| gold3 | `#60a5fa` | `#04203a` |
| gold5 | `#47cfb1` | `#06251f` |
| gold6 | `#3bc9b0` | `#0a2f28` |
| gold7 | `#a78bfa` | `#1b1035` |
| gold8 | `#14b8a6` | `#032726` |
| gold9 | `#a3b544` | `#1b2410` |

### نحوهٔ mount در هر price.html
```html
<script src="../vendor/jszip/jszip.min.js"></script>
<script src="../price-import.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function () {
  window.EmaratPriceImport.mount({
    container: document.querySelector('.container'),
    storageKey: STORAGE_PRICES,
    getPrices: function () { return getPrices(); },
    savePrices: function (list) { savePrices(list); },
    accent: '...', accentFg: '...'
  });
});
</script>
```
کارت با `container.appendChild` به **انتهای** `.container` اضافه می‌شود و پیش‌فرض **بسته** است.

### API عمومی
`window.EmaratPriceImport.mount(opts)` + `window.EmaratPriceImport._internal` برای تست:
`normDate`, `parseNumber`, `detectColumns`, `extractRows`, `classify`, `unitMismatch`, `readWorkbook`, `lastSavedDate`.

### همگام‌سازی اندروید
assets وب‌اپ اندروید (`fund-automation-android/app/src/main/assets/webapp/`) فقط `gold4` و `gold5` را دارد.
پس فقط این‌ها لازم است همگام بمانند:
- `price-import.js`
- `vendor/jszip/jszip.min.js`
- `gold5/price.html`

### چک‌لیست پس از تغییر
1. `grep -c "price-import.js" <app>/price.html` باید ۱ باشد در ۶ اپ.
2. `grep -rnE '<(link|script)[^>]*(href|src)="https?://' --include=*.html .` → صفر.
3. `CACHE_NAME` در `sw.js` بامپ شود (الان `emarat-portal-v87`).
4. تست واقعی با Puppeteer/Chromium روی `file://` یا سرور محلی: آپلود فایل نمونه → پیش‌نمایش درست → ثبت → آپلود دوباره → همه 🟡 و دکمه غیرفعال.

### نتایج تست واقعی (۶ اپ)
| اپ | ستون تشخیص‌داده‌شده | ردیف جدید | آخرین قیمت |
|---|---|---|---|
| gold3 | `NAV ابطال` | ۱۱ | ۱۲٬۹۷۱ |
| gold5 | `NAV ابطال` | ۱۱ | ۱۲٬۹۷۱ |
| gold6 | `NAV ابطال` | ۱۱ | ۱۲٬۹۷۱ |
| gold7 | `NAV ابطال` | ۱۱ | ۱۲٬۹۷۱ |
| gold8 | `NAV ابطال` | ۱۱ | ۱۲٬۹۷۱ |
| gold9 | `قیمت ابطال واحد ممتاز` | ۱۱ | ۵۱٬۹۳۸ |

---

## 🔄 دکمهٔ «به‌روزرسانی» سراسری (refresh-button.js)

> ⚖️ **قانون اساسی الزام‌آور:** [قانون اساسی دکمهٔ «به‌روزرسانی»](#-قانون-اساسی-دکمهٔ-بهروزرسانی-سراسری-the-refresh-button-constitution) — هر اپ جدید **باید** این دکمه را داشته باشد و رفتارش دقیقاً همان استاندارد زیر باشد. این بخش فقط جزئیات پیاده‌سازی است.

### هدف
هر وقت سایت آپدیت شد، کاربر با **یک ضربه** نسخهٔ تازه را می‌گیرد؛ بدون رفتن به تنظیمات مرورگر و بدون پاک‌کردن داده‌ها.

### محل و ظاهر — «از زیر لبهٔ صفحه بیرون می‌آید»
- **پایین‌وسط**، `position: fixed` (با اسکرول جابه‌جا **نمی‌شود**)، `z-index: 2147483000`
- **پیش‌فرض کاملاً پنهان** است: `transform: translate3d(0, 110%, 0)` → دکمه دقیقاً زیر لبهٔ پایین viewport قرار می‌گیرد (نه نیمه‌پیدا).
- **حالت باز:** کلاس `.emr-rb.open` → `transform: translate3d(0,0,0)` با انیمیشن `.32s cubic-bezier(.22,.9,.3,1)`.
- متن دکمه شامل **شمارهٔ نسخهٔ کش** است (از `CACHE_NAME` در `sw.js` خوانده می‌شود): `🔄 به‌روزرسانی · v90`

### 🎯 چه زمانی بیرون می‌آید؟
فقط وقتی کاربر **در کف صفحه** است و **یک اسکرول اضافه به پایین** می‌زند:
- `wheel` با `deltaY > 0` → اگر ظرف اسکرول در کف باشد، شمارنده `bottomHits++`؛ با **۲ برخورد متوالی** دکمه باز می‌شود.
- `touchmove` → همان منطق با `dy = touchY - clientY > 0` (انگشت به بالا = اسکرول به پایین).
- اگر صفحه **اصلاً اسکرول ندارد** (کوتاه‌تر از viewport)، هر اسکرول رو به پایین دکمه را باز می‌کند.
- اسکرول رو به بالا (`deltaY < 0`) شمارنده را صفر می‌کند و دکمه را باز نمی‌کند.
- بعد از **۵ ثانیه** (`REVEAL_MS`) خودکار برمی‌گردد زیر لبه — مگر در حالت تأیید یا در حال به‌روزرسانی.

### 🖼️ صفحات iframe-محور (مثل `gold9/`)
**تلهٔ مهم:** `gold9/index.html` خودش اسکرول ندارد؛ همهٔ اسکرول داخل `iframe` (percent/calculator/price/growth) رخ می‌دهد و رویداد `wheel` به پنجرهٔ والد نمی‌رسد.
**درمان:** `bindFrames()` یک هوک کوچک داخل هر `iframe` **هم‌دامنه** تزریق می‌کند (`window.__emrRbHook`) که همان منطق «۲ اسکرول اضافه در کف» را اجرا و با `parent.postMessage({__emrRb:1}, '*')` به والد خبر می‌دهد. والد با `message` listener دکمه را باز می‌کند.
- تزریق در سه زمان انجام می‌شود: بلافاصله، ۱٫۲ ثانیه و ۳ ثانیه بعد + یک `setInterval` هر ۴ ثانیه (چون تب‌ها با `display` عوض می‌شوند و iframe تازه لود می‌شود).
- iframeهای **cross-origin** بی‌صدا رد می‌شوند (`try/catch`) — دکمه آن‌جا فقط با اسکرول خود صفحه کار می‌کند.

### جریان دو مرحله‌ای (ضد کلیک اتفاقی)
1. کلیک اول → `⚠️ مطمئنی؟ دوباره بزن` (۳٫۵ ثانیه مهلت، بعد خودکار لغو)
2. کلیک دوم → پاک‌سازی کش + `unregister` سرویس‌ورکر + `location.replace` با پارامتر `_r=<timestamp>`

### رفتار آفلاین
اگر `navigator.onLine === false` باشد، به‌جای رفرش، پیام `📡 اینترنت قطع است` می‌دهد و کش را پاک **نمی‌کند** (تا کاربر صفحه سفید نبیند).

### 🚨 قاعدهٔ حیاتی: داده‌ها دست‌نخورده می‌مانند
فقط `caches` و `ServiceWorkerRegistration` پاک می‌شوند. **`localStorage`، `IndexedDB`، کوکی و `cloud-sync` هیچ تغییری نمی‌کنند.**
تست واقعی: `localStorage.__probe = 'kept-value'` قبل از رفرش ست شد و بعد از رفرش هم `kept-value` بود ✅

### جلوگیری از تداخل (auto-lift)
اگر دکمه روی یک کنترل بایندد (نوار تایپ چت `#chatInput`، دکمهٔ پایین صفحه و…) بیفتد، کلاس `.emr-rb.lifted` می‌گیرد و ۷۴px بالا می‌رود.
سلکتور کنترل‌ها: `textarea, input, button, select, [contenteditable="true"]` — عناصر کوچک‌تر از ۲۴×۱۶ و نامرئی نادیده گرفته می‌شوند.
زمان‌بندی بررسی: ۶۰ms، ۹۰۰ms، ۲۴۰۰ms بعد از mount + روی `resize`/`orientationchange`/`transitionend` (با debounce ۱۲۰ms).

### نصب در هر صفحه
یک خط قبل از `</body>`:
```html
<script src="../refresh-button.js"></script>   <!-- صفحات زیرپوشه -->
<script src="refresh-button.js"></script>      <!-- index.html ریشه -->
```

### 🐛 دام بزرگ: `</body>` داخل template literal
در `monitor/index.html` و `family/index.html` تابعی وجود دارد که **یک HTML کامل می‌سازد** (سند بانکی / نقشهٔ ذهنی) و آن را در `Blob` می‌ریزد. آن HTML هم `</body>` دارد!
تزریق سادهٔ `s.replace('</body>', ...)` در **اولین** occurrence، اسکریپت را داخل رشتهٔ JS می‌انداخت → `Unexpected end of input` و **دکمه اصلاً mount نمی‌شد**.
**درمان:** همیشه از `s.rfind('</body>')` (آخرین occurrence) استفاده کن، یا بهتر: قبل از `</html>` انتهایی.
**درس:** هر «تزریق اسکریپت» سراسری باید با `rfind` انجام شود، نه `replace` ساده.

### داخل iframe غیرفعال است
`if (window.top !== window.self) return;` — چون پوستهٔ تب‌ها (`goldN/index.html`) خودش دکمه را دارد و دکمهٔ تکراری داخل iframe هم بی‌فایده و هم شلوغ است.
تأییدشده با تست: در هر ۳۵ صفحه، `count === 1` و `inIframe === false`.

### پوشش (۳۵ صفحه، تست‌شده)
`index.html` (پورتال) · `gold`..`gold9` (همهٔ زیرصفحه‌ها) · `gym` · `monitor` · `monthly-deposit` · `profit-calculator` (۴ صفحه) · `html-viewer` (۳ صفحه) · `ai-chat` · `simple-chat` · `clipboard` · `daily-report` · `detective` · `family` · `funds` · `image-enhancer` · `jules-agent` · `jules-bot` · `liquidity` · `peace` · `restricted` · `skincare` · `sync` · `tabdeal` · `vault` · `yandex` · `mockup`

### همگام‌سازی اندروید
- `fund-automation-android/app/src/main/assets/webapp/refresh-button.js`
- `restricted/android/app/src/main/assets/refresh-button.js`
- `restricted/android/app/src/main/assets/restricted/index.html` (کپی `restricted/index.html`)

### چک‌لیست پس از تغییر
1. `grep -c "refresh-button.js" <page>` → دقیقاً **۱** در هر صفحه.
2. تزریق با `rfind('</body>')` — نه `replace`.
3. `CACHE_NAME` بامپ شود (الان `emarat-portal-v90`) — تا خود دکمه هم تازه بیاید.
4. تست Puppeteer: `count===1`، `inIframe===false`، `opacity==='0.2'`، هاور → `opacity==='1'`، کلیک اول → `confirm`، کلیک دوم → `_r=` در URL و `localStorage` سالم.
5. تست تداخل: در `ai-chat` و `simple-chat`، `overlap` باید `false` باشد.

---

## 👣 اپ «ردپای من» — پایش زمان و تعداد باز شدن اپ‌ها (`usage/`)

### هویت
- **نام:** «ردپای من» | `<title>`: `ردپای من · آمار استفاده` | **پوشه:** `usage/`
- **آیکون:** ساعت طلایی + سه ستون فیروزه‌ای صعودی روی پس‌زمینهٔ سبز-آبی تیره (ساخته‌شده با Pillow، بدون متن).
- **کلید ذخیره‌سازی:** `emarat_usage_stats` (در `localStorage` مشترک همهٔ اپ‌ها چون یک origin هستند).

### 🧩 معماری: یک اسکریپت مشترک + یک صفحهٔ نمایش
| فایل | نقش |
|---|---|
| `usage-tracker.js` (ریشه) | شمارش زمان/باز شدن. در **۷۰ صفحه** با یک تگ تزریق شده. |
| `usage/index.html` | فقط **می‌خواند** و نمایش می‌دهد. هیچ‌وقت آمار نمی‌نویسد (جز بازیابی/پاک‌سازی دستی). |

**تزریق استاندارد:** `<script src="../usage-tracker.js" data-app="gold9"></script>` — در ریشه `src="usage-tracker.js"` بدون `../`.
**تزریق با `rfind('</body>')`** انجام می‌شود، نه `replace` (تلهٔ تکرار تگ).

### 📊 مدل داده: جمع روزانه، نه رکورد رکورد
```json
{ "gold9": { "2026-11-19": { "ms": 1820000, "opens": 4 } } }
```
اگر هر باز/بسته جداگانه ذخیره می‌شد، پس از چند ماه هزاران رکورد و فایل بکاپ چند مگابایتی می‌شد. جمع روزانه حجم را ثابت نگه می‌دارد.

### ⏱️ قواعد شمارش
- **آستانهٔ ۳ ثانیه:** بازدید کوتاه‌تر از `MIN_MS = 3000` **زمان** اضافه نمی‌کند، ولی **«باز شدن» همیشه** ثبت می‌شود.
- **Heartbeat هر ۱۵ ثانیه** + `flush` روی `visibilitychange`/`pagehide`/`beforeunload` تا بستن ناگهانی زمان را گم نکند.
- **`sessionStorage` برای جلوگیری از شمارش دوباره:** `cloud-sync.js` هنگام بازیابی داده `location.reload()` می‌زند؛ بدون این محافظ هر بازدید **دو بار** شمرده می‌شد. کلید: `emr_usage_open_<app>` با پنجرهٔ ۸ ثانیه.
- **داخل `iframe` غیرفعال است** (`window.top !== window.self`) — وگرنه هر تب داخلی gold9 یک باز شدن اضافه می‌ساخت.

### 🚫 استثنای مهم در `cloud-sync.js`
`cloud-sync.js` **همهٔ** کلیدهای `localStorage` را به MantleDB می‌فرستد/بازیابی می‌کند. آمار استفاده از هر دو مسیر **مستثنی** شد (`emarat_usage_stats*` و `emr_usage_*`):
- در `pushToCloud` → `continue` می‌شود (حجم ابر بی‌دلیل بزرگ نمی‌شود).
- در `pullFromCloud` → `return` می‌شود (نسخهٔ کهنهٔ ابری آمار تازه‌تر محلی را بازنویسی نمی‌کند).
**بکاپ این آمار فقط از مسیر گیت‌هاب انجام می‌شود.**

### ☁️ بکاپ گیت‌هاب (ادغام دوطرفه + فاصلهٔ زمانی)
- فایل پیش‌فرض: `usage/usage_backup.json` (قابل تغییر در ⚙️).
- کلیدها همان استاندارد پروژه: `github_backup_token/repo/branch/filepath` — **هرگز hardcode نمی‌شود**.
- **ادغام بر اساس `Math.max`** برای هر روز: نسخهٔ بزرگ‌تر برنده است، روزهای غایب حفظ می‌شوند. فایل نامعتبر داده را نابود نمی‌کند.
- **`MIN_GAP_MS = 10 دقیقه`** با کلید `emarat_usage_last_upload`: بدون این، هر بازدید یک کامیت تازه می‌ساخت و مخزن پر می‌شد.
- دکمهٔ «☁️ بکاپ فوری» فاصله را دور می‌زند.

### 🎨 UI
- ۴ کارت خلاصه (زمان، تعداد باز شدن، پرکاربردترین، میانگین هر بار) + نمودار Canvas ۷ روزه + فهرست اپ‌ها با نوار نسبت.
- فیلتر بازه: امروز / ۷ روز / ۳۰ روز / همه.
- پاک‌سازی **دومرحله‌ای** (`.armed` + تایمر ۴ ثانیه) — بدون `confirm()` مرورگر.
- کنتراست همهٔ ۲۰ سلکتور سنجیده شد: **کمترین ۷.۳۵** (حد AA = ۴.۵).

### 🔌 اتصال اکوسیستم
| مسیر | وضعیت |
|---|---|
| پورتال `index.html` → `{id:'usage', title:'ردپای من', icon:'usage/icon-192.png'}` | ✅ |
| `sw.js` → `CACHE_NAME` = `emarat-portal-v89` + ۹ فایل usage + `usage-tracker.js` + `refresh-button.js` + `price-import.js` | ✅ |
| آینه در `fund-automation-android/.../assets/webapp/` | ✅ |

### ✅ چک‌لیست تست
1. `grep -c "usage-tracker.js" <page>` → دقیقاً **۱** در هر ۷۰ صفحه.
2. باز کردن `gold9` ۵ ثانیه → در آمار `ms ≈ 5000` و `opens: 1` (نه ۲، با وجود رفرش خودکار cloud-sync).
3. بازدید < ۳ ثانیه → `ms` اضافه نمی‌شود ولی `opens` +۱.
4. تب جدید → `opens` +۱ (sessionStorage تازه است).
5. آفلاین واقعی: سرور را خاموش کن، رفرش کن → عنوان و نمودار و آیکون می‌آیند.
6. `cloud-sync` نباید `emarat_usage_stats` را در ابر ذخیره/بازیابی کند.

---

## 🌳 شجره‌نامه خانوادگی عمارت — چهار نمای رابط کاربری (`family/`)

### هویت
- **فایل:** `family/index.html` (تک‌فایل، ~۱۲۱KB → ~۱۳۰KB) | **پوشه:** `family/`
- **کلیدهای ذخیره‌سازی:** `emarat_family_tree` (اعضا)، `emarat_family_focused`، و **`emarat_family_theme`** (نما).

### 🎨 سیستم چهار نما (Themes)
| نما | کلید | پیش‌فرض | حس |
|---|---|---|---|
| گلستان | `garden` | ✅ | باغ ایرانی، سبز/طلایی، روشن |
| شب زمرد | `emerald` | — | تیرهٔ لوکس، زمرد درخشان |
| مینیمال | `minimal` | — | روشن/تخت، بیشترین خوانایی |
| طومار | `scroll` | — | کاغذ کهنه، قاب‌های اصیل |

- پیاده‌سازی: `html[data-theme="..."]` + توکن‌های CSS در `:root` هر نما. تابع‌ها: `applyTheme(key)` / `initTheme()`.
- سوییچر: دکمهٔ شناور `.theme-fab` (🎨، `top:64px; left:15px`) + پنل `.theme-panel`. کلیک بیرون پنل آن را می‌بندد.
- **قانون:** هر رنگ جدید باید توکن باشد، نه هاردکد. رنگ خطوط SVG درخت از `--line-color`/`--line-alt` می‌آید (کلاس‌های `.vine`/`.marriage-line`/`.leaf`)، پس تعویض نما **بدون رسم دوباره** انجام می‌شود.

### 🔤 فونت آفلاین
- `vendor/vazirmatn/fonts.css` + ۵ فایل `woff2` (Vazirmatn 400/500/700 + Noto Naskh Arabic 400/700).
- **بدون CDN** — طبق «قانون کارکرد آفلاین واقعی». فایل‌ها در `ASSETS` فایل `sw.js` هستند.
- نمای «طومار» از `Naskh` برای تیترها استفاده می‌کند (`--font-head`).

### ⚡ کارایی پن/زوم (اندازه‌گیری‌شده، نه حدس)
- **قبل:** ۶۶۲ms | **بعد:** ۳۳۸ms — کاهش ~۴۹٪ (`TaskDuration` با CPU throttling ۶×، میانهٔ ۵ اجرا، ۱۲۰ حرکت درگ).
- سه تغییر مؤثر: (۱) نوشتن `transform` در یک `requestAnimationFrame` (`pendingTransform`/`flushTransform`)، (۲) حذف `flushTransform()` از `getRelativeCoords()` (layout thrash)، (۳) `contain: layout paint` روی بوم.
- انیمیشن بی‌نهایت `box-shadow` حذف و با انیمیشن `opacity` روی شبه‌عنصر جایگزین شد؛ `backdrop-filter` از کارت‌های کدر حذف شد.
- **تله:** هر `flushTransform()` که داخل یک حلقهٔ اندازه‌گیری صدا زده شود، هر بار `getBoundingClientRect` را باطل می‌کند → layout thrash. اندازه‌گیری‌ها را اول جمع کن، بعد یک‌بار بنویس.

### ⚠️ کنتراست — اندازه‌گیری اجباری
- ابزار: Puppeteer + محاسبهٔ WCAG روی زنجیرهٔ واقعی `backgroundColor` والدها (نه حدس).
- **سه ایراد واقعی که پیدا شد:**
  | مورد | قبل | بعد |
  |---|---|---|
  | متن دکمهٔ اصلی در «شب زمرد» | **۱.۹۲** (سفید روی سبز روشن) | ۹.۶۵ (توکن `--on-primary`) |
  | رنگ متوفی (هاردکد `#777`) | ۳.۵۲ | ۵.۱۹ (حذف رنگ، فقط `opacity:0.75`) |
  | `--text-muted` مینیمال (`#7C7C76`) | ۴.۲۰ | ۵.۳۶ (`#6B6B65`) |
- **قانون:** هر تم تیره/روشن باید توکن `--on-primary` داشته باشد؛ `color: #fff` روی `background: var(--primary-green)` در تم‌های روشن می‌شکند.

### 🐛 برخورد کنترل‌ها
- دکمهٔ 🎨 اول وسط-بالا بود و روی استک دکمه‌های بالا-راست می‌افتاد؛ به `left:15px; top:64px` منتقل شد.
- `.zoom-controls` از `bottom:20px` به `bottom:112px` رفت (روی نوار پایین می‌افتاد — باگ از قبل موجود).
- **تست:** با Puppeteer جعبه‌های `.theme-fab`/`.top-right`/`.top-left`/`.bottom-controls`/`.zoom-controls` را بگیر و برخورد را چک کن؛ باید `collisions: []` باشد.

### ✅ چک‌لیست پس از تغییر
1. `python3 scripts/check-refresh-button.py` → پاس.
2. `grep -rnE '<(link|script)[^>]*(href|src)="https?://(cdnjs|fonts\.googleapis|fonts\.gstatic|unpkg|jsdelivr)' --include=*.html .` → **صفر**.
3. `grep -c "refresh-button.js" family/index.html` → **۱**.
4. کنتراست همهٔ ۴ نما ≥ ۴.۵ (اندازه‌گیری، نه حدس).
5. آفلاین واقعی: از **پورتال** باز کن (سرویس‌ورکر فقط از `/sw.js` ریشه ثبت می‌شود)، بعد `setOfflineMode(true)` و رفرش → کارت‌ها + فونت باید بیایند.
6. `CACHE_NAME` بامپ شود (الان `emarat-portal-v93`).

---

## 🧪 آزمایشگاه رابط کاربری شجره‌نامه (`family-lab/index.html`)

### هدف
صفحهٔ مستقل برای بررسی چهار چیدمان متفاوت شجره‌نامه **و** ویرایش کامل داده — بدون دست‌زدن به اپ اصلی `family/index.html`.

### چهار نما (منطق متفاوت، نه فقط رنگ)
| نما | ساختار | تعامل |
|---|---|---|
| نسل‌ها (`gen`) | ردیف عمودی نسل + نوار افقی هر نسل | کشیدن افقی هر ردیف · لمس → پنجرهٔ پایین |
| پرونده (`deck`) | یک‌نفره تمام‌صفحه + تب | تب اطلاعات/خویشاوندان/خط زمان |
| جدول (`table`) | آمار + جست‌وجو + مرتب‌سازی | فیلتر زنده/مرحوم · مرتب‌سازی چرخشی |
| شعاعی (`radial`) | مدارهای SVG + گره | لمس گره = مرکز جدید |

### 🚨 درس گران‌بها ۱ — قالب تاریخ
اپ اصلی `family/index.html` تاریخ‌ها را **رشتهٔ** `"1352/2/18"` ذخیره می‌کند (`${y}/${m}/${d}`)، **نه** شیء `{y,m,d}`.
نسخهٔ اول آزمایشگاه شیء می‌خواند → با دادهٔ واقعی کاربر **همهٔ سال‌ها «—»** می‌شد.
تست با دادهٔ نمونهٔ شیءمحور این را **نگرفت**؛ فقط تست با دادهٔ واقعی رشته‌ای لو داد.

**قانون:** هر کدی که با `localStorage` اپ دیگری کار می‌کند، باید **دقیقاً** قالب نوشتن آن اپ را از کد `saveData` بخواند، نه از کامنت یا حدس.
راه‌حل: `normDate()` هر دو قالب را می‌پذیرد و هنگام نوشتن **همیشه رشته** می‌نویسد.

### 🚨 درس گران‌بها ۲ — ترتیب پاک‌کردن state
```javascript
// غلط:
closeEditor();          // editingId = null
focusId = editingId ... // همیشه null → فوکوس به نفر اول می‌پرد
// درست:
const keepFocus = editingId;
closeEditor();
focusId = keepFocus && M[keepFocus] ? keepFocus : ids[0];
```
نتیجهٔ باگ: بعد از ویرایش، کاربر یک‌دفعه آدم دیگری می‌دید و **پیوند خویشاوندی روی عضو اشتباه** ثبت می‌شد.

### 🚨 درس گران‌بها ۳ — تست باید حالت را از DOM بخواند، نه از فرض
یک «باگ» گزارش شد که باگ نبود: تست فرض کرده بود فوکوس روی «علی» است، ولی روی «مظفر» (ریشه) بود. پیوند درست انجام شده بود.
**قانون:** قبل از هر ادعای باگ، مقدار واقعی را از `document.querySelector('.deck-name').textContent` بخوانید.

### 🔒 لایهٔ نوشتن امن
- `snapshot()` **پیش از هر نوشتن** یک نسخه در `emarat_family_lab_backup` می‌گذارد (۸ نسخهٔ آخر، هر کدام `{at, label, bytes, data}`).
- `persistTree()` = snapshot → `localStorage.setItem` → `EmaratCloudSync.push()` (در صورت وجود).
- حذف عضو: ارجاع‌هایش از `parents`/`spouses`/`children` **همهٔ** اعضا پاک می‌شود.
- پیوند دوطرفه: `children` ⇄ `parents` و `spouses` ⇄ `spouses` هر دو طرف به‌روز می‌شوند.

### 🎯 اندازهٔ لمس
اولین نسخه ۹ دکمهٔ زیر ۳۶px داشت (سخت لمس روی گوشی). استاندارد اعمال‌شده: **حداقل ۴۴px** برای هر کنترل تعاملی.
بازرس: `check_ed.js` (پروژه‌ای در `/tmp/uibuild`) تعداد `smallTaps` را می‌شمارد.

### ✅ چک‌لیست تست این صفحه
1. با دادهٔ **رشته‌ای** (فرمت اپ اصلی) seed کنید — نه شیء.
2. افزودن: نام + تاریخ → در `localStorage` با `birthDate` رشته‌ای و `spousesCount`/`childrenCount` ذخیره شود.
3. ویرایش: نام و تاریخ **حفظ** شوند، فقط فیلد تغییر‌یافته عوض شود.
4. پیوند فرزند: `parent.children` شامل فرزند **و** `child.parents` شامل والد باشد.
5. حذف: عضو برود **و** ارجاعش از بقیه پاک شود.
6. ذخیرهٔ بی‌نام: رد شود و فرم باز بماند.
7. `emarat_family_lab_backup` حداقل یک snapshot داشته باشد.
8. صفر خطای کنسول (آیکون `favicon` هم ست شده تا ۴۰۴ نباشد).

### 🔌 اتصال
- پورتال `index.html` → `{ id: 'family-lab', title: 'آزمایشگاه رابط کاربری' }`
- `sw.js` → در `ASSETS` + `CACHE_NAME` (الان `emarat-portal-v95`)
- `usage-tracker.js` با `data-app="family-lab"`
- `refresh-button.js` یک بار قبل از `</body>`
- شاخهٔ کار: `Y-5` → merge در `main`

### 🌳 دادهٔ نمونهٔ پنج‌نسلی (۴۲ نفر)
`DEMO` در `family-lab/index.html` یک خاندان واقعی‌نماست: **۱۰ / ۸ / ۱۴ / ۸ / ۲** نفر در ۵ نسل، ۳۷ زنده و ۵ مرحوم، همه با شغل، شهر، تاریخ شمسی **رشته‌ای** و زندگی‌نامه.
شناسه‌ها معنادارند: `g*` ریشه، `p*` والدین/عمو/خاله، `m*` نسل خود، `s*` همسران، `c*` نوه‌ها، `n*` نتیجه‌ها، `u*` شاخهٔ عموی بزرگ.

### 🚨 درس گران‌بها ۴ — از‌دست‌رفتن داده در حالت نمونه
`readRawTree()` مستقیم `localStorage` را می‌خواند. در حالت «دادهٔ نمونه» آنجا **خالی** است، پس `{}` برمی‌گشت و ذخیره یعنی **پاک‌شدن ۴۱ نفر**.
**درمان:** `currentTree()` — اگر `source === 'demo'` از مجموعهٔ درون‌حافظه کپی می‌گیرد. `persistTree()` هم در همین حالت فقط `M` را به‌روز می‌کند و `localStorage` را دست نمی‌زند.
**قانون:** هر مسیر نوشتن باید بداند داده از کجا آمده؛ «خالی» با «نمونه» یکی نیست.

### 🚨 درس گران‌بها ۵ — عمق نسل با والدِ ثبت‌نشده
عمق فقط از `parents` محاسبه می‌شد. همسرانی که به خاندان وارد شده‌اند و عموزاده‌های ناقص والد ثبت‌نشده دارند → همه `depth = 0` → **۱۸ نفر در ردیف «ریشه»**.
**درمان:** سه‌مرحله‌ای — (۱) عمق از والد، (۲) اگر والد نبود از **همسر**، (۳) اگر آن هم نبود از **فرزندان** (`min(kids) - 1`). با ۶ گذر تا همگرایی.
**درس:** درخت خانوادگی همیشه کامل نیست؛ الگوریتم چیدمان باید با دادهٔ ناقص هم آبرومند باشد.

### 🌳 نمای درختی دوطرفه (تب پنجم `tree`)

**هدف:** سمت پدر و سمت مادر در **دو پنل مستقل** رسم شوند، با تشخیص خودکار نسبت فارسی و نمایش ازدواج بین دو خانواده.

#### توابع کلیدی
| تابع | کار |
|---|---|
| `ancestorSet(id, maxUp=8)` | همهٔ نیاکان یک نفر (پیمایش صرفاً رو به بالا) |
| `sideOf(id, root, seen)` | تعلق به `'p'` / `'m'` / `'self'` |
| `kinshipOf(id, root)` | عنوان فارسی نسبت (دو گذر: اول نسب، بعد سبب) |
| `renderTree()` | چیدمان + SVG + تشخیص ازدواج بین دو سمت |

#### 🚨 درس ۶ — `sideOf` با BFS دوسویه همه را در یک پنل می‌ریخت
نسخهٔ اول برای یافتن «کدام سمت» یک BFS روی `parents + spouses` می‌زد. همسران و خواهر/برادرها هیچ‌وقت به والد روت نمی‌رسیدند → همه `'p'` می‌شدند و پنل مادر **خالی** می‌ماند.
**درمان:** `ancestorSet` صرفاً رو به بالا + مقایسهٔ مجموعهٔ نیاکان با نیاکانِ پدر و مادر. برای کسانی که **هیچ** والد ثبت‌شده ندارند (همسرانی که وارد خاندان شده‌اند، عموزاده‌های ناقص)، سمت از **همسر** و بعد از **فرزند** ارث می‌رسد.
**درس:** درخت خانوادگی همیشه ناقص است؛ هر الگوریتم سمت/نسل باید یک مسیر «ارث‌بری از خویشاوند نزدیک‌تر» داشته باشد.

#### 🚨 درس ۷ — عمو/عمه/دایی/خاله «خواهر/برادر» خوانده می‌شدند
شرط خواهر/برادر این بود: `rParents.some(pa => shareParent(id, pa))` — یعنی «آیا این نفر با **پدرِ من** والد مشترک دارد؟». عمو دقیقاً همین ویژگی را دارد (هر دو در پدربزرگ مشترک‌اند) → پس **همهٔ عمو/عمه/دایی/خاله** «برادر/خواهر» می‌شدند.
**درمان:** `shareParent(id, root)` — مقایسه باید با **خودِ روت** باشد، نه با والدِ روت.
**درس:** در گراف خویشاوندی، «والد مشترک با والدِ من» = عمو، و «والد مشترک با من» = خواهر/برادر. یک سطح اختلاف، یک نسبت کاملاً متفاوت.

#### 🚨 درس ۸ — نسبت سببی نباید بر نسبی اولویت داشته باشد
مردی که هم **دایی** بود و هم با **عمه** ازدواج کرده بود، «شوهرِ عمه» نمایش داده می‌شد؛ چون حلقهٔ همسرانِ خویشاوندان **قبل** از حلقهٔ عمو/دایی اجرا می‌شد.
**درمان:** `kinshipOf` به دو بخش صریح تقسیم شد: `/* 1. blood */` و `/* 2. marriage-in */`. همهٔ نسبت‌های خونی اول، بعد نسبت‌های سببی.
**درس:** ترتیب بررسی‌ها در تابع تشخیص نسبت، بخشی از منطق است نه جزئیات پیاده‌سازی.

#### 📐 چیدمان
- ردیف‌ها: `depth - depth[root]` محدود به `[-2, +2]` (جد → والد → خود → فرزند → نوه).
- ستون‌ها: هر پنل به‌اندازهٔ پرجمعیت‌ترین ردیفش عرض می‌گیرد.
- **روت در شکاف میان دو پنل** (`GAP = COL * 1.5`) قرار می‌گیرد تا هرگز روی کارتی نیفتد.
- ارتفاع بوم از `usedRows` واقعی حساب می‌شود، نه از تعداد کل ردیف‌ها (وگرنه ~۷۵px فضای خالی می‌ماند).

#### ✅ تست
```javascript
// ۱) صفر همپوشانی
rects.reduce(...) // باید 0 باشد
// ۲) دو پنل
[...document.querySelectorAll('.side-badge')].length === 2
// ۳) عنوان‌های درست روی دادهٔ نمونه
omo:'عمو' · amme:'عمه' · daii:'دایی' · khale:'خاله' · cousin:'پسرعمو'
// ۴) ازدواج بین دو سمت
document.querySelector('.marriage-note').innerText.includes('عمه') && includes('دایی')
```

#### 📦 دادهٔ نمونه (۴۵ نفر، ۵ نسل: ۱۲/۷/۱۰/۱۰/۶)
شامل **۳ ازدواج بین دو سمت**: پدر×مادر، **عمه×دایی** (فرزند: مهدی)، پسرعمو×دختردایی.
`CACHE_NAME` = `emarat-portal-v97`.

#### ⚠️ سقف کپشن تلگرام
`sendPhoto` حداکثر **۱۰۲۴ کاراکتر** کپشن می‌پذیرد. پیام بلندتر → `Bad Request: message caption is too long`. متن بلند را در `sendMessage` جدا بفرست یا کپشن را کوتاه کن.

---

## 🎨 شش مدل رسم درختی (`tree-samples/`)

### ساختار
| فایل | نقش |
|---|---|
| `tree-samples/shared.js` | دادهٔ نمونه (۴۵ نفر) + `esc`/`initial`/`yearOf`/`isDead` + `ancestorSet`/`sideOf`/`kinshipOf` + `computeDepth` |
| `tree-samples/m1.html` … `m6.html` | شش چیدمان مستقل، هر کدام فقط منطق چیدمان خودش را دارد |

**قانون:** منطق نسب **یک منبع حقیقت** دارد (`shared.js`). اگر نسب اشتباه بود، فقط همان‌جا اصلاح شود — نه در شش فایل.

### شش چیدمان
| # | نام | منطق | پهنا×ارتفاع |
|---|---|---|---|
| ۱ | ستون‌های نسل | ردیف نسلی، قاب رنگی خانواده | ۱۲۲۸×۷۲۰ |
| ۲ | دو بال آینه‌ای | روت روی ستون مرکزی، خانواده‌ها دو طرف | ۲۱۶۸×۶۷۸ |
| ۳ | شجره‌نامهٔ کلاسیک | جعبهٔ باریک افقی + خطوط پررنگ | ۱۹۱۴×**۴۲۰** |
| ۴ | کارت‌های پشته‌ای | هر نسل یک سکو با کارت برجسته | ۱۴۸۰×۷۶۰ |
| ۵ | خوشه‌های خانواده | جزیرهٔ رنگی جدا برای هر خانواده | ۲۵۳۴×۷۱۰ |
| ۶ | نقشهٔ عمودی | پدری/مادری دو طرف + خطوط ضخیم | **۱۳۲۲**×۷۴۲ |

### 🚨 درس گران‌بها ۹ — `element.screenshot()` با بوم بزرگ‌تر از ویوپورت
`await (await p.$('#cv')).screenshot({path})` روی بومی به عرض ۲۴۵۶px و ویوپورتی به عرض ۳۹۰px، **فقط گوشهٔ بالا-چپ** را می‌گیرد؛ بقیهٔ تصویر خالی می‌ماند و **هیچ خطایی هم نمی‌دهد**.
مدرک: تصویر ۳۶۸۴×۲۱۶۰ بود ولی ۹۱٪ پیکسل‌ها پس‌زمینه و محتوا فقط در `bbox (0,24,378,843)`.

**درمان (سه‌گانه، هر سه لازم است):**
```javascript
const dim = await p.evaluate(()=>{ const cv=document.getElementById('cv');
  return {w:Math.ceil(parseFloat(cv.style.width)), h:Math.ceil(parseFloat(cv.style.height))}; });
await p.setViewport({width:dim.w+8, height:dim.h+8, deviceScaleFactor:2});
await p.evaluate(()=>{ const w=document.querySelector('.wrap');
  w.style.overflow='visible'; w.style.width='auto'; w.style.padding='0';
  document.body.style.overflow='hidden'; window.scrollTo(0,0); });
```
**درس:** همیشه **قبل از** عکس گرفتن، ویوپورت را به اندازهٔ عنصر بزرگ کنید. `fullPage:true` هم کمک نمی‌کند چون عنصر داخل `overflow-x:auto` است.

**بازرس:** نسبت پیکسل‌های «جوهر» به کل تصویر. اگر < ۵٪ بود، عکس ناقص است.
```python
bg = px[2,2]; ink = sum(1 for ... if dist(p,bg) > 25) / total
```

### 🚨 درس گران‌بها ۱۰ — روت باید ردیف اختصاصی داشته باشد
در m1 و m6 ابتدا روت با `+RH*0.9` و `+RH*0.62` به ردیف نسلی‌اش چسبانده شد → **۴ و ۲ همپوشانی**. روت روی هم‌نسل‌هایش می‌افتاد.
**درمان:** روت در **ردیف آخر مخصوص خودش** (`46 + gKeys.length * RH`) و ارتفاع بوم یک ردیف بیشتر.
**درس:** عنصری که «همه را به هم وصل می‌کند» نباید در شبکهٔ ردیف‌ها جای بگیرد؛ ردیف خودش را لازم دارد.

### ⚠️ سقف‌های تلگرام
| مورد | سقف |
|---|---|
| `sendPhoto` — کپشن | ۱۰۲۴ کاراکتر |
| `sendPhoto` — ابعاد | ۲۵۶۰px ضلع بزرگ‌تر (بیشتر → فشرده/رد) |
| `sendDocument` — کپشن | ۱۰۲۴ کاراکتر |
| `sendDocument` — حجم | ۵۰MB (HTTP API) |
| `sendMessage` — متن | ۴۰۹۶ کاراکتر |

برای تصویر بزرگ/دقیق از `sendDocument` استفاده کن (بدون فشرده‌سازی) — `sendPhoto` تصویر را مچاله می‌کند.

### ✅ چک‌لیست هر مدل جدید
1. `node --check` روی JS استخراج‌شده.
2. ۴۵ گره رندر شوند (`document.querySelectorAll('.nd').length === 45`).
3. صفر همپوشانی (مقایسهٔ `getBoundingClientRect` جفتی).
4. صفر گرهٔ بیرون بوم.
5. صفر متن بریده (`scrollWidth > clientWidth`).
6. صفر خطای کنسول.
7. عکس با ویوپورت هم‌اندازه — و بازرسی «جوهر٪».

---

## 🛡️ محافظ ذخیره‌سازی و رفع باگ «چهار ماه عقب رفتن داده» (storage-guard.js)

### علائم
دادهٔ اپ‌های درصد (gold..gold9) بی‌دلیل به چند ماه قبل برمی‌گشت — معمولاً بعد از یک
به‌روزرسانی، ساخت اپ جدید، یا باز کردن سایت روی دستگاه دیگر.

### سه ریشهٔ واقعی که با هم این باگ را می‌ساختند

| # | ریشه | چرا خطرناک بود |
|---|---|---|
| ۱ | `localStorage` تقریباً پر بود: **۹٫۸۴ از ۹٫۹۲ مگابایت** | `setItem` استثنای `QuotaExceededError` می‌داد، گرفته نمی‌شد، و چون `saveData` چند `setItem` جدا داشت، بعضی کلیدها ذخیره می‌شدند و بعضی نه → داده نیمه‌کاره |
| ۲ | `cloud-sync.js` در `pullFromCloud` هرگاه `cloudBackup.timestamp > localTimestamp` بود، **همهٔ** کلیدها را با نسخهٔ ابری بازنویسی می‌کرد | نبودِ یا کهنه بودن `emarat_last_modified` کافی بود تا نسخهٔ کهنهٔ ابری روی دادهٔ تازهٔ گوشی بنشیند |
| ۳ | اپ `gold` از کلیدهای **بی‌پسوند** استفاده می‌کرد (`percents`, `trash`, `goal`, ...) | روی `om2025p.github.io` که یک origin مشترک است، با هر اپ دیگری تصادم می‌کرد |

### یافتهٔ مهم دربارهٔ مصرف حافظه
از ۹٫۸۴ مگابایت مصرف‌شده، **۸٫۹۷ مگابایت مال کلیدهای «بیگانه»** بود:

```
symbolsCache           2.30 MB
navAnalysisDatasets    2.29 MB
navChartListDatasets   1.97 MB
marjan_images_v1       1.38 MB
navAnalysisData        0.27 MB
```

این کلیدها **در هیچ‌جای این مخزن و در هیچ‌کدام از ۱۰۸۹ کامیت تاریخچه نیستند**
(با `git log -S` هم بررسی شد). یعنی از اپ دیگری روی همان دامنهٔ `github.io` آمده‌اند.
اپ‌های درصد این مخزن فقط **۰٫۸۷ مگابایت** مصرف می‌کنند. تا وقتی آن اپ‌ها آن کلیدها را
نگه می‌دارند، فضا برای ذخیرهٔ درصدها تنگ می‌ماند — ولی با محافظ جدید، ذخیرهٔ درصد
**هرگز بی‌صدا گم نمی‌شود**.

### راه‌حل پیاده‌شده — `storage-guard.js` (ریشهٔ مخزن)

```javascript
EmaratStorage.safeSet(key, value)              // نوشتن یک کلید + پیام فارسی در صورت شکست
EmaratStorage.safeSetBatch({k1:v1, k2:v2})     // نوشتن اتمی: یا همه، یا هیچ (با rollback)
EmaratStorage.migrate(oldKey, newKey)          // مهاجرت امن؛ مقصد پر را بازنویسی نمی‌کند
EmaratStorage.migrateAll([[old,new], ...])
EmaratStorage.health()                         // {usedMB, quotaMB, percent, critical, biggest}
```

- **`safeSetBatch` اتمی است:** پیش از نوشتن، مقادیر قبلی را نگه می‌دارد؛ اگر یکی شکست
  خورد، نوشته‌های قبلی را برمی‌گرداند تا داده هرگز نیمه‌کاره نماند.
- **پیام فارسی با عدد واقعی:** «⚠️ حافظهٔ مرورگر پر است — این تغییر ذخیره نشد · مصرف فعلی: X مگابایت»
  به‌همراه بزرگ‌ترین کلیدهای مصرف‌کننده. کاربر **می‌فهمد**، به‌جای اینکه فکر کند ذخیره شد.
- **`isEmptyish()` — درس گران‌بها:** مقدارهای `[]`، `{}`، `null` و `""` «خالی» شمرده می‌شوند.
  بدون این، اگر اپ یک‌بار با وضعیت تهی لود می‌شد (مثلاً `beforeunload` وضعیت درون‌حافظهٔ
  خالی را می‌نوشت)، کلید جدید `[]` می‌گرفت و مهاجرت برای همیشه بلاک می‌شد و دادهٔ قدیمی گم می‌شد.
- **گارد fallback:** در هر `saveData`، اگر `window.EmaratStorage` موجود نباشد (کش کهنه)،
  نوشتن با `localStorage.setItem` ساده انجام می‌شود تا اپ **هرگز نشکند**.

### ترتیب بارگذاری (حیاتی)
`<script src="../storage-guard.js"></script>` باید **پیش از** اولین `<script>` درون‌خطی صفحه بیاید
(نه قبل از `</body>`). در ۳۹ صفحهٔ اپ‌های درصد این‌گونه تزریق شد.

### اصلاح `cloud-sync.js`
```javascript
// قبل: ابر میتوانست دادهٔ گوشی را بازنویسی کند
if (isLocalEmpty || cloudBackup.timestamp > localTimestamp) { ...restore... }

// بعد: ابر فقط «پرکنندهٔ جای خالی» است
if (isLocalEmpty) { ...restore... }
```
دادهٔ گوشی هرگز با نسخهٔ ابری جایگزین نمی‌شود. برای انتقال بین دستگاه‌ها، از بکاپ
گیت‌هاب (`autoSyncFromBackup`) استفاده کنید که **ادغام افزایشی** دارد.

### مهاجرت کلیدهای `gold`
کلیدهای بی‌پسوند به `gold_*` منتقل شدند (`gold_percents`, `gold_trash`, `gold_goal`,
`gold_highlightedStates`, `gold_highlightedPointIndices`, `gold_statsMenuOpen`) با
مهاجرت خودکار در اولین بارگذاری. دادهٔ کاربر حفظ می‌شود و کلید قدیمی پاک می‌شود.

### تست‌های تأییدشده
| تست | نتیجه |
|---|---|
| ۳۹ صفحهٔ اپ‌های درصد: بارگذاری، بدون خطای کنسول، بدون ۴۰۴ | ✅ |
| پر کردن حافظه تا سقف → `safeSet` روی کلید واقعی | `ok:false` + دادهٔ قبلی **دست‌نخورده** + پیام فارسی |
| `safeSetBatch` با کلید بزرگ در میانه | rollback کامل، هیچ کلیدی تغییر نکرد |
| مهاجرت کلیدهای قدیمی `gold` (۲ درصد + ۱ حذف + هدف) | همه منتقل شد، UI هم ۲/۱ نشان داد |
| ابر کهنهٔ ۴ ماه پیش + گوشی با دادهٔ تازه | دادهٔ تازه حفظ شد (`[4.4, 5.5]`) |
| `scripts/check-refresh-button.py` و وابستگی خارجی | ✅ پاس / صفر |

### ⚠️ نکتهٔ باقی‌مانده برای کاربر
اگر پیام «حافظهٔ مرورگر پر است» دیدید، یعنی هنوز آن ۸٫۹۷ مگابایت کلید بیگانه آنجاست.
راه‌حل قطعی: در DevTools → Application → Local Storage، کلیدهای `symbolsCache`،
`navAnalysisDatasets`، `navChartListDatasets`، `marjan_images_v1`، `navAnalysisData` را
پاک کنید (یا از «جعبهٔ نجات» بکاپ بگیرید و داده‌های اضافی را حذف کنید).

---

## 🚨 باگ بحرانی «چهار ماه عقب رفتن داده» — ریشهٔ واقعی و درمان کامل (v104)

### نشانه
کاربر گزارش داد پس از به‌روزرسانی یا ساخت وب‌اپ جدید، تاریخچهٔ درصدها **چهار ماه به عقب** برمی‌گردد و بعضی کلیدها قدیمی می‌شوند — مخصوصاً در «ثبت درصد ۱ تا ۹».

### 🔴 ریشهٔ ۱ — `beforeunload → saveData()` وضعیت کهنه را می‌نویسد
سه اپ `gold`، `gold2`، `gold4` روی `beforeunload` به `saveData()` وصل بودند. اگر صفحه با **حافظهٔ خالی** بارگذاری می‌شد (مثلاً کلید تازه/مهاجرت‌نشده، یا خطای خواندن)، هنگام بستن، آرایهٔ **درون‌حافظهٔ خالی** روی دادهٔ سالم `localStorage` می‌نشست و **کل تاریخچه نابود می‌شد**.
- **اثبات:** seed کردن ۲ رکورد، سپس ناوبری به صفحهٔ دیگر → `percents` شد `[]`.
- **درمان:** پرچم `stateLoaded` / `window.__stateLoaded` که فقط بعد از بارگذاری داده ست می‌شود؛ `saveData` پیش از آن `return` می‌کند. به‌علاوه ادغام محافظتی: هیچ رکوردی که در حافظه نیست از `localStorage` حذف نمی‌شود (مگر در `trash` باشد).

### 🔴 ریشهٔ ۲ — مهاجرت کلید بدون آینه، ۶ مصرف‌کننده را کور کرد
کلید `percents` به `gold_percents` منتقل شد ولی این‌ها هنوز قدیمی می‌خواندند:
| فایل | نقش |
|---|---|
| `monitor/index.html` | دیدبان — دادهٔ ثبت درصد ۱ صفر می‌شد |
| `detective/index.html` | بکاپ/بازیابی — کل gold دیده نمی‌شد |
| `profit-calculator/calc2.html` | منبع دیدبان خالی |
| `gold/calculator.html` | `PERCENT_LIST_KEY="percents"` → درصد در کلید قدیم می‌نوشت |
| `gold/percent.html` | `__emaratAutoSync` و شنوندهٔ `storage` |
- **درمان:** `EmaratStorage.registerMirror(master, mirror)` — هر نوشتن روی کلید اصلی، آینه را هم می‌نویسد. جهت همیشه **master → mirror** است (نه برعکس؛ وگرنه آینهٔ خالی، master را پاک می‌کند).

### 🔴 ریشهٔ ۳ — `detective` با `localStorage.clear()` کل origin را نابود می‌کرد
`handleFullImport` اول `localStorage.clear()` می‌زد و بعد فایل را می‌نوشت. چون همهٔ اپ‌ها یک origin مشترک دارند، یک کلیک بازیابی، دادهٔ **همهٔ ۹ اپ** را پاک می‌کرد.
- **درمان:** فقط کلیدهای موجود در فایل نوشته می‌شوند؛ هیچ `clear()`ی نیست. پیام تأیید هم صادق شد.

### 🟢 حافظهٔ قدرتمند مرورگر (IndexedDB) — درخواست کاربر: «همهٔ اپ‌ها از حافظهٔ قدرتمند استفاده کنند»
`storage-guard.js` نسخهٔ ۲:
- **هوک سراسری:** `localStorage.setItem` بازنویسی می‌شود تا هر نوشتن خودکار در IndexedDB (`emarat_power_store`) آینه شود. سهمیهٔ IndexedDB صدها مگابایت تا چند گیگابایت است در برابر ~۱۰ مگابایت localStorage.
- **پر شدن حافظه:** اگر `QuotaExceededError` رخ دهد، داده در IndexedDB محفوظ می‌ماند و در بارگذاری بعدی برمی‌گردد.
- **`shadowHeal()`:** فقط کلیدهای **کاملاً غایب** را برمی‌گرداند. کلید موجود ولی خالی (`"[]"`) وضعیت واقعی اپ است و دست نمی‌خورد.
- **مهر زمانی در سایه:** هر رکورد `{v, t}` ذخیره می‌شود تا سایهٔ کهنه روی دادهٔ تازه ننشیند.
- **⚠️ دام رفرش تصادفی:** نسخهٔ اول `autoHealOnLoad` کلیدهای «خالی‌نما» را هم بازیابی می‌شمرد و صفحه را بی‌دلیل رفرش می‌کرد (`Execution context was destroyed` در تست). درمان: رفرش فقط وقتی واقعاً کلیدی نجات یابد.

### 📦 پوشش
`storage-guard.js` در `<head>` **۶۰ صفحه** (نه انتهای `<body>`) تزریق شد — چون هوک باید **قبل از** کد اپ نصب شود. تزریق با `rfind('</body>')`/`<head>` و شمارش `grep -c` تأیید شد (هر صفحه دقیقاً ۱).

### ✅ تست (۳۱ سنجه، همه موفق)
| سناریو | نتیجه |
|---|---|
| ۱۲۰ رکورد چهارماهه + مهاجرت | ✅ ۱۲۰ در هر دو کلید |
| رفت‌وبرگشت بین اپ‌ها (`beforeunload`) | ✅ ۱۲۰ سالم |
| ثبت جدید بعد از چهار ماه | ✅ ۱۲۱ (نه ۱) |
| `localStorage` خالی → بازیابی از IndexedDB | ✅ ۱۲۱ بازگشت |
| دادهٔ کهنهٔ ابر | ✅ محلی دست‌نخورده |
| پر شدن حافظه | ✅ داده در IndexedDB |
| دیدبان/کارآگاه/ماشین‌حساب | ✅ همه داده را می‌بینند |
| ۹ اپ gold | ✅ بدون خطا |

### 🐛 نکتهٔ `gym/index.html`
این صفحه روی `file://` **hang می‌کند** — با **و بدون** `storage-guard`. یعنی باگ از قبل موجود است و ربطی به این تغییر ندارد (روی HTTPS سالم است).

### 🔁 نسخه
`CACHE_NAME` → `emarat-portal-v104` · آینهٔ اندروید همگام شد.

### 🐛 باگ آلودگی کلید «setItem» — رفع‌شده در v105

**نشانه:** پس از v104، در `Object.keys(localStorage)` کلیدی به نام `setItem` با مقدار `null` ظاهر می‌شد.

**ریشه:** `installWriteHook()` با `localStorage.setItem = function(){}` هوک را روی **نمونهٔ** localStorage می‌نوشت. مرورگر این assignment را به‌عنوان یک **آیتم ذخیره‌شده** ثبت می‌کند (نه یک متد) → کلید زائد `setItem` ساخته می‌شد.

**درمان:** هوک روی `Storage.prototype.setItem` نوشته می‌شود (نه روی نمونه)، و `cleanupPoisonKey()` در بارگذاری کلید آلوده را یک‌بار حذف می‌کند. مقدار آن هرگز داده نبود، پس حذف بی‌خطر است.

**درس:** هرگز متدهای `localStorage` را روی **نمونه** override نکن؛ همیشه `Storage.prototype`. وگرنه یک کلید زائد در حافظهٔ کاربر می‌کاری و سهمیهٔ تنگ را تنگ‌تر می‌کنی.

### 🔴 پاپ‌آپ قرمز «حافظهٔ معمولی پر است» — نگهبان است، نه باگ

با دادهٔ واقعی کاربر (۵.۰۴ مگابایت در ۳۴۵ کلید) و سهمیهٔ ~۱۰ مگابایت، **۴.۱۱ مگابایت** آن مال کلیدهای **یتیم** است:

```
symbolsCache            1.15 MB
navAnalysisDatasets     1.15 MB
navChartListDatasets    0.98 MB
marjan_images_v1        0.69 MB
navAnalysisData         0.14 MB
```

این کلیدها در **هیچ‌جای مخزن نیستند** (نه در کد، نه در ۱۰۸۹ کامیت) — از اپ دیگری روی همان دامنهٔ `github.io` آمده‌اند و هیچ اپی آن‌ها را نمی‌خواند یا پاک نمی‌کند.

پاپ‌آپ قرمز (`#8c2b20`) از `quotaMessage()` می‌آید و یعنی: **نوشتن در localStorage شکست خورد، ولی داده در IndexedDB سالم است** و در بارگذاری بعدی برمی‌گردد. متن صریح می‌گوید «داده از دست نرفت».

**درمان قطعی برای کاربر:** پاک کردن آن ۵ کلید یتیم از DevTools → Application → Local Storage. این کار ۴.۱ مگابایت آزاد می‌کند و پاپ‌آپ برای همیشه تمام می‌شود. **هیچ دادهٔ اپی از دست نمی‌رود.**

### 🔔 پاپ‌آپ «حافظه پر است» — یک بار برای همیشه (v106)

**تصمیم کاربر:** گزینهٔ «یک بار تا ابد» (نه هر نشست، نه هر نسخه).

**پیاده‌سازی:** یک پرچم مشترک `emarat_quota_warned_v1` در `localStorage` که **هر چهار** منبع هشدار قرمز را کنترل می‌کند:

| منبع | قبلاً | الان |
|---|---|---|
| `warnIfCritical()` | `sessionStorage` → هر نشست یک بار | پرچم مشترک |
| `safeSet._warned` | هر بارگذاری صفحه یک بار | پرچم مشترک |
| `safeSetBatch._warned` | هر بارگذاری صفحه یک بار | پرچم مشترک |
| `installWriteHook._warned` | هر بارگذاری صفحه یک بار | پرچم مشترک |

**Re-arm (تسلیح مجدد):** `rearmIfRecovered()` در هر بارگذاری چک می‌کند؛ اگر مصرف زیر **۸۰٪** بیاید پرچم برداشته می‌شود. پس اگر کاربر فضا آزاد کند و بعداً دوباره پر شود، **یک** هشدار تازه می‌گیرد — نه بیشتر.

**تست (۷/۷ + ۱۴/۱۴):** اولین پر شدن = دقیقاً ۱ هشدار · ۵ رفرش بعدی = صفر · آزادسازی = پرچم برداشته شد · پر شدن دوباره = ۱ هشدار تازه · ۳ رفرش بعدی = صفر.

**⚠️ نکته:** کلیدهای یتیم (`symbolsCache` و…) به تصمیم کاربر **دست‌نخورده** ماندند. یعنی حافظه همچنان پر می‌ماند؛ فقط هشدارش دیگر تکرار نمی‌شود. داده در IndexedDB سالم است.

### 📱 محافظ در دو آینهٔ اندرویدی (v106)

`fund-automation-android/.../webapp/usage/index.html` و `restricted/android/.../restricted/index.html` تنها صفحاتی بودند که `localStorage` داشتند ولی محافظ نداشتند. اکنون `<script src="../storage-guard.js">` در ابتدای `<head>` هر دو تزریق شده است.

**نکته:** تغییر در `assets` اندروید فقط با **بیلد و نصب مجدد APK** به گوشی می‌رسد.

### 🪞 آینهٔ کامل + آزادسازی فضای یتیم (v107)

**مسئله:** هوک `installWriteHook` فقط نوشتن‌های **بعد از نصب** را آینه می‌کرد. کلیدهایی که پیش از v104 نوشته شده بودند (مثل `baharan_percents`، `energy_fund_synergy`، `symbolsCache`) هیچ آینه‌ای در IndexedDB نداشتند — شکاف مهاجرت. تست با صفحهٔ خام (بدون محافظ) این شکاف را ثابت کرد.

**راه‌حل — دو تابع جدید در `storage-guard.js`:**

| تابع | کار |
|---|---|
| `mirrorAll(opts)` | هر کلید localStorage که در IndexedDB نیست را کپی می‌کند. **هرگز کلید موجود را بازنویسی نمی‌کند** (سایه ممکن است تازه‌تر باشد). یک بار در هر نشست (`sessionStorage.emarat_mirror_all_done`). |
| `freeVerifiedSpace()` | فقط کلیدهای `ORPHAN_KEYS` را آزاد می‌کند، و **فقط اگر** کپیِ بایت‌به‌بایت یکسان در IndexedDB موجود باشد. |

**فهرست سفید `ORPHAN_KEYS`** (۹ کلید، هیچ‌کدام در مخزن خوانده نمی‌شوند — با `grep` تأیید شد):
`symbolsCache`, `navAnalysisDatasets`, `navChartListDatasets`, `navAnalysisData`, `navAnalysisMeta`, `navAnalysisCurrentId`, `navChartListCurrentId`, `navAnalysisMigratedToIDB_v1`, `marjan_images_v1`

**⚠️ چرا کلیدهای اپ‌ها آزاد نمی‌شوند؟** ۶۴۷ جا در کد `localStorage.getItem()` **همگام** می‌خواند و هیچ‌کدام `await` ندارند. IndexedDB ناهمگام است و نمی‌تواند جای `getItem` را بگیرد. اگر localStorage خالی شود، اپ‌ها `null` می‌بینند → همان باگ «چهار ماه عقب» ولی دائمی. پس **LS اصل است، IDB کپی**.

**جریان در `autoHealOnLoad`:**
```
shadowHeal() → اگر کلید غایبی بود، بازگردان + رفرش
     ↓
mirrorAll() → شکاف را ببند
     ↓
freeVerifiedSpace() → فقط یتیم‌های تأییدشده را آزاد کن
```

**نتایج تست:**
- تست واقعی‌نما (۱.۵۷ MB، ۱۵ کلید): حافظه به **۰.۰۴ MB** رسید (۹۷٪ آزاد)، ۳۰۰۰ ردیف NAV + ۸۰۰ نماد + ۵ تصویر کامل منتقل شدند، ۴۴۳ رکورد gold سالم.
- رگرسیون ۱۲/۱۲: مهاجرت ۱۲۵ رکورد، ۴ رفت‌وبرگشت، ۹ اپ بدون خطا، پاپ‌آپ یک‌باره.

**تله‌ها:**
1. `EmaratStorage.health()` **همگام** است، Promise نیست (`shadowAll` و `shadowCount` ناهمگام‌اند).
2. `shadowAll()` ردیف خام `{v, t}` برمی‌گرداند، نه `{value, at}` — `unwrapShadow()` را برای تبدیل استفاده کن.
3. `navAnalysisMigratedToIDB_v1 = 1` نشان می‌دهد آن اپ NAV خودش قبلاً مهاجرت کرده و کپی localStorage فقط باقی‌مانده بوده.

**بامپ:** `CACHE_NAME` → `emarat-portal-v107`.

### 💾 گیج دو محل ذخیره‌سازی در «جعبهٔ نجات» (v108)

**هدف:** کاربر با یک نگاه ببیند هر دو حافظه چقدر پر است، بدون خواندن عدد.

**دو گیج دایره‌ای SVG** (بدون کتابخانه، فقط `stroke-dasharray`/`stroke-dashoffset`):

| گیج | منبع | سهمیه |
|---|---|---|
| حافظهٔ معمولی | محاسبهٔ واقعی مجموع `key.length + value.length` | **اندازه‌گیری واقعی** با `EmaratStorage.probeQuota()` |
| حافظهٔ قدرتمند | `EmaratStorage.shadowAll()` | `navigator.storage.estimate().quota` |

**رنگ پویا:** سبز `<75٪` → زرد `75-89٪` → قرمز `≥90٪` (هم حلقه و هم نوار).

**سه چیپ آینه:** کلید در localStorage · کلید در IndexedDB · **بدون آینه** (سبز اگر صفر، زرد اگر شکاف).

#### 🚨 تلهٔ گران‌بها ۱ — سهمیهٔ هاردکد غلط است
اول `9.92` هاردکد گذاشتم (عدد رایج وبلاگ‌ها). تست واقعی نشان داد این مرورگر **۴.۵ MB** و `probeFreeMB` هم ۵۰MB در حالت خالی بود. سهمیه بین مرورگرها ۲.۵ / ۵ / ۱۰ MB متغیر است.
**درمان:** `probeQuota()` در `storage-guard.js` — با `rawSet` (نه `setItem`، تا هوک آینه اجرا نشود و IndexedDB بی‌دلیل پر نشود) تکه‌های ۵۱۲KB می‌نویسد، جمع می‌کند، پاک می‌کند. نتیجه در `_quotaProbe` کش می‌شود.

#### 🚨 تلهٔ گران‌بها ۲ — `navigator.storage.estimate().quota` سهمیهٔ IDB نیست
`quota` سهمیهٔ **کل مبدأ** است (اینجا ۱۰۲۴۰ MB = ۱۰GB). نمایش خام آن به‌صورت «۱۰۲۴۰ مگابایت» زشت است.
**درمان:** `fmtQuota()` + `quotaUnit()` — بالای ۱۰۲۴MB به گیگابایت تبدیل می‌شود → «۱۰ گیگابایت».

#### 🚨 تلهٔ گران‌بها ۳ — گرید در موبایل یک‌ستونه می‌شد
`grid-template-columns: 1fr 1fr` + `@media (max-width:400px){ 1fr }` باعث می‌شد در ۳۹۰px (رایج‌ترین عرض موبایل) کارت‌ها زیر هم بیفتند.
**درمان:** مدیاکوئری حذف شد و `min-width:0` روی `.store` گذاشته شد. حالا در ۳۶۰px هم کنار هم‌اند (۱۴۷px هر کدام).

#### تلهٔ ۴ — متن‌های ریز
اولین نسخه فونت ۹.۶px داشت. استاندارد اعمال‌شده: **حداقل ۱۰.۴px** برای متن‌های کمکی (`.store-tech`, `.store-note`, `.mirror-chip span`, `.gauge .cap`).

**اندازه‌گیری‌های نهایی (Puppeteer، ۳۹۰px):**
- کنتراست: کمترین **۵.۳۱** (حد AA = ۴.۵) — بقیه ۶.۳ تا ۱۲.۴
- همپوشانی: **۰**
- المان کوچک‌تر از ۳۶px: **۰**
- سرریز افقی: **۰** (در ۳۶۰/۳۹۰/۱۲۸۰)
- تست ۱۴/۱۴ پاس (۳ ویوپورت + حالت ۹۳٪ پر + رنگ قرمز)

**بامپ:** `CACHE_NAME` → `emarat-portal-v108`.

### 🐛 باگ «حافظه آزاد نشد» — دو ریشهٔ هم‌زمان (v109)

**نشانهٔ کاربر:** گیج می‌گفت «۴.۹۵ از ۴.۹۵ مگابایت — تقریباً پر» در حالی که IndexedDB همه را داشت. یعنی `freeVerifiedSpace()` هرگز اجرا نشده بود.

#### ریشهٔ ۱ — دروازهٔ غلط در `autoHealOnLoad` 🚨
```javascript
// غلط (v107/v108):
mirrorAll().then(function (m) {
    if (!m || !m.mirrored) return null;   // ← اگر آینه کامل بود، آزادسازی رد می‌شد
    return freeVerifiedSpace();
})
```
اگر آینه **از قبل** کامل بود (`mirrored === 0`)، آزادسازی **هرگز** اجرا نمی‌شد. این حالت دقیقاً روی گوشی کاربر رخ می‌داد: v107 آینه را ساخته بود، ولی نسخهٔ v108 آزاد نکرد چون چیزی برای آینه نمانده بود.

**درمان:** شرط حذف شد — `mirrorAll()` همیشه `freeVerifiedSpace()` را صدا می‌زند. آزادسازی خودش بررسی می‌کند که کپی یکسان هست یا نه، پس بی‌خطر است.

#### ریشهٔ ۲ — `shadowPutMany` «fire-and-forget» بود 🚨
```javascript
// غلط: هیچ Promise برنمی‌گرداند
function shadowPutMany(map) {
    openDB().then(function (db) { /* put */ });   // ← بدون return
}
```
`freeVerifiedSpace()` بلافاصله بعد از `mirrorAll()` اجرا می‌شد، در حالی که نوشتن IndexedDB هنوز تمام نشده بود → کپی «یکسان» پیدا نمی‌شد → کلید آزاد نمی‌شد.

**درمان:** `shadowPutMany` اکنون Promise برمی‌گرداند که با `tx.oncomplete` resolve می‌شود. `mirrorAll` هم منتظر آن می‌ماند.

#### باگ سوم — تکرار واحد
`fmtMB()` خودش «کیلو» می‌چسباند و HTML هم «مگابایت» ثابت داشت → «۱۹ کیلو MB».
**درمان:** `usedText()` واحد صحیح را خودش می‌دهد (کیلو/مگا/گیگا) و واحد سهمیه جدا در `<span id="unit*">` است.

#### تست تأیید (Puppeteer، دادهٔ ۱.۵۷ MB)
```
قبل:  localStorage 6 کلید | 1.57 MB
بعد:  localStorage 4 کلید | 0.02 MB   ← ۹۹٪ آزاد
      IndexedDB 10 کلید
      NAV=3000 ردیف ✅ · نماد=900 ✅ · تصویر=5 ✅ · gold=443 ✅
```
۷/۷ تست پاس.

**درس:** در زنجیرهٔ `A().then(B)`, هر تابع میانی **باید** Promise برگرداند، وگرنه `B` قبل از پایان `A` اجرا می‌شود. و هرگز یک عملیات حیاتی را پشت شرطی نگذار که ممکن است در حالت «از قبل انجام‌شده» غلط باشد.

**بامپ:** `CACHE_NAME` → `emarat-portal-v109`.

## 🧘 اسکرول محترم در اپ‌های چت (`chat-autoscroll.js`)

### مشکل
در حین استریم پاسخ، هر توکن یک اسکرول اجباری به پایین می‌داد. پاسخ ۳۰۰ کلمه‌ای = **۳۰۰ اسکرول**. کاربر نمی‌توانست متن قبلی را بخواند؛ هر بار که بالا می‌رفت، فوراً به کف پرت می‌شد.

### سه مقصر واقعی
1. **`scrollToBottom()` در callback استریم** — با هر توکن صدا زده می‌شد (`second-brain/app.js`, `simple-chat`, `ai-chat`).
2. **`scroll-behavior: smooth`** روی `.chat-viewport` — هر اسکرول ۳۰۰ms انیمیشن داشت؛ ۳۰۰ اسکرول روی هم = گیر.
3. **`visualViewport.resize`** — باز/بسته شدن کیبورد هم اسکرول اجباری می‌داد.

### ماژول مشترک: `chat-autoscroll.js` (ریشهٔ مخزن)
```html
<script src="../chat-autoscroll.js"></script>   <!-- باید در <head> باشد -->
```
```javascript
EmaratAutoScroll.attach(chatContainer);   // یک‌بار در init
EmaratAutoScroll.toBottom();              // اسکرول محترم
EmaratAutoScroll.toBottom(true);          // اسکرول اجباری (پیام خود کاربر)
EmaratAutoScroll.beginStream();           // شروع استریم
EmaratAutoScroll.endStream();             // پایان (در finally)
```

### رفتار
| وضعیت | نتیجه |
|---|---|
| کاربر در کف (فاصله ≤ ۸۰px) | اسکرول خودکار ادامه دارد |
| کاربر خودش بالا رفت (فاصله > ۱۴۰px) | اسکرول متوقف، دکمهٔ شناور ظاهر می‌شود |
| کلیک «⬇️ پیام جدید» | پرش به کف + خاموش شدن دکمه |
| کاربر پیام خودش را فرستاد (`force`) | اسکرول اجباری به کف |
| کیبورد باز/بسته شد | فقط اگر در کف بود، اسکرول می‌کند |

### 🚨 درس گران‌بها ۱ — ترتیب بارگذاری اسکریپت
`simple-chat` و `ai-chat` اسکریپت را **انتهای `<body>`** داشتند، ولی `attach()` در **وسط** اسکریپت اصلی صدا زده می‌شد → `window.EmaratAutoScroll` هنوز `undefined` بود → دکمه ساخته نمی‌شد (بی‌صدا).
**درمان:** اسکریپت به `<head>` منتقل شد. **قانون:** هر ماژول مشترکی که در init صدا زده می‌شود، باید **قبل از** اسکریپت اصلی بار شود.

### 🚨 درس گران‌بها ۲ — `bottom: calc(100% + 10px)`
دکمه را **بالای** والدش می‌گذاشت → `y = -54` (بیرون از viewport، دیده نمی‌شد).
**درمان:** `bottom: var(--emr-rb-offset, 16px)` و `placeBtn()` که فاصله را از **بالای نوار ارسال** حساب می‌کند (نه از کف ظرف).

### 🚨 درس گران‌بها ۳ — `smooth` حین استریم
`scroll-behavior: smooth` در حین استریم باعث می‌شد هر `scrollTop =` یک انیمیشن ۳۰۰ms بسازد و کاربر «کشیده» شود.
**درمان:** کلاس `.emr-streaming { scroll-behavior: auto !important }` که `beginStream()` می‌گذارد و `endStream()` برمی‌دارد.

### ✅ استریم لحظه‌به‌لحظه دست‌نخورده ماند
تست: ۲۳ کلمه توکن‌به‌توکن، همه رندر شدند، متن کامل، رشد تدریجی، مارک‌داون (`**bold**` + لیست) سالم.

### تست‌ها
- **۱۳/۱۳** ماژول مستقل (auto-scroll، حفظ موقعیت، دکمه، force، ۴۴px، aria)
- **۲۱/۲۱** روی سه اپ واقعی
- **۱۸/۱۸** بصری (در viewport، بدون تداخل، کنتراست **۱۳.۱۴**، ≥۴۴px)
- **۶/۶** استریم زنده + مارک‌داون

### اتصال
| مورد | مقدار |
|---|---|
| `sw.js` | `'./chat-autoscroll.js'` در ASSETS |
| `CACHE_NAME` | `emarat-portal-v110` |
| اپ‌ها | `second-brain`, `simple-chat`, `ai-chat` |
| شاخه | `Y-9` → `main` |

## 🧱 محافظ سرریز محتوای پیام در «مغز دوم» (v111)

### مشکل
«بعضی مواقع پیام‌های هوش مصنوعی سرریز می‌شود و پشت پلتفرم می‌ریزد، دیده نمی‌شود.»

### ریشهٔ واقعی (اندازه‌گیری‌شده، نه حدس)
`.chat-viewport` دارای `overflow-x: hidden` است؛ پس **هر چیزی که پهن‌تر از قاب شود بی‌رحمانه بریده و ناپدید می‌شود**.

سه مسیر سرریز پیدا شد:

| مسیر | چرا | اندازهٔ واقعی |
|---|---|---|
| **کد با تورفتگی ۴ فاصله** | marked آن را `<pre>` خام می‌سازد؛ **هیچ CSS‌ای برای `pre` نبود** (`overflow-x: visible`، `white-space: pre`) | محتوا ۸۰۴px در قاب ۳۳۴px (۲.۴ برابر) — **کارت هم به ۶۶۵px شکسته می‌شد** |
| جدول ۲۰ ستونه | `min-width: 320px` روی `.table-scroll table` | روی صفحهٔ باریک‌تر از ۳۲۰px سرریز می‌ساخت |
| تصویر بزرگ | هیچ `max-width` نداشت | می‌توانست قاب را بشکند |

**نکتهٔ کلیدی:** کدِ **فنس‌دار** (` ``` `) سالم بود چون `CodeRenderer` کارت با `.code-card-body { overflow-x: auto }` می‌سازد. فقط کد **تورفته** می‌شکست — و مدل‌ها اغلب کد را با تورفتگی می‌دهند، پس «بعضی مواقع» دقیقاً همین بود.

### درمان (دو لایه)
**۱) CSS محافظ (پس‌زمینهٔ امن):**
- `.msg-row`, `.msg-card`, `.msg-body` → `min-width: 0; max-width: 100%`
- `.msg-body pre` → `overflow-x: auto` + قاب + `direction: ltr`
- `.msg-body code` → `overflow-wrap: anywhere`
- `.code-card`, `.table-card`, `.chart-card`, `.math-block-scroll`, `.json-tree-wrap`, `.sb-callout`, `.sb-stats-grid` → `max-width: 100%`
- `.table-scroll table` → `min-width: min(320px, 100%)`
- `.msg-body img` → `max-width: 100%; height: auto`

**۲) ارتقای کد تورفته (`enhanceRawCodeBlocks`):**
هر `<pre>` بدون `.code-card` به کارت حرفه‌ای `CodeRenderer` تبدیل می‌شود → شمارهٔ خط، رنگ‌آمیزی، کپی، جمع‌کردن.

### 🚨 دام: `min-width: 0` الزامی است
در چیدمان flex، فرزند به‌طور پیش‌فرض `min-width: auto` دارد و **کوچک‌تر از محتوایش نمی‌شود**. بدون `min-width: 0`، حتی `max-width: 100%` هم کار نمی‌کند.

### ✅ تست (۲۴/۲۴)
۸ حالت × ۲ (عادی/استریم): کد تورفته، JSON تورفته، کد فنس‌دار، فنس ناتمام حین استریم، URL بلند، کلمهٔ بدون فاصله، جدول ۲۰ ستونه، کارت آمار.
معیار: هیچ عنصری «بیرون از viewport و بدون نیای اسکرول‌پذیر» نباشد + `bodyScrollWidth ≤ clientWidth` + بدون اسکرول افقی صفحه.
رگرسیون: تیتر/پررنگ/مورب/لیست/نقل‌قول/جدول/کد فنس‌دار (دقیقاً **۱** کارت، نه دو) — همه سالم.

### اتصال
`CACHE_NAME` → `emarat-portal-v111` · شاخه `Y-9` → `main`

## 📝 پیش‌نویس‌ها و ویرایش درجای پیام در «مغز دوم» (v112)

### قانون حاکم: **هیچ‌چیز هرگز پاک نمی‌شود**
تصمیم صریح کاربر: «من می‌خوام هیچی پاک نشه». این قانون بر همهٔ تصمیم‌های طراحی اولویت دارد.
هر جا کد می‌توانست چیزی را حذف کند، به‌جایش **آرشیو** می‌کند (`archived: true`).

### زیرساخت: IndexedDB (نه localStorage)
- `dbVersion` از **۱ به ۲** رفت و انبار `drafts` اضافه شد.
- **🚨 ارتقای امن:** بلوک `onupgradeneeded` فقط `if (!db.objectStoreNames.contains(...))` است. هرگز `deleteObjectStore` صدا زده نمی‌شود، پس `conversations`/`secrets`/`presets` و همهٔ گفتگوهای کاربر دست‌نخورده می‌مانند. تست ۱ تأیید می‌کند هر چهار انبار پس از ارتقا وجود دارند.
- `putMany()` برای نوشتن دسته‌ای اضافه شد.

### کلاس `DraftManager` (انبار `drafts`)
دو نوع رکورد در یک انبار، با فیلد `kind`:

| `kind` | معنی | فیلدها |
|---|---|---|
| `draft` | متنی که نوشتی و نفرستادی | `id, convId, text, createdAt, updatedAt, archived, consumedAt?` |
| `revision` | نسخهٔ قبلی یک پیام | `id, msgId, convId, text, label, createdAt` |

متدها: `saveDraft`, `liveDrafts`, `archivedDrafts`, `findForConversation`, `archiveDraft`, `consumeDraft`, `revisionsOf`, `addRevision`, `clearDrafts`.

- `MAX_DRAFTS = 60` — قدیمی‌ترها **آرشیو** می‌شوند، حذف نمی‌شوند.
- ارسال پیام → `consumeDraft()` (آرشیو، نه حذف).
- خالی کردن کادر تایپ → پیش‌نویس آرشیو می‌شود (متن حفظ می‌شود).

### ذخیرهٔ خودکار پیش‌نویس
- **debounce ۵۰۰ms** روی هر `input` (`scheduleDraftSave`).
- **flush فوری** روی `pagehide` / `beforeunload` / `visibilitychange === 'hidden'` (`flushDraftSave`).
- بازگردانی خودکار پیش‌نویسِ گفتگوی فعال در `bootstrap()` (`restoreActiveDraft`) — **فقط اگر کادر تایپ خالی باشد** تا نوشتهٔ کاربر را پایمال نکند.

### 🚨 تلهٔ `openModal` / `closeModal`
این‌ها **متد کلاس `AppController`** هستند، نه تابع سراسری. صدا زدن `openModal('x')` بدون `this.` خطای `openModal is not defined` می‌دهد و مودال باز نمی‌شود (باگ واقعی که تست گرفت). همیشه `this.openModal(...)`.

### ویرایش درجا (`openInlineUserEdit`)
- `async` است (نسخه‌ها را از IndexedDB می‌خواند) — **باید `await` شود**.
- حباب خودش به `textarea` تبدیل می‌شود (`bodyEl.innerHTML = ''` سپس `.edit-msg-box`).
- سه دکمه:
  - **💾 ذخیره** — فقط متن را عوض می‌کند. هیچ پیامی حذف نمی‌شود.
  - **📤 ذخیره و ارسال مجدد** — متن را عوض می‌کند **و** یک پیام کاربر تازه در انتها `push` می‌کند. **هیچ `slice()` وجود ندارد.**
  - **✕ انصراف**
- قبل از هر ویرایش، `addRevision(msgId, convId, original, 'قبل از ویرایش')` اجرا می‌شود.
- نوار «🕘 N نسخهٔ قبلی» **همیشه** رندر می‌شود (حتی وقتی خالی است) تا وضعیت برای کاربر روشن باشد.
- کلیک روی چیپ نسخه → متن در textarea گذاشته می‌شود؛ ثبت با «💾 ذخیره».
- در حین استریم، ویرایش مسدود است (`isGenerating`).
- پیام ویرایش‌شده `editedAt` و `editCount` می‌گیرد → نشان «ویرایش‌شده» با tooltip زمان در هدر پیام.

### 🚨 تفاوت بنیادین با نسخهٔ قبل
```js
// قبل (داده از دست می‌رفت):
conv.messages = conv.messages.slice(0, idx + 1);

// بعد (هیچ‌چیز پاک نمی‌شود):
conv.messages.push({ ...newUserMsg, resentFrom: msgId });
```

### حباب فقط برای پیام کاربر
`.msg-row.assistant .msg-card` → `background: transparent; border-color: transparent`.
پاسخ مدل مثل یک مقالهٔ تمام‌عرض خوانده می‌شود؛ حباب فقط برای پیام‌های خود کاربر.

### پنل پیش‌نویس‌ها
- دکمهٔ `📝 پیش‌نویس‌ها` در نوار ابزار کامپوزر + نشان تعداد (`draftCountBadge`).
- مودال `draftsModal`: جست‌وجو + سوییچ `📦 آرشیو` / `↩️ بازگشت`.
- هر ردیف: پیش‌نمایش خط اول (۹۰ کاراکتر) + زمان + تعداد کاراکتر + نام گفتگو + سه دکمه (`↩️ ادامه`, `📋 کپی`, `📦 آرشیو`).
- «↩️ ادامه» اگر پیش‌نویس مربوط به گفتگوی دیگری باشد، **آن گفتگو را فعال می‌کند** و متن را در کادر می‌گذارد.

### ✅ تست‌ها (۴۷ تست، ۰ شکست)
| فایل | تعداد | پوشش |
|---|---|---|
| `t.js` | ۳۰ | ارتقای DB، ذخیره/بازیابی پیش‌نویس، پنل، حباب‌ها، ویرایش درجا، حفظ ۴ پیام، پایداری پس از رفرش، بازگشت به نسخهٔ قبلی |
| `reg.js` | ۸ | اتصال، dbVersion، اسکرول محترم، بستن مودال، صفر خطای کنسول |
| `flow.js` | ۹ | چرخهٔ کامل نوشتن→ارسال→آرشیو→پیش‌نویس جدید، بازگرداندن از آرشیو، جست‌وجو |
| `verify.js` (سرریز) | ۲۴ | رگرسیون محافظ سرریز — سالم ماند |

**تست کلیدی:** پس از ویرایش پیام میانی، `conv.messages.length === 4` باقی می‌ماند و پیام‌های ۳ و ۴ عیناً دست‌نخورده‌اند.

### 🐛 دو باگ واقعی که تست گرفت
1. `openModal is not defined` — متد کلاس بود، بدون `this.` صدا زده شده بود.
2. نوار نسخه‌های قبلی فقط وقتی نسخه وجود داشت رندر می‌شد → کاربر «هیچ» نمی‌دید و فکر می‌کرد قابلیت نیست.

### اتصال
`CACHE_NAME` → `emarat-portal-v112` · شاخه `Y-9` → `main`

## 🎛️ منوی کشویی ابزارها + آواتار پیام + فلش پیش‌نویس‌ها در «مغز دوم» (v113)

### ۱) منوی کشویی ابزارها (`.tools-menu-wrap`)
نوار پایین کامپوزر از **۳ دکمهٔ جدا + متن** به **یک دکمهٔ `⋯`** تبدیل شد.

| قبل | بعد |
|---|---|
| `[🌐 اینترنت: خاموش] [📎 فایل] [📝 پیش‌نویس‌ها]` | `[⋯ ●]` — یک دکمه |

- گزینه‌ها: `#btnWebToggle` · `#btnAttachFile` · `#btnOpenDrafts` — **همان شناسه‌های قبلی**، پس هیچ کد دیگری نشکست.
- **`aria-haspopup` + `aria-expanded` + `aria-controls` + `role="menu"`** برای دسترس‌پذیری.
- بسته‌شدن با: کلیک بیرون · کلید `Esc` · انتخاب هر گزینه (به‌جز سوییچ اینترنت که باز می‌ماند).
- موقعیت: `position: absolute; bottom: calc(100% + 8px); inset-inline-end: 0` — همیشه بالای دکمه، داخل صفحه.
- `max-height: 60vh; overflow-y: auto` برای صفحه‌های کوتاه.

### 🚨 نکتهٔ حیاتی: وضعیت اینترنت نباید پنهان شود
چون متن «اینترنت: روشن/خاموش» داخل منو رفت، یک **نقطهٔ وضعیت** روی خود دکمهٔ `⋯` گذاشته شد:
- `.tools-dot` خاکستری = خاموش · `.tools-dot.on` سبز + هاله = روشن
- متد `syncToolsDot()` در `syncHeaderAndToggles()` صدا زده می‌شود (همان‌جا که تم/مدل به‌روز می‌شود).

### ۲) دکمهٔ توقف دیده نمی‌شود
`#btnStopMsg` **در DOM می‌ماند** (برای سازگاری و تست) ولی `hidden` + `display:none` است.

به‌جایش، **دکمهٔ ارسال نقش توقف می‌گیرد** — متد `syncSendButtonMode()`:

| حالت | متن | کلاس | tooltip |
|---|---|---|---|
| عادی | `➤` | — | ارسال پیام |
| در حین تولید | `■` | `.is-stopping` (پس‌زمینهٔ قرمز) | توقف فوری تولید |

- کلیک `#btnSendMsg`: اگر `isGenerating` → `stopGeneration()`، وگرنه `handleSend()`.
- `syncSendButtonMode()` در سه نقطه صدا زده می‌شود: شروع تولید، `finally` پایان، و `syncHeaderAndToggles()`.

### ۳) علامت (آواتار) کنار حباب پیام کاربر
- هر پیام `role === 'user'` یک `<span class="msg-avatar">👤</span>` می‌گیرد و ردیف کلاس `has-avatar` می‌گیرد.
- چیدمان: `.msg-row.user.has-avatar { display: grid; grid-template-columns: auto minmax(0,1fr); }`
- **`minmax(0, 1fr)` الزامی است** — بدون آن، ستون دوم کوچک‌تر از محتوایش نمی‌شود و سرریز برمی‌گردد.
- پاسخ مدل آواتار **نمی‌گیرد** (حباب هم ندارد).

### ۴) فلش جابه‌جایی بین پیش‌نویس‌ها
نوار `.draft-nav` در مودال پیش‌نویس‌ها:

```
[▲]  ۲ / ۵  [▼]              [↩️ استفاده]
```

- `#btnDraftPrev` / `#btnDraftNext` / `#btnDraftUse` + `#draftNavCounter`
- کلیدهای **`ArrowUp` / `ArrowDown`** و **`Enter`** داخل مودال (وقتی فوکوس روی جست‌وجو نیست).
- ردیف انتخاب‌شده `.is-focused` می‌گیرد (قاب accent + نوار کناری) و `scrollIntoView({block:'nearest'})`.
- کلیک روی ردیف = انتخاب · **دابل‌کلیک = استفادهٔ فوری**.
- متدهای `currentDraftItems()` / `moveDraftFocus()` / `highlightDraftRow()` / `useFocusedDraft()` / `applyDraftToComposer()`.

### 🚨 باگ واقعی که تست گرفت
`moveDraftFocus()` شمارنده را به‌روز می‌کرد ولی **وضعیت `disabled` فلش‌ها را نه** → در آخرین پیش‌نویس، فلش «بعدی» همچنان فعال می‌ماند و کاربر فکر می‌کرد پیش‌نویس بیشتری هست. درمان: `highlightDraftRow()` حالا `disabled` هر سه کنترل را هم همگام می‌کند.

### ✅ تست‌ها (۱۰۶ تست، ۰ شکست)
| فایل | تعداد | پوشش |
|---|---|---|
| `t2.js` | ۳۵ | منو (باز/بسته/بیرون/Esc/موقعیت)، حذف دکمه‌های قدیمی، نقطهٔ اینترنت، توقف روی دکمهٔ ارسال، آواتار، فلش پیش‌نویس، استفاده با فلش |
| `t.js` | ۳۰ | پیش‌نویس/ویرایش/IndexedDB (رگرسیون) |
| `flow.js` | ۹ | چرخهٔ کامل پیش‌نویس (رگرسیون) |
| `reg.js` | ۸ | اتصال‌ها + صفر خطای کنسول (رگرسیون) |
| `verify.js` | ۲۴ | محافظ سرریز (رگرسیون) |

### اتصال
`CACHE_NAME` → `emarat-portal-v113` · شاخه `Y-9` → `main`

## 🔧 رفع سه باگ چیدمان + فلش نسخه‌های پیام در «مغز دوم» (v114)

### 🚨 باگ ۱ — مربع فیروزه‌ای «۰» همیشه دیده می‌شد
**نشانه:** کنار دکمهٔ ابزارها یک مربع فیروزه‌ای ۱۸×۱۸ با متن `0` بود، حتی با صفر پیش‌نویس.

**دو ریشهٔ هم‌زمان:**
1. **`[hidden]` بی‌اثر بود.** `.draft-count-badge { display: inline-flex }` ویژگی `hidden` مرورگر (`display:none`) را بازنویسی می‌کرد. اندازه‌گیری: `hidden=true` ولی `display="flex"`.
2. **`String(0).toLocaleString('fa-IR')` عدد را فارسی نمی‌کند.** `String.prototype.toLocaleString` همان `toString` است → `"0"` لاتین می‌ماند.

**درمان:**
```css
[hidden] { display: none !important; }
```
```js
badge.textContent = count === 0 ? '' : (count > 9 ? '۹+' : count.toLocaleString('fa-IR'));
badge.hidden = count === 0;
```
**درس:** `Number.prototype.toLocaleString` فارسی می‌سازد، ولی `String.prototype.toLocaleString` **هیچ کاری نمی‌کند**. همیشه اول `Number` باشد.

### 🚨 باگ ۲ — دکمهٔ `⋯` دیده نمی‌شد (زیر متن می‌رفت)
**نشانه:** کاربر گفت «دکمهٔ ابزارها را نمی‌بینم».

**ریشه:** `.composer-toolbar` مقدار `flex-wrap: wrap` داشت و متن `ارسال متن ساده…` با `white-space: nowrap` عرض **۲۳۸px** می‌خواست. مجموع با دکمه (۷۰px) از عرض ۳۷۰px بیشتر می‌شد → `⋯` به **سطر دوم** رانده می‌شد.

**درمان:** متن حذف شد + `flex-wrap: nowrap` + `justify-content: flex-start`.

### 🚨 باگ ۳ — منو از لبهٔ صفحه بیرون می‌زد
**نشانه:** منو باز می‌شد ولی نیمی از آن بیرون viewport بود (تست: `inVp=false`).

**ریشه — تلهٔ RTL:** در `dir="rtl"`، **`inset-inline-end` به `left` نگاشت می‌شود**، نه `right`.
اندازه‌گیری واقعی:

| مقدار | `left` محاسبه‌شده | نتیجه |
|---|---|---|
| `inset-inline-end: 0` | `left: 0` | منو از ۳۳۳ تا ۵۶۵ → **بیرون صفحه** ❌ |
| `inset-inline-start: 0` | `right: 0` | منو از ۱۴۸ تا ۳۸۰ → **داخل** ✅ |

**درمان:** `inset-inline-start: 0` (یعنی راست در RTL).
**درس:** در RTL، «شروع» = راست و «پایان» = چپ. هر جا می‌خواهی چیزی به لبهٔ **راست** بچسبد، `inset-inline-start` است.

### 🚨 باگ ۴ — ترتیب نسخه‌ها می‌پرید
**نشانه:** سه نسخه پشت‌سرهم ساخته می‌شد، ولی فلش قبلی ترتیب اشتباه می‌داد.

**ریشه:** `addRevision` از `Date.now()` استفاده می‌کرد. سه فراخوانی در **یک میلی‌ثانیه** → `createdAt` یکسان → `sort` بی‌ثبات.

**درمان:** زمان اکیداً صعودی:
```js
const createdAt = Math.max(Date.now(), (this._lastRevisionAt || 0) + 1);
this._lastRevisionAt = createdAt;
```
**درس:** هر ترتیب‌دهی بر پایهٔ `Date.now()` باید یک «تضمین یکتایی» داشته باشد؛ وگرنه عملیات دسته‌ای آن را می‌شکند.

### ✨ گزینهٔ 🅰️ — فلش نسخه‌ها کنار حباب پیام
`buildRevisionNav(msg, bodyEl)` در `buildMessageActions` برای پیام‌های کاربر:

```
[✏️ ویرایش] [📤 ارسال مجدد] [📋 کپی] [📝 پیش‌نویس]  [◀ ۳/۴ ▶]
```

- نسخه‌ها: `revisionsOf(msg.id)` معکوس (قدیمی → جدید) + متن فعلی به‌عنوان آخرین نسخه.
- شروع از نسخهٔ فعلی (`idx = length - 1`).
- `◀ ▶` متن حباب (`.user-plain-body`) را همان‌جا عوض می‌کنند — **بدون ورود به حالت ویرایش**.
- پیام بدون نسخه: `۱/۱` + `.is-empty` + هر دو فلش غیرفعال (به‌جای مخفی‌کردن نوار).
- **`📝 پیش‌نویس`** = متن پیام را به پیش‌نویس‌ها می‌فرستد (بدون حذف پیام).
- پاسخ مدل **نوار ندارد** (فقط پیام‌های کاربر).

### ✅ تست‌ها (۱۳۸ تست، ۰ شکست)
| فایل | تعداد | پوشش |
|---|---|---|
| `t3.js` | ۳۲ | نشان پنهان، حذف متن، دکمهٔ یک‌خطی راست، منو داخل صفحه، فلش نسخه‌ها، چرخهٔ کامل، حالت خالی |
| `t2.js` | ۳۵ | منوی ابزارها + آواتار + فلش پیش‌نویس (رگرسیون) |
| `t.js` | ۳۰ | پیش‌نویس/ویرایش/IndexedDB (رگرسیون) |
| `flow.js` | ۹ | چرخهٔ پیش‌نویس (رگرسیون) |
| `reg.js` | ۸ | اتصال‌ها (رگرسیون) |
| `verify.js` | ۲۴ | محافظ سرریز (رگرسیون) |

### 🧪 روش تشخیص که جواب داد
1. `getComputedStyle` + `getBoundingClientRect` برای هر عنصر → معلوم شد `hidden` بی‌اثر است و منو بیرون است.
2. **ردیابی نویسندهٔ `textContent`** با `Object.defineProperty` روی `Node.prototype` → معلوم شد `refreshDraftBadge` مقدار `"0"` می‌نویسد.
3. تست جداگانهٔ نگاشت `inset-inline-*` در RTL با اندازه‌گیری `left`/`right` محاسبه‌شده.

### اتصال
`CACHE_NAME` → `emarat-portal-v114` · شاخه `Y-9` → `main`

## 🚨 رفع تداخل کلید ذخیره‌سازی (بازگشت چهار ماهه) + تنظیم طول پاسخ و محافظه‌کاری (v115)

### 🔴 باگ بحرانی ۱ — کلید مشترک `github_backup_filepath`
**نشانهٔ کاربر:** «وقتی آپدیت یا وب‌اپ جدید می‌آید، بعضی مواقع کلیدها قدیمی جایگزین می‌شوند و محاسبات چهار ماه به عقب برمی‌گردند.»

**ریشه (اثبات‌شده با تست):** `gold3/price.html`، `gold5/price.html` و `gold6/price.html` همه از **یک کلید مشترک** استفاده می‌کردند:

```
۱. gold3/price.html → setItem('github_backup_filepath', 'backups/gold3_price_backup.json')
۲. gold5/price.html → setItem('github_backup_filepath', 'backups/synergy_price_backup.json')  ← بازنویسی!
۳. بازگشت به gold3 → مسیر حالا به فایل بکاپ gold5 اشاره می‌کند
۴. gold5 قیمت‌های چهار ماه پیش دارد → روی gold3 می‌نشیند
```

**نکتهٔ مهم:** `percent.html` ها از قبل کلید اختصاصی داشتند (`github_backup_filepath_gold3`)، ولی `price.html` ها نه. همین ناهمگونی، منبع این باگ بود.

**درمان — سه بخش:**
```javascript
const FILEPATH_KEY = "github_backup_filepath_gold3";
const DEFAULT_FILEPATH = "backups/gold3_price_backup.json";

// مهاجرت یک‌باره هنگام بارگذاری صفحه (نه هنگام آپلود — نسخهٔ اول تنبل بود
// و فرم تنظیمات مقدار قدیمی را نشان نمی‌داد)
(function migrateLegacyFilepath() {
    try {
        if (localStorage.getItem(FILEPATH_KEY)) return;
        const legacy = localStorage.getItem("github_backup_filepath");
        if (legacy && legacy.indexOf("gold3") !== -1) {
            localStorage.setItem(FILEPATH_KEY, legacy);
        }
    } catch (_) {}
})();
```
- **فیلتر `indexOf(key)`:** مقدار قدیمی فقط اگر مربوط به همین اپ باشد مهاجرت می‌کند؛ وگرنه مقدار gold5 به gold3 منتقل می‌شد.
- **اجرای سطح‌ماژول:** تضمین می‌کند `openGithubSettings()` هم مقدار درست را ببیند.
- **درس:** هر کلید `localStorage` که در بیش از یک اپ خوانده/نوشته می‌شود، **ذاتاً** باگ است. یک origin مشترک = یک فضای نام مشترک.

### 🔴 باگ بحرانی ۲ — گارد `cloud-sync` نسخهٔ کهنه را روی دادهٔ تازه می‌نشاند
**ریشه:**
```javascript
const isLocalEmpty = localStorage.length <= 2;  // ❌
```
این شمارش **همهٔ** کلیدها را می‌شمرد: تم، تنظیمات، توکن گیت‌هاب. با یک کلید تنظیمات (`sb_settings_v1`)، `length = 1 ≤ 2` می‌شد و کل بکاپ ابری روی گوشی می‌نشست.

**درمان — شمارش داده‌محور:**
```javascript
const DATA_KEY_PATTERN = /(_percents$|_history$|_baseNumber$|_peakNumber$|^percents$|^trash$|^gold_percents$|_prices_|_prices$|_percents_|fundManagerV10|emarat_family_tree|calculatorTab_)/;
let localDataKeys = 0;
for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (IGNORED_KEYS.indexOf(k) !== -1) continue;
    if (k.indexOf('emarat_usage_stats') === 0 || k.indexOf('emr_usage_') === 0) continue;
    if (DATA_KEY_PATTERN.test(k)) localDataKeys++;
}
const isLocalEmpty = localDataKeys === 0;
```
**درس:** «آیا داده دارم؟» با «آیا کلید دارم؟» یکی نیست. تنظیمات، تم و توکن **داده** نیستند.

### ✨ قابلیت ۱ — چهار سطح طول پاسخ
`RESPONSE_LENGTHS` در `second-brain/app.js`:

| سطح | `max_tokens` | توضیح |
|---|---|---|
| `short` | ۵۱۲ | پاسخ فشرده و بدون حاشیه |
| `medium` | ۲٬۰۴۸ | متعادل (پیش‌فرض) |
| `long` | ۸٬۱۹۲ | مفصل با مثال |
| `max` | ۳۲٬۷۶۸ | تا جای ممکن — تا سقف مدل |

- UI: `#lengthPresets` چهار دکمهٔ رادیویی با آیکون ارتفاع (`▁▄▆█`)، اندازهٔ لمس ۷۹×۶۲px.
- `applyLengthLevel(level)` کلاس `.active` را جابه‌جا می‌کند و `#setMaxTokens` را همگام می‌کند (فیلد عددی دستی حفظ شده).
- `max_tokens: RESPONSE_LENGTHS[d.responseLength]?.tokens || Number(d.maxTokens) || 2048`
- **هزینه:** سطح «حداکثر» گران‌تر و کندتر است — در `#lengthHelp` صریح گفته می‌شود.

### ✨ قابلیت ۲ — اسلایدر «محافظه‌کاری پاسخ» (۰..۱۰۰)
`buildEthicsDirective(level)` یک **system message جداگانه** می‌سازد؛ دستورالعمل پایهٔ کاربر دست‌نخورده می‌ماند:

```javascript
const ethicsDirective = buildEthicsDirective(d.ethicsLevel);
const outMessages = messages.slice();
const firstSystemIdx = outMessages.findIndex((m) => m.role === 'system');
if (firstSystemIdx === -1) {
    outMessages.unshift({ role: 'system', content: ethicsDirective });
} else {
    outMessages[firstSystemIdx] = {
        ...outMessages[firstSystemIdx],
        content: `${outMessages[firstSystemIdx].content}\n\n${ethicsDirective}`
    };
}
```

پنج باند: `≤۱۵` آزادتر · `≤۴۰` کمی آزادتر · `≤۶۵` متعادل · `≤۸۵` محافظه‌کار · `>۸۵` سخت‌گیرتر.

**⚠️ محدودیت صادقانه (در UI هم نوشته شده):** این تنظیم فقط **لحن و میزان احتیاط** را تغییر می‌دهد. فیلترهای ایمنی خودِ سرویس‌دهندهٔ مدل همیشه فعال‌اند و از سمت کلاینت قابل خاموش‌شدن نیستند.

### ✅ تست‌ها (۱۷۰ تست، ۰ شکست)
| فایل | تعداد | پوشش |
|---|---|---|
| `t4.js` | ۲۵ | چهار سطح، اسلایدر، ذخیره/بازگشایی، تزریق `max_tokens`، حفظ دستورالعمل پایه |
| `t6.js` | ۷ | مهاجرت خودکار، رد مقدار اپ دیگر، فرم تنظیمات، پیش‌فرض، استقلال gold3/gold5 |
| `t3.js` | ۳۲ | رگرسیون v114 |
| `t2.js` | ۳۵ | رگرسیون v113 |
| `t.js` | ۳۰ | رگرسیون v112 |
| `flow.js` | ۹ | رگرسیون پیش‌نویس |
| `reg.js` | ۸ | رگرسیون اتصال |
| `verify.js` | ۲۴ | رگرسیون سرریز |

### 🧪 روش تشخیص
1. **اسکن برنامه‌ای همهٔ کلیدها** در ۹ اپ و مقایسهٔ جفتی → کلیدهای تکراری پیدا شدند.
2. **شبیه‌سازی سناریوی کاربر** (gold3 → gold5 → gold3) در Node → فاجعه اثبات شد.
3. **تست مرورگر واقعی** با seed کردن مقدار قدیمی و `reload` → مهاجرت تأیید شد.

### اتصال
`CACHE_NAME` → `emarat-portal-v115` · شاخه `Y-7` → `main`

### 🔁 انتقال دکمهٔ ابزارها به سمت چپ (v116)
**درخواست:** «دکمه ابزارها سمت چپ باشد».

**نکتهٔ حیاتی — جابه‌جایی دکمه به‌تنهایی کافی نیست:**
دکمه و منو یک جفت هستند. اگر فقط `justify-content` عوض شود، منو دوباره از لبهٔ صفحه بیرون می‌زند (همان باگ v114، برعکس).

| تغییر | قبل | بعد |
|---|---|---|
| `.composer-toolbar` → `justify-content` | `flex-start` (راست در RTL) | `flex-end` (چپ در RTL) |
| `.tools-menu` → `inset-inline-*` | `inset-inline-start: 0` | `inset-inline-end: 0` |

**نگاشت در RTL:**
- `flex-start` = راست · `flex-end` = چپ
- `inset-inline-start` = راست · `inset-inline-end` = چپ

دکمه در چپ است → منو باید به **راست** باز شود → یعنی `inset-inline-end: 0`.

**اندازه‌گیری واقعی (Puppeteer، ۳۹۰px):**
- دکمه: `left 10 → right 57` (سمت چپ نوار) ✅
- منو: `left 10 → right 242` از عرض `390` → کامل داخل صفحه ✅
- عرض ۳۲۰px: هم داخل صفحه ✅
- سرریز افقی: صفر ✅

**تست:** `t7.js` ۱۲ تست (چپ بودن، داخل صفحه در ۳۹۰ و ۳۲۰، جهت باز شدن، بسته شدن با کلیک بیرون، صفر سرریز).
**تست قدیمی `t3.js`:** انتظار «سمت راست» به «سمت چپ» به‌روزرسانی شد — تغییر عمدی طراحی، نه باگ.

`CACHE_NAME` → `emarat-portal-v116` · شاخه `Y-7` → `main`

## 📤 ارسال گزارش تصویری باکیفیت به تلگرام (دستورالعمل تکرارپذیر)

### 🚨 چرا Pillow کافی نیست
Pillow فونت فارسی را **شکل‌دهی (shaping)** نمی‌کند — حروف جدا از هم می‌آیند («س ل ا م» به‌جای «سلام») و اتصالات خراب می‌شود. برای فارسی همیشه **Chromium** رندر کن.

### 🚨 دام بزرگ: سقف ابعاد تلگرام
`sendPhoto` تصویر را به **حداکثر ۲۵۶۰px در ضلع بزرگ‌تر** فشرده می‌کند. اگر تصویر بزرگ‌تر باشد، تلگرام آن را مچاله می‌کند و **متن تار می‌شود** — دقیقاً همان چیزی که نباید اتفاق بیفتد.

| رویکرد | ابعاد | نتیجه |
|---|---|---|
| تک‌ستونی، `deviceScaleFactor: 3` | ۳۵۴۰×۵۴۹۳ | ❌ تلگرام فشرده می‌کند → تار |
| **دو‌ستونی، `deviceScaleFactor: 2`** | **۲۴۸۰×۱۶۶۶** | ✅ زیر سقف، متن تیز |

**قانون:** قبل از ارسال، `max(width, height) <= 2560` را بررسی کن. اگر بیشتر بود، **چیدمان را فشرده کن** (دو‌ستونی/سه‌ستونی) نه اینکه scale را کم کنی.

### 🎯 دستور پخت رندر تیز

```javascript
const b = await puppeteer.launch({
  executablePath: '/usr/bin/chromium',
  args: ['--no-sandbox', '--allow-file-access-from-files',
         '--font-render-hinting=none',   // جلوگیری از hinting ناهموار
         '--disable-lcd-text',           // بدون subpixel (برای PNG بهتر)
         '--force-color-profile=srgb'],
  headless: true
});
await pg.setViewport({ width: 1240, height: 1000, deviceScaleFactor: 2 });
await pg.goto('file:///tmp/docimg/report.html', { waitUntil: 'networkidle0' });
await pg.evaluate(() => document.fonts.ready);   // ← حیاتی: بدون این فونت لود نشده رندر می‌شود
await new Promise(r => setTimeout(r, 1000));
const h = await pg.evaluate(() => document.body.scrollHeight);
await pg.setViewport({ width: 1240, height: h, deviceScaleFactor: 2 });
await (await pg.$('body')).screenshot({ path: 'final.png', type: 'png' });
```

**نکته:** `element.screenshot()` روی `body` بهتر از `fullPage: true` است — دقیقاً به اندازهٔ محتوا عکس می‌گیرد و حاشیهٔ اضافی نمی‌گذارد.

### 🔤 فونت آفلاین
`vendor/vazirmatn/fonts/Vazirmatn-{Regular,Bold}.woff2` با `@font-face` و مسیر **مطلق** (`/workspace/project/.../fonts/...`) در `file://` کار می‌کند.
بعد از `goto`، **`document.fonts.ready`** را `await` کن؛ وگرنه متن با فونت پیش‌فرض رندر می‌شود.

### 📏 سنجش کیفیت (بدون OCR)
Tesseract در این محیط نیست. جایگزین: **واریانس لاپلاسی**.

```python
from PIL import Image, ImageFilter
import statistics
im = Image.open('final.png').convert('L')
crop = im.crop((60, int(h*0.30), w-60, int(h*0.75)))   # ناحیهٔ متن
lap = crop.filter(ImageFilter.Kernel((3,3), [-1,-1,-1,-1,8,-1,-1,-1,-1], scale=1, offset=128))
var = statistics.pvariance(list(lap.get_flattened_data()))
# بالای ۲۰۰ = تیز · زیر ۵۰ = تار
```
اندازه‌گیری واقعی این گزارش: **۱۱۷۳** (خیلی تیز) ✅

### 📨 ارسال
```bash
curl -s -F "chat_id=-1002617482597" \
     -F "photo=@/tmp/docimg/final.png" \
     -F "caption=<caption.txt" \
     "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendPhoto"
```
- `caption=<file` (نه `caption="$VAR"`) — برای متن چندخطی فارسی امن‌تر است.
- **سقف کپشن `sendPhoto` = ۱۰۲۴ کاراکتر.** بیشتر → `Bad Request: message caption is too long`.
- برای فایل بزرگ‌تر/بدون فشرده‌سازی: `sendDocument` (تا ۵۰MB).

### 📍 کانال
`TELEGRAM_CHAT_ID` در محیط نیست. با `getChat` از بین شناسه‌های موجود در مخزن انتخاب شد:

| شناسه | نتیجه |
|---|---|
| `-1003757877147` | ❌ chat not found |
| **`-1002617482597`** | ✅ channel «دنیا های قشنگ» |

اگر `getUpdates` خالی بود (هیچ آپدیت تازه‌ای نبود)، `getChat` روی شناسه‌های کاندید را امتحان کن.


---

## 🛡️ قانون مالکیت کلیدهای ذخیره‌سازی (Key Ownership Constitution)

> 🚨 **این قانون از یک باگ واقعیِ نابودکنندهٔ داده زاده شد. قبل از هر تغییر در `storage-guard.js` بخوانید.**

### ریشهٔ باگ (v103 → v107)
`storage-guard.js` در `autoHealOnLoad()` — که **هر بار با لود شدن هر صفحه** اجرا می‌شود — تابع `freeVerifiedSpace()` را صدا می‌زد. آن تابع ۹ کلید را «یتیم» می‌شمرد و **از `localStorage` حذف می‌کرد**:

```
symbolsCache · navAnalysisDatasets · navChartListDatasets · navAnalysisData
navAnalysisMeta · navAnalysisCurrentId · navChartListCurrentId
navAnalysisMigratedToIDB_v1 · marjan_images_v1
```

محتوای واقعی‌شان (از بکاپ ۵٫۶MB کاربر) **دادهٔ آپلودی** بود، نه کش:

| کلید | محتوا |
|---|---|
| `symbolsCache` | ۸ نماد بورسی — عیار ۱٬۹۹۷ روز (۱۳۹۷/۰۳/۱۲..۱۴۰۵/۰۷/۰۴)، آبادا ۱٬۴۹۷ روز |
| `navChartListDatasets` | دیتاست ۳٬۸۷۵ روزه (۱۳۹۴/۱۱/۱۷ تا ۱۴۰۵/۰۶/۲۴) |
| `navAnalysisDatasets` | ۳ دیتاست: ۳٬۸۷۵ + ۵۰۶ + ۱۱۴ روز |
| `navAnalysisData` | ۵۰۶ روز NAV |
| `marjan_images_v1` | ۵ تصویر base64 (WebP + JPEG) |

### 🎯 درس کلیدی
**«یتیم» یعنی «هیچ صفحه‌ای در مخزن فعلی نمی‌خواند» — نه «بی‌ارزش» و نه «کش».**
اپی که این کلیدها را می‌نوشت از مخزن حذف شده بود. شرط «کپی یکسان در IndexedDB» هم نجات نمی‌داد، چون فقط یعنی «جای دیگری هست»، نه «کاربر نمی‌خواهد».

### ✅ قوانین الزامی
۱. **`ORPHAN_KEYS` فقط برای کش واقعیِ بازتولیدشدنی.** هر کلیدی که کاربر یا اپ ساخته (آپلود، تاریخچه، تصویر، توکن) هرگز در این فهرست نمی‌آید.
۲. **هر کلید داده‌ای باید مالک داشته باشد** در `KEY_OWNERS` (ثبت‌شده در `storage-guard.js`). `freeVerifiedSpace` قبل از هر حذف `isProtected(k)` را می‌سنجد — گارد دوم، حتی اگر کلید به `ORPHAN_KEYS` برگردد.
۳. **اپ جدید** باید در اولین لود خود ثبت مالکیت کند:
   ```html
   <script src="../storage-guard.js"></script>
   <script>
   if (window.EmaratStorage) window.EmaratStorage.registerOwner('myapp_', 'نام اپ');
   </script>
   ```
۴. **پیشوند کلید باید یکتا باشد** و با نام اپ هم‌خوان. `html_viewer_` = نمایشگر کد (۱۳ کلید).
۵. **قبل از هر تغییر در `freeVerifiedSpace`** با Chromium تست کن: کلید داده‌ای seed کن → `mirrorAll()` + `freeVerifiedSpace()` → بررسی `alive` و `freed.length === 0`.

### 📤 API عمومی
```javascript
EmaratStorage.KEY_OWNERS          // نقشهٔ پیشوند → نام اپ
EmaratStorage.ownerOf(key)        // نام مالک یا null
EmaratStorage.registerOwner(p,a)  // ثبت مالکیت در زمان اجرا
EmaratStorage.isProtected(key)    // true اگر مالک داشته باشد
```

---

## 💾 بکاپ کامل رمزگذاری‌شده (monitor/index.html)

### دو خروجی، دو هدف
| خروجی | محتوا | رمز |
|---|---|---|
| **فایل محلی** (دانلود) | `_meta` + `data` (همهٔ localStorage) + `_shadow` (سایهٔ IndexedDB) | 🔓 همیشه بدون رمز |
| **ابر کلودفلر** | اگر `cf_backup_pass` تنظیم شده باشد → پوشش رمزگذاری‌شده؛ وگرنه فقط `data` | 🔐 اختیاری |

### قالب فایل محلی (v2)
```json
{ "_meta": { "format":"emarat-full-backup-v2", "localStorageKeys":362,
             "shadowKeys":0, "ownedCounts":{"نمایشگر کد":13}, "hasIndexedDB":true },
  "data": { "key":"value", ... },
  "_shadow": { "key":"value", ... } }
```

### پوشش رمزگذاری‌شده
```json
{ "_meta": { "format":"emarat-encrypted-v1", "kdf":"PBKDF2-SHA256",
             "iterations":310000, "cipher":"AES-GCM-256", "salt":"…", "iv":"…" },
  "payload": "base64(ciphertext)" }
```
پیاده‌سازی: `crypto.subtle` بومی مرورگر — **بدون کتابخانهٔ خارجی** (قانون آفلاین). توابع: `bkEncrypt` / `bkDecrypt` / `collectFullBackup`.

### ⚠️ ریسک‌ها
- **رمز فراموش‌شده = بکاپ ابری از دست رفته.** هیچ راه بازیابی وجود ندارد (کلید از رمز مشتق می‌شود). فایل محلی نجات‌دهنده است.
- PBKDF2 با ۳۱۰٬۰۰۰ دور روی گوشی قدیمی ۱–۲ ثانیه طول می‌کشد — عمدی است.
- `cf_backup_pass` فقط در `localStorage` همان مرورگر است؛ بین دستگاه‌ها منتقل نمی‌شود.

### بازیابی — سه قالب پذیرفته می‌شود
۱. **مسطح قدیمی** (`{gold_history:"…"}`) → سازگاری کامل با بکاپ‌های قبل از v117
۲. **v2** (`{_meta, data, _shadow}`) → سایهٔ IndexedDB هم بازگردانده می‌شود
۳. **رمزگذاری‌شده** → رمز پرسیده می‌شود؛ رمز غلط پیام تمیز می‌دهد، داده را خراب نمی‌کند

---

## 🔐 وضعیت رازها (بررسی‌شده با git history)

| راز | در گیت فعلی | در تاریخچهٔ گیت | در بکاپ ابری |
|---|---|---|---|
| سشن تلگرام (`BAGUY…`) | ✅ **نه** | ✅ **نه** (۰ کامیت) | ⚠️ بله |
| توکن CF (`cfut_…`) | ⚠️ در `monitor/index.html` (تکه‌تکه) | 🔴 بله (`4fafe8a`) | — |
| کلید Gemini (`AQ.Ab8…`) | ⚠️ در `gym/index.html` (atob) | 🔴 بله (`0cb2e2b`) | — |

**تصمیم کاربر:** توکن‌ها **حفظ شدند** تا اپ‌ها نیاز به وارد کردن دستی نداشته باشند. `getCfBackupToken()` اکنون توکن `localStorage` را در اولویت می‌گذارد تا امکان چرخش بدون تغییر کد باشد.

**⚠️ برای امنیت کامل:** توکن CF و کلید Gemini را در کنسول ارائه‌دهنده **باطل** کنید — حذف از کد کافی نیست چون در تاریخچه باقی می‌مانند.

### `_incoming/` — هرگز کامیت نمی‌شود
بکاپ‌های محلی حاوی ۲۸ راز هستند (شامل `restricted_bot_tgSession`). در `.gitignore:53` هستند و روی ریموت وجود ندارند (تأیید با API: HTTP 404).

### 🔴 ادامهٔ باگ — چهار فایل باقی‌مانده (v118)

رفع v115 فقط `price.html` های gold3/gold5/gold6 را درست کرد. **چهار فایل دیگر هنوز کلید مشترک را می‌نوشتند** و همان بازگشت چند ماهه را می‌ساختند:

| فایل | کلید تازه |
|---|---|
| `gym/index.html` | `github_backup_filepath_gym` |
| `skincare/index.html` | `github_backup_filepath_skincare` |
| `ai-chat/index.html` | `github_backup_filepath_ai_chat` |
| `fund-automation-android/.../webapp/gold5/price.html` | `github_backup_filepath_gold5` |

**نکته:** آینهٔ اندروید از رفع v115 جا مانده بود — همان دام «همگام‌سازی آینه» که در بخش‌های دیگر هم تکرار شده.

**الگوی درست (سه بخش، هر سه لازم):**
```javascript
const FILEPATH_KEY = "github_backup_filepath_<app>";
const DEFAULT_FILEPATH = "backups/<app>_backup.json";
(function migrateLegacyFilepath() {           // مهاجرت یک‌باره
    try {
        if (localStorage.getItem(FILEPATH_KEY)) return;
        const legacy = localStorage.getItem("github_backup_filepath");
        if (legacy && legacy.indexOf("<app>") !== -1) {   // ← فیلتر اجباری
            localStorage.setItem(FILEPATH_KEY, legacy);
        }
    } catch (_) {}
})();
// همهٔ خواندن/نوشتن‌ها با FILEPATH_KEY — نه رشتهٔ ثابت
```
**فیلتر `indexOf(app)` حیاتی است:** بدون آن، مسیر gold5 به gold3 منتقل می‌شود و باگ فقط جابه‌جا می‌شود.

**بررسی خودکار:**
```bash
grep -rn 'setItem(\s*"github_backup_filepath"' --include=*.html .   # باید صفر باشد
grep -rn 'getItem(\s*"github_backup_filepath"' --include=*.html .   # فقط داخل migrateLegacyFilepath
```
**تست (Chromium، شبکه مسدود):** سه صفحه را پشت‌سرهم باز کن، مسیر هرکدام را جدا ذخیره کن، سپس بررسی کن که هر کلید مقدار خودش را دارد و `github_backup_filepath` خالی مانده.

**gold7/gold8/gold9:** `price.html` آن‌ها هیچ بکاپ گیت‌هابی ندارد (صفر ارجاع) → این باگ در آن‌ها وجود ندارد.

`CACHE_NAME` → `emarat-portal-v118`
