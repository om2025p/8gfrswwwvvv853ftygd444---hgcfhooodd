package ir.omarat.fundautomation

import android.annotation.SuppressLint
import android.content.Context
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
 * خواندن حافظهٔ وب‌اپ‌های ثبت درصد (صفحهٔ `file://` داخل assets).
 *
 * چرا WebView جداگانه؟ چون `localStorage` به **origin** گره خورده و حافظهٔ
 * WebView اتوماسیون (روی `m.easytrader.ir`) با حافظهٔ وب‌اپ یکی نیست.
 * برای «جلوگیری از ثبت تکراری» و «پشتیبان‌گیری محلی» باید همان فضای کلید
 * کاربر را بخوانیم.
 */
class WebAppReader(private val context: Context) {

    /** یک رکورد سبک از تاریخچهٔ درصدها. */
    data class PercentEntry(val value: Double, val timestampMs: Long, val manual: Boolean)

    /** آخرین مقدار پایهٔ ثبت‌شده در تاریخچهٔ وب‌اپ (منبع حقیقت واحد). */
    data class HistoryBase(val value: Long, val timestampMs: Long)

    /**
     * درصدهای **دستی** که امروز ثبت شده‌اند.
     *
     * ⚠️ فیلتر `manual` باید واقعاً اعمال شود. در نسخهٔ پیشین این تابع نامش
     * «دستی» بود ولی همهٔ رکوردها را برمی‌گرداند؛ پس رکورد خودِ اتوماسیون
     * (که `source=automation` دارد) هم «ثبت دستی امروز» شمرده می‌شد و
     * اتوماسیون خودش را رد می‌کرد — باگ «هر دو صندوق دست‌نخورده رها شد».
     */
    suspend fun manualEntries(pageUrl: String, fund: String): List<PercentEntry> =
        withContext(Dispatchers.Main) {
            val raw = readLocalStorage(pageUrl, fund) ?: return@withContext emptyList()
            parseEntries(raw).filter { it.manual }
        }

    /**
     * آخرین مقدار پایه از تاریخچهٔ وب‌اپ.
     *
     * چرا از اینجا و نه از `prefs` اپ؟ چون تاریخچهٔ وب‌اپ **منبع حقیقت** است:
     * کاربر ممکن است در خودِ صفحهٔ وب‌اپ مقداری دستی ثبت کرده باشد که اپ از آن
     * بی‌خبر است. اگر پایه از `prefs` خوانده شود، محاسبه روی عدد قدیمی انجام
     * می‌شود و درصد بی‌معنا می‌شود (مثلاً همیشه صفر).
     *
     * ⚠️ `fund` الزامی است: صفحات وب‌اپ روی `file://` هستند و **همه یک origin
     * مشترک** دارند، پس `localStorage` مشترک است. اگر اسکریپت بدون تفکیک
     * صندوق اجرا شود، همیشه کلید صندوق ۴ برگردانده می‌شود و پایهٔ سینرژی
     * اشتباهاً عدد آتیه می‌شود.
     */
    suspend fun lastHistoryBase(pageUrl: String, fund: String): HistoryBase? =
        withContext(Dispatchers.Main) {
            val raw = readLocalStorage(pageUrl, fund) ?: return@withContext null
            parseLastHistoryBase(raw)
        }

