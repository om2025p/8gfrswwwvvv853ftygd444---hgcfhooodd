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
