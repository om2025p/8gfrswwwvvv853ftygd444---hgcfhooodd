# 📌 وضعیت پروژه و نقطهٔ ادامه (وضعیت در ۱۴۰۵/۰۸/۲۸)

این سند «عکس فوری» وضعیت پروژه است تا اگر چند روز بعد کار ادامه یافت،
هیچ چیز از دست نرود. **همه‌چیز در گیت ذخیره شده است** — چیزی فقط در حافظهٔ
سرور نیست.

---

## ✅ آخرین وضعیت تثبیت‌شده

| مورد | مقدار |
|---|---|
| نسخهٔ اپ | **۱٫۹٫۰** (versionCode 10) |
| کامیت | `1654781` — روی `main` **و** `S-15` |
| امضای APK | `SHA-256 4603b639c0ed4480630c6db3598e5112f97b85f4aed6ac55d501b886b94e9585` (پایدار) |
| تست‌ها | **۴۴ تست JVM، ۰ شکست** |
| ریلیز | `fund-automation-v1.9.0` (ID: 449762908) با APK ۶٫۸۸MB |

**دانلود APK:**
`https://github.com/om2025p/8gfrswwwvvv853ftygd444---hgcfhooodd/releases/download/fund-automation-v1.9.0/fund-automation-v1.9.0.apk`

---

## 🔧 کارهایی که در v1.9.0 انجام شد (تثبیت‌شده)

### سه باگ بحرانی که اتوماسیون را کاملاً از کار انداخته بود

1. **پایهٔ سینرژی، عدد آتیه خوانده می‌شد.**
   صفحات وب‌اپ روی `file://` هستند و در WebView اندروید **همه یک origin
   مشترک** دارند → `localStorage` مشترک. اسکریپت خواندن مشترک (`READ_SCRIPT`)
   همیشه اول `mofid_atie_history` را برمی‌گرداند.
   **درمان:** `ATIE_READ_SCRIPT` و `SYNERGY_READ_SCRIPT` جدا + پارامتر الزامی
   `fund` در `WebAppReader.manualEntries/lastHistoryBase`.

2. **«امروز دستی ثبت شده» دروغین.**
   `manualEntries` نامش «دستی» بود ولی فیلتر `manual` را اعمال **نمی‌کرد**؛
   پس رکورد خودِ اتوماسیون (`source=automation`) هم «ثبت دستی امروز» شمرده
   می‌شد و اپ خودش را رد می‌کرد.
   **درمان:** `.filter { it.manual }`.

3. **استخراج آتیه هرگز اجرا نشد** — نتیجهٔ زنجیره‌ای باگ ۲.

### افزودهٔ گزینه ب: موتور محاسبهٔ خودِ وب‌اپ

- فایل جدید **`WebAppCalculator.kt`**: صفحهٔ `goldN/calculator.html` را در
  WebView باز می‌کند، دو عدد را در فیلدهای خودش می‌گذارد و **تابع خودش**
  (`calculateAndSave(false)`) را صدا می‌زند تا **نوع تغییر**
  (increase/recovering/decrease) و **قله** عیناً از منطق وب‌اپ بیاید.
- **درصد با دقت ۶ رقم از اپ** محاسبه می‌شود (وب‌اپ فقط `toFixed(2)` می‌دهد و
  همان باگ «۰٫۰۰٪» بود).
- `calculateAndSave(false)` یعنی **تاریخچه را وب‌اپ نمی‌نویسد**؛ نوشتن با
  اسکریپت اپ انجام می‌شود تا فیلد `source=automation` حفظ شود. اگر مستقیم
  `addPercent()` صدا زده می‌شد، رکورد **بدون `source`** ذخیره می‌شد و باگ ۲
  **برمی‌گشت**.
- `WebAppStore.buildInjectScript` پارامتر `peak: Long?` گرفت و قله را در
  `pension_peakNumber`/`sinergy_peakNumber` می‌نویسد.
- نگاشت «کلاس CSS → نوع تغییر» در `WebAppCalculator.typeFromClassName` و در
  **کاتلین** (نه در رشتهٔ JS) → قابل تست و مستقل از مرورگر.
- `FundOutcome` دو فیلد `engineType` و `enginePeak` گرفت.

### فایل‌های تغییریافته در v1.9.0

