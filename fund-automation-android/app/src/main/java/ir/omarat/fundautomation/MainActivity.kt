package ir.omarat.fundautomation

import android.app.AlertDialog
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Bundle
import android.text.InputType
import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.util.Locale
import kotlin.coroutines.resume

class MainActivity : AppCompatActivity() {

    private lateinit var session: SessionStore
    private lateinit var backup: BackupManager
    private lateinit var txtLog: TextView
    private lateinit var txtConnection: TextView
    private lateinit var txtLastRun: TextView
    private lateinit var txtStorage: TextView
    private lateinit var txtBackup: TextView
    private lateinit var txtAtieBase: TextView
    private lateinit var txtAtiePercent: TextView
    private lateinit var txtSynergyBase: TextView
    private lateinit var txtSynergyPercent: TextView

    private lateinit var automationPanel: View
    private lateinit var webViewContainer: FrameLayout
    private lateinit var txtWebStatus: TextView

    private val prefs by lazy { getSharedPreferences("omarat_fund_automation_state", Context.MODE_PRIVATE) }
    private val logLines = StringBuilder()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        session = SessionStore(this)
        backup = BackupManager(session)

        txtLog = findViewById(R.id.txtLog)
        txtConnection = findViewById(R.id.txtConnection)
        txtLastRun = findViewById(R.id.txtLastRun)
        txtStorage = findViewById(R.id.txtStorage)
        txtBackup = findViewById(R.id.txtBackup)
        txtAtieBase = findViewById(R.id.txtAtieBase)
        txtAtiePercent = findViewById(R.id.txtAtiePercent)
        txtSynergyBase = findViewById(R.id.txtSynergyBase)
        txtSynergyPercent = findViewById(R.id.txtSynergyPercent)

        automationPanel = findViewById(R.id.automationPanel)
        webViewContainer = findViewById(R.id.webViewContainer)
        txtWebStatus = findViewById(R.id.txtWebStatus)

        findViewById<TextView>(R.id.btnRun).setOnClickListener { startAutomation() }
        findViewById<TextView>(R.id.btnSettings).setOnClickListener { openSettings() }
        findViewById<TextView>(R.id.btnOpenWeb).setOnClickListener {
            startActivity(Intent(this, WebViewActivity::class.java))
        }

