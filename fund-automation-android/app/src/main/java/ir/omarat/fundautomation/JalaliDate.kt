package ir.omarat.fundautomation

import java.util.Calendar
import java.util.GregorianCalendar
import java.util.TimeZone

/**
 * تبدیل تاریخ میلادی به شمسی.
 *
 * از الگوریتم استاندارد `jalaali-js`/`jdatetime` استفاده می‌کند (پایهٔ ۳۳سالهٔ
 * ۱۲۰۵۳روزه). نسخهٔ پیشین با محاسبهٔ `gy - 621` و سپس افزودن `33 * np` سال را
 * دو بار جابه‌جا می‌کرد و ۲۰۲۶ را ۳۴۳۰ نشان می‌داد.
 *
 * منطقهٔ زمانی `Asia/Tehran` است تا با ساعت کاربر و گزارش‌های فارسی پروژه
 * (که با تاریخ محلی ثبت می‌شوند) یکی باشد.
 */
object JalaliDate {

    private val cumulativeGregorianDays =
        intArrayOf(0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)

    /** تاریخ شمسی به شکل «۱۴۰۵/۰۸/۲۶» یا همراه با ساعت. */
    fun format(timestampMs: Long, withTime: Boolean = true): String {
        val cal = GregorianCalendar(TimeZone.getTimeZone("Asia/Tehran"))
        cal.timeInMillis = timestampMs
        val (jy, jm, jd) = toJalali(
            cal.get(Calendar.YEAR),
            cal.get(Calendar.MONTH) + 1,
            cal.get(Calendar.DAY_OF_MONTH)
        )
        val p = { n: Int, len: Int -> n.toString().padStart(len, '0') }
        val date = "${p(jy, 4)}/${p(jm, 2)}/${p(jd, 2)}"
        if (!withTime) return date
        val hh = p(cal.get(Calendar.HOUR_OF_DAY), 2)
        val mm = p(cal.get(Calendar.MINUTE), 2)
        val ss = p(cal.get(Calendar.SECOND), 2)
        return "$date $hh:$mm:$ss"
    }

    /** تاریخ شمسی فشرده برای شناسهٔ عملیات: «1405-08-26». */
    fun compactId(timestampMs: Long): String =
        format(timestampMs, withTime = false).replace('/', '-')

    private fun toJalali(gy: Int, gm: Int, gd: Int): Triple<Int, Int, Int> {
        val gregorianYearForLeap = if (gm > 2) gy + 1 else gy
        var days = 355666 + 365 * gy +
            (gregorianYearForLeap + 3) / 4 -
            (gregorianYearForLeap + 99) / 100 +
            (gregorianYearForLeap + 399) / 400 +
            gd + cumulativeGregorianDays[gm - 1]

        var jy = -1595 + 33 * (days / 12053)
        days %= 12053
        jy += 4 * (days / 1461)
        days %= 1461
        if (days > 365) {
            jy += (days - 1) / 365
            days = (days - 1) % 365
        }
        val jm: Int
        val jd: Int
        if (days < 186) {
            jm = 1 + days / 31
            jd = 1 + days % 31
        } else {
            jm = 7 + (days - 186) / 30
            jd = 1 + (days - 186) % 30
        }
        return Triple(jy, jm, jd)
    }
}
