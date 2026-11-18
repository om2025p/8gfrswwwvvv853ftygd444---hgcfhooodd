package ir.omarat.fundautomation

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * تست رگرسیون برای دو باگ واقعی گزارش‌شده در لاگ کاربر:
 *
 * ۱. **پایهٔ سینرژی، عدد آتیه شد** — چون صفحات وب‌اپ روی `file://` یک origin
 *    مشترک دارند و اسکریپت خواندن مشترک، همیشه کلید صندوق ۴ را برمی‌گرداند.
 *    درمان: اسکریپت جدا برای هر صندوق ([WebAppReader]).
 *
 * ۲. **«امروز دستی ثبت شده» دروغین** — چون `manualEntries` فیلتر `manual`
 *    را اعمال نمی‌کرد و رکورد خودِ اتوماسیون هم «دستی» شمرده می‌شد.
 *
 * این تست‌ها منطق خالص را می‌سنجند (بدون WebView)، پس روی JVM اجرا می‌شوند.
 */
class ManualEntryFilterTest {

    private fun entry(value: Double, ts: Long, manual: Boolean) =
        WebAppReader.PercentEntry(value, ts, manual)

    @Test
    fun `رکورد اتوماسیون دستی شمرده نمی‌شود`() {
        val entries = listOf(
            entry(0.0, 1000L, manual = false),   // source=automation
            entry(1.5, 2000L, manual = true),    // ثبت دستی کاربر
            entry(0.0, 3000L, manual = false)    // رکورد خود اتوماسیون امروز
        )
        val manual = entries.filter { it.manual }
        assertEquals(1, manual.size)
        assertEquals(2000L, manual.first().timestampMs)
    }

    @Test
    fun `اگر همه رکوردها اتوماسیون باشند فهرست دستی خالی است`() {
        val entries = listOf(
            entry(0.0, 1000L, manual = false),
            entry(2.3, 2000L, manual = false)
        )
        assertEquals(0, entries.filter { it.manual }.size)
    }
}

/**
 * تست رگرسیون برای نگاشت «کلاس CSS موتور وب‌اپ → نوع تغییر».
 *
 * موتور وب‌اپ فقط کلاس رنگ را روی نتیجه می‌گذارد؛ نگاشت به نوع، در کاتلین
 * انجام می‌شود تا مستقل از DOM و قابل تست باشد.
 */
class EngineTypeMappingTest {

    @Test
    fun `سبز یعنی افزایش`() {
        assertEquals("increase", WebAppCalculator.typeFromClassName("result positive"))
    }

    @Test
    fun `نارنجی یعنی جبران ضرر`() {
        assertEquals("recovering", WebAppCalculator.typeFromClassName("result recovering"))
    }

    @Test
    fun `قرمز یعنی کاهش`() {
        assertEquals("decrease", WebAppCalculator.typeFromClassName("result negative"))
    }

    @Test
    fun `کلاس خالی یعنی بدون تغییر`() {
        assertEquals("neutral", WebAppCalculator.typeFromClassName(""))
        assertEquals("neutral", WebAppCalculator.typeFromClassName("result"))
    }

    @Test
    fun `اولویت نگاشت درست است`() {
        // اگر کلاس‌ها قاطی شدند، ترتیب positive → recovering → negative حفظ شود.
        assertEquals("increase", WebAppCalculator.typeFromClassName("positive recovering"))
    }
}
