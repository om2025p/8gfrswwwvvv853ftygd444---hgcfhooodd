package com.emarat.downloadshield;

import android.content.Context;
import android.content.Intent;
import android.webkit.JavascriptInterface;
import android.widget.Toast;
import androidx.core.content.ContextCompat;

public class AndroidBridge {
    private Context context;

    public AndroidBridge(Context context) {
        this.context = context;
    }

    @JavascriptInterface
    public void showToast(String message) {
        Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
    }

    @JavascriptInterface
    public void startClipboardService() {
        Intent serviceIntent = new Intent(context, ClipboardService.class);
        serviceIntent.setAction(ClipboardService.ACTION_START);
        ContextCompat.startForegroundService(context, serviceIntent);
        showToast("سرویس شنود کلیپ‌بورد روشن شد 🟢");
    }

    @JavascriptInterface
    public void stopClipboardService() {
        Intent serviceIntent = new Intent(context, ClipboardService.class);
        serviceIntent.setAction(ClipboardService.ACTION_STOP);
        context.startService(serviceIntent);
        showToast("سرویس شنود کلیپ‌بورد خاموش شد 🔴");
    }

    @JavascriptInterface
    public boolean isClipboardServiceRunning() {
        return ClipboardService.isRunning;
    }
}
