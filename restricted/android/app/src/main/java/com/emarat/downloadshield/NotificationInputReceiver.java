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
import android.util.Log;
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
    private static final String TAG = "NotificationReceiver";

    private static final Pattern URL_PATTERN = Pattern.compile(
            "(https?://[^\\s]+)",
            Pattern.CASE_INSENSITIVE
    );

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) {
            Log.e(TAG, "❌ دریافت اینتنت خالی یا بدون اکشن!");
            return;
        }

        String action = intent.getAction();
        Log.d(TAG, "📢 دریافت اکشن اعلان: " + action);
        String linkToDownload = null;

        if (ACTION_SUBMIT_LINK.equals(action)) {
            Log.d(TAG, "📥 پردازش ارسال دستی لینک از نوار اعلان...");
            Bundle remoteInput = RemoteInput.getResultsFromIntent(intent);
            if (remoteInput != null) {
                CharSequence text = remoteInput.getCharSequence(KEY_TEXT_REPLY);
                if (text != null) {
                    linkToDownload = text.toString().trim();
                    Log.d(TAG, "✅ متن دریافتی از RemoteInput: " + linkToDownload);
                } else {
                    Log.w(TAG, "⚠️ RemoteInput متن تهی بازگرداند.");
                }
            } else {
                Log.w(TAG, "⚠️ RemoteInput Bundle تهی است.");
            }
            ClipboardService.refreshNotification(context);
        } else if (ACTION_QUICK_PASTE.equals(action)) {
            Log.d(TAG, "📋 پردازش چسباندن سریع از کلیپ‌بورد در اکشن اعلان...");
            ClipboardManager clipboardManager = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            String pastedUrl = null;
            try {
                if (clipboardManager == null) {
                    Log.e(TAG, "❌ ClipboardManager در دسترس نیست!");
                } else if (!clipboardManager.hasPrimaryClip()) {
                    Log.w(TAG, "⚠️ ClipboardManager فاقد PrimaryClip است (کلیپ‌بورد خالی است).");
                } else {
                    ClipData clip = clipboardManager.getPrimaryClip();
                    if (clip != null && clip.getItemCount() > 0) {
                        CharSequence text = clip.getItemAt(0).getText();
                        if (text != null) {
                            String raw = text.toString().trim();
                            Log.d(TAG, "📄 متن استخراج‌شده از کلیپ‌بورد: " + raw);
                            Matcher matcher = URL_PATTERN.matcher(raw);
                            if (matcher.find()) {
                                pastedUrl = matcher.group(1);
                                Log.d(TAG, "🔗 پیوند شناسایی‌شده با Regex: " + pastedUrl);
                            } else {
                                pastedUrl = raw;
                                Log.d(TAG, "📄 استفاده مستقیم از متن کلیپ‌بورد: " + pastedUrl);
                            }
                        } else {
                            Log.w(TAG, "⚠️ آیتم کلیپ‌بورد دارای متن (getText) تهی است.");
                        }
                    } else {
                        Log.w(TAG, "⚠️ ClipData تهی است یا آیتمی ندارد.");
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "❌ استثنا در خواندن کلیپ‌بورد: " + e.getMessage(), e);
            }

            ClipboardService.refreshNotification(context);

            if (pastedUrl != null && !pastedUrl.isEmpty()) {
                linkToDownload = pastedUrl;
            } else {
                Log.w(TAG, "⚠️ پیوندی در کلیپ‌بورد یافت نشد. باز کردن MainActivity برای بازخوانی کلیپ‌بورد در foreground...");
                Toast.makeText(context, "⚠️ کلیپ‌بورد خالی است یا پیوندی یافت نشد!", Toast.LENGTH_SHORT).show();
                Intent openIntent = new Intent(context, MainActivity.class);
                openIntent.setAction(ACTION_QUICK_PASTE);
                openIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                context.startActivity(openIntent);
                return;
            }
        }

        if (linkToDownload != null && !linkToDownload.isEmpty()) {
            Log.i(TAG, "🚀 شروع ارسال به گیت‌هاب برای لینک: " + linkToDownload);
            Toast.makeText(context, "🚀 در حال چسباندن و ارسال آنی به گیت‌هاب...\n" + linkToDownload, Toast.LENGTH_SHORT).show();
            registerNativeUniqueLink(context, linkToDownload);
            saveNativeDownloadHistory(context, linkToDownload, "⚡ ارسال‌شده از اعلان اندروید");
            dispatchToGitHub(context, linkToDownload);
        } else if (ACTION_SUBMIT_LINK.equals(action)) {
            Log.w(TAG, "⚠️ عدم ارسال به گیت‌هاب: لینک ورودی تهی است.");
            Toast.makeText(context, "⚠️ متن ورودی خالی است!", Toast.LENGTH_SHORT).show();
        }
    }

    public static void registerNativeUniqueLink(Context context, String link) {
        if (link == null || link.trim().isEmpty()) return;
        try {
            SharedPreferences prefs = context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);
            String rawUnique = prefs.getString("restricted_unique_download_links", "[]");
            org.json.JSONArray array = new org.json.JSONArray(rawUnique);

            boolean exists = false;
            for (int i = 0; i < array.length(); i++) {
                if (link.trim().equals(array.getString(i))) {
                    exists = true;
                    break;
                }
            }

            if (!exists) {
                array.put(link.trim());
                prefs.edit().putString("restricted_unique_download_links", array.toString()).apply();
                Log.d(TAG, "🔗 لینک منحصربه‌فرد جدید در حافظه نیتیو ثبت شد. مجموع: " + array.length());
            }
        } catch (Exception e) {
            Log.e(TAG, "❌ خطا در ثبت لینک منحصربه‌فرد نیتیو: " + e.getMessage(), e);
        }
    }

    public static void saveNativeDownloadHistory(Context context, String link, String statusText) {
        try {
            SharedPreferences prefs = context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);
            String rawHistory = prefs.getString("restricted_download_history", "[]");
            org.json.JSONArray historyArray = new org.json.JSONArray(rawHistory);

            org.json.JSONObject item = new org.json.JSONObject();
            item.put("id", "dl_native_" + System.currentTimeMillis());
            item.put("link", link);
            item.put("timestamp", "اعلان اندروید");
            item.put("status", "in_progress");
            item.put("statusText", statusText);
            item.put("isUnique", true);

            org.json.JSONArray updatedArray = new org.json.JSONArray();
            updatedArray.put(item);

            for (int i = 0; i < Math.min(49, historyArray.length()); i++) {
                updatedArray.put(historyArray.get(i));
            }

            prefs.edit().putString("restricted_download_history", updatedArray.toString()).apply();
            Log.d(TAG, "💾 تاریخچه نیتیو با موفقیت ذخیره شد.");
        } catch (Exception e) {
            Log.e(TAG, "❌ خطا در ذخیره تاریخچه نیتیو: " + e.getMessage(), e);
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

        Log.d(TAG, "🗝️ تنظیمات گیت‌هاب: Repo=" + fullRepo + " | Branch=" + ghBranch + " | TokenPresent=" + (!ghToken.isEmpty()));

        if (ghToken.isEmpty()) {
            Log.e(TAG, "❌ توکن گیت‌هاب تنظیم نشده است!");
            Toast.makeText(context, "⚠️ توکن گیت‌هاب خالی است! لطفاً ابتدا تنظیمات را وارد کنید.", Toast.LENGTH_LONG).show();
            return;
        }

        String tgApiId = prefs.getString("restricted_bot_tgApiId", "").trim();
        String tgApiHash = prefs.getString("restricted_bot_tgApiHash", "").trim();
        String tgBotToken = prefs.getString("restricted_bot_tgBotToken", "").trim();
        String tgSession = prefs.getString("restricted_bot_tgSession", "").trim();
        String tgOwner = prefs.getString("restricted_bot_tgOwner", "").trim();

        String apiUrl = "https://api.github.com/repos/" + fullRepo + "/actions/workflows/restricted_bot.yml/dispatches";
        Log.d(TAG, "🌐 URL درخواست: " + apiUrl);

        org.json.JSONObject inputs = new org.json.JSONObject();
        try {
            inputs.put("TELEGRAM_LINK", link);
            inputs.put("API_ID", tgApiId);
            inputs.put("API_HASH", tgApiHash);
            inputs.put("BOT_TOKEN", tgBotToken);
            inputs.put("SESSION_STRING", tgSession);
            inputs.put("OWNER_ID", tgOwner);
        } catch (Exception e) {
            Log.e(TAG, "❌ خطا در ساخت JSON ورودی‌ها: " + e.getMessage());
        }

        org.json.JSONObject payload = new org.json.JSONObject();
        try {
            payload.put("ref", ghBranch);
            payload.put("inputs", inputs);
        } catch (Exception e) {
            Log.e(TAG, "❌ خطا در ساخت JSON پِی‌لود: " + e.getMessage());
        }

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
                Log.e(TAG, "❌ شکست در درخواست شبکه به گیت‌هاب: " + e.getMessage(), e);
                mainHandler.post(() -> Toast.makeText(context, "❌ خطا در ارسال: " + e.getMessage(), Toast.LENGTH_LONG).show());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                int code = response.code();
                Log.i(TAG, "📥 پاسخ گیت‌هاب: کد وضعیت HTTP " + code);
                if (response.isSuccessful() || code == 204) {
                    Log.i(TAG, "✅ ارسال موفقیت‌آمیز به گیت‌هاب انجام شد (کد 204).");
                    mainHandler.post(() -> Toast.makeText(context, "✅ لینک با موفقیت به گیت‌هاب ارسال شد 🚀", Toast.LENGTH_LONG).show());
                } else if (code == 404) {
                    Log.e(TAG, "❌ کد 404: مخزن یا ورک‌فلو یافت نشد.");
                    mainHandler.post(() -> Toast.makeText(context, "❌ خطا ۴۰۴: مخزن (" + fullRepo + ") یا فایل restricted_bot.yml یافت نشد!", Toast.LENGTH_LONG).show());
                } else if (code == 401) {
                    Log.e(TAG, "❌ کد 401: توکن دسترسی منقضی یا نامعتبر.");
                    mainHandler.post(() -> Toast.makeText(context, "❌ خطا ۴۰۱: توکن دسترسی گیت‌هاب منقضی یا نامعتبر است!", Toast.LENGTH_LONG).show());
                } else if (code == 422) {
                    Log.e(TAG, "❌ کد 422: شاخه یا ورودی‌ها نامعتبرند.");
                    mainHandler.post(() -> Toast.makeText(context, "⚠️ خطا ۴۲۲: شاخه " + ghBranch + " یا ورودی‌ها در گیت‌هاب تایید نشدند!", Toast.LENGTH_LONG).show());
                } else {
                    Log.w(TAG, "⚠️ کد وضعیت غیرمنتظره: " + code);
                    mainHandler.post(() -> Toast.makeText(context, "⚠️ پاسخ گیت‌هاب (" + code + "): لطفا توکن و اطلاعات مخزن را بررسی کنید", Toast.LENGTH_LONG).show());
                }
                response.close();
            }
        });
    }
}
