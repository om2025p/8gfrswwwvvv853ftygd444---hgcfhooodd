package com.emarat.downloadshield;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.webkit.JavascriptInterface;
import android.widget.Toast;
import androidx.core.content.ContextCompat;

import org.json.JSONObject;

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
    public String getClipboardText() {
        try {
            ClipboardManager clipboardManager = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboardManager != null && clipboardManager.hasPrimaryClip()) {
                ClipData clip = clipboardManager.getPrimaryClip();
                if (clip != null && clip.getItemCount() > 0) {
                    CharSequence text = clip.getItemAt(0).getText();
                    if (text != null) {
                        return text.toString();
                    }
                }
            }
        } catch (Exception ignored) {}
        return "";
    }

    @JavascriptInterface
    public String getConfigData() {
        try {
            SharedPreferences prefs = context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);
            JSONObject json = new JSONObject();

            String token = prefs.getString("restricted_bot_ghToken", "");
            if (token.isEmpty()) token = prefs.getString("restricted_bot_ghPat", "");

            json.put("ghOwner", prefs.getString("restricted_bot_ghOwner", ""));
            json.put("ghRepo", prefs.getString("restricted_bot_ghRepo", ""));
            json.put("ghPat", token);
            json.put("ghToken", token);
            json.put("ghBranch", prefs.getString("restricted_bot_ghBranch", "100"));
            json.put("tgApiId", prefs.getString("restricted_bot_tgApiId", ""));
            json.put("tgApiHash", prefs.getString("restricted_bot_tgApiHash", ""));
            json.put("tgBotToken", prefs.getString("restricted_bot_tgBotToken", ""));
            json.put("tgSession", prefs.getString("restricted_bot_tgSession", ""));
            json.put("tgOwner", prefs.getString("restricted_bot_tgOwner", ""));

            return json.toString();
        } catch (Exception ignored) {}
        return "{}";
    }

    @JavascriptInterface
    public void saveConfigData(String jsonString) {
        try {
            if (jsonString != null && !jsonString.isEmpty()) {
                JSONObject json = new JSONObject(jsonString);
                SharedPreferences prefs = context.getSharedPreferences("restricted_bot_prefs", Context.MODE_PRIVATE);
                SharedPreferences.Editor editor = prefs.edit();

                String tokenVal = "";
                if (json.has("ghToken")) tokenVal = json.getString("ghToken").trim();
                else if (json.has("ghPat")) tokenVal = json.getString("ghPat").trim();

                if (!tokenVal.isEmpty()) {
                    editor.putString("restricted_bot_ghToken", tokenVal);
                    editor.putString("restricted_bot_ghPat", tokenVal);
                }

                if (json.has("ghOwner")) editor.putString("restricted_bot_ghOwner", json.getString("ghOwner").trim());
                if (json.has("ghRepo")) editor.putString("restricted_bot_ghRepo", json.getString("ghRepo").trim());
                if (json.has("ghBranch")) editor.putString("restricted_bot_ghBranch", json.getString("ghBranch").trim());
                if (json.has("tgApiId")) editor.putString("restricted_bot_tgApiId", json.getString("tgApiId").trim());
                if (json.has("tgApiHash")) editor.putString("restricted_bot_tgApiHash", json.getString("tgApiHash").trim());
                if (json.has("tgBotToken")) editor.putString("restricted_bot_tgBotToken", json.getString("tgBotToken").trim());
                if (json.has("tgSession")) editor.putString("restricted_bot_tgSession", json.getString("tgSession").trim());
                if (json.has("tgOwner")) editor.putString("restricted_bot_tgOwner", json.getString("tgOwner").trim());

                editor.apply();
            }
        } catch (Exception ignored) {}
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
