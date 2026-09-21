package com.emarat.downloadshield;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;

import androidx.core.app.NotificationCompat;
import androidx.core.app.RemoteInput;

import org.json.JSONObject;

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

public class ClipboardService extends Service {
    public static final String CHANNEL_ID = "download_shield_channel";
    public static final int NOTIFICATION_ID = 1001;
    private static final String TAG = "ClipboardService";

    public static final String ACTION_START = "ACTION_START";
    public static final String ACTION_STOP = "ACTION_STOP";
    public static final String ACTION_TOGGLE = "ACTION_TOGGLE";

    public static boolean isRunning = false;
    public static String lastCopiedUrl = "";
    public static String lastProcessedClip = "";

    private ClipboardManager clipboardManager;
    private ClipboardManager.OnPrimaryClipChangedListener clipListener;
    private OkHttpClient httpClient;
    private Handler mainHandler;

    private static final Pattern URL_PATTERN = Pattern.compile(
            "(https?://(?:www\\.)?(?:instagram\\.com|tiktok\\.com|t\\.me|telegram\\.me|youtube\\.com|youtu\\.be|twitter\\.com|x\\.com|threads\\.net|facebook\\.com)[^\\s]+)",
            Pattern.CASE_INSENSITIVE
    );

    @Override
    public void onCreate() {
        super.onCreate();
        httpClient = new OkHttpClient();
        mainHandler = new Handler(Looper.getMainLooper());
        createNotificationChannel();

        clipboardManager = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        clipListener = new ClipboardManager.OnPrimaryClipChangedListener() {
            @Override
            public void onPrimaryClipChanged() {
                if (!isRunning) return;
                processClipboard();
            }
        };

        if (clipboardManager != null) {
            clipboardManager.addPrimaryClipChangedListener(clipListener);
            updateCachedUrlFromClipboard();
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && intent.getAction() != null) {
            String action = intent.getAction();
            if (ACTION_STOP.equals(action)) {
                stopSelfService();
                return START_NOT_STICKY;
            } else if (ACTION_TOGGLE.equals(action)) {
                if (isRunning) {
                    stopSelfService();
                    return START_NOT_STICKY;
                }
            }
        }

        isRunning = true;
        updateCachedUrlFromClipboard();
        Notification notification = buildNotification();
        startForeground(NOTIFICATION_ID, notification);
        return START_STICKY;
    }

    private void stopSelfService() {
        isRunning = false;
        if (clipboardManager != null && clipListener != null) {
            clipboardManager.removePrimaryClipChangedListener(clipListener);
        }
        stopForeground(true);
        stopSelf();
    }

    private void updateCachedUrlFromClipboard() {
        if (clipboardManager == null || !clipboardManager.hasPrimaryClip()) return;
        try {
            ClipData clip = clipboardManager.getPrimaryClip();
            if (clip != null && clip.getItemCount() > 0) {
                CharSequence textChar = clip.getItemAt(0).getText();
                if (textChar != null) {
                    String raw = textChar.toString().trim();
                    Matcher matcher = URL_PATTERN.matcher(raw);
                    if (matcher.find()) {
                        lastCopiedUrl = matcher.group(1);
                        Log.d(TAG, "به‌روزرسانی اولیه کش سرویس: " + lastCopiedUrl);
                    } else if (raw.startsWith("http://") || raw.startsWith("https://")) {
                        lastCopiedUrl = raw;
                        Log.d(TAG, "به‌روزرسانی اولیه کش سرویس: " + lastCopiedUrl);
                    }
                }
            }
        } catch (Exception ignored) {}
    }