    /** خواندن کلیدهای تاریخچه و درصدها به‌صورت JSON خام. */
    @SuppressLint("SetJavaScriptEnabled")
    private suspend fun readLocalStorage(pageUrl: String, fund: String): String? =
        withContext(Dispatchers.Main) {
        val webView = WebView(context)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            cacheMode = WebSettings.LOAD_DEFAULT
        }
        var loaded = false
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String) {
                loaded = true
            }
        }

        try {
            webView.loadUrl(pageUrl)
            withTimeoutOrNull(20_000) {
                while (!loaded) delay(200)
            }
            delay(1_200)
            evaluate(webView, readScript(fund))
        } catch (e: Exception) {
            null
        } finally {
            webView.destroy()
        }
    }

    private fun parseEntries(raw: String): List<PercentEntry> {
        val json = decode(raw) ?: return emptyList()
        return try {
            val obj = JSONObject(json)
            val arr = obj.optJSONArray("percents") ?: return emptyList()
            val out = ArrayList<PercentEntry>(arr.length())
            for (i in 0 until arr.length()) {
                val it = arr.optJSONObject(i) ?: continue
                val value = it.optDouble("value", Double.NaN)
                if (value.isNaN()) continue
                val ts = it.optLong("timestamp", 0L)
                val manual = !(it.optString("source") == "automation" || it.optBoolean("auto", false))
                out += PercentEntry(value, ts, manual)
            }
            out
        } catch (e: Exception) {
            emptyList()
        }
    }

    /**
     * آخرین مقدار پایه از آرایهٔ `history`.
     *
     * هر رکورد تاریخچه دو شکل دارد: اپ‌های `calculator` مقدار عددی خام را در
     * `rawNew` می‌گذارند و اپ‌های `percent` رشتهٔ جداکننده‌دار در `new`. هر دو
     * پوشش داده می‌شوند و بزرگ‌ترین تایم‌استمپ برنده است (نه آخرین ایندکس، چون
     * ترتیب آرایه همیشه زمانی نیست).
     */
    private fun parseLastHistoryBase(raw: String): HistoryBase? {
        val json = decode(raw) ?: return null
        return try {
            val obj = JSONObject(json)
            val arr = obj.optJSONArray("history") ?: return null
            var best: HistoryBase? = null
            for (i in 0 until arr.length()) {
                val it = arr.optJSONObject(i) ?: continue
                val value = optLongAny(it, "rawNew", "new") ?: continue
                if (value < MIN_SANE_VALUE) continue
                val ts = it.optLong("timestamp", 0L)
                if (best == null || ts >= best.timestampMs) best = HistoryBase(value, ts)
            }
            best
        } catch (e: Exception) {
            null
        }
    }

    /** خواندن یک عدد از میان چند کلید؛ رشته‌های جداکننده‌دار هم پذیرفته می‌شوند. */
    private fun optLongAny(obj: JSONObject, vararg keys: String): Long? {
        for (k in keys) {
            if (!obj.has(k)) continue
            val raw = obj.optString(k, "")
            if (raw.isBlank() || raw == "null") continue
            val digits = raw.replace(",", "").replace("٬", "").replace("،", "").trim()
            digits.toLongOrNull()?.let { return it }
            digits.toDoubleOrNull()?.let { return it.toLong() }
        }
        return null
    }

    private fun decode(raw: String?): String? {
        if (raw == null || raw == "null") return null
        var s = raw.trim()
        if (s.startsWith("\"") && s.endsWith("\"") && s.length >= 2) {
            s = s.substring(1, s.length - 1)
        }
        return s.replace("\\\"", "\"").replace("\\/", "/").replace("\\n", "\n")
    }

    private suspend fun evaluate(webView: WebView, js: String): String? =
        withContext(Dispatchers.Main) {
            suspendCancellableCoroutine { cont ->
                try {
                    webView.evaluateJavascript(js) { value -> cont.resume(value) }
                } catch (e: Exception) {
                    cont.resume(null)
                }
            }
        }

    companion object {
        const val ATIE_PAGE = "file:///android_asset/webapp/gold4/percent.html"
        const val SYNERGY_PAGE = "file:///android_asset/webapp/gold5/percent.html"

        /** کمترین مقدار معقول دارایی (ریال) — فیلتر اعداد آشغال. */
        const val MIN_SANE_VALUE = 1_000_000L

        /**
         * اسکریپت خواندن برای هر صندوق، **جداگانه**.
         *
         * چرا جدا؟ چون صفحات وب‌اپ روی `file://` هستند و همه یک origin مشترک
         * دارند (`localStorage` مشترک). اگر یک اسکریپت مشترک با ترتیب fallback
         * نوشته شود، برای صفحهٔ سینرژی هم اول کلید آتیه خوانده می‌شود و پایهٔ
         * سینرژی اشتباهاً عدد آتیه می‌شود — باگ واقعی گزارش‌شده در لاگ کاربر.
         */
        private fun readScript(fund: String): String =
            if (fund == "synergy") SYNERGY_READ_SCRIPT else ATIE_READ_SCRIPT

        /**
         * صندوق ۵ (سینرژی). کلیدهای اصلی `energy_fund_synergy` و
         * `sinergy_history`/`sinergy_percents` هستند.
         */
        private val SYNERGY_READ_SCRIPT = """
        (function(){
          try {
            function arr(k){ try { var v = JSON.parse(localStorage.getItem(k) || '[]'); return v instanceof Array ? v : []; } catch(e){ return []; } }
            var percents = arr('sinergy_percents');
            var history = arr('sinergy_history');
            var obj = {};
            try { obj = JSON.parse(localStorage.getItem('energy_fund_synergy') || '{}'); } catch(e){ obj = {}; }
            if (!percents.length && obj.percents instanceof Array) percents = obj.percents;
            if (!history.length && obj.history instanceof Array) history = obj.history;
            return JSON.stringify({ percents: percents, history: history });
          } catch(e){ return JSON.stringify({ percents: [], history: [] }); }
        })();
        """.trimIndent()

        /**
         * صندوق ۴ (آتیه مفید). کلیدهای اصلی `mofid_atie_*` و دستهٔ موازی
         * `pension_*` هستند.
         */
        private val ATIE_READ_SCRIPT = """
        (function(){
          try {
            function arr(k){ try { var v = JSON.parse(localStorage.getItem(k) || '[]'); return v instanceof Array ? v : []; } catch(e){ return []; } }
            var percents = arr('mofid_atie_percents');
            var history = arr('mofid_atie_history');
            if (!percents.length) percents = arr('pension_percents');
            if (!history.length) history = arr('pension_history');
            return JSON.stringify({ percents: percents, history: history });
          } catch(e){ return JSON.stringify({ percents: [], history: [] }); }
        })();
        """.trimIndent()
    }
}
