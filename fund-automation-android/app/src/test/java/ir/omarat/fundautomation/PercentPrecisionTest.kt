package ir.omarat.fundautomation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * تست دقت درصد و نمایش تطبیقی.
 *
 * باگ واقعی کاربر: سینرژی از ۲۱۹٬۰۹۹٬۲۶۵ به ۲۱۹٬۱۰۶٬۷۷۶ رسید (۷٬۵۱۱ ریال
 * سود) ولی «۰٫۰۰٪» ثبت شد، چون درصد با دو رقم اعشار گرد می‌شد. این تست‌ها
 * همان عدد واقعی را می‌سنجند تا رگرسیون نشود.
 */
class PercentPrecisionTest {

    @Test
    fun `tiny real change is not lost`() {
        val r = FundCalculator.calculate(219_099_265L, 219_106_776L, null)!!
        // درصد واقعی ۰٫۰۰۳۴۲۸٪ است و نباید صفر شود.
        assertTrue("درصد نباید صفر شود", r.percent > 0.0)
        assertEquals(0.003428, r.percent, 0.000001)
    }

    @Test
    fun `formatter shows enough decimals for tiny change`() {
        // «۰٫۰۰٪» هرگز نباید نمایش داده شود وقتی تغییر واقعی وجود دارد.
        assertEquals("+0.0034%", PercentFormatter.format(0.003428))
        assertTrue(PercentFormatter.format(0.003428) != "+0.00%")
    }

    @Test
    fun `formatter keeps two decimals for normal change`() {
        assertEquals("+1.25%", PercentFormatter.format(1.25))
        assertEquals("−2.50%", PercentFormatter.format(-2.5))
    }

    @Test
    fun `formatter shows plain zero for real zero`() {
        assertEquals("0.00%", PercentFormatter.format(0.0))
    }

    @Test
    fun `formatter handles sub-one-percent change`() {
        assertEquals("+0.345%", PercentFormatter.format(0.345))
    }

    @Test
    fun `identical values give neutral zero`() {
        // آتیه واقعی: منبع هنوز به‌روز نشده و مقدار تغییر نکرده → صفر درست است.
        val r = FundCalculator.calculate(397_615_869L, 397_615_869L, null)!!
        assertEquals(0.0, r.percent, 0.0)
        assertEquals(ChangeType.NEUTRAL, r.type)
    }

    @Test
    fun `round trip percent preserves small change in stored value`() {
        val r = FundCalculator.calculate(219_099_265L, 219_106_776L, null)!!
        // مقداری که در percents[].value ذخیره می‌شود باید غیرصفر بماند.
        assertTrue(r.percent != 0.0)
        assertEquals(7511L, FundCalculator.changeAmount(r))
    }
}
