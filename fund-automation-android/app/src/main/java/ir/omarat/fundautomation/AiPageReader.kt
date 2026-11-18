package ir.omarat.fundautomation

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * لایهٔ هوش مصنوعی (Gemini) — تور نجات استخراج.
 *
 * وقتی هر سه لایهٔ معمولی (شنود API، اسکن متن، پیمایش DOM) شکست بخورند،
 * متن صفحه به Gemini داده می‌شود تا مقدار دارایی هر صندوق را از دل متن
 * بیرون بکشد. این یعنی اگر کارگزاری ظاهر فرم را عوض کند، لازم نیست
 * فوراً اپ را به‌روزرسانی کنیم.
 */
class AiPageReader(private val session: SessionStore) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    /**
     * از متن صفحه، مقدار دارایی یک صندوق را با کمک Gemini استخراج می‌کند.
     * @return مقدار به ریال، یا null اگر پیدا نشد.
     */
    suspend fun extractFundValue(pageText: String, fundKeywords: List<String>): Long? =
        withContext(Dispatchers.IO) {
            val apiKey = session.geminiApiKey
            if (apiKey.isBlank()) return@withContext null

            val prompt = buildPrompt(pageText, fundKeywords)
            val model = MODEL_CHAIN.first()
            val url =
                "https://generativelanguage.googleapis.com/v1beta/models/$model:generateContent?key=$apiKey"

            val body = JSONObject().apply {
                put("contents", JSONArray().put(JSONObject().apply {
                    put("parts", JSONArray().put(JSONObject().apply { put("text", prompt) }))
                }))
                put("generationConfig", JSONObject().apply {
                    put("temperature", 0.0)
                    put("responseMimeType", "application/json")
                })
            }

            try {
                val request = Request.Builder()
                    .url(url)
                    .post(body.toString().toRequestBody("application/json".toMediaType()))
                    .build()
                client.newCall(request).execute().use { resp ->
                    if (!resp.isSuccessful) return@withContext null
                    val text = resp.body?.string() ?: return@withContext null
                    parseValue(text)
                }
            } catch (e: Exception) {
                null
            }
        }

    private fun buildPrompt(pageText: String, keywords: List<String>): String {
        val trimmed = pageText.take(12000)
        return """
        تو یک استخراج‌گر دقیق عدد از صفحات مالی هستی.
        در متن زیر، «مقدار کل دارایی» صندوقی که با این کلیدواژه‌ها مشخص می‌شود را پیدا کن: ${keywords.joinToString(", ")}.
        قواعد:
        - فقط عدد ریالی را برگردان (بدون کاما، بدون واحد).
        - اگر عددی با واحد «همسنگ» یا «تومان» بود، آن را به ریال تبدیل نکن؛ همان عدد ریالی صندوق را بده.
        - اگر مطمئن نیستی، null برگردان.
        خروجی فقط JSON باشد: {"value": <عدد یا null>}

        متن صفحه:
        ---
        $trimmed
        ---
        """.trimIndent()
    }

    private fun parseValue(raw: String): Long? {
        return try {
            val outer = JSONObject(raw)
            val parts = outer.optJSONArray("candidates")
                ?.optJSONObject(0)
                ?.optJSONObject("content")
                ?.optJSONArray("parts")
            val txt = parts?.optJSONObject(0)?.optString("text") ?: return null
            val cleaned = txt.substringAfter("{", "").let { "{$it" }.substringBeforeLast("}")
            val obj = JSONObject("$cleaned}")
            val v = obj.opt("value")
            when (v) {
                null, JSONObject.NULL -> null
                is Number -> v.toLong().takeIf { it > 0 }
                is String -> v.replace(",", "").toLongOrNull()?.takeIf { it > 0 }
                else -> null
            }
        } catch (e: Exception) {
            // آخرین تلاش: بزرگ‌ترین عدد داخل متن
            Regex("\\d[\\d,]{5,}").findAll(raw)
                .mapNotNull { it.value.replace(",", "").toLongOrNull() }
                .maxOrNull()
        }
    }

    companion object {
        /** زنجیرهٔ مدل‌ها؛ اگر اولی بازنشسته شد، بعدی امتحان می‌شود. */
        val MODEL_CHAIN = listOf(
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-flash-latest"
        )
    }
}
