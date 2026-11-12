package com.emarat.downloadshield;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONObject;

import java.io.IOException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * ارسال لینک به موتور دانلود.
 *
 * مسیر اصلی: سرور اختصاصی (Railway) که کلاینت تلگرام را زنده نگه می‌دارد و در چند ثانیه دانلود می‌کند.
 * مسیر پشتیبان: اجرای ورک‌فلو گیت‌هاب؛ فقط زمانی استفاده می‌شود که سرور تنظیم نشده باشد
 * یا پاسخ ندهد. این پشتیبان عمداً حفظ شده تا قطعی سرور باعث از کار افتادن کامل اپ نشود.
 */
public class DownloadDispatcher {

    private static final String TAG = "DownloadDispatcher";
    private static final String DEFAULT_TARGET_CHANNEL = "-1003757877147";
    private static final String GITHUB_WORKFLOW = "restricted_bot.yml";

    private static final OkHttpClient client = new OkHttpClient();

    public interface Callback2 {
        /** via یکی از "server" یا "github" است تا بتوان در تاریخچه نشان داد. */
        void onSuccess(String via);

        void onFailure(String message, String detail);
    }

    public static void dispatch(final Context context, final String link, final Callback2 cb) {
        final SharedPreferences prefs =
                context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);

        final String srvUrl = safe(prefs.getString("restricted_bot_srvUrl", "")).replaceAll("/+$", "");
        final String srvToken = safe(prefs.getString("restricted_bot_srvToken", ""));

        if (!srvUrl.isEmpty() && !srvToken.isEmpty()) {
            dispatchToServer(context, prefs, srvUrl, srvToken, link, cb);
            return;
        }

        Log.i(TAG, "سرور تنظیم نشده؛ استفاده از مسیر پشتیبان گیت‌هاب");
        dispatchToGitHub(context, prefs, link, cb, "تنظیمات سرور کامل نیست");
    }

    private static void dispatchToServer(final Context context, final SharedPreferences prefs,
                                         final String srvUrl, final String srvToken,
                                         final String link, final Callback2 cb) {
        JSONObject payload = new JSONObject();
        try {
            payload.put("url", link);
            payload.put("targetChannel", DEFAULT_TARGET_CHANNEL);
        } catch (Exception ignored) {}

        RequestBody body = RequestBody.create(
                payload.toString(), MediaType.parse("application/json; charset=utf-8"));

        Request request = new Request.Builder()
                .url(srvUrl + "/api/download")
                .addHeader("X-Auth-Token", srvToken)
                .post(body)
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                Log.w(TAG, "سرور در دسترس نیست: " + e.getMessage());
                dispatchToGitHub(context, prefs, link, cb, "سرور پاسخ نداد: " + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                final int code = response.code();
                String errBody = "";
                try {
                    if (response.body() != null) errBody = response.body().string();
                } catch (Exception ignored) {}
                response.close();

                if (code == 200) {
                    cb.onSuccess("server");
                    return;
                }

                // 401 یعنی توکن سرور غلط است؛ این خطای پیکربندی است و با گیت‌هاب پوشانده نمی‌شود
                // تا کاربر متوجه اشتباه بودن توکن شود.
                if (code == 401) {
                    cb.onFailure("توکن سرور نادرست است", errBody);
                    return;
                }

                dispatchToGitHub(context, prefs, link, cb,
                        "سرور کد " + code + " برگرداند" + (errBody.isEmpty() ? "" : ": " + errBody));
            }
        });
    }

    private static void dispatchToGitHub(final Context context, final SharedPreferences prefs,
                                         final String link, final Callback2 cb,
                                         final String reason) {
        final String fullRepo = NotificationInputReceiver.getFullRepoPath(prefs);

        String rawToken = safe(prefs.getString("restricted_bot_ghToken", ""));
        if (rawToken.isEmpty()) rawToken = safe(prefs.getString("restricted_bot_ghPat", ""));
        final String ghToken = rawToken;
        final String ghBranch = safe(prefs.getString("restricted_bot_ghBranch", "100"));

        if (ghToken.isEmpty()) {
            cb.onFailure("نه سرور و نه گیت‌هاب تنظیم نشده است",
                    reason + " — و توکن گیت‌هاب هم خالی است.");
            return;
        }

        JSONObject inputs = new JSONObject();
        try {
            inputs.put("TELEGRAM_LINK", link);
            inputs.put("TARGET_CHANNEL", DEFAULT_TARGET_CHANNEL);
            inputs.put("API_ID", safe(prefs.getString("restricted_bot_tgApiId", "")));
            inputs.put("API_HASH", safe(prefs.getString("restricted_bot_tgApiHash", "")));
            inputs.put("BOT_TOKEN", safe(prefs.getString("restricted_bot_tgBotToken", "")));
            inputs.put("SESSION_STRING", safe(prefs.getString("restricted_bot_tgSession", "")));
            inputs.put("OWNER_ID", safe(prefs.getString("restricted_bot_tgOwner", "")));
        } catch (Exception ignored) {}

        JSONObject payload = new JSONObject();
        try {
            payload.put("ref", ghBranch);
            payload.put("inputs", inputs);
        } catch (Exception ignored) {}

        RequestBody body = RequestBody.create(
                payload.toString(), MediaType.parse("application/json; charset=utf-8"));

        Request request = new Request.Builder()
                .url("https://api.github.com/repos/" + fullRepo + "/actions/workflows/"
                        + GITHUB_WORKFLOW + "/dispatches")
                .addHeader("Authorization", "Bearer " + ghToken)
                .addHeader("Accept", "application/vnd.github.v3+json")
                .post(body)
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                cb.onFailure("خطای اتصال به گیت‌هاب", reason + " | " + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                final int code = response.code();
                response.close();
                if (code == 204 || code == 200 || code == 201) {
                    cb.onSuccess("github");
                } else if (code == 404) {
                    cb.onFailure("مخزن یا ورک‌فلو یافت نشد (۴۰۴)", reason + " | repo=" + fullRepo);
                } else if (code == 401) {
                    cb.onFailure("توکن گیت‌هاب معتبر نیست (۴۰۱)", reason);
                } else {
                    cb.onFailure("پاسخ گیت‌هاب کد " + code, reason);
                }
            }
        });
    }

    private static String safe(String s) {
        return s == null ? "" : s.trim();
    }
}
