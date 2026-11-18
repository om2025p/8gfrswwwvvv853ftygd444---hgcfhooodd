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
