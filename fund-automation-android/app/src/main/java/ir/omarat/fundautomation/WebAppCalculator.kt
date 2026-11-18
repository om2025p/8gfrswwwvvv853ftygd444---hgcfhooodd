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
 * محاسبه با **موتور خودِ وب‌اپ** (نه پیاده‌سازی دوباره).
 *
 * چرا؟ چون در `goldN/calculator.html` تابع `calculateAndSave()` هم درصد را
 * حساب می‌کند و هم «قله» (peak) را به‌روز می‌کند و هم نوع تغییر
 * (increase/recovering/decrease/neutral) را تعیین می‌کند. اگر این منطق را
 * دوباره در کاتلین پیاده کنیم، با هر تغییر کوچک وب‌اپ دو منطق از هم جدا
 * می‌افتند و اعداد ناسازگار می‌شوند.
 *
 * این کلاس صفحهٔ ماشین‌حساب را در WebView باز می‌کند، دو عدد را در فیلدهای
 * خودش می‌گذارد و تابع خودش را صدا می‌زند. **درصد نهایی با دقت کامل** از
 * همان دو عدد حساب می‌شود (چون موتور وب‌اپ فقط دو رقم اعشار می‌دهد و همان
 * باعث باگ «۰٫۰۰٪» می‌شد)، ولی **نوع و قله** از موتور وب‌اپ می‌آید.
 */
class WebAppCalculator(private val context: Context) {

    /**
     * نتیجهٔ محاسبهٔ وب‌اپ.
     *
     * @param percent  درصد با دقت کامل (۶ رقم مؤثر) — نه رشتهٔ دو رقمی وب‌اپ
     * @param type     نوع تغییر از موتور وب‌اپ: increase/recovering/decrease/neutral
     * @param peak     قلهٔ به‌روزشده (ریال)
     */
    data class CalcOutcome(
        val percent: Double,
        val type: String,
        val peak: Long,
        val rawText: String
    )

    /** کلید پایه/قلهٔ هر صندوق در `localStorage` وب‌اپ. */
    private fun peakKeyFor(fund: String) =
        if (fund == "synergy") "sinergy_peakNumber" else "pension_peakNumber"

    /**
     * محاسبه با موتور وب‌اپ.
     *
     * `calculateAndSave(false)` صدا زده می‌شود تا **تاریخچه نوشته نشود**؛
     * نوشتن تاریخچه کار خود اپ است (با درصد دقیق). ولی قله توسط موتور وب‌اپ
     * به‌روز می‌شود، چون همان معنای «قله» را می‌خواهیم.
     */
    @SuppressLint("SetJavaScriptEnabled")
    suspend fun calculate(
        pageUrl: String,
        fund: String,
        base: Long,
        newValue: Long
    ): CalcOutcome? = withContext(Dispatchers.Main) {
        val peakKey = peakKeyFor(fund)
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
            withTimeoutOrNull(20_000) { while (!loaded) delay(200) }
            delay(1_500)
            val raw = evaluate(webView, script(fund, peakKey, base, newValue))
            parse(raw)
        } catch (e: Exception) {
            null
        } finally {
            webView.destroy()
        }
    }

    /**
     * اسکریپت تزریقی.
     *
     * `num1Input`/`num2Input`/`calculateAndSave` در `<script>` سطح-بالای
     * صفحه با `const`/`function` تعریف شده‌اند؛ پس در محیط گلوبال با **نام
     * خالی** قابل دسترسی‌اند (نه با `window.`). اگر صفحه تغییر کرد و این
     * نام‌ها نبودند، با `ok:false` برمی‌گردیم و اپ به محاسبهٔ داخلی برمی‌گردد.
     */
    private fun script(
        fund: String, peakKey: String, base: Long, newValue: Long
    ): String {
        val prefix = if (fund == "synergy") "sinergy" else "pension"
        return """
        (function(){
          try {
            var num1 = document.getElementById('${prefix}_number1');
            var num2 = document.getElementById('${prefix}_number2');
            if (!num1 || !num2) return JSON.stringify({ok:false, err:'no-inputs'});
            if (typeof calculateAndSave !== 'function') return JSON.stringify({ok:false, err:'no-engine'});

            num1.value = '$base';
            num2.value = '$newValue';

            // compute-only: تاریخچه را اپ خودش می‌نویسد، پس اینجا ذخیره نمی‌کنیم.
            // خودِ موتور قله را در localStorage به‌روز می‌کند (اگر از قله بگذریم).
            calculateAndSave(false);

            var res = document.getElementById('${prefix}_differenceResult');
            var cls = (res && res.className) || '';

            // درصد با دقت کامل (موتور فقط دو رقم می‌دهد و همان باگ «۰٫۰۰٪» بود).
            var b = $base, n = $newValue;
            var pct = b !== 0 ? ((n - b) / b) * 100 : 0;

            var peakOut = parseInt(String(localStorage.getItem('$peakKey') || '').replace(/,/g,''), 10);
            if (!peakOut || isNaN(peakOut)) peakOut = n;

            return JSON.stringify({
              ok: true, cls: cls, percent: pct, peak: peakOut,
              text: (res && res.textContent) ? res.textContent : ''
            });
          } catch(e){ return JSON.stringify({ok:false, err:String(e)}); }
        })();
        """.trimIndent()
    }

    private fun parse(raw: String?): CalcOutcome? {
        if (raw == null || raw == "null") return null
        var s = raw.trim()
        if (s.startsWith("\"") && s.endsWith("\"") && s.length >= 2) s = s.substring(1, s.length - 1)
        s = s.replace("\\\"", "\"").replace("\\n", "\n").replace("\\/", "/")
        return try {
            val o = JSONObject(s)
            if (!o.optBoolean("ok", false)) return null
            CalcOutcome(
                percent = o.optDouble("percent", 0.0),
                // نگاشت کلاس CSS → نوع تغییر در کاتلین انجام می‌شود تا مستقل از
                // مرورگر و قابل تست باشد؛ نه درون رشتهٔ جاوااسکریپت.
                type = typeFromClassName(o.optString("cls", "")),
                peak = o.optLong("peak", 0L),
                rawText = o.optString("text", "")
            )
        } catch (e: Exception) {
            null
        }
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
        const val ATIE_CALC = "file:///android_asset/webapp/gold4/calculator.html"
        const val SYNERGY_CALC = "file:///android_asset/webapp/gold5/calculator.html"

        /**
         * انتخاب نوع تغییر از کلاس CSS موتور وب‌اپ.
         *
         * خالص و مستقل از اندروید، تا در تست JVM سنجیده شود.
         */
        fun typeFromClassName(cls: String): String = when {
            cls.contains("positive") -> "increase"
            cls.contains("recovering") -> "recovering"
            cls.contains("negative") -> "decrease"
            else -> "neutral"
        }
    }
}
