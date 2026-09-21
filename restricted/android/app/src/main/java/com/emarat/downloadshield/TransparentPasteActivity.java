package com.emarat.downloadshield;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.Toast;

import java.io.IOException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class TransparentPasteActivity extends Activity {
    private static final String TAG = "TransparentPasteAct";
    private static final Pattern URL_PATTERN = Pattern.compile(
            "(https?://[^\\s]+)",
            Pattern.CASE_INSENSITIVE
    );

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        String freshLink = getFreshClipboardUrl();

        if (freshLink != null && !freshLink.isEmpty()) {
            Toast.makeText(this, "🚀 چسباندن زنده و ارسال به گیت‌هاب:\n" + freshLink, Toast.LENGTH_LONG).show();

            ClipboardService.lastCopiedUrl = freshLink;
            NotificationInputReceiver.registerNativeUniqueLink(this, freshLink);
            NotificationInputReceiver.saveNativeDownloadHistory(this, freshLink, "⚡ چسباندن زنده از اعلان");
            dispatchToGitHub(freshLink);
        } else {
            Toast.makeText(this, "⚠️ کلیپ‌بورد خالی است یا لینک معتبری یافت نشد!", Toast.LENGTH_SHORT).show();
        }

        ClipboardService.refreshNotification(this);
        finish();
    }

    private String getFreshClipboardUrl() {
        ClipboardManager clipboardManager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboardManager == null) {
            Log.w(TAG, "ClipboardManager is null");
            return null;
        }

        boolean hasClip = clipboardManager.hasPrimaryClip();
        if (!hasClip) {
            String serviceCache = ClipboardService.lastCopiedUrl;
            if (!serviceCache.isEmpty()) return serviceCache;
            return null;
        }

        try {
            ClipData clip = clipboardManager.getPrimaryClip();
            if (clip != null && clip.getItemCount() > 0) {
                CharSequence textChar = clip.getItemAt(0).getText();
                if (textChar != null) {
                    String raw = textChar.toString().trim();
                    Matcher matcher = URL_PATTERN.matcher(raw);
                    if (matcher.find()) {
                        return matcher.group(1);
                    } else if (raw.startsWith("http://") || raw.startsWith("https://")) {
                        return raw;
                    }
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error reading clipboard: " + e.getMessage());
        }
        return null;
    }

    private void dispatchToGitHub(String link) {
        SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
        final String fullRepo = NotificationInputReceiver.getFullRepoPath(prefs);

        String rawToken = prefs.getString("restricted_bot_ghToken", "");
        if (rawToken == null || rawToken.trim().isEmpty()) {
            rawToken = prefs.getString("restricted_bot_ghPat", "");
        }
        String rawBranch = prefs.getString("restricted_bot_ghBranch", "100");

        final String ghToken = rawToken != null ? rawToken.trim() : "";
        final String ghBranch = rawBranch != null ? rawBranch.trim() : "100";

        if (ghToken.isEmpty()) {
            Toast.makeText(this, "⚠️ توکن گیت‌هاب خالی است! ابتدا تنظیمات را پر کنید.", Toast.LENGTH_LONG).show();
            return;
        }

        String tgApiId = prefs.getString("restricted_bot_tgApiId", "").trim();
        String tgApiHash = prefs.getString("restricted_bot_tgApiHash", "").trim();
        String tgBotToken = prefs.getString("restricted_bot_tgBotToken", "").trim();
        String tgSession = prefs.getString("restricted_bot_tgSession", "").trim();
        String tgOwner = prefs.getString("restricted_bot_tgOwner", "").trim();

        String apiUrl = "https://api.github.com/repos/" + fullRepo + "/actions/workflows/restricted_bot.yml/dispatches";

        try {
            org.json.JSONObject inputs = new org.json.JSONObject();
            inputs.put("TELEGRAM_LINK", link);
            inputs.put("API_ID", tgApiId);
            inputs.put("API_HASH", tgApiHash);
            inputs.put("BOT_TOKEN", tgBotToken);
            inputs.put("SESSION_STRING", tgSession);
            inputs.put("OWNER_ID", tgOwner);

            org.json.JSONObject payload = new org.json.JSONObject();
            payload.put("ref", ghBranch);
            payload.put("inputs", inputs);

            OkHttpClient client = new OkHttpClient();
            RequestBody body = RequestBody.create(payload.toString(), MediaType.parse("application/json; charset=utf-8"));

            Request request = new Request.Builder()
                    .url(apiUrl)
                    .addHeader("Authorization", "Bearer " + ghToken)
                    .addHeader("Accept", "application/vnd.github.v3+json")
                    .post(body)
                    .build();

            Context appContext = getApplicationContext();
            Handler mainHandler = new Handler(Looper.getMainLooper());

            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    mainHandler.post(() -> Toast.makeText(appContext, "❌ خطا در ارسال: " + e.getMessage(), Toast.LENGTH_LONG).show());
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    int code = response.code();
                    if (response.isSuccessful() || code == 204) {
                        mainHandler.post(() -> Toast.makeText(appContext, "✅ دانلود با موفقیت به گیت‌هاب فرستاده شد 🚀", Toast.LENGTH_LONG).show());
                    } else if (code == 404) {
                        mainHandler.post(() -> Toast.makeText(appContext, "❌ خطا ۴۰۴: مخزن یا ورک‌فلو یافت نشد!", Toast.LENGTH_LONG).show());
                    } else {
                        mainHandler.post(() -> Toast.makeText(appContext, "⚠️ پاسخ گیت‌هاب (" + code + "): تنظیمات مخزن را چک کنید", Toast.LENGTH_LONG).show());
                    }
                    response.close();
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "Error dispatching to GitHub: " + e.getMessage());
        }
    }
}
