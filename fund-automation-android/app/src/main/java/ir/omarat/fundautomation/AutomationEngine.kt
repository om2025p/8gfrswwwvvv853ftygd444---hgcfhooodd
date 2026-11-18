package ir.omarat.fundautomation

import android.annotation.SuppressLint
import android.content.Context
import android.webkit.CookieManager
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import org.json.JSONTokener
import kotlin.coroutines.resume

/**
 * موتور اتوماسیون: یک WebView می‌سازد، خودش وارد سامانهٔ ایزی‌تریدر می‌شود،
 * دارایی دو صندوق را استخراج می‌کند و نتیجه را برمی‌گرداند.
 *
 * چرا WebView و نه کروم؟ چون کروم اجازه نمی‌دهد اپ دیگری داخل صفحه‌اش
 * دست ببرد (نه کلیک کند، نه عدد بخواند). پس اتوماسیون اجباراً داخل
 * WebView خودِ اپ انجام می‌شود.
 */
class AutomationEngine(
    private val context: Context,
    private val session: SessionStore,
    private val log: (String, LogLevel) -> Unit
) {

    enum class LogLevel { INFO, OK, WARN, ERROR }

    /** آخرین زمانی که یک صفحه با موفقیت بارگذاری شد (برای انتظار هوشمند). */
    @Volatile
    private var lastPageFinishedAt: Long = 0

    private var otpProvider: (suspend () -> String?)? = null

    /** روشی که برای استخراج هر صندوق موفق شد (برای گزارش). */
    private val methodByFund = HashMap<String, String>()

    /**
     * تاریخچهٔ دستی امروز (از کد قدیمی پایتون: `is_already_recorded_today`).
     *
     * اگر کاربر امروز خودش درصدی را دستی ثبت کرده باشد، اتوماسیون نباید
     * رکورد تکراری بسازد. ثبت‌های خودِ اتوماسیون (`source == "automation"`)
     * نادیده گرفته می‌شوند تا دوباره‌اجرا کردن در همان روز مسدود نشود.
     *
     * کلید: `"atie"` یا `"synergy"` — مقدار: مجموعهٔ روزهای شمسی ثبت‌شدهٔ دستی.
     */
    private val manualDaysByFund = HashMap<String, Set<String>>()

    /** آیا کاربر امروز برای این صندوق دستی ثبت کرده است؟ */
    private fun isRecordedTodayByUser(fund: String, jalaliDay: String): Boolean =
        manualDaysByFund[fund]?.contains(jalaliDay) == true

    /** برای درخواست کد OTP از کاربر (در صورت انقضای نشست). */
    fun setOtpProvider(provider: suspend () -> String?) {
        otpProvider = provider
    }

    /** نتیجهٔ کامل اجرا برای یک صندوق. */
    data class FundOutcome(
        val fund: String,
        val base: Long,
        val newValue: Long,
        val result: PercentResult,
        val method: String
    )

    /**
     * کل جریان: ورود → انتظار → استخراج → محاسبه → نوشتن در حافظهٔ وب‌اپ.
     *
     * نوشتن در `localStorage` **داخل همین WebView** انجام می‌شود، پیش از آنکه
     * WebView نابود شود؛ چون حافظه به همان نمونهٔ WebView گره خورده است.
     *
     * @param baseAtie    مقدار پایهٔ قبلی آتیه (ریال)
     * @param baseSynergy مقدار پایهٔ قبلی سینرژی (ریال)
     * @param peakAtie    قلهٔ قبلی آتیه
     * @param peakSynergy قلهٔ قبلی سینرژی
     */
    suspend fun run(
        baseAtie: Long?,
        baseSynergy: Long?,
        peakAtie: Long?,
        peakSynergy: Long?,
        onWebViewReady: (WebView) -> Unit
    ): List<FundOutcome> = withContext(Dispatchers.Main) {
        val webView = createWebView()
        onWebViewReady(webView)
        val outcomes = mutableListOf<FundOutcome>()

        try {
            log("🌐 باز کردن صفحهٔ پرتفوی ایزی‌تریدر…", LogLevel.INFO)
            webView.loadUrl(PORTFOLIO_URL)
            awaitPageLoaded(webView, timeoutMs = 45_000)
            delay(3_000)

            performLoginIfNeeded(webView)

            log("⏳ انتظار برای بارگذاری کامل اعداد (۸ ثانیه)…", LogLevel.INFO)
            delay(HYDRATION_DELAY_MS)

            // ── جلوگیری از ثبت تکراری ──────────────────────────────────────
            // اگر کاربر امروز دستی ثبت کرده باشد، صندوق دست‌نخورده می‌ماند.
            val today = JalaliDate.format(System.currentTimeMillis(), withTime = false)
            runCatching {
                val reader = WebAppReader(context)
                manualDaysByFund["atie"] = reader.manualEntries(WebAppReader.ATIE_PAGE)
                    .map { JalaliDate.format(it.timestampMs, withTime = false) }.toSet()
                manualDaysByFund["synergy"] = reader.manualEntries(WebAppReader.SYNERGY_PAGE)
                    .map { JalaliDate.format(it.timestampMs, withTime = false) }.toSet()
            }.onFailure { log("ℹ️ بررسی ثبت تکراری ناموفق: ${it.message}", LogLevel.INFO) }

            for ((fund, base, peak) in listOf(
                Triple("synergy", baseSynergy, peakSynergy),
                Triple("atie", baseAtie, peakAtie)
            )) {
                if (isRecordedTodayByUser(fund, today)) {
                    log(
                        "ℹ️ صندوق «${displayName(fund)}» امروز ($today) دستی ثبت شده؛ " +
                            "اتوماسیون دست‌نخورده رهایش می‌کند.",
                        LogLevel.WARN
                    )
                    continue
                }
                val value = extractFund(webView, fund) ?: continue
                if (base == null || base <= 0) {
                    log("⚠️ پایهٔ صندوق «${displayName(fund)}» تنظیم نشده؛ محاسبه رد شد.", LogLevel.WARN)
                    continue
                }
                val result = FundCalculator.calculate(base, value, peak) ?: continue
                outcomes += FundOutcome(fund, base, value, result, methodByFund[fund] ?: "unknown")
            }
            outcomes
        } finally {
            webView.destroy()
        }
    }

    // ------------------------------------------------------------------ WebView

    @SuppressLint("SetJavaScriptEnabled")
    private fun createWebView(): WebView {
        val wv = WebView(context)
        wv.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true           // localStorage — حیاتی
            databaseEnabled = true
            userAgentString = MOBILE_UA        // جلوگیری از پاپ‌آپ «مرورگر قدیمی»
            cacheMode = WebSettings.LOAD_DEFAULT
        }
        CookieManager.getInstance().setAcceptCookie(true)

        wv.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                // شنود پاسخ‌ها با تزریق fetch در صفحه انجام می‌شود، نه اینجا
                return null
            }

            override fun onPageStarted(view: WebView, url: String?, favicon: android.graphics.Bitmap?) {
                super.onPageStarted(view, url, favicon)
                lastPageFinishedAt = 0
                // تزریق زودهنگام شنود: پیش از اجرای اسکریپت‌های صفحه انجام می‌شود،
                // پس درخواست‌های اولیهٔ SPA (که حامل مقدار صندوق‌ها هستند) از دست نمی‌روند.
                installNetworkSniffer(view)
            }

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                lastPageFinishedAt = System.currentTimeMillis()
            }
        }
        return wv
    }

    /**
     * نصب شنود شبکه با تزریق در «شروع سند».
     *
     * `WebViewCompat.addDocumentStartJavaScript` اسکریپت را پیش از هر اسکریپت
     * صفحه اجرا می‌کند؛ پس `window.fetch` پیش از آنکه اپ SPA اولین درخواست‌ها
     * را بفرستد بازنویسی می‌شود. نسخهٔ پیشین فقط بعد از پایان بارگذاری تزریق
     * می‌کرد و درخواست‌های اولیه (حاوی مقادیر صندوق) را از دست می‌داد.
     */
    private fun installNetworkSniffer(webView: WebView) {
        try {
            WebViewCompat.addDocumentStartJavaScript(webView, SNIFFER_JS, setOf("*"))
        } catch (e: Exception) {
            log("⚠️ تزریق زودهنگام شنود ناموفق (fallback به روش قدیمی): ${e.message}", LogLevel.WARN)
        }
    }

    /** نسخهٔ async قدیمی برای سازگاری با مرورگرهای قدیمی که addDocumentStart را ندارند. */
    private suspend fun installNetworkSnifferAsync(webView: WebView) {
        evaluate(webView, SNIFFER_JS)
    }

    // ------------------------------------------------------------------ Login

    /**
     * اطمینان از رسیدن به صفحهٔ پرتفوی.
     *
     * جریان «پرتفوی-اول» است: پیش از این تابع، `portfolio-fill` لود شده است.
     * اگر واقعاً روی پرتفوی باشیم، کار تمام است؛ وگرنه ورود انجام می‌شود.
     *
     * تشخیص «روی پرتفوی بودن» **سختگیرانه** است: هاست باید `m.easytrader.ir`
     * باشد و مسیر باید `portfolio` داشته باشد. صفحهٔ تبلیغاتی عمومی
     * (`https://easytrader.ir/`) هرگز پرتفوی محسوب نمی‌شود؛ نسخهٔ پیشین با
     * شرط شل `url.contains("easytrader")` آن را پرتفوی می‌پنداشت و بدون ورود
     * از آن رد می‌شد — ریشهٔ شکست هر چهار لایه.
     */
    private suspend fun performLoginIfNeeded(webView: WebView) {
        // ── حالت ۱: از قبل روی پرتفوی هستیم ────────────────────────────────
        if (isOnPortfolio(webView)) {
            log("✅ نشست فعال است؛ مستقیم روی پرتفوی هستیم.", LogLevel.OK)
            dismissModals(webView)
            installNetworkSnifferAsync(webView)
            return
        }

        // ── حالت ۲: وسط فرایند ورود (auth-callback) ─────────────────────────
        // مفید کد مجوز صادر کرده؛ فقط باید صبر کنیم تا سایت خودش به پرتفوی برود.
        // اینجا **هرگز** به فرم ورود برنمی‌گردیم و **هرگز** رمز را دوباره
        // نمی‌فرستیم — همان اشتباهی که خطای دروغین «رمز اشتباه» را می‌ساخت.
        if (isAuthCallback(webView)) {
            log("🔁 ایستگاه ورود (auth-callback) شناسایی شد؛ انتظار برای تکمیل ورود…", LogLevel.INFO)
            if (waitForPortfolio(webView, timeoutMs = 45_000)) {
                log("✅ ورود کامل شد و روی پرتفوی هستیم.", LogLevel.OK)
                dismissModals(webView)
                installNetworkSnifferAsync(webView)
                return
            }
            log("⚠️ پس از auth-callback در ۴۵ ثانیه به پرتفوی نرسیدیم؛ دوباره تلاش می‌کنیم.", LogLevel.WARN)
        }

        // ── حالت ۳: واقعاً باید وارد شویم ───────────────────────────────────
        log("🔑 نشست معتبر نیست (${describeLocation(webView)})؛ ورود لازم است…", LogLevel.WARN)
        webView.loadUrl(LOGIN_URL)
        awaitPageLoaded(webView, timeoutMs = 45_000)
        delay(1_500)

        // اگر SSO از قبل نشست دارد، بی‌درنگ به auth-callback می‌رود و فرمی
        // نشان نمی‌دهد؛ در این حالت `fillLoginForm` مقدار false برمی‌گرداند.
        val submitted = fillLoginForm(webView)
        if (submitted) {
            log("📤 نام کاربری و رمز ارسال شد.", LogLevel.INFO)
        } else {
            log("ℹ️ فرم ورودی نبود؛ فرض می‌کنیم نشست SSO از قبل فعال است.", LogLevel.INFO)
        }
        awaitNavigation(webView, timeoutMs = 45_000)

        if (isOtpScreen(webView)) {
            // handleOtp خودش ترتیب درست را رعایت می‌کند: پر کردن کد → تیک دستگاه → ارسال
            handleOtp(webView)
        } else {
            // صفحهٔ OTP نبود؛ شاید تیک «دستگاه مورد اعتماد» روی همین صفحه باشد.
            if (tickTrustDevice(webView)) {
                log("☑ تیک «دستگاه مورد اعتماد» روی صفحهٔ ورود زده شد.", LogLevel.OK)
            }
        }

        // اگر ورود واقعاً شکست خورده باشد، مفید دوباره صفحهٔ فرم را نشان می‌دهد.
        if (submitted && isStillOnLoginForm(webView)) {
            throw IllegalStateException(
                "ورود ناموفق بود؛ صفحهٔ ورود دوباره نشان داده شد. " +
                    "نام کاربری یا رمز عبور را در تنظیمات بررسی کنید."
            )
        }

        // ── رفتن به پرتفوی + صبر هوشمند ────────────────────────────────────
        log("🌐 رفتن به صفحهٔ پرتفوی…", LogLevel.INFO)
        webView.loadUrl(PORTFOLIO_URL)
        awaitPageLoaded(webView, timeoutMs = 45_000)
        delay(2_000)
        dismissModals(webView)
        installNetworkSnifferAsync(webView)

        if (!waitForPortfolio(webView, timeoutMs = 45_000)) {
            throw IllegalStateException(
                "پس از ورود هم به صفحهٔ پرتفوی نرسیدیم (${describeLocation(webView)}). " +
                    "اگر نشست منقضی شده، یک‌بار با دکمهٔ «باز کردن وب‌اپ» وارد شوید و بعد دوباره اجرا کنید."
            )
        }
        log("✅ ورود موفق و روی پرتفوی هستیم.", LogLevel.OK)
    }

    /**
     * آیا هنوز روی فرم ورود ایستاده‌ایم؟ (نشانهٔ قطعی رمز/نام کاربری نادرست)
     *
     * فقط وقتی معنا دارد که فرم را واقعاً پر و ارسال کرده باشیم؛ اگر نشست SSO
     * فعال باشد، فرمی وجود ندارد و این تابع همیشه false می‌دهد.
     */
    private suspend fun isStillOnLoginForm(webView: WebView): Boolean {
        val u = currentUrl(webView).lowercase()
        if (!u.contains("login.emofid.com")) return false
        if (isAuthCallback(webView)) return false
        val body = bodyText(webView)
        return body.contains("رمز عبور") || body.contains("Password")
    }

    /** نشانی واقعی را برای لاگ توصیف می‌کند. */
    private suspend fun describeLocation(webView: WebView): String {
        val u = currentUrl(webView)
        return if (u.isBlank()) "نشانی نامعلوم" else u
    }

    /**
     * آیا WebView واقعاً روی صفحهٔ پرتفوی است؟
     *
     * فقط هاست `m.easytrader.ir` با مسیر `portfolio` پذیرفته می‌شود. صفحهٔ
     * تبلیغاتی `easytrader.ir` (بدون زیردامنهٔ `m.` و بدون مسیر پرتفوی)
     * پذیرفته **نمی‌شود**.
     */
    private suspend fun isOnPortfolio(webView: WebView): Boolean {
        val u = currentUrl(webView)
        if (!u.contains("m.easytrader.ir")) return false
        if (!u.contains("portfolio")) return false
        // صفحهٔ ورود یا تأیید، پرتفوی نیست
        return !isLoginOrVerify(webView)
    }

    /**
     * آیا صفحه در «میانهٔ فرایند ورود» است؟
     *
     * `auth-callback` ایستگاه میانی OIDC است: مفید کد مجوز (`code=...`) را
     * صادر کرده و سایت ایزی‌تریدر در حال تبدیل آن به نشست است. در این لحظه
     * URL نه «ورود» است و نه «پرتفوی»؛ یک وضعیت میانیِ کاملاً مشروع.
     *
     * نسخهٔ پیشین این ایستگاه را نمی‌شناخت و چون `auth-callback` واژهٔ
     * `portfolio` ندارد، آن را «ورود ناموفق» می‌پنداشت و به فرم ورود برمی‌گشت
     * → خطای دروغین «رمز/نام کاربری نادرست است».
     */
    private suspend fun isAuthCallback(webView: WebView): Boolean {
        val u = currentUrl(webView).lowercase()
        return u.contains("auth-callback") ||
            u.contains("signin-oidc") ||
            u.contains("callback") && u.contains("code=")
    }

    /**
     * انتظار فعال برای رسیدن به صفحهٔ پرتفوی.
     *
     * به‌جای یک مکث کور، هر ۱ ثانیه URL را می‌خواند و به‌محض رسیدن به
     * پرتفوی برمی‌گردد. اگر وسط راه صفحهٔ OTP ظاهر شد، آن را به کاربر
     * می‌سپارد و منتظر می‌ماند.
     *
     * @return `true` اگر در مهلت به پرتفوی رسیدیم.
     */
    private suspend fun waitForPortfolio(webView: WebView, timeoutMs: Long): Boolean {
        val deadline = System.currentTimeMillis() + timeoutMs
        var lastUrl = ""
        while (System.currentTimeMillis() < deadline) {
            if (isOnPortfolio(webView)) return true
            val u = currentUrl(webView)
            if (u != lastUrl) {
                log("   ↳ ایستگاه میانی: ${u.take(140)}", LogLevel.INFO)
                lastUrl = u
            }
            if (isOtpScreen(webView)) {
                log("🔐 صفحهٔ کد تأیید ظاهر شد؛ منتظر ورود دستی شما…", LogLevel.WARN)
                handleOtp(webView)
            }
            delay(1_000)
        }
        return isOnPortfolio(webView)
    }

    private suspend fun isLoginOrVerify(webView: WebView): Boolean {
        val u = currentUrl(webView).lowercase()
        if (u.contains("login.emofid.com") || u.contains("verify")) return true
        val body = bodyText(webView)
        return body.contains("رمز عبور") && body.contains("ورود")
    }

    /**
     * بستن مودال‌های مزاحمی که ممکن است روی اعداد پرتفوی بیفتند.
     *
     * اسکریپت پایتون همین کار را می‌کند؛ بدون آن، مودال می‌تواند اعداد را
     * پنهان کند و استخراج را بی‌نتیجه بگذارد.
     */
    private suspend fun dismissModals(webView: WebView) {
        val js = """
        (function(){
          var sels = ['button[aria-label*="close" i]','button[class*="close"]','div[class*="close"]',
                      'span[class*="close"]','button[class*="Close"]','[class*="modal"] button'];
          var texts = ['✕','×','بستن','انصراف','باشه','متوجه شدم','تایید'];
          var closed = 0;
          var cands = document.querySelectorAll(sels.join(','));
          for (var i=0;i<cands.length;i++){
            var el = cands[i];
            var t = (el.innerText || el.getAttribute('aria-label') || '').trim();
            var visible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            if (!visible) continue;
            if (t.length > 25) continue;
            try { el.click(); closed++; } catch(e){}
          }
          for (var j=0;j<texts.length;j++){
            var all = document.querySelectorAll('button,span,a,div');
            for (var k=0;k<all.length;k++){
              var e2 = all[k];
              if (e2.children.length > 0) continue;
              if ((e2.innerText || '').trim() !== texts[j]) continue;
              var vis2 = !!(e2.offsetWidth || e2.offsetHeight || e2.getClientRects().length);
              if (!vis2) continue;
              try { e2.click(); closed++; } catch(e){}
            }
          }
          return String(closed);
        })();
        """.trimIndent()
        val n = decodeJsonString(evaluate(webView, js) ?: "0").toIntOrNull() ?: 0
        if (n > 0) {
            log("🧹 $n مودال/پاپ‌آپ مزاحم بسته شد.", LogLevel.INFO)
            delay(1_500)
        }
    }

    /**
     * پر کردن فرم ورود.
     *
     * @return `true` اگر هر دو فیلد پر شدند؛ `false` اگر فرمی روی صفحه نبود.
     *
     * نکتهٔ مهم: «نبودن فرم» همیشه خطا نیست. اگر نشست SSO از قبل فعال باشد،
     * `login.emofid.com` بی‌درنگ به `auth-callback` ریدایرکت می‌کند و هیچ فرمی
     * نشان نمی‌دهد. نسخهٔ پیشین این حالت را «فرم پیدا نشد» لاگ می‌کرد و بعد
     * به‌سراغ ارسال فرم می‌رفت — همان زنجیره‌ای که به خطای دروغین «رمز اشتباه»
     * می‌رسید.
     */
    private suspend fun fillLoginForm(webView: WebView): Boolean {
        val user = jsonEscape(session.username)
        val pass = jsonEscape(session.password)
        val js = """
        (function(){
          function setVal(sel, val){
            var el = document.querySelector(sel);
            if(!el) return false;
            el.focus();
            el.value = val;
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            return true;
          }
          var userSel = ['input[name="Username"]','input#Username','input[name="username"]','input[type="text"]','input[type="email"]'];
          var passSel = ['input[name="Password"]','input#Password','input[name="password"]','input[type="password"]'];
          var okU=false, okP=false;
          for (var i=0;i<userSel.length && !okU;i++) okU = setVal(userSel[i], "$user");
          for (var j=0;j<passSel.length && !okP;j++) okP = setVal(passSel[j], "$pass");
          return (okU && okP) ? 'OK' : 'MISS';
        })();
        """.trimIndent()
        val res = evaluate(webView, js)
        val filled = res?.contains("OK") == true
        if (!filled) {
            log("ℹ️ فرم ورودی روی صفحه نبود (احتمالاً نشست SSO از قبل فعال است).", LogLevel.INFO)
        }

        delay(600)
        if (!filled) return false

        val submitJs = """
        (function(){
          var btn = document.querySelector('button[type="submit"], input[type="submit"], button.btn-primary, form button');
          if(btn){ btn.click(); return 'CLICKED'; }
          var form = document.querySelector('form');
          if(form){ form.submit(); return 'SUBMITTED'; }
          return 'NOFORM';
        })();
        """.trimIndent()
        evaluate(webView, submitJs)
        return true
    }

    private suspend fun isOtpScreen(webView: WebView): Boolean {
        val js = """
        (function(){
          var t = document.body ? document.body.innerText : '';
          var hasOtpWord = /کد تایید|کد تأیید|رمز یکبار|verification code|otp/i.test(t);
          var hasOtpInput = !!document.querySelector('input[inputmode="numeric"], input[name*="code" i], input[name*="otp" i], input[type="tel"]');
          return (hasOtpWord || hasOtpInput) ? 'YES' : 'NO';
        })();
        """.trimIndent()
        return evaluate(webView, js)?.contains("YES") == true
    }

    /**
     * پر کردن کد تأیید و **سپس** تیک «دستگاه مورد اعتماد» و **آخر** ارسال فرم.
     *
     * ⚠️ ترتیب حیاتی است و از کد قدیمی پایتون (`easytrader_automation.py`) گرفته
     * شده که با همین ترتیب کار می‌کرد:
     *   ۱. کد را در فیلد بگذار
     *   ۲. تیک «تایید دو مرحله برای این سیستم لازم نیست» را بزن
     *   ۳. دکمهٔ تأیید را بزن
     * نسخهٔ پیشین ابتدا فرم را ارسال می‌کرد و بعد می‌کوشید تیک بزند؛ ولی
     * صفحه عوض می‌شد و تیک هرگز زده نمی‌شد → هر بار OTP دوباره لازم بود.
     */
    private suspend fun handleOtp(webView: WebView) {
        log("🔐 کارگزاری کد تأیید (OTP) می‌خواهد. لطفاً کد را وارد کن…", LogLevel.WARN)
        val code = otpProvider?.invoke()
        if (code.isNullOrBlank()) {
            throw IllegalStateException("کد تأیید دریافت نشد؛ عملیات متوقف شد.")
        }
        val safeCode = jsonEscape(code)

        // گام ۱: پر کردن کد (بدون ارسال)
        val fillJs = """
        (function(){
          var sel = ['input[name="Token"]','input#Token','input[name="token"]','input#token',
                     'input[inputmode="numeric"]','input[type="tel"]','input[type="number"]',
                     'input[name*="code" i]','input[name*="otp" i]','input[placeholder*="کد"]',
                     'input[placeholder*="code"]','input[type="text"]'];
          var el = null;
          for (var i=0;i<sel.length && !el;i++){
            var c = document.querySelector(sel[i]);
            if (c && (c.offsetWidth || c.offsetHeight || c.getClientRects().length)) el = c;
          }
          if (!el) return 'NOINPUT';
          el.focus();
          el.value = "$safeCode";
          el.dispatchEvent(new Event('input', {bubbles:true}));
          el.dispatchEvent(new Event('change', {bubbles:true}));
          el.dispatchEvent(new Event('blur', {bubbles:true}));
          return 'FILLED';
        })();
        """.trimIndent()
        val fillRes = evaluate(webView, fillJs)
        if (fillRes?.contains("NOINPUT") == true) {
            log("⚠️ فیلد کد تأیید روی صفحه پیدا نشد.", LogLevel.WARN)
        } else {
            log("✅ کد تأیید در فیلد گذاشته شد.", LogLevel.OK)
        }
        delay(400)

        // گام ۲: تیک «تایید دو مرحله برای این سیستم لازم نیست»
        val ticked = tickTrustDevice(webView)
        delay(300)

        // گام ۳: ارسال فرم
        val submitJs = """
        (function(){
          var sel = ['button[type="submit"]','button#verifyBtn','button.btn-primary',
                     'input[type="submit"]','button'];
          for (var i=0;i<sel.length;i++){
            var b = document.querySelector(sel[i]);
            if (!b) continue;
            if (!(b.offsetWidth || b.offsetHeight || b.getClientRects().length)) continue;
            var t = (b.innerText || '').trim();
            if (t && !/ادامه|ورود|تایید|تأیید|ارسال|ثبت|submit|verify|confirm/i.test(t)) continue;
            b.click();
            return 'SUBMITTED';
          }
          var form = document.querySelector('form');
          if (form) { form.submit(); return 'SUBMITTED_FORM'; }
          return 'NOBUTTON';
        })();
        """.trimIndent()
        val submitRes = evaluate(webView, submitJs)
        log(
            if (ticked) "☑ تیک «دستگاه مورد اعتماد» زده شد و فرم ارسال گردید."
            else "📤 فرم تأیید ارسال شد (تیک دستگاه روی صفحه نبود).",
            LogLevel.OK
        )
        if (submitRes?.contains("NOBUTTON") == true) {
            log("⚠️ دکمهٔ تأیید پیدا نشد؛ ممکن است فرم با Enter ارسال شود.", LogLevel.WARN)
        }
        awaitNavigation(webView, timeoutMs = 45_000)
    }

    /**
     * تیک «تایید دو مرحله برای این سیستم لازم نیست».
     *
     * متن دقیق تیک از کد قدیمی پایتون گرفته شده؛ نسخهٔ پیشین فقط به کلیدواژه‌های
     * انگلیسی (`trust`/`remember`/`device`) تکیه می‌کرد و تیک فارسی را نمی‌دید.
     *
     * @return `true` اگر چک‌باکسی تیک خورد.
     */
    private suspend fun tickTrustDevice(webView: WebView): Boolean {
        val js = """
        (function(){
          function isVisible(el){
            return !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
          }
          var direct = ['input#TrustDevice','input[name*="TrustDevice" i]','input[name*="trust" i]',
                        'input[name*="remember" i]','input[name*="device" i]'];
          for (var i=0;i<direct.length;i++){
            var b = document.querySelector(direct[i]);
            if (b && isVisible(b)) {
              if (!b.checked) { b.click(); }
              return b.checked ? 'TRUST:1' : 'TRUST:0';
            }
          }
          // جستجوی متنی: هر چک‌باکسی که برچسبش «دستگاه/اعتماد/دو مرحله/به خاطر بسپار» دارد
          var boxes = document.querySelectorAll('input[type="checkbox"]');
          for (var j=0;j<boxes.length;j++){
            var c = boxes[j];
            if (!isVisible(c)) continue;
            var labelText = '';
            if (c.id) {
              var lab = document.querySelector('label[for="' + c.id + '"]');
              if (lab) labelText += ' ' + (lab.innerText || '');
            }
            var parent = c.parentElement;
            for (var lvl=0; lvl<3 && parent; lvl++){
              labelText += ' ' + (parent.innerText || '');
              parent = parent.parentElement;
            }
            labelText = labelText.replace(/\s+/g, ' ');
            if (/اعتماد|دستگاه|دو ?مرحله|به ?خاطر|یاد|trust|remember|device/i.test(labelText)) {
              if (!c.checked) { c.click(); }
              return c.checked ? 'TRUST:1' : 'TRUST:0';
            }
          }
          return 'TRUST:NONE';
        })();
        """.trimIndent()
        val r = evaluate(webView, js) ?: return false
        return r.contains("TRUST:1")
    }

    // ------------------------------------------------------------------ Extraction

    /**
     * استخراج مقدار یک صندوق با سه لایه + لایهٔ هوش مصنوعی.
     *
     * پیش از اسکن، تب «سایر» باز می‌شود؛ چون صندوق‌های مفید زیر آن تب قرار
     * دارند و در تب پیش‌فرض «سهام» هیچ‌کدام دیده نمی‌شوند.
     */
    private suspend fun extractFund(webView: WebView, fund: String): Long? {
        val keywords = if (fund == "synergy") SYNERGY_KEYWORDS else ATIE_KEYWORDS
        log("🔎 استخراج مقدار صندوق «${displayName(fund)}»…", LogLevel.INFO)
        log("🌐 نشانی فعلی: ${currentUrl(webView)}", LogLevel.INFO)

        navigateToFund(webView, fund)

        // لایهٔ ۱: شنود شبکه
        sniffFromNetwork(webView, fund)?.let {
            log("✔ [لایهٔ ۱ · شنود API] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "network"
            return it
        }
        log("✖ [لایهٔ ۱ · شنود API] نتیجه‌ای نداد.", LogLevel.INFO)

        val bodyText = bodyText(webView)
        if (bodyText.isBlank()) {
            log("⛔ متن صفحه خالی است؛ اسکن متن و DOM بی‌فایده‌اند.", LogLevel.ERROR)
        }

        // لایهٔ ۲: اسکن متن بدنه (با الگوی اختصاصی هر صندوق)
        scanBodyTextForFund(bodyText, keywords, fund)?.let {
            log("✔ [لایهٔ ۲ · اسکن متن] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "text"
            return it
        }
        log(
            "✖ [لایهٔ ۲ · اسکن متن] نتیجه‌ای نداد. کلیدواژه‌های «${keywords.joinToString("، ")}» " +
                "در متن: ${keywords.count { bodyText.contains(it) }} مورد",
            LogLevel.INFO
        )

        // لایهٔ ۳: پیمایش DOM
        scanDom(webView, keywords)?.let {
            log("✔ [لایهٔ ۳ · DOM] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "dom"
            return it
        }
        log("✖ [لایهٔ ۳ · DOM] نتیجه‌ای نداد.", LogLevel.INFO)

        // لایهٔ ۴: هوش مصنوعی
        log("🤖 سه لایهٔ معمولی شکست خورد؛ لایهٔ هوش مصنوعی امتحان می‌شود…", LogLevel.WARN)
        AiPageReader(session).extractFundValue(bodyText, keywords)?.let {
            log("✔ [لایهٔ ۴ · هوش مصنوعی] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "ai"
            return it
        }

        log("❌ استخراج صندوق «${displayName(fund)}» از هیچ لایه‌ای موفق نشد.", LogLevel.ERROR)
        return null
    }

    /**
     * بردن WebView به صفحه‌ای که مقدار صندوق در آن دیده می‌شود.
     *
     * ⚠️ دو مسیر متفاوت، چون دو صندوق در دو صفحهٔ متفاوت‌اند:
     *   • **سینرژی (۵)** روی **پرتفوی** است، در جدول نمادهای سهام
     *     (`/portfolio-fill`). نباید از پرتفوی خارج شویم، وگرنه مقدار از دست می‌رود.
     *     نسخهٔ پیشین همیشه اول به تب «سایر» می‌رفت → سینرژی هرگز خوانده نمی‌شد.
     *   • **آتیه (۴)** روی **صندوق‌های مفید** است (`/menu/funds`). رفتن مستقیم با
     *     `loadUrl` انجام می‌شود؛ کلیک روی `span` در SPA ناوبری نمی‌کند.
     */
    private suspend fun navigateToFund(webView: WebView, fund: String) {
        if (fund == "synergy") {
            // سینرژی روی پرتفوی است؛ اگر از آن خارج شده‌ایم، برگردیم.
            val url = currentUrl(webView)
            if (!url.contains("portfolio")) {
                log("🌐 بازگشت به پرتفوی برای خواندن سینرژی…", LogLevel.INFO)
                webView.loadUrl(PORTFOLIO_URL)
                awaitPageLoaded(webView, timeoutMs = 45_000)
                delay(3_000)
            }
            return
        }

        // آتیه: صفحهٔ «صندوق‌های مفید»
        if (pageHasKeyword(webView, ATIE_KEYWORDS)) return

        log("🌐 رفتن به صفحهٔ صندوق‌های مفید…", LogLevel.INFO)
        webView.loadUrl(FUNDS_URL)
        awaitPageLoaded(webView, timeoutMs = 45_000)
        delay(4_000)

        if (!pageHasKeyword(webView, ATIE_KEYWORDS)) {
            // پشتیبان: اگر URL مستقیم کار نکرد، با کلیک تب تلاش کن.
            log("ℹ️ صفحهٔ صندوق‌ها با URL مستقیم باز نشد؛ تلاش با کلیک تب…", LogLevel.INFO)
            logTabProbe(webView)
            tryClickTab(webView, listOf("سایر", "سایرین"), "سایر", 3_000)
            tryClickTab(
                webView,
                listOf("صندوق‌های مفید", "صندوق ها", "صندوق‌ها", "صندوق هاي مفيد"),
                "صندوق‌های مفید",
                4_000
            )
        }

        if (!pageHasKeyword(webView, ATIE_KEYWORDS)) {
            dumpNavigationDiagnostics(webView, fund)
        }
    }

    /** یک کلیک تب با لاگ خوانا. */
    private suspend fun tryClickTab(
        webView: WebView,
        texts: List<String>,
        label: String,
        waitMs: Long
    ) {
        when (val r = clickTab(webView, texts)) {
            "ALREADY" -> log("🗂 تب «$label» از قبل فعال بود.", LogLevel.INFO)
            "NOTFOUND" -> log("ℹ️ تب «$label» روی صفحه نبود.", LogLevel.INFO)
            else -> {
                log("🗂 تب «$label» کلیک شد ($r).", LogLevel.INFO)
                delay(waitMs)
            }
        }
    }

    /**
     * کلیک روی **لینک**ی که متنش یکی از [texts] است.
     *
     * فقط عناصر لینک‌دار (`a[href]`) یا نقش دکمه/تب کلیک می‌شوند — هرگز
     * دکمه‌های عملیاتی مثل «خرید/فروش» لمس نمی‌شوند (قانون امنیتی پروژه).
     */
    private suspend fun tryClickLink(webView: WebView, texts: List<String>, label: String): Boolean {
        val arr = texts.joinToString(",") { "'${jsonEscape(it)}'" }
        val js = """
        (function(){
          var texts = [$arr];
          var cands = document.querySelectorAll('a[href],[role="button"],[role="tab"]');
          for (var i=0;i<cands.length;i++){
            var el = cands[i];
            var t = (el.innerText || '').trim();
            if (!t || t.length > 30) continue;
            var hit = false;
            for (var k=0;k<texts.length;k++){
              if (t === texts[k] || t.indexOf(texts[k]) >= 0) { hit = true; break; }
            }
            if (!hit) continue;
            // محافظ امنیتی: دکمه‌های عملیاتی ممنوع
            if (/خرید|فروش|برداشت|واریز|انتقال|سفارش/.test(t)) continue;
            var vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            if (!vis) continue;
            try { el.click(); return 'CLICKED:' + t; } catch(e){}
          }
          return 'NOTFOUND';
        })();
        """.trimIndent()
        val r = decodeJsonString(evaluate(webView, js) ?: "NOTFOUND")
        return if (r.startsWith("CLICKED")) {
            log("🔗 لینک «$label» کلیک شد ($r).", LogLevel.INFO)
            delay(4_000)
            true
        } else {
            log("ℹ️ لینک «$label» پیدا نشد.", LogLevel.INFO)
            false
        }
    }

    /** آیا متن نمایان صفحه یکی از کلیدواژه‌ها را دارد؟ */
    private suspend fun pageHasKeyword(webView: WebView, keywords: List<String>): Boolean {
        val body = bodyText(webView)
        return keywords.any { body.contains(it) }
    }

    /**
     * دامپ عیب‌یابی ناوبری — وقتی هیچ راهی به صندوق نبرد.
     *
     * همهٔ لینک‌های صفحه (`href` + متن) و عناصر حاوی «صندوق»/«آتیه»/«سینرژی»
     * را برمی‌گرداند تا **آدرس واقعی صفحهٔ صندوق** در لاگ ظاهر شود. دفعهٔ بعد
     * می‌توان ناوبری مستقیم با `loadUrl` گذاشت که از هر کلیکی پایدارتر است.
     */
    private suspend fun dumpNavigationDiagnostics(webView: WebView, fund: String) {
        log("🔬 دامپ عیب‌یابی ناوبری برای «${displayName(fund)}»…", LogLevel.WARN)
        log("🌐 نشانی فعلی: ${currentUrl(webView)}", LogLevel.INFO)

        val js = """
        (function(){
          try {
            var links = [];
            var as = document.querySelectorAll('a[href]');
            for (var i=0;i<as.length && links.length<40;i++){
              var a = as[i];
              var t = (a.innerText || '').trim().replace(/\s+/g,' ');
              if (!t) continue;
              links.push(t.substring(0,40) + ' → ' + a.getAttribute('href'));
            }
            var fundish = [];
            var all = document.querySelectorAll('*');
            for (var j=0;j<all.length && fundish.length<30;j++){
              var el = all[j];
              if (el.children.length > 0) continue;
              var s = (el.innerText || '').trim();
              if (!s || s.length > 40) continue;
              if (/صندوق|آتیه|بازنشستگی|سینرژی|سایر/.test(s)) fundish.push(s);
            }
            return JSON.stringify({ links: links, fundish: fundish });
          } catch(e){ return JSON.stringify({ links: [], fundish: [], err: ''+e }); }
        })();
        """.trimIndent()

        val raw = decodeJsonString(evaluate(webView, js) ?: "{}")
        try {
            val obj = org.json.JSONObject(raw)
            val links = obj.optJSONArray("links")
            val fundish = obj.optJSONArray("fundish")
            if (links != null && links.length() > 0) {
                log("🔗 لینک‌های صفحه:", LogLevel.INFO)
                for (i in 0 until links.length()) log("   • ${links.optString(i)}", LogLevel.INFO)
            } else {
                log("🔗 هیچ لینک href داری در صفحه نبود.", LogLevel.INFO)
            }
            if (fundish != null && fundish.length() > 0) {
                val list = (0 until fundish.length()).map { fundish.optString(it) }
                log("🏷 عناصر مرتبط با صندوق: ${list.joinToString(" | ")}", LogLevel.INFO)
            } else {
                log("🏷 عنصر مرتبط با صندوق پیدا نشد.", LogLevel.INFO)
            }
        } catch (e: Exception) {
            log("🔬 دامپ خام: ${raw.take(400)}", LogLevel.WARN)
        }
    }

    /** کاوشگر تب‌ها را اجرا و نتیجه را در لاگ ثبت می‌کند. */
    private suspend fun logTabProbe(webView: WebView) {
        val probe = evaluate(webView, TAB_PROBE) ?: return
        try {
            val arr = org.json.JSONArray(decodeJsonString(probe))
            val tabs = (0 until arr.length()).map { arr.optString(it) }
            log("🗂 تب‌های پیداشده در صفحه: ${if (tabs.isEmpty()) "(هیچ)" else tabs.joinToString(" | ")}", LogLevel.INFO)
        } catch (e: Exception) {
            log("🗂 کاوش تب‌ها ناموفق: ${probe.take(150)}", LogLevel.WARN)
        }
    }

    /**
     * کلیک روی نخستین عنصری که متنش دقیقاً یکی از [texts] است.
     *
     * @return `"CLICKED:<متن>"`، `"ALREADY"` (خودِ عنصر فعال بود)، یا `"NOTFOUND"`.
     *
     * ⚠️ باگ نسخهٔ پیشین: شرط «از قبل باز است» روی **کل متن صفحه** سنجیده
     * می‌شد (`/سینرژی|آتیه/.test(document.body.innerText)`). روی صفحهٔ
     * پرتفوی، واژهٔ «سینرژی» به‌عنوان **نام یک نماد سهام** در جدول هست، نه
     * به‌عنوان تب. پس همیشه `ALREADY` برمی‌گشت و **هرگز کلیک نمی‌شد** →
     * هرگز به تب «صندوق‌های مفید» و صفحهٔ آتیه نمی‌رسیدیم.
     *
     * اکنون «فعال بودن» فقط از وضعیت **خودِ عنصر** خوانده می‌شود
     * (`aria-selected`، `aria-current`، یا کلاس فعال). و اگر شک داشتیم،
     * محتاطانه کلیک می‌کنیم — کلیک تکراری روی یک تب بی‌خطر است، ولی
     * کلیک‌نکردن، ناوبری را برای همیشه متوقف می‌کند.
     */
    private suspend fun clickTab(webView: WebView, texts: List<String>): String {
        val arr = texts.joinToString(",") { "'${jsonEscape(it)}'" }
        val js = """
        (function(){
          var texts = [$arr];
          var all = document.querySelectorAll('span,a,button,div,li,[role="tab"],[role="button"]');
          for (var i=0;i<all.length;i++){
            var el = all[i];
            var t = (el.innerText || '').trim();
            if (el.children.length > 1 || t.length > 20) continue;
            if (texts.indexOf(t) < 0) continue;
            var vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
            if (!vis) continue;
            if (isActive(el)) return 'ALREADY';
            try { el.click(); } catch(e){ return 'NOTFOUND'; }
            return 'CLICKED:' + t;
          }
          return 'NOTFOUND';

          function isActive(node){
            var n = node;
            for (var lvl=0; lvl<4 && n; lvl++){
              var a = n.getAttribute && (n.getAttribute('aria-selected') || n.getAttribute('aria-current'));
              if (a === 'true' || a === 'page') return true;
              var cls = (n.className && typeof n.className === 'string') ? n.className : '';
              if (/\b(active|selected|current|is-active|tab-active)\b/i.test(cls)) return true;
              n = n.parentElement;
            }
            return false;
          }
        })();
        """.trimIndent()
        return decodeJsonString(evaluate(webView, js) ?: "NOTFOUND")
    }

    private suspend fun sniffFromNetwork(webView: WebView, fund: String): Long? {
        val varName = if (fund == "synergy") "__emaratSynergyRaw" else "__emaratAtieRaw"
        val js = "window.$varName ? String(window.$varName).substring(0, 60000) : ''"
        val raw = decodeJsonString(evaluate(webView, js) ?: "")
        if (raw.isBlank()) {
            log("   ↳ شنود API: هیچ پاسخ حاوی کلیدواژهٔ این صندوق ثبت نشد.", LogLevel.INFO)
            return null
        }
        log("   ↳ شنود API: ${raw.length} کاراکتر پاسخ ثبت شد؛ در جستجوی مقدار…", LogLevel.INFO)

        val numbers = Regex("\"(?:totalValue|assetValue|value|totalPrice|marketValue|sumPrice)\"\\s*:\\s*\"?([\\d,]+)\"?")
            .findAll(raw)
            .mapNotNull { it.groupValues[1].replace(",", "").toLongOrNull() }
            .filter { it >= MIN_ASSET_VALUE }
            .toList()
        if (numbers.isEmpty()) {
            log("   ↳ در پاسخ، عدد معتبری (≥ ${fmt(MIN_ASSET_VALUE)}) یافت نشد.", LogLevel.INFO)
            return null
        }
        return numbers.maxOrNull()
    }

    /**
     * یافتن مقدار ریالی یک صندوق از متن صفحه.
     *
     * `innerText` در WebView اندروید، برخلاف Playwright، بین عناصر `\n` نمی‌گذارد؛
     * پس «سینرژی۲۲۰,۳۵۱,۲۶۰همسنگ ۲۲۰,۳۵۱,۲۶۰» به‌هم‌چسبیده می‌آید. به‌جای پیمایش
     * خط‌به‌خط، یک پنجرهٔ کاراکتری بعد از کلیدواژه اسکن می‌شود و بزرگ‌ترین عدد
     * ۶رقمی+ برگردانده می‌شود. منطق کامل در [FundTextScanner] است تا در تست JVM
     * مستقیماً سنجیده شود.
     */
    private fun scanBodyTextForFund(text: String, keywords: List<String>, fund: String?): Long? =
        FundTextScanner.extractValue(text, keywords, fund ?: "")

    private suspend fun scanDom(webView: WebView, keywords: List<String>): Long? {
        val kw = keywords.joinToString("|")
        val js = """
        (function(){
          var kws = "$kw".split('|');
          var all = document.querySelectorAll('*');
          for (var i=0;i<all.length;i++){
            var el = all[i];
            if (el.children.length > 3) continue;
            var t = el.innerText || '';
            if (!t || t.length > 120) continue;
            var hit = kws.some(function(k){ return t.indexOf(k) >= 0; });
            if (!hit) continue;
            var p = el;
            for (var lvl=0; lvl<10 && p; lvl++){
              p = p.parentElement;
              if(!p) break;
              var pt = p.innerText || '';
              if (pt.indexOf('همسنگ') >= 0) continue;
              var m = pt.match(/[\d,]{6,}/g);
              if (m && m.length){
                var nums = m.map(function(x){ return parseInt(x.replace(/,/g,''),10); })
                            .filter(function(n){ return n >= $MIN_ASSET_VALUE; });
                if (nums.length) return String(Math.max.apply(null, nums));
              }
            }
          }
          return '';
        })();
        """.trimIndent()
        return decodeJsonString(evaluate(webView, js) ?: "").toLongOrNull()
    }

    // ------------------------------------------------------------------ Helpers

    private suspend fun awaitPageLoaded(@Suppress("UNUSED_PARAMETER") webView: WebView, timeoutMs: Long) {
        lastPageFinishedAt = 0
        withTimeoutOrNull(timeoutMs) {
            while (lastPageFinishedAt == 0L) {
                delay(300)
            }
        }
        // مکث کوتاه پس از پایان بارگذاری تا اسکریپت‌های صفحه مستقر شوند
        delay(800)
    }

    private suspend fun awaitNavigation(webView: WebView, timeoutMs: Long) {
        awaitPageLoaded(webView, timeoutMs)
        delay(1500)
    }

    private suspend fun currentUrl(webView: WebView): String =
        withContext(Dispatchers.Main) { webView.url ?: "" }

    /**
     * متن نمایان صفحه با تشخیص دقیق.
     *
     * `innerText` به رندر نیاز دارد و اگر WebView به پنجره وصل نباشد خالی
     * برمی‌گردد؛ پس در صورت خالی بودن، `textContent` جایگزین می‌شود و علت
     * در لاگ ثبت می‌گردد تا دفعهٔ بعد کورکورانه عیب‌یابی نکنیم.
     */
    private suspend fun bodyText(webView: WebView): String {
        val raw = evaluate(webView, BODY_TEXT_PROBE) ?: return ""
        val diag = decodeJsonString(raw)
        val obj = try {
            JSONObject(diag)
        } catch (e: Exception) {
            log("⚠️ خواندن متن صفحه ناموفق: ${diag.take(120)}", LogLevel.WARN)
            return diag
        }

        val inner = obj.optString("inner")
        val textContent = obj.optString("text")
        val attached = obj.optBoolean("attached")
        val w = obj.optInt("w")
        val h = obj.optInt("h")

        log(
            "🔬 متن صفحه: innerText=${inner.length} کاراکتر | textContent=${textContent.length} " +
                "| اندازه=${w}×${h} | متصل=$attached",
            LogLevel.INFO
        )

        val chosen = when {
            inner.isNotBlank() -> inner
            textContent.isNotBlank() -> {
                log("⚠️ innerText خالی بود؛ از textContent استفاده می‌شود.", LogLevel.WARN)
                textContent
            }
            else -> ""
        }

        if (chosen.isNotBlank()) {
            log("👀 نمونهٔ متن صفحه: «${chosen.take(300).replace("\n", " ⏎ ")}»", LogLevel.INFO)
        } else {
            log("❌ صفحه هیچ متنی ندارد (حتی textContent) — احتمالاً هنوز بارگذاری نشده.", LogLevel.ERROR)
        }
        return chosen
    }

    /** اجرای جاوااسکریپت و برگرداندن نتیجهٔ خام. */
    private suspend fun evaluate(webView: WebView, js: String): String? =
        withContext(Dispatchers.Main) {
            suspendCancellableCoroutine { cont ->
                try {
                    webView.evaluateJavascript(js) { value ->
                        cont.resume(value)
                    }
                } catch (e: Exception) {
                    cont.resume(null)
                }
            }
        }

    private fun unquote(v: String?): String {
        if (v == null || v == "null") return ""
        var s = v
        if (s.startsWith("\"") && s.endsWith("\"") && s.length >= 2) {
            s = s.substring(1, s.length - 1)
        }
        return s.replace("\\n", "\n").replace("\\\"", "\"").replace("\\/", "/")
    }

    /**
     * باز کردن رشتهٔ JSON-encoded که `evaluateJavascript` برمی‌گرداند.
     *
     * `evaluateJavascript` خروجی رشته‌ای را با escape کامل JSON می‌دهد
     * (`"{\"inner\":\"خط۱\\nخط۲\"}"`). `unquote` سادهٔ قبلی `\n` را زودتر از
     * موعد به newline واقعی تبدیل می‌کرد و JSON را می‌شکست؛ `JSONTokener`
     * ترتیب درست escapeها را رعایت می‌کند.
     */
    private fun decodeJsonString(raw: String): String {
        if (raw == "null" || raw.isEmpty()) return ""
        if (!raw.startsWith("\"")) return raw
        return try {
            JSONTokener(raw).nextValue() as? String ?: unquote(raw)
        } catch (e: Exception) {
            unquote(raw)
        }
    }


    private fun jsonEscape(s: String): String = JSONObject.quote(s).removeSurrounding("\"")

    private fun fmt(n: Long): String = String.format("%,d", n)

    private fun displayName(fund: String) = if (fund == "synergy") "سینرژی (۵)" else "آتیه مفید (۴)"

    companion object {
        private const val LOGIN_URL = "https://login.emofid.com/Login"
        private const val PORTFOLIO_URL = "https://m.easytrader.ir/portfolio-fill"

        /**
         * صفحهٔ «صندوق‌های مفید» — محل نمایش دارایی «آتیه».
         *
         * آدرس از دامپ ناوبری تأیید شد. نسخهٔ پیشین می‌کوشید با کلیک روی
         * تب‌ها به این صفحه برسد، ولی کلیک روی `span` در SPA ناوبری نمی‌کند؛
         * رفتن مستقیم با `loadUrl` پایدار و مستقل از ظاهر است.
         */
        private const val FUNDS_URL = "https://m.easytrader.ir/menu/funds"
        private const val HYDRATION_DELAY_MS = 8_000L
        private const val MIN_ASSET_VALUE = 1_000_000L

        private val SYNERGY_KEYWORDS = listOf("سینرژی", "synergy")
        private val ATIE_KEYWORDS = listOf("آتیه", "بازنشستگی", "atie")

        /**
         * کاوشگر متن صفحه: هر سه معیار را یک‌جا برمی‌گرداند تا در لاگ ببینیم
         * دقیقاً کدام‌یک خالی است. `attached` می‌گوید WebView به پنجره وصل است یا نه.
         */
        private val BODY_TEXT_PROBE = """
        (function(){
          try {
            var b = document.body;
            return JSON.stringify({
              inner: b ? (b.innerText || '') : '',
              text: b ? (b.textContent || '') : '',
              attached: !!(document.documentElement && document.documentElement.isConnected),
              w: window.innerWidth || 0,
              h: window.innerHeight || 0
            });
          } catch(e){ return JSON.stringify({inner:'',text:'',attached:false,w:0,h:0,err:''+e}); }
        })();
        """.trimIndent()

        /**
         * کاوشگر تب‌ها: متن همهٔ عناصر کوچک (کمتر از ۲۰ کاراکتر) را برمی‌گرداند
         * تا در لاگ ببینیم تب‌های واقعی صفحه چه نامی دارند.
         */
        private val TAB_PROBE = """
        (function(){
          try {
            var out = [];
            var all = document.querySelectorAll('span,a,button,li,[role="tab"],[role="button"]');
            for (var i=0;i<all.length;i++){
              var el = all[i];
              if (el.children.length > 1) continue;
              var t = (el.innerText || '').trim();
              if (!t || t.length > 20) continue;
              if (out.indexOf(t) < 0) out.push(t);
              if (out.length >= 40) break;
            }
            return JSON.stringify(out);
          } catch(e){ return '[]'; }
        })();
        """.trimIndent()

        private const val MOBILE_UA =
            "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"

        /**
         * شنود `fetch` و `XMLHttpRequest` برای گرفتن بدنهٔ پاسخ‌های API.
         *
         * هم `fetch` و هم XHR پوشش داده می‌شوند؛ بعضی SPAها از XHR استفاده
         * می‌کنند و نسخهٔ پیشین فقط `fetch` را می‌گرفت.
         */
        private val SNIFFER_JS = """
        (function(){
          if (window.__emaratSniffer) return 'already';
          window.__emaratSniffer = true;

          function inspect(t){
            if (!t || typeof t !== 'string') return;
            try {
              if (t.indexOf('سینرژی') >= 0 || t.indexOf('synergy') >= 0) {
                window.__emaratSynergyRaw = t;
              }
              if (t.indexOf('آتیه') >= 0 || t.indexOf('بازنشستگی') >= 0 || t.indexOf('atie') >= 0) {
                window.__emaratAtieRaw = t;
              }
            } catch(e){}
          }

          try {
            var origFetch = window.fetch;
            if (origFetch) {
              window.fetch = function(){
                return origFetch.apply(this, arguments).then(function(res){
                  try { res.clone().text().then(inspect).catch(function(){}); } catch(e){}
                  return res;
                });
              };
            }
          } catch(e){}

          try {
            var OrigXHR = window.XMLHttpRequest;
            if (OrigXHR) {
              var origOpen = OrigXHR.prototype.open;
              OrigXHR.prototype.open = function(){
                try {
                  this.addEventListener('load', function(){
                    try { inspect(this.responseText); } catch(e){}
                  });
                } catch(e){}
                return origOpen.apply(this, arguments);
              };
            }
          } catch(e){}

          return 'installed';
        })();
        """.trimIndent()
    }
}
