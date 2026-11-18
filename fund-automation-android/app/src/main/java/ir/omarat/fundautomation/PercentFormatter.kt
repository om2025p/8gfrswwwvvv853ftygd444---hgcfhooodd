package ir.omarat.fundautomation

import java.util.Locale
import kotlin.math.abs

/**
 * نمایش درصد با «دقت تطبیقی».
 *
 * قاعدهٔ پروژه دو رقم اعشار است، ولی وقتی تغییر واقعی ریز است — مثلاً
 * ۰٫۰۰۳۴٪ که معادل ۷٬۵۱۱ ریال روی پایهٔ ۲۱۹ میلیونی است — دو رقم اعشار آن
 * را به «۰٫۰۰٪» تبدیل می‌کند و کاربر گمان می‌کند محاسبه خراب است. پس برای
 * مقادیر ریز رقم اعشار بیشتری نشان می‌دهیم تا درصد هرگز صفر کاذب نشود.
 *
 * این کلاس خالص است (بدون Android) تا مستقیماً در تست JVM سنجیده شود.
 */
object PercentFormatter {

    /** رقم اعشار لازم برای دیده‌شدن تغییر در هر بزرگی. */
    fun decimalsFor(percent: Double): Int {
        val abs = abs(percent)
        return when {
            abs == 0.0 -> 2
            abs < 0.01 -> 4
            abs < 1.0 -> 3
            else -> 2
        }
    }

    /** «+۰٫۰۰۳۴٪» / «−۱٫۲۵٪» / «۰٫۰۰٪» — با علامت و نماد درصد. */
    fun format(percent: Double): String {
        val sign = if (percent > 0) "+" else if (percent < 0) "−" else ""
        return String.format(
            Locale.US, "%s%.${decimalsFor(percent)}f%%", sign, abs(percent)
        )
    }

    /** همان مقدار بدون علامت و بدون نماد درصد (برای برچسب‌های خالص عددی). */
    fun formatNumber(percent: Double): String =
        String.format(Locale.US, "%.${decimalsFor(percent)}f", abs(percent))
}
