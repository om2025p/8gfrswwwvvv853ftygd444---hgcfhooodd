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
            val sha = fetchExistingSha(url, branch, token)
            val base64Content = Base64.encodeToString(
                contentString.toByteArray(Charsets.UTF_8),
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

    private fun fetchExistingSha(url: String, branch: String, token: String): String? {
        return try {
            val request = Request.Builder()
                .url("$url?ref=$branch")
                .header("Authorization", "token $token")
                .header("Accept", "application/vnd.github.v3+json")
                .get()
                .build()
            client.newCall(request).execute().use { resp ->
                if (resp.code == 200) {
                    JSONObject(resp.body?.string() ?: "{}").optString("sha").ifBlank { null }
                } else null
            }
        } catch (e: Exception) {
            null
        }
    }
}
