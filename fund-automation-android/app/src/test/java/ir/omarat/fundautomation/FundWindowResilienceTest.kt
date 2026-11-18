package ir.omarat.fundautomation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * تست پایداری پنجرهٔ استخراج با چیدمان‌های متفاوت صفحه.
 *
 * در لاگ واقعی، لایهٔ شنود API هر دو بار شکست خورد و فقط اسکن متن نجات داد.
 * پس پنجره باید مستقل از «همسنگ» هم کار کند و اعداد صندوق‌های دیگر را نبلعد.
 */
class FundWindowResilienceTest {

    private val synergyKeywords = listOf("سینرژی", "synergy")
    private val atieKeywords = listOf("آتیه", "بازنشستگی", "atie")

    @Test
    fun `synergy works without hesang marker`() {
        // چیدمان واقعی امروز: بعد از ارزش فعلی، ستون‌های سود و زیان و نماد بعدی.
        val row = "سینرژی 2,507 ۸۷٬۵۰۳ (1.09%) 88,070 (1.75%) 219,106,776 3,359,507 (1.54%) " +
            "خرید فروش کل دارایی دارونو 1,510 46,712 70,372,889"
        assertEquals(219_106_776L, FundTextScanner.extractValue(row, synergyKeywords, "synergy"))
    }

    @Test
    fun `synergy window stops at next symbol columns`() {
        val row = "سینرژی 2,507 87,503 219,106,776 سود و زیان 999,999,999"
        // «سود و زیان» مرز پنجره است، پس عدد بزرگ بعدی نباید برداشته شود.
        assertEquals(219_106_776L, FundTextScanner.extractValue(row, synergyKeywords, "synergy"))
    }

    @Test
    fun `atie window stops at other funds header`() {
        val page = "آتیه 397,615,869 7,581 واحد ماه اخیر 7% سایر صندوق‌های مفید " +
            "ممتاز 123,456,789 امید توسعه 999,888,777"
        assertEquals(397_615_869L, FundTextScanner.extractValue(page, atieKeywords, "atie"))
    }

    @Test
    fun `atie picks asset not unit count`() {
        val page = "آتیه 397,615,869 7,581 واحد ممتاز"
        // واحد (۷٬۵۸۱) باید نادیده برود چون زیر یک میلیون است.
        assertEquals(397_615_869L, FundTextScanner.extractValue(page, atieKeywords, "atie"))
    }

    @Test
    fun `persian digits with separator are handled in both funds`() {
        val synergy = "سینرژی ۲٬۵۰۷ ۲۱۹٬۱۰۶٬۷۷۶ همسنگ ۱۵۳"
        val atie = "آتیه ۳۹۷٬۶۱۵٬۸۶۹ ۷٬۵۸۱ واحد ممتاز"
        assertEquals(219_106_776L, FundTextScanner.extractValue(synergy, synergyKeywords, "synergy"))
        assertEquals(397_615_869L, FundTextScanner.extractValue(atie, atieKeywords, "atie"))
    }

    @Test
    fun `zero values in page are ignored while numbers load`() {
        // صفحهٔ اولِ پرتفوی که هنوز هیدریت نشده: همه صفر → هیچ عدد معتبری نیست.
        val loading = "دارایی کل 0 ارزش پرتفوی 0 سود و زیان پرتفوی 0 سینرژی 0 همسنگ 0"
        assertEquals(null, FundTextScanner.extractValue(loading, synergyKeywords, "synergy"))
    }

    @Test
    fun `source update date is captured from funds page text`() {
        val text = FundTextScanner.normalize("تاریخ بروز رسانی دارایی 1405/08/25 سایر")
        val m = Regex("(?:تاریخ\\s*بروز\\s*رسانی\\s*دارایی|آخرین\\s*به\\s*روزرسانی)[^0-9]{0,30}(\\d{4}/\\d{1,2}/\\d{1,2})")
            .find(text)?.groupValues?.get(1)
        assertEquals("1405/08/25", m)
        assertTrue(m != null)
    }
}
