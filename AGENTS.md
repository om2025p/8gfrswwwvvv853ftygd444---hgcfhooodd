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
