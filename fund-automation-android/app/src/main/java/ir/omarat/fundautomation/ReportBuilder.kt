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
        val method: String,
        /** تاریخ به‌روزرسانی دارایی که منبع اعلام کرده (توضیح ۰٪ بودن). */
        val sourceUpdatedAt: String? = null
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
            sb.appendLine("  • درصد تغییر: ${f.percent?.let { PercentFormatter.format(it) } ?: "—"}")
            if (f.base != null && f.newValue != null) {
                val diff = f.newValue - f.base
                sb.appendLine("  • تغییر مبلغ: ${if (diff >= 0) "+" else "−"}${fmt(kotlin.math.abs(diff))}")
            }
            sb.appendLine("  • وضعیت استخراج: ${if (f.extractionOk) "✅ موفق (${methodLabel(f.method)})" else "❌ ناموفق"}")
            sb.appendLine("  • وضعیت محاسبه: ${if (f.percent != null) "✅" else "—"}")
            if (f.sourceUpdatedAt != null) {
                sb.appendLine("  • آخرین به‌روزرسانی منبع: ${f.sourceUpdatedAt}")
            }
            if (f.percent == 0.0 && f.base != null && f.newValue != null && f.base == f.newValue) {
                sb.appendLine("  ℹ️ مقدار منبع تغییر نکرده؛ صفر درصد درست است.")
            }
            sb.appendLine()
        }

        sb.appendLine("──────────────────────────")
        sb.appendLine("💾 ذخیرهٔ تاریخچه: ${if (savedOk) "✅ موفق" else "❌ ناموفق"}")
        sb.appendLine("📦 پشتیبان‌گیری: ${if (backupOk) "✅ موفق" else "❌ ناموفق"}")
        return sb.toString()
    }

    private fun fmt(n: Long): String = String.format("%,d ریال", n)

    private fun methodLabel(m: String): String = when (m) {
        "network" -> "شنود API"
        "text" -> "اسکن متن"
        "dom" -> "پیمایش DOM"
        "ai" -> "هوش مصنوعی"
        else -> m
    }
}