        refreshStatus()
    }

    /**
     * WebView اتوماسیون را داخل پنل قرار می‌دهد و پنل را نمایان می‌کند.
     *
     * بدون این کار، WebView به پنجره وصل نیست؛ رندر و layout انجام نمی‌شود و
     * `document.body.innerText` خالی برمی‌گردد — همان چیزی که باعث شکست
     * هر چهار لایهٔ استخراج می‌شد.
     */
    private fun attachAutomationWebView(webView: WebView) {
        (webView.parent as? ViewGroup)?.removeView(webView)
        webViewContainer.removeAllViews()
        webViewContainer.addView(
            webView,
            FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )
        automationPanel.visibility = View.VISIBLE
    }

    private fun detachAutomationWebView() {
        webViewContainer.removeAllViews()
        automationPanel.visibility = View.GONE
    }

    // ------------------------------------------------------------------ Status

    private fun refreshStatus() {
        val online = isOnline()
        txtConnection.text = if (online) "اتصال اینترنت: ✅ متصل" else "اتصال اینترنت: ❌ قطع"
        txtLastRun.text = "آخرین اجرای موفق: " + (prefs.getString("last_run", null) ?: "—")
        txtStorage.text = "وضعیت ذخیره‌سازی: " + if (session.hasCredentials) "آماده (اطلاعات ورود ذخیره شده)" else "نیازمند تنظیم اطلاعات ورود"
        txtBackup.text = "آخرین پشتیبان: " + (prefs.getString("last_backup", null) ?: "—")
        txtAtieBase.text = "پایه: " + (prefs.getString("atie_base", "—") ?: "—")
        txtAtiePercent.text = "آخرین درصد: " + (prefs.getString("atie_percent", "—") ?: "—")
        txtSynergyBase.text = "پایه: " + (prefs.getString("synergy_base", "—") ?: "—")
        txtSynergyPercent.text = "آخرین درصد: " + (prefs.getString("synergy_percent", "—") ?: "—")
    }

    private fun isOnline(): Boolean {
        val cm = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val net = cm.activeNetwork ?: return false
        val caps = cm.getNetworkCapabilities(net) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    // ------------------------------------------------------------------ Automation

    private fun startAutomation() {
        if (!isOnline()) {
            toast("اینترنت وصل نیست.")
            return
        }
        if (!session.hasCredentials) {
            toast("اول از ⚙️ تنظیمات، اطلاعات ورود را وارد کن.")
            openSettings()
            return
        }

        logLines.clear()
        appendLog("🚀 شروع اتوماسیون…")
        findViewById<TextView>(R.id.btnRun).isEnabled = false

        lifecycleScope.launch {
            try {
                val now = System.currentTimeMillis()
                val jalali = JalaliDate.format(now)

                val atieBase = prefs.getString("atie_base_num", null)?.toLongOrNull()
                val synergyBase = prefs.getString("synergy_base_num", null)?.toLongOrNull()
                val atiePeak = prefs.getString("atie_peak", null)?.toLongOrNull()
                val synergyPeak = prefs.getString("synergy_peak", null)?.toLongOrNull()

                val engine = AutomationEngine(this@MainActivity, session) { msg, level ->
                    runOnUiThread { appendLog(msg, level) }
                }
                engine.setOtpProvider { askOtp() }

                val outcomes = engine.run(
                    baseAtie = atieBase,
                    baseSynergy = synergyBase,
                    peakAtie = atiePeak,
                    peakSynergy = synergyPeak
                ) { webView ->
                    runOnUiThread { attachAutomationWebView(webView) }
                }

                var savedOk = false
                var backupOk = false

                for (o in outcomes) {
                    val isAtie = o.fund == "atie"
                    appendLog("📊 ${if (isAtie) "آتیه مفید" else "سینرژی"}: ${fmt(o.result.percent)}%", AutomationEngine.LogLevel.OK)
                    val e = prefs.edit()
                    if (isAtie) {
                        e.putString("atie_percent", fmt(o.result.percent) + "%")
                        e.putString("atie_base", fmt(o.newValue))
                        e.putString("atie_base_num", o.newValue.toString())
                        e.putString("atie_peak", FundCalculator.newPeak(o.result).toString())
                    } else {
                        e.putString("synergy_percent", fmt(o.result.percent) + "%")
                        e.putString("synergy_base", fmt(o.newValue))
                        e.putString("synergy_base_num", o.newValue.toString())
                        e.putString("synergy_peak", FundCalculator.newPeak(o.result).toString())
                    }
                    e.apply()
                    savedOk = true
                }

                // پشتیبان‌گیری گیت‌هاب — این همان کانالی است که وب‌اپ‌ها و دیدبان از آن می‌خوانند
                val atieOutcome = outcomes.firstOrNull { it.fund == "atie" }
                val synergyOutcome = outcomes.firstOrNull { it.fund == "synergy" }

                if (atieOutcome != null) {
                    val payload = WebAppStore.buildAtieBackupPayload(
                        atieOutcome.result.percent, atieOutcome.base, atieOutcome.newValue, now
                    )
                    val r = backup.uploadToGitHub(payload, "gold4/gold4_backup.json", "بکاپ خودکار آتیه - $jalali")
                    if (r.success) backupOk = true
                    appendLog(if (r.success) "📦 پشتیبان آتیه در گیت‌هاب ذخیره شد." else "⚠️ پشتیبان آتیه: ${r.message}", AutomationEngine.LogLevel.WARN)
                }

                if (synergyOutcome != null) {
                    val payload = WebAppStore.buildSynergyBackupPayload(
                        synergyOutcome.result.percent, synergyOutcome.base, synergyOutcome.newValue, now
                    )
                    val r = backup.uploadToGitHub(payload, "gold5/gold5_backup.json", "بکاپ خودکار سینرژی - $jalali")
                    if (r.success) backupOk = true
                    appendLog(if (r.success) "📦 پشتیبان سینرژی در گیت‌هاب ذخیره شد." else "⚠️ پشتیبان سینرژی: ${r.message}", AutomationEngine.LogLevel.WARN)
                }

                prefs.edit().putString("last_run", jalali).apply()
                if (backupOk) prefs.edit().putString("last_backup", jalali).apply()

                val report = ReportBuilder.build(
                    jalaliDate = jalali,
                    funds = listOf(
                        ReportBuilder.FundReport("آتیه مفید (۴)", atieOutcome?.base ?: atieBase, atieOutcome?.newValue, atieOutcome?.result?.percent, atieOutcome?.result?.type?.name ?: "-", atieOutcome != null, atieOutcome?.method ?: "-"),
                        ReportBuilder.FundReport("سینرژی (۵)", synergyOutcome?.base ?: synergyBase, synergyOutcome?.newValue, synergyOutcome?.result?.percent, synergyOutcome?.result?.type?.name ?: "-", synergyOutcome != null, synergyOutcome?.method ?: "-")
                    ),
                    savedOk = savedOk,
                    backupOk = backupOk
                )
                appendLog("\n$report")
                toast("اتوماسیون تمام شد.")

            } catch (e: Exception) {
                appendLog("❌ خطا: ${e.message}", AutomationEngine.LogLevel.ERROR)
            } finally {
                findViewById<TextView>(R.id.btnRun).isEnabled = true
                detachAutomationWebView()
                refreshStatus()
            }
        }
    }

    // ------------------------------------------------------------------ OTP

    private suspend fun askOtp(): String? = withContext(Dispatchers.Main) {
        suspendCancellableCoroutine { cont ->
            val input = EditText(this@MainActivity).apply {
                inputType = InputType.TYPE_CLASS_NUMBER
                hint = "کد تأیید ۶ رقمی"
            }
            AlertDialog.Builder(this@MainActivity)
                .setTitle("🔐 کد تأیید (OTP)")
                .setMessage("کارگزاری کد تأیید فرستاده است. لطفاً وارد کن:")
                .setView(input)
                .setCancelable(false)
                .setPositiveButton("ارسال") { _, _ ->
                    cont.resume(input.text.toString().trim().ifBlank { null })
                }
                .setNegativeButton("لغو") { _, _ ->
                    cont.resume(null)
                }
                .show()
        }
    }

    // ------------------------------------------------------------------ Settings

    private fun openSettings() {
        val container = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 24, 48, 8)
        }

        val userField = field("نام کاربری کارگزاری", session.username)
        val passField = field("رمز عبور", session.password, isPassword = true)
        val atieBaseField = field(
            "مقدار پایهٔ آتیه مفید (ریال)",
            prefs.getString("atie_base_num", "") ?: "",
            number = true
        )
        val synergyBaseField = field(
            "مقدار پایهٔ سینرژی (ریال)",
            prefs.getString("synergy_base_num", "") ?: "",
            number = true
        )
        val geminiField = field("کلید Gemini (اختیاری)", session.geminiApiKey)
        val ghTokenField = field("توکن گیت‌هاب (بکاپ)", session.githubToken, isPassword = true)
        val ghRepoField = field("مخزن گیت‌هاب (owner/repo)", session.githubRepo)
        val ghBranchField = field("شاخهٔ گیت‌هاب", session.githubBranch.ifBlank { "main" })

        container.addView(userField)
        container.addView(passField)
        container.addView(atieBaseField)
        container.addView(synergyBaseField)
        container.addView(geminiField)
        container.addView(ghTokenField)
        container.addView(ghRepoField)
        container.addView(ghBranchField)

        AlertDialog.Builder(this)
            .setTitle("⚙️ تنظیمات")
            .setView(container)
            .setPositiveButton("ذخیره") { _, _ ->
                session.username = userField.text.toString().trim()
                session.password = passField.text.toString()
                session.geminiApiKey = geminiField.text.toString().trim()
                session.githubToken = ghTokenField.text.toString().trim()
                session.githubRepo = ghRepoField.text.toString().trim()
                session.githubBranch = ghBranchField.text.toString().trim().ifBlank { "main" }
                prefs.edit()
                    .putString("atie_base_num", digits(atieBaseField.text.toString()))
                    .putString("synergy_base_num", digits(synergyBaseField.text.toString()))
                    .apply()
                toast("ذخیره شد (رمزنگاری‌شده).")
                refreshStatus()
            }
            .setNegativeButton("انصراف", null)
            .show()
    }

    private fun field(
        hint: String,
        value: String,
        isPassword: Boolean = false,
        number: Boolean = false
    ): EditText =
        EditText(this).apply {
            this.hint = hint
            setText(value)
            inputType = when {
                number -> InputType.TYPE_CLASS_NUMBER
                isPassword -> InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
                else -> InputType.TYPE_CLASS_TEXT
            }
        }

    /** حذف کاما و ارقام غیرانگلیسی از ورودی عددی. */
    private fun digits(raw: String): String {
        val persian = "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩"
        val sb = StringBuilder()
        for (c in raw) {
            when {
                c.isDigit() -> sb.append(c)
                c in persian -> sb.append(persian.indexOf(c) % 10)
            }
        }
        return sb.toString()
    }

    // ------------------------------------------------------------------ Helpers

    private fun appendLog(msg: String, level: AutomationEngine.LogLevel = AutomationEngine.LogLevel.INFO) {
        val icon = when (level) {
            AutomationEngine.LogLevel.OK -> "✅"
            AutomationEngine.LogLevel.WARN -> "⚠️"
            AutomationEngine.LogLevel.ERROR -> "❌"
            else -> "•"
        }
        logLines.append("$icon ").append(msg).append("\n")
        txtLog.text = logLines.toString()
    }

    private fun toast(m: String) = Toast.makeText(this, m, Toast.LENGTH_SHORT).show()

    private fun fmt(v: Double): String = String.format(Locale.US, "%.2f", v)

    private fun fmt(v: Long): String = String.format("%,d", v)
}
