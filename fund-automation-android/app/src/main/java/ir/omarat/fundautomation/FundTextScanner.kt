package ir.omarat.fundautomation

/**
 * اسکن متن صفحه و استخراج مقدار دارایی یک صندوق.
 *
 * این منطق **خالص** است (بدون WebView و Android) تا مستقیماً در تست JVM
 * سنجیده شود. الگوها عیناً از کد قدیمی پایتون (`easytrader_automation.py`)
 * گرفته شده‌اند که با همین روش مقادیر را درست می‌خواند.
 */
object FundTextScanner {

    /** کمترین مقدار معتبر دارایی (ریال). */
    const val MIN_ASSET_VALUE = 1_000_000L

    /** پنجرهٔ کاراکتری اسکن بعد از کلیدواژه. */
    const val WINDOW_CHARS = 320

    /**
     * تبدیل ارقام فارسی/عربی به انگلیسی و یکسان‌سازی جداکنندهٔ هزارگان.
     *
     * ⚠️ باگ بحرانی نسخهٔ پیشین: فقط ارقام تبدیل می‌شد، ولی جداکنندهٔ هزارگان
     * فارسی `٬` (U+066C) به کامای انگلیسی تبدیل نمی‌شد. پس «۲۲۰٬۳۵۱٬۲۶۰»
     * به «220٬351٬260» تبدیل می‌شد و regex `[\d,]{6,}` هیچ عددی پیدا نمی‌کرد.
     */
    fun normalize(input: String): String {
        val digits = mapOf(
            '۰' to '0', '۱' to '1', '۲' to '2', '۳' to '3', '۴' to '4',
            '۵' to '5', '۶' to '6', '۷' to '7', '۸' to '8', '۹' to '9',
            '٠' to '0', '١' to '1', '٢' to '2', '٣' to '3', '٤' to '4',
            '٥' to '5', '٦' to '6', '٧' to '7', '٨' to '8', '٩' to '9'
        )
        val sb = StringBuilder(input.length)
        for (c in input) {
            when {
                digits.containsKey(c) -> sb.append(digits[c])
                c == '٬' || c == '،' -> sb.append(',')
                c == '\u00A0' || c == '\u200C' || c == '\u200F' -> {}
                else -> sb.append(c)
            }
        }
        return sb.toString()
    }

    /**
     * استخراج مقدار یک صندوق از متن صفحه.
     *
     * @param fund `"synergy"` یا `"atie"` — الگوی اختصاصی هرکدام.
     * @return مقدار به ریال، یا `null`.
     */
    fun extractValue(rawText: String, keywords: List<String>, fund: String): Long? {
        val text = normalize(rawText)
        for (keyword in keywords) {
            var from = text.indexOf(keyword)
            while (from >= 0) {
                val best = when (fund) {
                    "synergy" -> synergyWindow(text, from + keyword.length)
                    "atie" -> atieWindow(text, from + keyword.length)
                    else -> genericWindow(text, from + keyword.length)
                }
                best?.let { return it }
                from = text.indexOf(keyword, from + keyword.length)
            }
        }
        return null
    }

    /**
     * الگوی سینرژی روی پرتفوی: بزرگ‌ترین عدد ۶رقمی+ پس از نام نماد، تا
     * رسیدن به نماد بعدی («همسنگ»). «ارزش فعلی» بزرگ‌ترین عدد پنجره است.
     */
    fun synergyWindow(text: String, startIndex: Int): Long? {
        val window = safeWindow(text, startIndex)
        val end = window.indexOf("همسنگ").takeIf { it >= 0 } ?: window.length
        return largestNumber(window.substring(0, end))
    }

    /**
     * الگوی آتیه روی «صندوق‌های مفید»: بزرگ‌ترین عدد ۶رقمی+ پس از «آتیه» تا
     * صندوق بعدی («ممتاز»/«امید توسعه»). دارایی از تعداد واحد بزرگ‌تر است.
     */
    fun atieWindow(text: String, startIndex: Int): Long? {
        val window = safeWindow(text, startIndex)
        val end = listOf(window.indexOf("ممتاز"), window.indexOf("امید توسعه"))
            .filter { it >= 0 }.minOrNull() ?: window.length
        return largestNumber(window.substring(0, end))
    }

    /** الگوی عمومی: پنجرهٔ پس از کلیدواژه تا نشانهٔ پایان. */
    fun genericWindow(text: String, startIndex: Int): Long? {
        val window = safeWindow(text, startIndex)
        val end = listOf("همسنگ", "تومان", "کارگزاری")
            .map { window.indexOf(it) }.filter { it >= 0 }.minOrNull() ?: window.length
        return largestNumber(window.substring(0, end))
    }

    private fun safeWindow(text: String, startIndex: Int): String {
        if (startIndex >= text.length) return ""
        return text.substring(startIndex, minOf(startIndex + WINDOW_CHARS, text.length))
    }

    /** بزرگ‌ترین عدد ۶رقمی+ در یک قطعه (با حذف جداکننده‌ها). */
    fun largestNumber(segment: String): Long? =
        Regex("[\\d,]{6,}").findAll(segment)
            .mapNotNull { it.value.replace(",", "").toLongOrNull() }
            .filter { it >= MIN_ASSET_VALUE }
            .maxOrNull()
}
