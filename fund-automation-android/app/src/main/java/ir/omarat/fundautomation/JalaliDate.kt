package ir.omarat.fundautomation

import java.util.Calendar
import java.util.GregorianCalendar
import java.util.TimeZone

/**
 * تبدیل تاریخ میلادی به شمسی (الگوریتم استاندارد جلالی).
 *
 * از تاریخ‌گذاری UTC استفاده می‌کنیم تا با داده‌های موجود پروژه
 * (که با `toISOString()` ذخیره شده‌اند) هم‌خوان بماند.
 */
object JalaliDate {

    private val gDaysInMonth = intArrayOf(31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    private val jDaysInMonth = intArrayOf(31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29)

    /** تاریخ شمسی به شکل «۱۴۰۵/۰۶/۲۵» یا با ساعت. */
    fun format(timestampMs: Long, withTime: Boolean = true): String {
        val cal = GregorianCalendar(TimeZone.getTimeZone("UTC"))
        cal.timeInMillis = timestampMs
        val gy = cal.get(Calendar.YEAR)
        val gm = cal.get(Calendar.MONTH) + 1
        val gd = cal.get(Calendar.DAY_OF_MONTH)
        val (jy, jm, jd) = toJalali(gy, gm, gd)
        val p = { n: Int, len: Int -> n.toString().padStart(len, '0') }
        val date = "${jy}/${p(jm, 2)}/${p(jd, 2)}"
        if (!withTime) return date
        val hh = p(cal.get(Calendar.HOUR_OF_DAY), 2)
        val mm = p(cal.get(Calendar.MINUTE), 2)
        val ss = p(cal.get(Calendar.SECOND), 2)
        return "$date $hh:$mm:$ss"
    }

    /** تاریخ شمسی فشرده برای شناسهٔ عملیات: «1405-06-25». */
    fun compactId(timestampMs: Long): String =
        format(timestampMs, withTime = false).replace('/', '-')

    private fun toJalali(gy0: Int, gm: Int, gd: Int): Triple<Int, Int, Int> {
        var gy = gy0
        var jy = gy - 621
        val gDayNo = gregorianDayNo(gy, gm, gd)
        val jDayNo = gDayNo - 79
        val jNp = div(jDayNo, 12053)
        var rem = jDayNo % 12053
        jy += 33 * jNp
        if (rem >= 0) {
            jy += 4 * div(rem, 1461)
            rem %= 1461
        }
        if (rem > 365) {
            jy += div(rem - 1, 365)
            rem = (rem - 1) % 365
        }
        val jm: Int
        val jd: Int
        if (rem < 186) {
            jm = 1 + div(rem, 31)
            jd = 1 + (rem % 31)
        } else {
            jm = 7 + div(rem - 186, 30)
            jd = 1 + ((rem - 186) % 30)
        }
        return Triple(jy, jm, jd)
    }

    private fun gregorianDayNo(gy: Int, gm: Int, gd: Int): Int {
        var days = 0
        for (i in 1 until gm) days += gDaysInMonth[i - 1]
        if (gm > 2 && isLeap(gy)) days += 1
        var y = gy - 1
        days += y * 365 + div(y, 4) - div(y, 100) + div(y, 400)
        return days + gd
    }

    private fun div(a: Int, b: Int): Int = Math.floorDiv(a, b)

    private fun isLeap(gy: Int): Boolean =
        (gy % 4 == 0 && gy % 100 != 0) || gy % 400 == 0
}
