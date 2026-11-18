package ir.omarat.fundautomation

import android.content.Context
import android.content.SharedPreferences
import android.util.Base64
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.security.SecureRandom

/**
 * نگهداری امن رمز عبور، کد OTP و کوکی نشست کارگزاری.
 *
 * رمزها با کلید سخت‌افزاری Android Keystore رمزنگاری می‌شوند؛ هیچ‌گاه
 * در گزارش‌ها یا بکاپ‌ها نوشته نمی‌شوند.
 */
class SessionStore(context: Context) {

    private val prefs: SharedPreferences by lazy {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    var username: String
        get() = prefs.getString(KEY_USER, "") ?: ""
        set(v) = prefs.edit().putString(KEY_USER, v).apply()

    var password: String
        get() = prefs.getString(KEY_PASS, "") ?: ""
        set(v) = prefs.edit().putString(KEY_PASS, v).apply()

    var geminiApiKey: String
        get() = prefs.getString(KEY_GEMINI, "") ?: ""
        set(v) = prefs.edit().putString(KEY_GEMINI, v).apply()

    var githubToken: String
        get() = prefs.getString(KEY_GH_TOKEN, "") ?: ""
        set(v) = prefs.edit().putString(KEY_GH_TOKEN, v).apply()

    var githubRepo: String
        get() = prefs.getString(KEY_GH_REPO, "") ?: ""
        set(v) = prefs.edit().putString(KEY_GH_REPO, v).apply()

    var githubBranch: String
        get() = prefs.getString(KEY_GH_BRANCH, "main") ?: "main"
        set(v) = prefs.edit().putString(KEY_GH_BRANCH, v).apply()

    /** نشست فعال است؟ */
    val hasCredentials: Boolean get() = username.isNotBlank() && password.isNotBlank()

    /**
     * شناسهٔ دستگاهی که به کارگزاری معرفی می‌شود (برای «تیک دستگاه مورد اعتماد»).
     * یک‌بار ساخته و برای همیشه ثابت می‌ماند.
     */
    val deviceId: String
        get() {
            prefs.getString(KEY_DEVICE_ID, null)?.let { return it }
            val bytes = ByteArray(16)
            SecureRandom().nextBytes(bytes)
            val id = Base64.encodeToString(bytes, Base64.NO_WRAP or Base64.URL_SAFE)
            prefs.edit().putString(KEY_DEVICE_ID, id).apply()
            return id
        }

    /** پاک کردن کامل اطلاعات حساس (خروج اضطراری). */
    fun clearAll() = prefs.edit().clear().apply()

    companion object {
        private const val PREFS_NAME = "omarat_fund_automation_prefs"
        private const val KEY_USER = "session_username"
        private const val KEY_PASS = "session_password"
        private const val KEY_GEMINI = "gemini_api_key"
        private const val KEY_GH_TOKEN = "github_backup_token"
        private const val KEY_GH_REPO = "github_backup_repo"
        private const val KEY_GH_BRANCH = "github_backup_branch"
        private const val KEY_DEVICE_ID = "session_device_id"
    }
}
