package ir.omarat.fundautomation

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * تست ادغام روی **دادهٔ واقعی مخزن**.
 *
 * فایل‌های `gold4/gold4_backup.json` و `gold5/gold5_backup.json` رکوردهای
 * واقعی کاربر را دارند. این تست ثابت می‌کند آپلود تازه (که فقط یک رکورد
 * دارد) هیچ‌کدام از آن‌ها را نابود نمی‌کند — همان فاجعه‌ای که یک‌بار رخ داد.
 */
class BackupMergerRealDataTest {

    private fun repoFile(path: String): File? {
        // پوشهٔ اجرای تست، پوشهٔ ماژول (app/) است
        val candidates = listOf(
            File("../$path"),
            File("../../$path"),
            File(System.getProperty("user.dir"), "../$path")
        )
        return candidates.firstOrNull { it.exists() }
    }

    private fun assertMergeKeepsEverything(path: String) {
        val file = repoFile(path)
        if (file == null) {
            println("⚠️ فایل $path پیدا نشد؛ تست رد شد.")
            return
        }
        val existing = file.readText()
        val existingJson = JSONObject(existing)
        val beforeCount = existingJson.getJSONArray("history").length()
        assertTrue("فایل واقعی باید رکورد داشته باشد", beforeCount > 0)

        // payload تازه با یک رکورد کاملاً جدید (زمانی در آینده)
        val freshTs = System.currentTimeMillis() + 3_600_000
        val fresh = JSONObject().apply {
            put("baseNumber", 999_999_999L)
            put("history", JSONArray().put(
                JSONObject().put("id", freshTs).put("timestamp", freshTs)
                    .put("rawBase", 999_000_000L).put("rawNew", 999_999_999L)
                    .put("percent", "0.10")
            ))
            put("percents", JSONArray().put(
                JSONObject().put("value", 0.10).put("timestamp", freshTs)
            ))
            put("trash", JSONArray())
        }.toString()

        val merged = JSONObject(BackupMerger.merge(existing, fresh))
        val after = merged.getJSONArray("history").length()

        assertEquals("$path : هیچ رکورد قدیمی نباید از دست برود", beforeCount + 1, after)
        assertEquals(
            "$path : baseNumber باید مقدار جدیدترین رکورد باشد",
            999_999_999L, merged.getLong("baseNumber")
        )
        println("✅ $path : $beforeCount → $after رکورد (هیچ داده‌ای از دست نرفت)")
    }

    @Test
    fun `gold5 real backup survives a fresh upload`() {
        assertMergeKeepsEverything("gold5/gold5_backup.json")
    }

    @Test
    fun `gold4 real backup survives a fresh upload`() {
        assertMergeKeepsEverything("gold4/gold4_backup.json")
    }

    @Test
    fun `merging the same file with itself changes nothing`() {
        val file = repoFile("gold5/gold5_backup.json") ?: return
        val content = file.readText()
        val before = JSONObject(content).getJSONArray("history").length()
        val merged = JSONObject(BackupMerger.merge(content, content))
        assertEquals("ادغام فایل با خودش نباید رکورد اضافه کند", before, merged.getJSONArray("history").length())
    }
}
