package ir.omarat.fundautomation

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * تست موتور ادغام دوطرفه — سناریوی فاجعهٔ واقعی.
 *
 * پیش از این رفع، هر آپلود کل تاریخچهٔ گیت‌هاب را با یک رکورد جایگزین
 * می‌کرد (۶۰ رکورد → ۱ رکورد). این تست تضمین می‌کند رکوردهای قدیمی
 * حفظ شوند و تکراری‌ها فیلتر شوند.
 */
class BackupMergerTest {

    private fun record(id: Long, rawNew: Long, percent: String = "1.00"): JSONObject =
        JSONObject().apply {
            put("id", id)
            put("base", "1,000,000")
            put("new", String.format("%,d", rawNew))
            put("percent", percent)
            put("rawBase", 1000000)
            put("rawNew", rawNew)
            put("timestamp", id)
        }

    private fun backup(records: List<JSONObject>, base: Long): String =
        JSONObject().apply {
            put("baseNumber", base)
            put("history", JSONArray().apply { records.forEach { put(it) } })
            put("percents", JSONArray().apply {
                records.forEach { put(JSONObject().put("value", 1.0).put("timestamp", it.getLong("id"))) }
            })
            put("trash", JSONArray())
        }.toString()

    @Test
    fun `merge does not destroy 60-record history`() {
        val t0 = 1_700_000_000_000L
        val existing = (0 until 60).map { record(t0 + it * 86_400_000L, 1_000_000L + it) }
        val fresh = listOf(record(t0 + 60 * 86_400_000L, 5_000_000L, "14.11"))

        val merged = JSONObject(BackupMerger.merge(backup(existing, 1_059_000L), backup(fresh, 5_000_000L)))
        val history = merged.getJSONArray("history")

        assertEquals("60 old + 1 new = 61", 61, history.length())
        assertEquals("61 percents too", 61, merged.getJSONArray("percents").length())
        assertEquals("baseNumber from newest record", 5_000_000L, merged.getLong("baseNumber"))
    }

    @Test
    fun `duplicate record is not added twice`() {
        val t0 = 1_700_000_000_000L
        val existing = listOf(record(t0, 2_000_000L))
        val fresh = listOf(record(t0, 2_000_000L))

        val merged = JSONObject(BackupMerger.merge(backup(existing, 2_000_000L), backup(fresh, 2_000_000L)))
        assertEquals("duplicate filtered", 1, merged.getJSONArray("history").length())
        assertEquals("percents duplicate filtered too", 1, merged.getJSONArray("percents").length())
    }

    @Test
    fun `two distinct records close in time both survive`() {
        val t0 = 1_700_000_000_000L
        // دو اندازه‌گیری واقعی، فقط ۱.۵ ثانیه فاصله — نباید حذف شوند
        val existing = listOf(record(t0, 2_000_000L))
        val fresh = listOf(record(t0 + 1_500L, 2_500_000L))

        val merged = JSONObject(BackupMerger.merge(backup(existing, 2_000_000L), backup(fresh, 2_500_000L)))
        assertEquals("distinct ids both kept", 2, merged.getJSONArray("history").length())
    }

    @Test
    fun `output is sorted by time`() {
        val t0 = 1_700_000_000_000L
        val existing = listOf(record(t0, 2_000_000L))
        val fresh = listOf(record(t0 - 86_400_000L, 1_500_000L))

        val merged = JSONObject(BackupMerger.merge(backup(existing, 2_000_000L), backup(fresh, 1_500_000L)))
        val history = merged.getJSONArray("history")
        assertEquals(2, history.length())
        assertTrue(
            "older record first",
            history.getJSONObject(0).getLong("id") < history.getJSONObject(1).getLong("id")
        )
    }

    @Test
    fun `ISO string timestamp is preserved`() {
        val iso = JSONObject().apply {
            put("id", 1786649789615L)
            put("timestamp", "2026-08-13T19:36:29.615665Z")
            put("rawNew", 102666552L)
        }
        val existing = JSONObject().apply {
            put("baseNumber", 102666552L)
            put("history", JSONArray().put(iso))
            put("percents", JSONArray())
            put("trash", JSONArray())
        }.toString()
        val fresh = backup(listOf(record(1_700_000_000_000L, 5_000_000L)), 5_000_000L)

        val merged = JSONObject(BackupMerger.merge(existing, fresh))
        assertEquals("ISO record kept", 2, merged.getJSONArray("history").length())
    }

    @Test
    fun `invalid old file does not destroy fresh content`() {
        val fresh = backup(listOf(record(1_700_000_000_000L, 5_000_000L)), 5_000_000L)
        val merged = BackupMerger.merge("{invalid json", fresh)
        assertNotNull(JSONObject(merged))
        assertEquals(1, JSONObject(merged).getJSONArray("history").length())
    }

    @Test
    fun `trash array is union of both sides`() {
        val existing = JSONObject().apply {
            put("baseNumber", 1L)
            put("history", JSONArray())
            put("percents", JSONArray())
            put("trash", JSONArray().put(JSONObject().put("id", 111L).put("timestamp", 111L)))
        }.toString()
        val fresh = JSONObject().apply {
            put("baseNumber", 2L)
            put("history", JSONArray())
            put("percents", JSONArray())
            put("trash", JSONArray().put(JSONObject().put("id", 222L).put("timestamp", 222L)))
        }.toString()

        val merged = JSONObject(BackupMerger.merge(existing, fresh))
        assertEquals("both trashed records kept", 2, merged.getJSONArray("trash").length())
    }

    @Test
    fun `second-based timestamp converted to millis`() {
        val seconds = 1_700_000_000L
        val existing = JSONObject().apply {
            put("baseNumber", 1L)
            put("history", JSONArray().put(
                JSONObject().put("id", seconds).put("timestamp", seconds).put("rawNew", 100L)
            ))
            put("percents", JSONArray())
            put("trash", JSONArray())
        }.toString()
        val fresh = JSONObject().apply {
            put("baseNumber", 2L)
            put("history", JSONArray().put(
                JSONObject().put("id", seconds * 1000 + 86_400_000L)
                    .put("timestamp", seconds * 1000 + 86_400_000L).put("rawNew", 200L)
            ))
            put("percents", JSONArray())
            put("trash", JSONArray())
        }.toString()

        val merged = JSONObject(BackupMerger.merge(existing, fresh))
        assertEquals("two records one day apart both kept", 2, merged.getJSONArray("history").length())
    }
}