    private void processClipboard() {
        if (clipboardManager == null || !clipboardManager.hasPrimaryClip()) return;

        try {
            ClipData clip = clipboardManager.getPrimaryClip();
            if (clip != null && clip.getItemCount() > 0) {
                CharSequence textChar = clip.getItemAt(0).getText();
                if (textChar == null) return;
                String text = textChar.toString().trim();

                if (text.isEmpty() || text.equals(lastProcessedClip)) return;

                Matcher matcher = URL_PATTERN.matcher(text);
                if (matcher.find()) {
                    lastCopiedUrl = matcher.group(1);
                    lastProcessedClip = text;
                    Log.d(TAG, "تغییر کلیپ‌بورد شناسایی شد: " + lastCopiedUrl);
                } else if (text.startsWith("http://") || text.startsWith("https://")) {
                    lastCopiedUrl = text;
                    lastProcessedClip = text;
                    Log.d(TAG, "تغییر کلیپ‌بورد شناسایی شد: " + lastCopiedUrl);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in processClipboard: " + e.getMessage());
        }
    }

    public static void refreshNotification(Context context) {
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;

        Intent openAppIntent = new Intent(context, MainActivity.class);
        PendingIntent openAppPendingIntent = PendingIntent.getActivity(
                context, 0, openAppIntent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        RemoteInput remoteInput = new RemoteInput.Builder(NotificationInputReceiver.KEY_TEXT_REPLY)
                .setLabel("تایپ یا چسباندن لینک (بدون محدودیت طول)...")
                .setAllowFreeFormInput(true)
                .build();

        Intent submitIntent = new Intent(context, NotificationInputReceiver.class);
        submitIntent.setAction(NotificationInputReceiver.ACTION_SUBMIT_LINK);
        PendingIntent submitPendingIntent = PendingIntent.getBroadcast(
                context, 2, submitIntent, PendingIntent.FLAG_MUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        NotificationCompat.Action directReplyAction = new NotificationCompat.Action.Builder(
                R.drawable.ic_stat_download,
                "📥 ارسال مستقیم",
                submitPendingIntent
        ).addRemoteInput(remoteInput).build();

        Intent pasteIntent = new Intent(context, TransparentPasteActivity.class);
        pasteIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pastePendingIntent = PendingIntent.getActivity(
                context, 3, pasteIntent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        NotificationCompat.Action quickPasteAction = new NotificationCompat.Action.Builder(
                R.drawable.ic_stat_download,
                "📋 چسباندن و ارسال آنی",
                pastePendingIntent
        ).build();

        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setContentTitle("سپر دانلود (فعال)")
                .setContentText("شنود هوشمند کلیپ‌بورد فعال است")
                .setSmallIcon(R.drawable.ic_stat_download)
                .setContentIntent(openAppPendingIntent)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .addAction(directReplyAction)
                .addAction(quickPasteAction);

        manager.notify(NOTIFICATION_ID, builder.build());
    }

    private Notification buildNotification() {
        Intent openAppIntent = new Intent(this, MainActivity.class);
        PendingIntent openAppPendingIntent = PendingIntent.getActivity(
                this, 0, openAppIntent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        RemoteInput remoteInput = new RemoteInput.Builder(NotificationInputReceiver.KEY_TEXT_REPLY)
                .setLabel("تایپ یا چسباندن لینک (بدون محدودیت طول)...")
                .setAllowFreeFormInput(true)
                .build();

        Intent submitIntent = new Intent(this, NotificationInputReceiver.class);
        submitIntent.setAction(NotificationInputReceiver.ACTION_SUBMIT_LINK);
        PendingIntent submitPendingIntent = PendingIntent.getBroadcast(
                this, 2, submitIntent, PendingIntent.FLAG_MUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        NotificationCompat.Action directReplyAction = new NotificationCompat.Action.Builder(
                R.drawable.ic_stat_download,
                "📥 ارسال مستقیم",
                submitPendingIntent
        ).addRemoteInput(remoteInput).build();

        Intent pasteIntent = new Intent(this, TransparentPasteActivity.class);
        pasteIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pastePendingIntent = PendingIntent.getActivity(
                this, 3, pasteIntent, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
        );

        NotificationCompat.Action quickPasteAction = new NotificationCompat.Action.Builder(
                R.drawable.ic_stat_download,
                "📋 چسباندن و ارسال آنی",
                pastePendingIntent
        ).build();

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setContentTitle("سپر دانلود (فعال)")
                .setContentText("شنود هوشمند کلیپ‌بورد فعال است")
                .setSmallIcon(R.drawable.ic_stat_download)
                .setContentIntent(openAppPendingIntent)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .addAction(directReplyAction)
                .addAction(quickPasteAction);

        return builder.build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "سرویس سپر دانلود",
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            channel.setDescription("اعلان دائم جهت چسباندن سریع لینک و ارسال به گیت‌هاب");
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
