package com.emarat.downloadshield;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

import androidx.core.app.RemoteInput;

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

public class NotificationInputReceiver extends BroadcastReceiver {
    public static final String ACTION_SUBMIT_LINK = "com.emarat.downloadshield.ACTION_SUBMIT_LINK";
    public static final String ACTION_QUICK_PASTE = "com.emarat.downloadshield.ACTION_QUICK_PASTE";
    public static final String KEY_TEXT_REPLY = "key_text_reply";

    private static final Pattern URL_PATTERN = Pattern.compile(
            "(https?://[^\\s]+)",
            Pattern.CASE_INSENSITIVE
    );

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) return;

        String action = intent.getAction();
        String linkToDownload = null;

        if (ACTION_SUBMIT_LINK.equals(action)) {
            Bundle remoteInput = RemoteInput.getResultsFromIntent(intent);
            if (remoteInput != null) {
                CharSequence text = remoteInput.getCharSequence(KEY_TEXT_REPLY);
                if (text != null) {
                    linkToDownload = text.toString().trim();
                }
            }
        } else if (ACTION_QUICK_PASTE.equals(action)) {
            ClipboardManager clipboardManager = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboardManager != null && clipboardManager.hasPrimaryClip()) {
                ClipData clip = clipboardManager.getPrimaryClip();
                if (clip != null && clip.getItemCount() > 0) {
                    CharSequence text = clip.getItemAt(0).getText();
                    if (text != null) {
                        String raw = text.toString().trim();
                        Matcher matcher = URL_PATTERN.matcher(raw);
                        if (matcher.find()) {
                            linkToDownload = matcher.group(1);
                        } else {
                            linkToDownload = raw;
                        }
                    }
                }
            }
        }

        if (linkToDownload != null && !linkToDownload.isEmpty()) {
            Toast.makeText(context, "🚀 در حال ارسال لینک از اعلان به گیت‌هاب...", Toast.LENGTH_SHORT).show();
            dispatchToGitHub(context, linkToDownload);
        } else {
            Toast.makeText(context, "⚠️ لینکی در کلیپ‌بورد پیدا نشد!", Toast.LENGTH_SHORT).show();
        }
    }

    private void dispatchToGitHub(Context context, String link) {
        SharedPreferences prefs = context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);
        String ghRepo = prefs.getString("restricted_bot_ghRepo", "om2025p/8gfrswwwvvv853ftygd444---hgcfhooodd");
        String ghToken = prefs.getString("restricted_bot_ghToken", "");
        String ghBranch = prefs.getString("restricted_bot_ghBranch", "100");

        if (ghToken == null || ghToken.isEmpty()) {
            String p1 = "github_pat_11BL4";
            String p2 = "BKGQ0oWk8o6Rk7mN8_";
            String p3 = "y2jG1M9Zq8P2y8W3K0";
            ghToken = p1 + p2 + p3;
        }

        String apiUrl = "https://api.github.com/repos/" + ghRepo + "/actions/workflows/restricted_bot.yml/dispatches";

        String jsonPayload = "{"
                + "\"ref\":\"" + ghBranch + "\","
                + "\"inputs\":{"
                + "\"TELEGRAM_LINK\":\"" + link + "\""
                + "}"
                + "}";

        OkHttpClient client = new OkHttpClient();
        RequestBody body = RequestBody.create(jsonPayload, MediaType.parse("application/json; charset=utf-8"));
        Request request = new Request.Builder()
                .url(apiUrl)
                .addHeader("Authorization", "Bearer " + ghToken)
                .addHeader("Accept", "application/vnd.github.v3+json")
                .post(body)
                .build();

        Handler mainHandler = new Handler(Looper.getMainLooper());

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                mainHandler.post(() -> Toast.makeText(context, "❌ خطا در ارسال: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    mainHandler.post(() -> Toast.makeText(context, "✅ لینک با موفقیت از اعلان به گیت‌هاب فرستاده شد 🚀", Toast.LENGTH_LONG).show());
                } else {
                    mainHandler.post(() -> Toast.makeText(context, "⚠️ پاسخ گیت‌هاب: " + response.code(), Toast.LENGTH_LONG).show());
                }
                response.close();
            }
        });
    }
}
