package ir.omarat.fundautomation

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * پشتیبان‌گیری و بازیابی **داخل خود اپ** — مستقل از گیت‌هاب.
 *
 * هر بکاپ یک فایل JSON در پوشهٔ خصوصی اپ است و می‌تواند با «اشتراک‌گذاری»
 * به هر جایی (درایو، تلگرام، ایمیل) فرستاده شود. پیش از هر بازیابی، از
 * اطلاعات فعلی یک نسخهٔ ایمنی گرفته می‌شود تا اشتباه جبران‌پذیر باشد.
 */
class LocalBackupManager(private val context: Context) {

    private val dir: File get() = File(context.filesDir, "backups").apply { mkdirs() }

    data class BackupFile(val file: File, val label: String)

    /** فهرست بکاپ‌های موجود، تازه‌ترین اول. */
    fun list(): List<BackupFile> =
        (dir.listFiles { f -> f.name.endsWith(".json") } ?: emptyArray())
            .sortedByDescending { it.lastModified() }
            .map { BackupFile(it, prettyLabel(it)) }

    /**
     * ذخیرهٔ یک بکاپ از کلیدهای حافظهٔ وب‌اپ.
     *
     * @param source `"manual"` (دکمهٔ کاربر) یا `"auto"` (پیش از بازیابی).
     */
    fun save(snapshotJson: String, source: String = "manual"): File {
        val stamp = SimpleDateFormat("yyyyMMdd-HHmmss", Locale.US).format(Date())
        val name = "fund-backup-$stamp-$source.json"
        val f = File(dir, name)
        f.writeText(snapshotJson, Charsets.UTF_8)
        return f
    }

    /** خواندن محتوای یک بکاپ. */
    fun read(file: File): String = file.readText(Charsets.UTF_8)

    /**
     * حذف بکاپ‌های قدیمی و نگه‌داشتن [keep] تای جدید.
     */
    fun prune(keep: Int = 20) {
        val all = (dir.listFiles { f -> f.name.endsWith(".json") } ?: emptyArray())
            .sortedByDescending { it.lastModified() }
        all.drop(keep).forEach { it.delete() }
    }

    /** Intent اشتراک‌گذاری یک فایل بکاپ (تلگرام، درایو، ایمیل…). */
    fun shareIntent(file: File): Intent {
        val uri: Uri = FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
        return Intent(Intent.ACTION_SEND).apply {
            type = "application/json"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
    }

    /** ساخت اسنپ‌شات JSON از فهرست کلید/مقدار خوانده‌شده از حافظهٔ وب‌اپ. */
    fun buildSnapshot(pairs: Map<String, String>): String {
        val obj = JSONObject()
        obj.put("app", "fund-automation")
        obj.put("version", 1)
        obj.put("createdAt", System.currentTimeMillis())
        obj.put("jalaliDate", JalaliDate.format(System.currentTimeMillis()))
        val data = JSONObject()
        for ((k, v) in pairs) data.put(k, v)
        obj.put("data", data)
        return obj.toString(2)
    }

    /**
     * استخراج جفت‌های کلید/مقدار از یک فایل بکاپ.
     *
     * هم قالب خودِ اپ (`{data:{...}}`) و هم قالب خام بکاپ وب‌اپ‌ها
     * (`{baseNumber:..., history:[...]}`) پذیرفته می‌شود تا بکاپ‌های قدیمی
     * گیت‌هاب هم قابل بازیابی باشند.
     */
    fun parseSnapshot(json: String): Map<String, String>? {
        return try {
            val obj = JSONObject(json)
            val out = LinkedHashMap<String, String>()
            val data = obj.optJSONObject("data")
            if (data != null) {
                for (k in data.keys()) out[k] = data.getString(k)
                return out
            }
            // قالب خام وب‌اپ: همهٔ مقادیر را به رشته تبدیل کن
            for (k in obj.keys()) {
                val v = obj.get(k)
                out[k] = when (v) {
                    is JSONArray, is JSONObject -> v.toString()
                    else -> v.toString()
                }
            }
            if (out.isEmpty()) null else out
        } catch (e: Exception) {
            null
        }
    }

    private fun prettyLabel(f: File): String {
        val parts = f.nameWithoutExtension.split("-")
        val stamp = parts.getOrNull(2) ?: ""
        val source = if (f.name.contains("-auto")) "پیش از بازیابی" else "دستی"
        val pretty = if (stamp.length == 15) {
            "${stamp.substring(0, 4)}/${stamp.substring(4, 6)}/${stamp.substring(6, 8)} " +
                "${stamp.substring(9, 11)}:${stamp.substring(11, 13)}"
        } else stamp
        return "$pretty · $source · ${f.length() / 1024} KB"
    }
}
