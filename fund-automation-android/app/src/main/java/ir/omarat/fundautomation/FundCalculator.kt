package ir.omarat.fundautomation

import kotlin.math.abs
import kotlin.math.roundToLong

/**
 * نتیجهٔ محاسبهٔ درصد برای یک صندوق.
 */
data class PercentResult(
    val base: Long,
    val newValue: Long,
    val previousPeak: Long,
    val percent: Double,
    val type: ChangeType,
    val tomanProfit: Long
)

enum class ChangeType { INCREASE, RECOVERING, DECREASE, NEUTRAL }

/**
 * موتور محاسبهٔ درصد، بازپیاده‌سازی دقیق منطق فعلی پروژه
 * (`gold4/calculator.html` و `gold5/calculator.html`).
 *
 * فرمول:  ((جدید − پایه) ÷ پایه) × ۱۰۰
 * منطق قله (peak):
 *   جدید > قله            → سود خالص واقعی (سبز)
 *   پایه < جدید ≤ قله     → جبران ضرر (نارنجی)
 *   جدید < پایه           → کاهش (قرمز)
 *   جدید == پایه          → بدون تغییر
 */
object FundCalculator {

    fun calculate(base: Long, newValue: Long, previousPeak: Long?): PercentResult? {
        if (base <= 0) return null

        val peak = previousPeak?.takeIf { it > 0 } ?: base
        val percent = ((newValue - base).toDouble() / base.toDouble()) * 100.0
        val percentFixed = roundTo2(percent)

        val type: ChangeType
        val tomanProfit: Long
        when {
            newValue > peak -> {
                type = ChangeType.INCREASE
                tomanProfit = ((newValue - peak) / 10000.0).roundToLong()
            }
            newValue > base -> {
                type = ChangeType.RECOVERING
                tomanProfit = ((newValue - base) / 10000.0).roundToLong()
            }
            newValue < base -> {
                type = ChangeType.DECREASE
                tomanProfit = ((newValue - base) / 10000.0).roundToLong()
            }
            else -> {
                type = ChangeType.NEUTRAL
                tomanProfit = 0L
            }
        }

        return PercentResult(
            base = base,
            newValue = newValue,
            previousPeak = peak,
            percent = percentFixed,
            type = type,
            tomanProfit = tomanProfit
        )
    }

    /** قلهٔ جدید پس از محاسبه: اگر از قله گذشتیم، مقدار جدید قلهٔ تازه است. */
    fun newPeak(result: PercentResult): Long =
        if (result.newValue > result.previousPeak) result.newValue else result.previousPeak

    /** مقدار مطلق تغییر به ریال (برای نمایش در گزارش). */
    fun changeAmount(result: PercentResult): Long =
        abs(((result.percent / 100.0) * result.base).roundToLong())

    private fun roundTo2(v: Double): Double = (v * 100.0).roundToLong() / 100.0
}
