package ir.omarat.fundautomation

import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone

/**
 * ادغام دوطرفهٔ فایل‌های بکاپ (gold4/gold5).
 *
 * 🚨 چرا لازم است: نسخهٔ پیشین `BackupManager` فقط `sha` را می‌خواند و فایل
 * گیت‌هاب را با محتوای تازه **کاملاً بازنویسی** می‌کرد. هر اجرای اتوماسیون
 * تاریخچهٔ ۶۰ رکوردی را به یک رکورد می‌رساند. این تابع فایل موجود را با
 * محتوای تازه ترکیب می‌کند و رکوردهای قدیمی را حفظ می‌کند.
 *
 * قواعد:
 *   • `history` و `percents` بر اساس برچسب زمانی (`id`/`timestamp`) ادغام می‌شوند.
 *   • رکوردهای تکراری (اختلاف کمتر از ۲ ثانیه) حذف می‌شوند.
 *   • آرایهٔ `trash` اجتماع دو طرف است (سوابق حذف‌شده نباید برگردند).
 *   • `baseNumber` از **جدیدترین** رکورد گرفته می‌شود، نه از فایل تازه.
 *   • سایر فیلدهای متنی/ساختاری از فایل تازه می‌آیند، مگر خالی باشند.
 */
object BackupMerger {

    /**
     * ادغام محتوای موجود گیت‌هاب با محتوای تازه.
     *
     * @param existingContent محتوای فعلی فایل در گیت‌هاب (ممکن است خالی باشد)
     * @param newContent      محتوای تازه‌ای که اپ ساخته است
     * @return محتوای ادغام‌شده به‌صورت رشتهٔ JSON
     */
    fun merge(existingContent: String, newContent: String): String {
        val existing = parseObject(existingContent)
            ?: return newContent   // فایل قدیمی نامعتبر است → محتوای تازه بی‌تغییر می‌ماند
        val fresh = parseObject(newContent)
            ?: return existingContent

        val merged = JSONObject(fresh.toString())   // پایه: فایل تازه

        merged.put("history", mergeArray(
            existing.optJSONArray("history"),
            fresh.optJSONArray("history")
        ))
        merged.put("percents", mergeArray(
            existing.optJSONArray("percents"),
            fresh.optJSONArray("percents")
        ))
        merged.put("trash", mergeArray(
            existing.optJSONArray("trash"),
            fresh.optJSONArray("trash")
        ))

        // baseNumber = مقدار جدیدِ جدیدترین رکورد تاریخچه
        newestBase(merged.optJSONArray("history"))?.let { merged.put("baseNumber", it) }

        return merged.toString(2)
    }

    /**
     * ادغام دو آرایهٔ JSON بر اساس شناسهٔ یکتا، مرتب بر اساس زمان.
     *
     * رکوردهای **تازه** برنده‌اند: اگر رکوردی با همان شناسه در فایل قدیمی
     * باشد، نسخهٔ تازه جایگزینش می‌شود. رکوردهای قدیمی که در فایل تازه
     * نیستند، دست‌نخورده می‌مانند — این همان «ادغام دوطرفه» است.
     *
     * ⚠️ چرا بر اساس شناسه و نه پنجرهٔ زمانی: دادهٔ واقعی نشان می‌دهد هر
     * رکورد `id` یکتا دارد. پنجرهٔ زمانی (مثلاً ۲ ثانیه) دو اندازه‌گیری
     * واقعیِ نزدیک به هم را بی‌گناه حذف می‌کرد.
     */
    private fun mergeArray(a: JSONArray?, b: JSONArray?): JSONArray {
        val map = LinkedHashMap<String, JSONObject>()

        fun addAll(src: JSONArray?, overwrite: Boolean) {
            if (src == null) return
            for (i in 0 until src.length()) {
                val item = src.optJSONObject(i) ?: continue
                val key = dedupeKey(item)
                if (!overwrite && map.containsKey(key)) continue
                map[key] = item
            }
        }

        addAll(a, overwrite = false)   // رکوردهای قدیمی (فایل گیت‌هاب)
        addAll(b, overwrite = true)    // رکوردهای تازه برنده می‌شوند

        val result = JSONArray()
        map.values.sortedBy { timestampOf(it) }.forEach { result.put(it) }
        return result
    }

    /**
     * شناسهٔ یکتای رکورد.
     *
     * `id` دقیق اگر موجود باشد، وگرنه برچسب زمانی. رکوردهای `percents`
     * معمولاً `id` ندارند و فقط `timestamp` دارند.
     */
    private fun dedupeKey(item: JSONObject): String {
        val idRaw = item.opt("id")
        val idStr = when (idRaw) {
            null, JSONObject.NULL -> ""
            is Number -> idRaw.toLong().toString()
            else -> idRaw.toString().trim()
        }
        if (idStr.isNotBlank()) return "id:$idStr"
        return "ts:${timestampOf(item)}"
    }

    /**
     * استخراج برچسب زمانی از یک رکورد.
     *
     * رکوردها چند فرمت دارند:
     *   • `timestamp` عددی (میلی‌ثانیه) — اپ‌های percent
     *   • `timestamp` رشتهٔ ISO — اپ‌های calculator
     *   • `id` عددی — به‌عنوان جایگزین
     */
    private fun timestampOf(item: JSONObject): Long {
        val raw = item.opt("timestamp") ?: item.opt("id") ?: return 0L
        return when (raw) {
            is Number -> raw.toLong()
            is String -> {
                val asNumber = raw.replace(",", "").trim().toLongOrNull()
                if (asNumber != null) {
                    // ثانیه‌ای را به میلی‌ثانیه تبدیل کن
                    if (asNumber in 1_000_000_000L..99_999_999_999L) asNumber * 1000 else asNumber
                } else parseIso(raw)
            }
            else -> 0L
        }
    }

    private fun parseIso(s: String): Long = try {
        val cleaned = s.trim().replace(" ", "T")
        SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).apply {
            timeZone = TimeZone.getTimeZone("UTC")
        }.parse(cleaned)?.time ?: 0L
    } catch (e: Exception) {
        0L
    }

    /** مقدار عددی «new/rawNew» جدیدترین رکورد تاریخچه. */
    private fun newestBase(history: JSONArray?): Long? {
        if (history == null || history.length() == 0) return null
        val newest = (0 until history.length())
            .map { history.getJSONObject(it) }
            .maxByOrNull { timestampOf(it) } ?: return null
        val rawNew = newest.opt("rawNew")
        if (rawNew is Number) return rawNew.toLong()
        val newStr = newest.optString("new").replace(",", "").replace("٬", "").trim()
        return newStr.toLongOrNull()
    }

    private fun parseObject(s: String): JSONObject? {
        if (s.isBlank()) return null
        return try {
            JSONObject(s)
        } catch (e: Exception) {
            null
        }
    }
}
