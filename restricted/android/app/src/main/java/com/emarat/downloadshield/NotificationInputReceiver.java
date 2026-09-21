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
            // Launch MainActivity into foreground to gain window focus for reading Clipboard safely on Android 10+
            Intent openIntent = new Intent(context, MainActivity.class);
            openIntent.setAction(ACTION_QUICK_PASTE);
            openIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            context.startActivity(openIntent);
            return;
        }

        if (linkToDownload != null && !linkToDownload.isEmpty()) {
            Toast.makeText(context, "🚀 در حال ارسال آنی به گیت‌هاب...", Toast.LENGTH_SHORT).show();
            dispatchToGitHub(context, linkToDownload);
        } else if (ACTION_SUBMIT_LINK.equals(action)) {
            Toast.makeText(context, "⚠️ متن ورودی خالی است!", Toast.LENGTH_SHORT).show();
        }
    }

    public static String getFullRepoPath(SharedPreferences prefs) {
        String ghOwner = prefs.getString("restricted_bot_ghOwner", "").trim();
        String ghRepo = prefs.getString("restricted_bot_ghRepo", "").trim();

        ghRepo = ghRepo.replace("https://github.com/", "")
                       .replace("http://github.com/", "")
                       .replaceAll("\\.git$", "")
                       .replaceAll("^/+", "")
                       .replaceAll("/+$", "");

        ghOwner = ghOwner.replace("https://github.com/", "")
                        .replaceAll("^/+", "")
                        .replaceAll("/+$", "");

        if (ghRepo.contains("/")) {
            return ghRepo;
        }

        if (!ghOwner.isEmpty() && !ghRepo.isEmpty()) {
            return ghOwner + "/" + ghRepo;
        }

        if (!ghRepo.isEmpty()) {
            return "om2025p/" + ghRepo;
        }

        return "om2025p/8gfrswwwvvv853ftygd444---hgcfhooodd";
    }

    private void dispatchToGitHub(Context context, String link) {
        SharedPreferences prefs = context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);
        final String fullRepo = getFullRepoPath(prefs);

        String rawToken = prefs.getString("restricted_bot_ghToken", "");
        if (rawToken == null || rawToken.trim().isEmpty()) {
            rawToken = prefs.getString("restricted_bot_ghPat", "");
        }
        String rawBranch = prefs.getString("restricted_bot_ghBranch", "100");

        if (rawToken == null) {
            rawToken = "";
        }

        final String ghToken = rawToken.trim();
        final String ghBranch = rawBranch.trim();

        String tgApiId = prefs.getString("restricted_bot_tgApiId", "").trim();
        String tgApiHash = prefs.getString("restricted_bot_tgApiHash", "").trim();
        String tgBotToken = prefs.getString("restricted_bot_tgBotToken", "").trim();
        String tgSession = prefs.getString("restricted_bot_tgSession", "").trim();
        String tgOwner = prefs.getString("restricted_bot_tgOwner", "").trim();

        String apiUrl = "https://api.github.com/repos/" + fullRepo + "/actions/workflows/restricted_bot.yml/dispatches";

        org.json.JSONObject inputs = new org.json.JSONObject();
        try {
            inputs.put("TELEGRAM_LINK", link);
            inputs.put("API_ID", tgApiId);
            inputs.put("API_HASH", tgApiHash);
            inputs.put("BOT_TOKEN", tgBotToken);
            inputs.put("SESSION_STRING", tgSession);
            inputs.put("OWNER_ID", tgOwner);
        } catch (Exception ignored) {}

        org.json.JSONObject payload = new org.json.JSONObject();
        try {
            payload.put("ref", ghBranch);
            payload.put("inputs", inputs);
        } catch (Exception ignored) {}

        OkHttpClient client = new OkHttpClient();
        RequestBody body = RequestBody.create(payload.toString(), MediaType.parse("application/json; charset=utf-8"));

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
                int code = response.code();
                if (response.isSuccessful() || code == 204) {
                    mainHandler.post(() -> Toast.makeText(context, "✅ لینک با موفقیت به گیت‌هاب ارسال شد 🚀", Toast.LENGTH_LONG).show());
                } else if (code == 404) {
                    mainHandler.post(() -> Toast.makeText(context, "❌ خطا ۴۰۴: مخزن (" + fullRepo + ") یا فایل restricted_bot.yml یافت نشد!", Toast.LENGTH_LONG).show());
                } else if (code == 401) {
                    mainHandler.post(() -> Toast.makeText(context, "❌ خطا ۴۰۱: توکن دسترسی گیت‌هاب منقضی یا نامعتبر است!", Toast.LENGTH_LONG).show());
                } else if (code == 422) {
                    mainHandler.post(() -> Toast.makeText(context, "⚠️ خطا ۴۲۲: شاخه " + ghBranch + " یا ورودی‌ها در گیت‌هاب تایید نشدند!", Toast.LENGTH_LONG).show());
                } else {
                    mainHandler.post(() -> Toast.makeText(context, "⚠️ پاسخ گیت‌هاب (" + code + "): لطفا توکن و اطلاعات مخزن را بررسی کنید", Toast.LENGTH_LONG).show());
                }
                response.close();
            }
        });
    }
}