```
M  fund-automation-android/app/build.gradle                 (نسخه 1.8.0 → 1.9.0)
M  fund-automation-android/.../AutomationEngine.kt          (FundOutcome + فراخوانی موتور)
M  fund-automation-android/.../MainActivity.kt              (پاس دادن fund + قلهٔ موتور)
M  fund-automation-android/.../WebAppReader.kt              (اسکریپت جدا برای هر صندوق)
M  fund-automation-android/.../WebAppStore.kt               (پارامتر peak)
A  fund-automation-android/.../WebAppCalculator.kt          (جدید — موتور وب‌اپ)
A  fund-automation-android/.../ManualEntryFilterTest.kt     (جدید — ۷ تست)
M  AGENTS.md                                                (مستندسازی کامل باگ‌ها)
```

---

## 🔜 قدم بعدی پیشنهادی (وقتی کار ادامه یافت)

۱. **نصب APK v1.9.0 روی گوشی** و اجرای یک‌بارهٔ اتوماسیون.
   - انتظار: پایهٔ سینرژی باید `۲۱۹٬۰۹۹٬۲۶۵` ریال باشد (نه `۳۹۷٬۶۱۵٬۸۶۹`).
   - انتظار: هیچ پیام «امروز دستی ثبت شده» نباید بیاید.
   - لاگ جدید را برای بررسی بفرست.

۲. **بررسی لاگ واقعی** برای دیدن اینکه آیا موتور وب‌اپ
   (`🧮 موتور وب‌اپ: نوع=...`) پاسخ می‌دهد یا به fallback می‌رود.

۳. **مسئلهٔ باقی‌مانده (حل‌نشده):** در بکاپ `gold4/gold4_backup.json`،
   ۲۹ رکورد `percents` وجود دارد که بسیاری `value: 0` با
   `source: "automation"` هستند. این‌ها از نسخه‌های قدیمی‌اند. اگر لازم شد،
   می‌توان پاک‌سازی کرد — **ولی نیاز به تأیید صریح کاربر دارد**.

---

## 🔐 کارهای امنیتی که منتظر تأیید کاربر است

| # | مورد | وضعیت |
|---|---|---|
| ۱ | **توکن گیت‌هاب** که در مکالمه فرستاده شد (`ghp_VAIf...`) | ⚠️ **باید revoke شود** — در متن پیام ثبت شده |
| ۲ | `gold5/easytrader_session.json` (۲۱KB) در مخزن **Public** ردیابی می‌شود | ⚠️ نشست فعال کارگزاری علنی است — نیاز به تأیید برای حذف + `gitignore` + **باطل کردن نشست در ایزی‌تریدر** |
| ۳ | `git remote` به URL بدون توکن بازگردانده شد | ✅ انجام شد |

---

## 🧠 نکات فنی کلیدی (برای آینده)

- **origin مشترک `file://`:** هر صفحهٔ `file:///android_asset/webapp/...` در
  WebView اندروید `localStorage` **مشترک** دارد. پس هر خواندن/نوشتن **باید**
  صندوق را صریح مشخص کند.
- **صفحهٔ ماشین‌حساب vs تب درصد:**
  - `goldN/calculator.html` → کلیدهای `pension_*` / `sinergy_*` + منطق قله
  - `gold4/percent.html` → کلیدهای `mofid_atie_*` (دستهٔ موازی!)
  - `gold5/percent.html` → کلید `energy_fund_synergy` (شیء کامل)
- **`addPercent()` وب‌اپ فیلد `source` نمی‌گذارد** → هرگز برای ثبت خودکار
  استفاده نشود.
- **`calculateAndSave(false)`** یعنی بدون نوشتن تاریخچه — برای compute-only
  امن است.
- **بیلد:**
  ```bash
  export JAVA_HOME=/tmp/androidbuild/jdk17
  export ANDROID_HOME=/tmp/androidbuild/android-sdk
  export PATH=$JAVA_HOME/bin:/tmp/androidbuild/gradle-8.7/bin:$PATH
  cd fund-automation-android
  gradle testDebugUnitTest assembleDebug assembleRelease --no-daemon
  ```

---

## 📜 تاریخچهٔ نسخه‌ها

| نسخه | commit | تغییر کلیدی |
|---|---|---|
| 1.7.0 | — | نسخهٔ اولیهٔ اپ اندروید |
| 1.8.0 | `0d6737a` | رفع باگ «درصد ۰٫۰۰٪» + خواندن پایه از تاریخچه + انتظار هوشمند هیدریشن |
| **1.9.0** | **`1654781`** | **رفع پایهٔ اشتباه سینرژی + تشخیص تکراری دروغین + موتور محاسبهٔ وب‌اپ** |

---

> این سند توسط یک ایجنت هوش مصنوعی (OpenHands) ساخته شده است.
