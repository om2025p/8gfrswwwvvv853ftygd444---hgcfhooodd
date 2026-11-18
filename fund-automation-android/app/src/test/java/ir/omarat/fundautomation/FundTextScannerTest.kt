package ir.omarat.fundautomation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * تست اسکنر متن با **دادهٔ واقعی صفحه‌های ایزی‌تریدر** (برگرفته از
 * اسکرین‌شات‌های کاربر). این تست‌ها همان باگی را می‌سنجند که استخراج را
 * کاملاً می‌شکست: جداکنندهٔ هزارگان فارسی `٬` (U+066C).
 */
class FundTextScannerTest {

    private val synergyKeywords = listOf("سینرژی", "synergy")
    private val atieKeywords = listOf("آتیه", "بازنشستگی", "atie")

    // ── باگ بحرانی: جداکنندهٔ هزارگان فارسی ──────────────────────────────

    @Test
    fun `normalize converts persian thousands separator to comma`() {
        // این دقیقاً همان چیزی است که regex را می‌شکست.
        assertEquals("220,351,260", FundTextScanner.normalize("۲۲۰٬۳۵۱٬۲۶۰"))
    }

    @Test
    fun `normalize handles arabic thousands separator and thin spaces`() {
        assertEquals("397,615,869", FundTextScanner.normalize("۳۹۷،۶۱۵،۸۶۹"))
        assertEquals("1234567", FundTextScanner.normalize("1\u00A02\u200C3\u200F4 567".replace(" ", "")))
    }

    @Test
    fun `normalize keeps decimal point untouched`() {
        // نقطهٔ اعشار نباید به کاما تبدیل شود، وگرنه «150.28%» به عدد غلط می‌شد.
        assertEquals("150.28", FundTextScanner.normalize("۱۵۰.۲۸"))
    }

    // ── سینرژی روی پرتفوی (عکس ۲ کاربر) ─────────────────────────────────

    @Test
    fun `extracts synergy current value from portfolio row`() {
        // ردیف واقعی پرتفوی: نماد | تعداد | آخرین قیمت | قیمت پایانی | ارزش فعلی | سود و زیان
        val row = "سینرژی 2,507 88,000 (1.66%) 88,070 (1.75%) 220,351,260 3,359,507 (1.54%) " +
            "دارونو 1,510 46,712 70,372,889 همسنگ 153"
        val value = FundTextScanner.extractValue(row, synergyKeywords, "synergy")
        // «ارزش فعلی» = ۲۲۰٬۳۵۱٬۲۶۰ و بزرگ‌ترین عدد پنجره تا «دارونو»/«همسنگ» است.
        assertEquals(220_351_260L, value)
    }

    @Test
    fun `extracts synergy value with persian digits and separator`() {
        val row = "سینرژی ۲٬۵۰۷ ۸۸٬۰۰۰ ۲۲۰٬۳۵۱٬۲۶۰ همسنگ ۱۵۳"
        assertEquals(220_351_260L, FundTextScanner.extractValue(row, synergyKeywords, "synergy"))
    }

    // ── آتیه روی «صندوق‌های مفید» (عکس ۳ کاربر) ─────────────────────────

    @Test
    fun `extracts atie asset value from funds page`() {
        val page = "ارزش صندوق‌ها 397,615,869 صندوق های من آتیه 397,615,869 7,581 واحد " +
            "ماه اخیر 7% 3 ماه اخیر 35.3% سال اخیر 150.28% سایر صندوق‌های مفید " +
            "ممتاز 4.85% امید توسعه 3.48%"
        val value = FundTextScanner.extractValue(page, atieKeywords, "atie")
        assertEquals(397_615_869L, value)
    }

    @Test
    fun `extracts atie value with persian digits`() {
        val page = "آتیه ۳۹۷٬۶۱۵٬۸۶۹ ۷٬۵۸۱ واحد ممتاز"
        assertEquals(397_615_869L, FundTextScanner.extractValue(page, atieKeywords, "atie"))
    }

    @Test
    fun `atie window stops before next fund so umid values are not mixed`() {
        // اگر مرز «ممتاز» رعایت نشود، عددی از صندوق‌های بعدی برمی‌گردد.
        val page = "آتیه 397,615,869 7,581 واحد ممتاز 123,456,789 امید توسعه 999,888,777"
        assertEquals(397_615_869L, FundTextScanner.extractValue(page, atieKeywords, "atie"))
    }

    // ── موارد منفی ───────────────────────────────────────────────────────

    @Test
    fun `returns null when keyword absent`() {
        assertNull(FundTextScanner.extractValue("دارونو 70,372,889 همسنگ 3,926,872", synergyKeywords, "synergy"))
    }

    @Test
    fun `ignores numbers below one million`() {
        assertNull(FundTextScanner.extractValue("آتیه 7,581 واحد 150.28% ممتاز", atieKeywords, "atie"))
    }

    @Test
    fun `largestNumber picks max in a segment`() {
        assertEquals(999_999_999L, FundTextScanner.largestNumber("12,345 و 999,999,999 و 1,000,000"))
    }

    // ── ثبت تکراری: منطق روز شمسی ────────────────────────────────────────

    @Test
    fun `jalali day format is stable for duplicate detection`() {
        // دو زمان در یک روز باید یک رشتهٔ روز بدهند.
        val a = JalaliDate.format(1_760_000_000_000L, withTime = false)
        val b = JalaliDate.format(1_760_000_000_000L + 3_600_000L, withTime = false)
        assertEquals(a, b)
        assertTrue(a.matches(Regex("""\d{4}/\d{2}/\d{2}""")))
    }
}
