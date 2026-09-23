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
        Log.d(TAG, "📢 دریافت اکشن اعلان پس‌زمینه: " + action);

        String linkToDownload = null;

        if (ACTION_SUBMIT_LINK.equals(action)) {
            Bundle remoteInput = RemoteInput.getResultsFromIntent(intent);
            if (remoteInput != null) {
                CharSequence text = remoteInput.getCharSequence(KEY_TEXT_REPLY);
                if (text != null) {
                    linkToDownload = text.toString().trim();
                    Log.d(TAG, "✅ متن دریافتی از RemoteInput: " + linkToDownload);
                }
            }
            ClipboardService.refreshNotification(context);
        } else if (ACTION_QUICK_PASTE.equals(action)) {
            Log.d(TAG, "📋 پردازش چسباندن ۱۰۰٪ پس‌زمینه بدون باز شدن برنامه...");

            // اولویت اول: استعلام مستقیم کلیپ‌بورد سیستم بدون محدودیت طول متن
            ClipboardManager clipboardManager = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            try {
                if (clipboardManager != null && clipboardManager.hasPrimaryClip()) {
                    ClipData clip = clipboardManager.getPrimaryClip();
                    if (clip != null && clip.getItemCount() > 0) {
                        CharSequence text = clip.getItemAt(0).getText();
                        if (text != null) {
                            String raw = text.toString().trim();
                            if (!raw.isEmpty()) {
                                linkToDownload = raw;
                            }
                        }
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "❌ خطا در استعلام کلیپ‌بورد سیستم: " + e.getMessage());
            }

            // اولویت دوم: کش اخیر سرویس پس‌زمینه
            if ((linkToDownload == null || linkToDownload.isEmpty()) && ClipboardService.lastCopiedUrl != null && !ClipboardService.lastCopiedUrl.isEmpty()) {
                linkToDownload = ClipboardService.lastCopiedUrl;
                Log.d(TAG, "🎯 استفاده از کش سرویس: " + linkToDownload);
            }

            ClipboardService.refreshNotification(context);
        }

        // سیستم هوشمند سرهم‌سازی تکه‌های متن (Chunk Assembly Engine)
        if (linkToDownload != null && !linkToDownload.isEmpty()) {
            String assembled = assembleTextChunks(context, linkToDownload);
            if (assembled == null) {
                // هنوز بقیه تکه‌ها نرسیده‌اند
                Toast.makeText(context, "🧩 تکه جدید دریافت شد... در حال تکمیل سرهم‌سازی", Toast.LENGTH_SHORT).show();
                return;
            }
            linkToDownload = assembled;

            Log.i(TAG, "🚀 شروع ارسال پس‌زمینه به گیت‌هاب برای لینک سرهم‌شده (طول " + linkToDownload.length() + "): " + linkToDownload);
            Toast.makeText(context, "🚀 چسباندن و ارسال پس‌زمینه متن کامل (سرهم‌شده):\n" + linkToDownload.substring(0, Math.min(linkToDownload.length(), 60)) + "...", Toast.LENGTH_LONG).show();

            registerNativeUniqueLink(context, linkToDownload);
            saveNativeDownloadHistory(context, linkToDownload, "⚡ چسباندن آنی و سرهم‌شده اعلان");
            dispatchToGitHub(context, linkToDownload);

            // ریست کامل کلیپ‌بورد سیستم و کش سرویس جهت آماده‌سازی دکمه برای ارسال بعدی
            clearClipboardSystem(context);
            ClipboardService.lastCopiedUrl = "";
            ClipboardService.lastProcessedClip = "";
            ClipboardService.refreshNotification(context);
        } else {
            Log.w(TAG, "⚠️ کلیپ‌بورد خالی است یا لینک معتبری یافت نشد.");
            Toast.makeText(context, "⚠️ کلیپ‌بورد خالی است یا لینکی یافت نشد!", Toast.LENGTH_SHORT).show();
        }
    }

    public static void clearClipboardSystem(Context context) {
        try {
            ClipboardManager clipboardManager = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboardManager != null) {
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
                    clipboardManager.clearPrimaryClip();
                } else {
                    clipboardManager.setPrimaryClip(ClipData.newPlainText("", ""));
                }
                Log.d(TAG, "کلیپ‌بورد سیستم با موفقیت ریست شد.");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error clearing clipboard: " + e.getMessage());
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
                Log.d(TAG, "🔗 لینک منحصربه‌فرد جدید ثبت شد. مجموع: " + array.length());
            }
        } catch (Exception e) {
            Log.e(TAG, "❌ خطا در ثبت لینک منحصربه‌فرد: " + e.getMessage());
        }
    }

    public static String assembleTextChunks(Context context, String incomingText) {
        if (incomingText == null || incomingText.trim().isEmpty()) return incomingText;

        if (incomingText.startsWith("[CHUNK:")) {
            try {
                int closingBracket = incomingText.indexOf("]");
                if (closingBracket > 7) {
                    String header = incomingText.substring(7, closingBracket);
                    String payload = incomingText.substring(closingBracket + 1);
                    String[] parts = header.split(":");
                    if (parts.length == 3) {
                        String chunkId = parts[0];
                        int partNum = Integer.parseInt(parts[1]);
                        int totalParts = Integer.parseInt(parts[2]);

                        SharedPreferences prefs = context.getSharedPreferences("restricted_chunk_buffer", Context.MODE_PRIVATE);
                        prefs.edit().putString(chunkId + "_part_" + partNum, payload).apply();

                        boolean allReceived = true;
                        StringBuilder fullAssembled = new StringBuilder();
                        for (int i = 1; i <= totalParts; i++) {
                            String p = prefs.getString(chunkId + "_part_" + i, null);
                            if (p == null) {
                                allReceived = false;
                                break;
                            }
                            fullAssembled.append(p);
                        }

                        if (allReceived) {
                            SharedPreferences.Editor editor = prefs.edit();
                            for (int i = 1; i <= totalParts; i++) {
                                editor.remove(chunkId + "_part_" + i);
                            }
                            editor.apply();
                            Log.d(TAG, "🧩 سرهم‌سازی موفقیت‌آمیز تمام تکه‌های متن (" + totalParts + " تکه)! طول کل: " + fullAssembled.length());
                            return fullAssembled.toString();
                        } else {
                            Log.d(TAG, "🧩 تکه " + partNum + " از " + totalParts + " ذخیره شد. در انتظار سایر تکه‌ها...");
                            return null;
                        }
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Error in chunk assembly: " + e.getMessage());
            }
        }

        return incomingText;
    }

    public static String[] splitTextIntoChunks(String fullText, int chunkSize) {
        if (fullText == null) return new String[0];
        if (fullText.length() <= chunkSize) return new String[]{fullText};

        int totalParts = (int) Math.ceil((double) fullText.length() / chunkSize);
        String chunkId = "chk_" + System.currentTimeMillis();
        String[] chunks = new String[totalParts];

        for (int i = 0; i < totalParts; i++) {
            int start = i * chunkSize;
            int end = Math.min(start + chunkSize, fullText.length());
            String sub = fullText.substring(start, end);
            chunks[i] = "[CHUNK:" + chunkId + ":" + (i + 1) + ":" + totalParts + "]" + sub;
        }

        return chunks;
    }

    public static void show2SecondToast(Context context, String message) {
        Handler mainHandler = new Handler(Looper.getMainLooper());
        mainHandler.post(() -> {
            Toast toast = Toast.makeText(context, message, Toast.LENGTH_SHORT);
            toast.show();
            mainHandler.postDelayed(toast::cancel, 2000);
        });
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
            Log.e(TAG, "❌ خطا در ذخیره تاریخچه نیتیو: " + e.getMessage());
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

        if (ghToken.isEmpty()) {
            Toast.makeText(context, "⚠️ توکن گیت‌هاب خالی است! ابتدا تنظیمات را پر کنید.", Toast.LENGTH_LONG).show();
            return;
        }

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
                    show2SecondToast(context, "🎬 کلیپ با موفقیت به تلگرام ارسال شد 🚀");
                } else if (code == 404) {
                    mainHandler.post(() -> Toast.makeText(context, "❌ خطا ۴۰۴: مخزن (" + fullRepo + ") یا ورک‌فلو یافت نشد!", Toast.LENGTH_LONG).show());
                } else if (code == 401) {
                    mainHandler.post(() -> Toast.makeText(context, "❌ خطا ۴۰۱: توکن دسترسی گیت‌هاب معتبر نیست!", Toast.LENGTH_LONG).show());
                } else {
                    mainHandler.post(() -> Toast.makeText(context, "⚠️ پاسخ گیت‌هاب (" + code + "): لطفا تنظیمات مخزن را چک کنید", Toast.LENGTH_LONG).show());
                }
                response.close();
            }
        });
    }
}
