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
import kotlin.coroutines.resume

/**
 * نوشتن درصد محاسبه‌شده در `localStorage` خودِ وب‌اپ‌های ثبت درصد.
 *
 * ⚠️ چرا WebView جداگانه؟ چون `localStorage` به **origin** گره خورده است.
 * WebView اتوماسیون روی `https://m.easytrader.ir` کار می‌کند و حافظهٔ آن
 * با حافظهٔ وب‌اپ (که روی `file:///android_asset/webapp/...` است) یکی نیست.
 * پس اگر تزریق در WebView اتوماسیون انجام شود، نوشتن بی‌اثر است و کاربر
 * رکورد جدید را در صفحهٔ صندوق نمی‌بیند.
 *
 * این کلاس صفحهٔ واقعی صندوق را در یک WebView بارگذاری می‌کند تا اسکریپت در
 * همان origin و همان فضای کلید اجرا شود که کاربر هنگام باز کردن وب‌اپ می‌بیند.
 */
class WebAppWriter(private val context: Context) {

    /**
     * یک رکورد را در حافظهٔ وب‌اپ می‌نویسد.
     *
     * @param pageUrl  نشانی `file://` صفحهٔ صندوق (همان که کاربر می‌بیند)
     * @param script   اسکریپت تزریقی از [WebAppStore.buildInjectScript]
     * @param onReady  کال‌بک برای وصل کردن WebView به پنجره (رندر لازم نیست،
     *                 ولی اتصال، رفتار WebView را پایدارتر می‌کند)
     * @return `true` اگر نوشتن موفق بود.
     */
    @SuppressLint("SetJavaScriptEnabled")
    suspend fun write(
        pageUrl: String,
        script: String,
        onReady: (WebView) -> Unit
    ): WriteResult = withContext(Dispatchers.Main) {
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

        onReady(webView)

        try {
            webView.loadUrl(pageUrl)
            withTimeoutOrNull(20_000) {
                while (!loaded) delay(200)
            }
            // مکث تا IIFE صفحه (loadData/saveData) کامل مستقر شود
            delay(1_500)

            val raw = evaluate(webView, script)
            val result = decodeResult(raw)
            when (result) {
                "OK" -> WriteResult(true, "ثبت شد")
                "SKIP" -> WriteResult(true, "از قبل ثبت بود (بدون تکرار)")
                else -> WriteResult(false, result)
            }
        } catch (e: Exception) {
            WriteResult(false, e.message ?: "خطای نامعلوم")
        } finally {
            webView.destroy()
        }
    }

    /** `evaluateJavascript` خروجی رشته را JSON-encode می‌کند؛ کوتیشن‌ها حذف می‌شوند. */
    private fun decodeResult(raw: String?): String {
        if (raw == null || raw == "null") return "ERR:پاسخی از صفحه نیامد"
        var s = raw.trim()
        if (s.startsWith("\"") && s.endsWith("\"") && s.length >= 2) {
            s = s.substring(1, s.length - 1)
        }
        return s.replace("\\\"", "\"").replace("\\n", "\n")
    }

    /**
     * خواندن همهٔ کلیدهای مرتبط با صندوق از `localStorage` صفحهٔ وب‌اپ.
     *
     * @return نگاشت کلید → مقدار رشته‌ای، یا `null` اگر صفحه بارگذاری نشد.
     */
    @SuppressLint("SetJavaScriptEnabled")
    suspend fun readKeys(pageUrl: String, keys: List<String>): Map<String, String>? =
        withContext(Dispatchers.Main) {
            val webView = newWebView()
            var loaded = false
            webView.webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView, url: String) {
                    loaded = true
                }
            }
            try {
                webView.loadUrl(pageUrl)
                withTimeoutOrNull(20_000) { while (!loaded) delay(200) }
                delay(1_000)
                val keyList = keys.joinToString(",") { "'${jsonEscape(it)}'" }
                val js = """
                (function(){
                  var out = {};
                  var keys = [$keyList];
                  for (var i=0;i<keys.length;i++){
                    var v = localStorage.getItem(keys[i]);
                    if (v !== null && v !== undefined) out[keys[i]] = v;
                  }
                  return JSON.stringify(out);
                })();
                """.trimIndent()
                parseMap(evaluate(webView, js))
            } catch (e: Exception) {
                null
            } finally {
                webView.destroy()
            }
        }

    /**
     * نوشتن نگاشت کلید/مقدار در `localStorage` صفحهٔ وب‌اپ (برای بازیابی).
     *
     * @return تعداد کلیدهای نوشته‌شده، یا `-1` در صورت خطا.
     */
    @SuppressLint("SetJavaScriptEnabled")
    suspend fun writeKeys(pageUrl: String, values: Map<String, String>): Int =
        withContext(Dispatchers.Main) {
            val webView = newWebView()
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
                val pairs = values.entries.joinToString(",") {
                    "'${jsonEscape(it.key)}':'${jsonEscape(it.value)}'"
                }
                val js = """
                (function(){
                  try {
                    var data = {$pairs};
                    var n = 0;
                    for (var k in data){ localStorage.setItem(k, data[k]); n++; }
                    try {
                      if (typeof window.reloadLocalData === 'function') window.reloadLocalData();
                      if (typeof window.saveData === 'function') window.saveData();
                    } catch(e){}
                    return String(n);
                  } catch(e){ return '-1'; }
                })();
                """.trimIndent()
                decodeResult(evaluate(webView, js)).toIntOrNull() ?: -1
            } catch (e: Exception) {
                -1
            } finally {
                webView.destroy()
            }
        }

    @SuppressLint("SetJavaScriptEnabled")
    private fun newWebView(): WebView = WebView(context).apply {
        settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            cacheMode = WebSettings.LOAD_DEFAULT
        }
    }

    private fun parseMap(raw: String?): Map<String, String>? {
        if (raw == null || raw == "null") return null
        val json = decodeResult(raw)
        return try {
            val obj = org.json.JSONObject(json)
            val out = LinkedHashMap<String, String>()
            for (k in obj.keys()) out[k] = obj.getString(k)
            out
        } catch (e: Exception) {
            null
        }
    }

    private fun jsonEscape(s: String): String =
        org.json.JSONObject.quote(s).removeSurrounding("\"")

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

    data class WriteResult(val success: Boolean, val message: String)

    companion object {
        /** نشانی صفحهٔ صندوق ۴ (آتیه مفید) داخل assets. */
        const val ATIE_PAGE = "file:///android_asset/webapp/gold4/percent.html"

        /** نشانی صفحهٔ صندوق ۵ (سینرژی) داخل assets. */
        const val SYNERGY_PAGE = "file:///android_asset/webapp/gold5/percent.html"
    }
}
