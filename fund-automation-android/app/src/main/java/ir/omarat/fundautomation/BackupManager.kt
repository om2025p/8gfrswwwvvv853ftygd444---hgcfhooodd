package ir.omarat.fundautomation

import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * نتیجهٔ یک تلاش آپلود.
 */
data class UploadResult(val success: Boolean, val message: String)

/**
 * پشتیبان‌گیری دوگانه: فایل JSON محلی + آپلود مستقیم به گیت‌هاب با API.
 *
 * این مسیر به GitHub Actions نیازی ندارد؛ فقط یک توکن و نام مخزن کافی است.
 * توکن از [SessionStore] خوانده می‌شود و هرگز در کد یا گزارش نوشته نمی‌شود.
 */
class BackupManager(private val session: SessionStore) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    /**
     * آپلود یا به‌روزرسانی یک فایل در مخزن گیت‌هاب.
     *
     * اگر فایل از قبل وجود داشته باشد، SHA فعلی خوانده و به‌عنوان نسخهٔ
     * قبلی ارسال می‌شود تا گیت‌هاب آن را به‌عنوان «به‌روزرسانی» بپذیرد.
     */
    suspend fun uploadToGitHub(
        contentString: String,
        filePath: String,
        commitMessage: String
    ): UploadResult = withContext(Dispatchers.IO) {
        val token = session.githubToken
        val repo = session.githubRepo
        val branch = session.githubBranch.ifBlank { "main" }

        if (token.isBlank() || repo.isBlank()) {
            return@withContext UploadResult(false, "تنظیمات گیت‌هاب کامل نیست.")
        }

        val url = "https://api.github.com/repos/$repo/contents/$filePath"

        try {
            val existing = fetchExistingFile(url, branch, token)
            val sha = existing?.first

            // ── ادغام دوطرفه: فایل موجود را با محتوای تازه ترکیب می‌کنیم ────
            // بدون این کار، هر آپلود کل تاریخچهٔ گیت‌هاب را با یک رکورد
            // جایگزین می‌کرد و سوابق ارزشمند کاربر نابود می‌شد.
            val mergedContent = if (existing != null) {
                BackupMerger.merge(existing.second, contentString)
            } else contentString

            val base64Content = Base64.encodeToString(
                mergedContent.toByteArray(Charsets.UTF_8),
                Base64.NO_WRAP
            )
            val body = JSONObject().apply {
                put("message", commitMessage)
                put("content", base64Content)
                put("branch", branch)
                if (sha != null) put("sha", sha)
            }

            val request = Request.Builder()
                .url(url)
                .header("Authorization", "token $token")
                .header("Accept", "application/vnd.github.v3+json")
                .put(body.toString().toRequestBody("application/json".toMediaType()))
                .build()

            client.newCall(request).execute().use { resp ->
                if (resp.isSuccessful) UploadResult(true, "آپلود موفق")
                else UploadResult(false, "خطای گیت‌هاب: ${resp.code}")
            }
        } catch (e: Exception) {
            UploadResult(false, e.message ?: "خطای نامشخص")
        }
    }

    /**
     * خواندن SHA و **محتوای** فایل موجود.
     *
     * نسخهٔ پیشین فقط SHA را می‌خواند؛ نتیجه این بود که فایل گیت‌هاب به‌طور
     * کامل بازنویسی می‌شد و تاریخچه از دست می‌رفت.
     *
     * @return جفت `(sha, محتوای متنی)` یا `null` اگر فایل نبود.
     */
    private fun fetchExistingFile(url: String, branch: String, token: String): Pair<String, String>? {
        return try {
            val request = Request.Builder()
                .url("$url?ref=$branch")
                .header("Authorization", "token $token")
                .header("Accept", "application/vnd.github.v3+json")
                .get()
                .build()
            client.newCall(request).execute().use { resp ->
                if (resp.code != 200) return null
                val json = JSONObject(resp.body?.string() ?: "{}")
                val sha = json.optString("sha").ifBlank { return null }
                val b64 = json.optString("content").replace("\n", "").replace("\r", "")
                if (b64.isBlank()) return sha to ""
                val decoded = String(Base64.decode(b64, Base64.DEFAULT), Charsets.UTF_8)
                sha to decoded
            }
        } catch (e: Exception) {
            null
        }
    }
}
