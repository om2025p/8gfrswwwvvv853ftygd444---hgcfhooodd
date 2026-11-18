package ir.omarat.fundautomation

import android.annotation.SuppressLint
import android.os.Bundle
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

/**
 * نمایش صفحات محلی ثبت درصد ۴ و ۵ داخل خود اپ.
 *
 * این صفحات همان فایل‌های HTML فعلی پروژه‌اند که در `assets/webapp` کپی
 * شده‌اند و از `localStorage` همین WebView می‌خوانند. صفحهٔ خانهٔ کوچک
 * (`webapp/index.html`) امکان انتخاب صندوق را می‌دهد؛ پیش از این، مسیر
 * `gold4` هاردکد بود و سینرژی هیچ راه دسترسی نداشت.
 */
class WebViewActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        webView = WebView(this)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            userAgentString =
                "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 " +
                "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        }
        webView.webViewClient = WebViewClient()
        setContentView(webView)
        webView.loadUrl("file:///android_asset/webapp/index.html")
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else finish()
    }
}
