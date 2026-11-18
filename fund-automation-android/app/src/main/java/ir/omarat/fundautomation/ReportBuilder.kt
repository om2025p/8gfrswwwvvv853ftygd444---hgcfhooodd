package ir.omarat.fundautomation

/**
 * ساخت گزارش فارسی پایان اجرا.
 *
 * اطلاعات محرمانهٔ حساب (نام کاربری، رمز، کوکی) هرگز در گزارش نمی‌آید.
 */
object ReportBuilder {

    data class FundReport(
        val fundName: String,
        val base: Long?,
        val newValue: Long?,
        val percent: Double?,
        val type: String,
        val extractionOk: Boolean,
        val method: String
    )

    fun build(
        jalaliDate: String,
        funds: List<FundReport>,
        savedOk: Boolean,
        backupOk: Boolean
    ): String {
        val sb = StringBuilder()
        sb.appendLine("📄 گزارش اجرای اتوماسیون")
        sb.appendLine("🗓 تاریخ: $jalaliDate")
        sb.appendLine("──────────────────────────")

        for (f in funds) {
            sb.appendLine("🏦 ${f.fundName}")
            sb.appendLine("  • مقدار پایهٔ قبلی: ${f.base?.let { fmt(it) } ?: "—"}")
            sb.appendLine("  • مقدار جدید: ${f.newValue?.let { fmt(it) } ?: "—"}")
            sb.appendLine("  • درصد تغییر: ${f.percent?.let { pct(it) } ?: "—"}")
            sb.appendLine("  • وضعیت استخراج: ${if (f.extractionOk) "✅ موفق (${methodLabel(f.method)})" else "❌ ناموفق"}")
            sb.appendLine("  • وضعیت محاسبه: ${if (f.percent != null) "✅" else "—"}")
            sb.appendLine()
        }

        sb.appendLine("──────────────────────────")
        sb.appendLine("💾 ذخیرهٔ تاریخچه: ${if (savedOk) "✅ موفق" else "❌ ناموفق"}")
        sb.appendLine("📦 پشتیبان‌گیری: ${if (backupOk) "✅ موفق" else "❌ ناموفق"}")
        return sb.toString()
    }

    private fun fmt(n: Long): String = String.format("%,d ریال", n)

    private fun pct(p: Double): String {
        val sign = if (p >= 0) "+" else "−"
        return String.format(java.util.Locale.US, "%s%.2f%%", sign, kotlin.math.abs(p))
    }

    private fun methodLabel(m: String): String = when (m) {
        "network" -> "شنود API"
        "text" -> "اسکن متن"
        "dom" -> "پیمایش DOM"
        "ai" -> "هوش مصنوعی"
        else -> m
    }
}
