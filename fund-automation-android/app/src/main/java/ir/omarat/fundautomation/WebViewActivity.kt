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
 * شده‌اند و از `localStorage` همین WebView می‌خوانند.
 */
class WebViewActivity : AppCompatActivity() {

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val wv = WebView(this)
        wv.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            userAgentString =
                "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 " +
                "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        }
        wv.webViewClient = WebViewClient()
        setContentView(wv)
        wv.loadUrl("file:///android_asset/webapp/gold4/index.html")
    }

    override fun onBackPressed() {
        finish()
    }
}
