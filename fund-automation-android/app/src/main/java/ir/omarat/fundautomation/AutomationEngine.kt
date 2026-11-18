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

            for ((fund, base, peak) in listOf(
                Triple("synergy", baseSynergy, peakSynergy),
                Triple("atie", baseAtie, peakAtie)
            )) {
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
            handleOtp(webView)
        }

        // تیک «این دستگاه را به خاطر بسپار» — برای عبور از تأیید دو مرحله‌ای در بارهای بعد
        tickTrustDevice(webView)

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

    private suspend fun handleOtp(webView: WebView) {
        log("🔐 کارگزاری کد تأیید (OTP) می‌خواهد. لطفاً کد را وارد کن…", LogLevel.WARN)
        val code = otpProvider?.invoke()
        if (code.isNullOrBlank()) {
            throw IllegalStateException("کد تأیید دریافت نشد؛ عملیات متوقف شد.")
        }
        val safeCode = jsonEscape(code)
        val js = """
        (function(){
          var el = document.querySelector('input[inputmode="numeric"], input[name*="code" i], input[name*="otp" i], input[type="tel"], input[type="text"]');
          if(!el) return 'NOINPUT';
          el.focus(); el.value = "$safeCode";
          el.dispatchEvent(new Event('input', {bubbles:true}));
          el.dispatchEvent(new Event('change', {bubbles:true}));
          var btn = document.querySelector('button[type="submit"], input[type="submit"], form button');
          if(btn) btn.click();
          return 'OK';
        })();
        """.trimIndent()
        evaluate(webView, js)
        log("✅ کد تأیید ارسال شد.", LogLevel.OK)
        awaitNavigation(webView, timeoutMs = 45_000)
    }

    private suspend fun tickTrustDevice(webView: WebView) {
        val js = """
        (function(){
          var boxes = document.querySelectorAll("input[type='checkbox']");
          var done = 0;
          for (var i=0;i<boxes.length;i++){
            var b = boxes[i];
            var n = (b.id + ' ' + b.name + ' ' + (b.parentElement?b.parentElement.innerText:'')).toLowerCase();
            if (n.indexOf('trust')>=0 || n.indexOf('remember')>=0 || n.indexOf('device')>=0 || n.indexOf('یاد')>=0 || n.indexOf('اعتماد')>=0){
              if(!b.checked){ b.click(); }
              done++;
            }
          }
          return 'TRUST:' + done;
        })();
        """.trimIndent()
        val r = evaluate(webView, js)
        if (r?.contains("TRUST:0") == true) {
            log("ℹ️ تیک «این دستگاه را به خاطر بسپار» روی صفحه نبود (یا از قبل تیک بود).", LogLevel.INFO)
        } else {
            log("☑ تیک «این دستگاه را به خاطر بسپار» زده شد.", LogLevel.OK)
        }
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

        openOtherTab(webView)

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

        // لایهٔ ۲: اسکن متن بدنه
        scanBodyText(bodyText, keywords)?.let {
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
     * باز کردن تب صندوق‌ها در صفحهٔ پرتفوی.
     *
     * صندوق‌های مفید (سینرژی، آتیه) در تب پیش‌فرض «سهام» نیستند. اسکریپت
     * پایتون **دو کلیک** می‌زند: اول «سایر»، بعد «صندوق‌های مفید». نسخهٔ
     * پیشین فقط «سایر» را می‌گشت و چون در لاگ جدید «سایر» در فهرست تب‌ها
     * نبود، آتیه هرگز پیدا نمی‌شد.
     *
     * اینجا هر دو کلیک به‌ترتیب زده می‌شوند؛ اما اگر تب‌ها از قبل باز باشند
     * (سینرژی/آتیه در متن دیده شوند) کلیک تکراری انجام نمی‌شود.
     */
    private suspend fun openOtherTab(webView: WebView) {
        logTabProbe(webView)

        val clickResult = clickTab(webView, listOf("سایر", "سایرین"))
        when {
            clickResult.startsWith("CLICKED") -> {
                log("🗂 تب «سایر» باز شد.", LogLevel.INFO)
                delay(3_000)
            }
            clickResult == "ALREADY" ->
                log("🗂 تب «سایر» از قبل باز بود.", LogLevel.INFO)
            else ->
                log("ℹ️ تب «سایر» نبود؛ شاید ساختار عوض شده.", LogLevel.INFO)
        }

        // کلیک دوم: «صندوق‌های مفید» — کلید دیدن آتیه در پرتفوی
        val fundsResult = clickTab(webView, listOf("صندوق‌های مفید", "صندوق ها", "صندوق‌ها", "صندوق هاي مفيد"))
        when {
            fundsResult.startsWith("CLICKED") -> {
                log("🗂 تب «صندوق‌های مفید» باز شد.", LogLevel.INFO)
                delay(4_000)
            }
            fundsResult == "ALREADY" ->
                log("🗂 تب «صندوق‌های مفید» از قبل باز بود.", LogLevel.INFO)
            else ->
                log("ℹ️ تب «صندوق‌های مفید» نبود (شاید صندوق‌ها در همین صفحه‌اند).", LogLevel.INFO)
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
     * @return `"CLICKED:<متن>"`، `"ALREADY"` (باز بود)، یا `"NOTFOUND"`.
     */
    private suspend fun clickTab(webView: WebView, texts: List<String>): String {
        val arr = texts.joinToString(",") { "'${jsonEscape(it)}'" }
        val js = """
        (function(){
          var texts = [$arr];
          var all = document.querySelectorAll('span,a,button,div,li');
          for (var i=0;i<all.length;i++){
            var el = all[i];
            var t = (el.innerText || '').trim();
            if (el.children.length > 1 || t.length > 20) continue;
            if (texts.indexOf(t) >= 0){
              var vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
              if (!vis) continue;
              var already = /سینرژی|آتیه/.test(document.body.innerText || '');
              if (already) return 'ALREADY';
              try { el.click(); } catch(e){ return 'NOTFOUND'; }
              return 'CLICKED:' + t;
            }
          }
          return 'NOTFOUND';
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
     * پس «سینرژی۲۵۰,۰۰۰,۰۰۰همسنگ ۲۵,۰۰۰,۰۰۰» به‌هم‌چسبیده می‌آید. به‌جای پیمایش
     * خط‌به‌خط، یک پنجرهٔ کاراکتری بعد از کلیدواژه اسکن می‌شود و تا اولین نشانهٔ
     * پایان («همسنگ» یا «تومان») ادامه می‌یابد؛ سپس بزرگ‌ترین عدد ۶رقمی+ برگردانده می‌شود.
     */
    private fun scanBodyText(text: String, keywords: List<String>): Long? {
        val normalized = toEnglishDigits(text)
        for (keyword in keywords) {
            var from = normalized.indexOf(keyword)
            while (from >= 0) {
                val window = normalized.substring(
                    from + keyword.length,
                    minOf(from + keyword.length + WINDOW_CHARS, normalized.length)
                )
                val endIndex = listOf(
                    window.indexOf("همسنگ"), window.indexOf("تومان"), window.indexOf("کارگزاری")
                ).filter { it >= 0 }.minOrNull() ?: window.length
                val segment = window.substring(0, endIndex)

                val candidates = Regex("[\\d,]{6,}").findAll(segment)
                    .mapNotNull { it.value.replace(",", "").toLongOrNull() }
                    .filter { it >= MIN_ASSET_VALUE }
                    .toList()
                candidates.maxOrNull()?.let { return it }

                from = normalized.indexOf(keyword, from + keyword.length)
            }
        }
        return null
    }

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

    private fun toEnglishDigits(input: String): String {
        val map = mapOf(
            '۰' to '0', '۱' to '1', '۲' to '2', '۳' to '3', '۴' to '4',
            '۵' to '5', '۶' to '6', '۷' to '7', '۸' to '8', '۹' to '9',
            '٠' to '0', '١' to '1', '٢' to '2', '٣' to '3', '٤' to '4',
            '٥' to '5', '٦' to '6', '٧' to '7', '٨' to '8', '٩' to '9'
        )
        val sb = StringBuilder(input.length)
        for (c in input) sb.append(map[c] ?: c)
        return sb.toString()
    }

    private fun jsonEscape(s: String): String = JSONObject.quote(s).removeSurrounding("\"")

    private fun fmt(n: Long): String = String.format("%,d", n)

    private fun displayName(fund: String) = if (fund == "synergy") "سینرژی (۵)" else "آتیه مفید (۴)"

    companion object {
        private const val LOGIN_URL = "https://login.emofid.com/Login"
        private const val PORTFOLIO_URL = "https://m.easytrader.ir/portfolio-fill"
        private const val HYDRATION_DELAY_MS = 8_000L
        private const val MIN_ASSET_VALUE = 1_000_000L

        /** پنجرهٔ کاراکتری اسکن متن بعد از کلیدواژهٔ صندوق. */
        private const val WINDOW_CHARS = 200

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
