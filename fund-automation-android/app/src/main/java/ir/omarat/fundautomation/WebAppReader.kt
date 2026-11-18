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

    /** درصدهای امروز که **دستی** ثبت شده‌اند (ثبت‌های اتوماسیون نادیده می‌روند). */
    suspend fun manualEntries(pageUrl: String): List<PercentEntry> =
        withContext(Dispatchers.Main) {
            val raw = readLocalStorage(pageUrl) ?: return@withContext emptyList()
            parseEntries(raw)
        }

    /**
     * آخرین مقدار پایه از تاریخچهٔ وب‌اپ.
     *
     * چرا از اینجا و نه از `prefs` اپ؟ چون تاریخچهٔ وب‌اپ **منبع حقیقت** است:
     * کاربر ممکن است در خودِ صفحهٔ وب‌اپ مقداری دستی ثبت کرده باشد که اپ از آن
     * بی‌خبر است. اگر پایه از `prefs` خوانده شود، محاسبه روی عدد قدیمی انجام
     * می‌شود و درصد بی‌معنا می‌شود (مثلاً همیشه صفر).
     */
    suspend fun lastHistoryBase(pageUrl: String): HistoryBase? =
        withContext(Dispatchers.Main) {
            val raw = readLocalStorage(pageUrl) ?: return@withContext null
            parseLastHistoryBase(raw)
        }

    /** خواندن کلیدهای تاریخچه و درصدها به‌صورت JSON خام. */
    @SuppressLint("SetJavaScriptEnabled")
    private suspend fun readLocalStorage(pageUrl: String): String? = withContext(Dispatchers.Main) {
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
            evaluate(webView, READ_SCRIPT)
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
         * درصدهای هر دو دستهٔ کلیدی صندوق ۴ را یک‌جا برمی‌گرداند تا هیچ رکوردی
         * از قلم نیفتد (`mofid_atie_percents` و `pension_history`).
         */
        private val READ_SCRIPT = """
        (function(){
          try {
            function arr(k){ try { var v = JSON.parse(localStorage.getItem(k) || '[]'); return v instanceof Array ? v : []; } catch(e){ return []; } }
            var percents = arr('mofid_atie_percents');
            if (!percents.length) percents = arr('sinergy_percents');
            if (!percents.length) {
              var obj = {};
              try { obj = JSON.parse(localStorage.getItem('energy_fund_synergy') || '{}'); } catch(e){ obj = {}; }
              if (obj.percents instanceof Array) percents = obj.percents;
            }
            var history = arr('mofid_atie_history');
            if (!history.length) history = arr('pension_history');
            if (!history.length) history = arr('sinergy_history');
            if (!history.length) {
              var obj2 = {};
              try { obj2 = JSON.parse(localStorage.getItem('energy_fund_synergy') || '{}'); } catch(e){ obj2 = {}; }
              if (obj2.history instanceof Array) history = obj2.history;
            }
            return JSON.stringify({ percents: percents, history: history });
          } catch(e){ return JSON.stringify({ percents: [], history: [] }); }
        })();
        """.trimIndent()
    }
}
