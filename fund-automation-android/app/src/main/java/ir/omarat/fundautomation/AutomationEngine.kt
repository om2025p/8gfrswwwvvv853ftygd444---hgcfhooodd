package ir.omarat.fundautomation

import android.annotation.SuppressLint
import android.content.Context
import android.webkit.CookieManager
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
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
            log("🌐 باز کردن صفحهٔ ورود ایزی‌تریدر…", LogLevel.INFO)
            webView.loadUrl(LOGIN_URL)
            awaitPageLoaded(webView, timeoutMs = 45_000)

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

            override fun onPageFinished(view: WebView, url: String) {
                super.onPageFinished(view, url)
                lastPageFinishedAt = System.currentTimeMillis()
            }
        }
        return wv
    }

    /**
     * تزریق یک اسکریپت کوچک برای شنود پاسخ‌های شبکه‌ای که کلمهٔ صندوق‌ها
     * را دارند. چون WebView اندروید به بدنهٔ پاسخ‌ها دسترسی مستقیم نمی‌دهد،
     * از `fetch` صفحه استفاده می‌کنیم تا پاسخ‌ها را ببینیم.
     */
    private suspend fun installNetworkSniffer(webView: WebView) {
        val js = """
        (function(){
          if (window.__emaratSniffer) return 'already';
          window.__emaratSniffer = true;
          var origFetch = window.fetch;
          window.fetch = function(){
            return origFetch.apply(this, arguments).then(function(res){
              try {
                res.clone().text().then(function(t){
                  if (!t) return;
                  if (t.indexOf('سینرژی') >= 0 || t.indexOf('synergy') >= 0) {
                    var m = t.match(/"(?:totalValue|assetValue|value|totalPrice|marketValue|sumPrice)"\s*:\s*"?([\d,]+)"?/g);
                    if (m) { window.__emaratSynergyRaw = t; }
                  }
                  if (t.indexOf('آتیه') >= 0 || t.indexOf('بازنشستگی') >= 0 || t.indexOf('atie') >= 0) {
                    window.__emaratAtieRaw = t;
                  }
                });
              } catch(e){}
              return res;
            });
          };
          return 'installed';
        })();
        """.trimIndent()
        evaluate(webView, js)
    }

    // ------------------------------------------------------------------ Login

    private suspend fun performLoginIfNeeded(webView: WebView) {
        val url = currentUrl(webView)
        val body = bodyText(webView)

        if (url.contains("portfolio-fill") || (url.contains("easytrader") && !body.contains("رمز"))) {
            log("✅ نشست فعال است؛ نیازی به ورود مجدد نیست.", LogLevel.OK)
            installNetworkSniffer(webView)
            return
        }

        log("🔑 ورود خودکار با رمز ذخیره‌شده…", LogLevel.INFO)
        fillLoginForm(webView)
        awaitNavigation(webView, timeoutMs = 45_000)

        if (isOtpScreen(webView)) {
            handleOtp(webView)
        }

        // تیک «این دستگاه را به خاطر بسپار» — برای عبور از تأیید دو مرحله‌ای در بارهای بعد
        tickTrustDevice(webView)

        log("🌐 رفتن به صفحهٔ پرتفوی…", LogLevel.INFO)
        webView.loadUrl(PORTFOLIO_URL)
        awaitPageLoaded(webView, timeoutMs = 45_000)
        installNetworkSniffer(webView)
    }

    private suspend fun fillLoginForm(webView: WebView) {
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
        if (res?.contains("OK") != true) {
            log("⚠️ فرم ورود پیدا نشد؛ ممکن است ظاهر صفحه تغییر کرده باشد.", LogLevel.WARN)
        }

        delay(600)
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

        openOtherTab(webView)

        // لایهٔ ۱: شنود شبکه
        sniffFromNetwork(webView, fund)?.let {
            log("✔ [لایهٔ ۱ · شنود API] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "network"
            return it
        }

        val bodyText = bodyText(webView)

        // لایهٔ ۲: اسکن متن بدنه
        scanBodyText(bodyText, keywords)?.let {
            log("✔ [لایهٔ ۲ · اسکن متن] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "text"
            return it
        }

        // لایهٔ ۳: پیمایش DOM
        scanDom(webView, keywords)?.let {
            log("✔ [لایهٔ ۳ · DOM] مقدار ${fmt(it)} ریال", LogLevel.OK)
            methodByFund[fund] = "dom"
            return it
        }

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
     * باز کردن تب «سایر» در صفحهٔ پرتفوی.
     *
     * صندوق‌های مفید (سینرژی، آتیه) در تب پیش‌فرض «سهام» نیستند و بدون این
     * کلیک، `innerText` صفحه هیچ‌کدام را نشان نمی‌دهد.
     */
    private suspend fun openOtherTab(webView: WebView) {
        val js = """
        (function(){
          var texts = ['سایر','سایرین','صندوق‌های مفید','صندوق ها','صندوق‌ها'];
          var all = document.querySelectorAll('span,a,button,div,li');
          for (var i=0;i<all.length;i++){
            var el = all[i];
            var t = (el.innerText || '').trim();
            if (el.children.length > 1 || t.length > 20) continue;
            if (texts.indexOf(t) >= 0){
              var already = document.body.innerText.indexOf('سینرژی') >= 0;
              if (already) return 'ALREADY';
              el.click();
              return 'CLICKED:' + t;
            }
          }
          return 'NOTFOUND';
        })();
        """.trimIndent()
        val r = evaluate(webView, js)
        if (r?.contains("CLICKED") == true) {
            log("🗂 تب «سایر» باز شد.", LogLevel.INFO)
            delay(4_000)
        }
    }

    private suspend fun sniffFromNetwork(webView: WebView, fund: String): Long? {
        val varName = if (fund == "synergy") "__emaratSynergyRaw" else "__emaratAtieRaw"
        val js = "window.$varName ? String(window.$varName).substring(0, 60000) : ''"
        val raw = evaluate(webView, js) ?: return null
        if (raw.isBlank()) return null

        val numbers = Regex("\"(?:totalValue|assetValue|value|totalPrice|marketValue|sumPrice)\"\\s*:\\s*\"?([\\d,]+)\"?")
            .findAll(raw)
            .mapNotNull { it.groupValues[1].replace(",", "").toLongOrNull() }
            .filter { it >= MIN_ASSET_VALUE }
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
        return evaluate(webView, js)?.toLongOrNull()
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

    private suspend fun bodyText(webView: WebView): String {
        val res = evaluate(webView, "document.body ? document.body.innerText : ''")
        return unquote(res)
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

        private const val MOBILE_UA =
            "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    }
}
