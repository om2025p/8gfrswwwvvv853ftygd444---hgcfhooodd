package com.emarat.downloadshield;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
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

    /** اکشن اختصاصی این اکتیویتی تا اینتنت اعلان با سایر اینتنت‌ها تداخل نکند. */
    public static final String ACTION_PASTE = "com.emarat.downloadshield.ACTION_PASTE";

    /** جلوگیری از پردازش دوبارهٔ همان اینتنت در یک چرخهٔ حیات. */
    private boolean handled = false;

    /** شمارندهٔ تلاش‌های خواندن کلیپ‌بورد (اندروید ۱۰+ پیش از فوکوس خالی می‌دهد). */
    private int attempts = 0;

    private static final Pattern URL_PATTERN = Pattern.compile(
            "(https?://[^\\s]+)",
            Pattern.CASE_INSENSITIVE
    );

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        arm();
    }

    /**
     * وقتی اکتیویتی از قبل زنده باشد، اندروید اینتنت جدید را به‌جای onCreate به این متد
     * تحویل می‌دهد. بدون این متد، دکمهٔ «چسباندن» اعلان فقط بار اول کار می‌کرد.
     */
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        arm();
    }

    /**
     * در اندروید ۱۰+ خواندن کلیپ‌بورد فقط پس از گرفتن فوکوس پنجره ممکن است؛
     * پس تا لحظهٔ فوکوس صبر می‌کنیم و یک تایمر پشتیبان هم می‌گذاریم.
     */
    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) tryPaste();
    }

    private void arm() {
        handled = false;
        attempts = 0;
        tryPaste();
    }

    private void tryPaste() {
        if (handled) return;

        String freshLink = getFreshClipboardUrl();

        // در اندروید ۱۰+ ممکن است چند صد میلی‌ثانیه طول بکشد تا خواندن کلیپ‌بورد مجاز شود؛
        // پس چند بار تلاش می‌کنیم تا لینک از دست نرود.
        if ((freshLink == null || freshLink.isEmpty()) && attempts < 6) {
            attempts++;
            new Handler(Looper.getMainLooper()).postDelayed(this::tryPaste, 250);
            return;
        }

        handled = true;

        if (freshLink != null && !freshLink.isEmpty()) {
            String assembled = NotificationInputReceiver.assembleTextChunks(this, freshLink);
            if (assembled == null) {
                Toast.makeText(this, "🧩 تکه جدید دریافت شد... در حال تکمیل سرهم‌سازی", Toast.LENGTH_SHORT).show();
                finish();
                return;
            }
            freshLink = assembled;

            Toast.makeText(this, "🚀 چسباندن زنده و ارسال به گیت‌هاب:\n" + freshLink.substring(0, Math.min(freshLink.length(), 60)) + "...", Toast.LENGTH_LONG).show();

            // پاکسازی کامل کلیپ‌بورد سیستم و حافظه سرویس تا لینک قدیمی پاک شود و جا برای لینک جدید باز گردد
            clearClipboardSystem();
            ClipboardService.lastCopiedUrl = "";
            ClipboardService.lastProcessedClip = "";

            NotificationInputReceiver.registerNativeUniqueLink(this, freshLink);
            NotificationInputReceiver.saveNativeDownloadHistory(this, freshLink, "⚡ چسباندن زنده از اعلان");
            dispatchToGitHub(freshLink);
        } else {
            Toast.makeText(this, "⚠️ کلیپ‌بورد خالی است یا لینک معتبری یافت نشد!", Toast.LENGTH_SHORT).show();
        }

        ClipboardService.refreshNotification(this);
        finish();
    }

    private void clearClipboardSystem() {
        try {
            ClipboardManager clipboardManager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboardManager != null) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                    clipboardManager.clearPrimaryClip();
                } else {
                    clipboardManager.setPrimaryClip(ClipData.newPlainText("", ""));
                }
                Log.d(TAG, "کلیپ‌بورد سیستم با موفقیت پاکسازی شد.");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error clearing clipboard: " + e.getMessage());
        }
    }

    private String getFreshClipboardUrl() {
        ClipboardManager clipboardManager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboardManager == null) {
            Log.w(TAG, "ClipboardManager is null");
            return null;
        }

        boolean hasClip = clipboardManager.hasPrimaryClip();
        if (hasClip) {
            try {
                ClipData clip = clipboardManager.getPrimaryClip();
                if (clip != null && clip.getItemCount() > 0) {
                    CharSequence textChar = clip.getItemAt(0).getText();
                    if (textChar != null) {
                        String raw = textChar.toString().trim();
                        if (!raw.isEmpty()) {
                            return raw;
                        }
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, "Error reading clipboard: " + e.getMessage());
            }
        }

        // اگر سیستم کلیپ بورد مستقیم تهی داد، از کش اخیر سرویس استفاده کن
        String serviceCache = ClipboardService.lastCopiedUrl;
        if (serviceCache != null && !serviceCache.isEmpty()) {
            return serviceCache;
        }

        return null;
    }

    private void dispatchToGitHub(String link) {
        final Context appContext = getApplicationContext();
        DownloadDispatcher.dispatch(appContext, link, new DownloadDispatcher.Callback2() {
            @Override
            public void onSuccess(String via) {
                String msg = "server".equals(via)
                        ? "🎬 لینک به سرور اختصاصی ارسال شد 🚀"
                        : "🐢 سرور در دسترس نبود؛ از مسیر پشتیبان گیت‌هاب ارسال شد";
                NotificationInputReceiver.show2SecondToast(appContext, msg);
            }

            @Override
            public void onFailure(String message, String detail) {
                Log.w(TAG, "dispatch failed: " + message + " | " + detail);
                new Handler(Looper.getMainLooper()).post(() ->
                        Toast.makeText(appContext, "⚠️ " + message, Toast.LENGTH_LONG).show());
            }
        });
    }
}
