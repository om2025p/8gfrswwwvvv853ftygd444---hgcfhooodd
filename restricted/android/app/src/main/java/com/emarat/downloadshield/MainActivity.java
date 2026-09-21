package com.emarat.downloadshield;

import android.Manifest;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.button.MaterialButton;
import com.google.android.material.textfield.TextInputEditText;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {
    private static final int PERMISSION_REQUEST_CODE = 101;

    private TextInputEditText etDownloadLink;
    private MaterialButton btnPasteLink, btnDownload, btnToggleNotification, btnConfigBackupRestore, btnClearHistory;
    private TextView tvServerStatus, tvUniqueCount, tvEmptyHistory;
    private RecyclerView rvDownloadHistory;
    private DownloadHistoryAdapter historyAdapter;

    private OkHttpClient httpClient;
    private Handler mainHandler;
    private List<DownloadHistoryItem> historyList = new ArrayList<>();
    private Set<String> uniqueLinks = new HashSet<>();

    public static class DownloadHistoryItem {
        public String id;
        public String link;
        public String timestamp;
        public String status;
        public String statusText;
        public String errorLog;

        public DownloadHistoryItem(String id, String link, String timestamp, String status, String statusText) {
            this.id = id;
            this.link = link;
            this.timestamp = timestamp;
            this.status = status;
            this.statusText = statusText;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        httpClient = new OkHttpClient();
        mainHandler = new Handler(Looper.getMainLooper());

        initViews();
        setupListeners();
        loadSavedData();
        checkPermissionsAndStartService();

        handleIntent(getIntent());
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadHistory();
        updateNotificationBtnUI();
        checkServerStatus();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleIntent(intent);
    }

    private void handleIntent(Intent intent) {
        if (intent != null && NotificationInputReceiver.ACTION_QUICK_PASTE.equals(intent.getAction())) {
            pasteAndDownload();
        }
    }

    private void initViews() {
        etDownloadLink = findViewById(R.id.etDownloadLink);
        btnPasteLink = findViewById(R.id.btnPasteLink);
        btnDownload = findViewById(R.id.btnDownload);
        btnToggleNotification = findViewById(R.id.btnToggleNotification);
        btnConfigBackupRestore = findViewById(R.id.btnConfigBackupRestore);
        btnClearHistory = findViewById(R.id.btnClearHistory);
        tvServerStatus = findViewById(R.id.tvServerStatus);
        tvUniqueCount = findViewById(R.id.tvUniqueCount);
        tvEmptyHistory = findViewById(R.id.tvEmptyHistory);
        rvDownloadHistory = findViewById(R.id.rvDownloadHistory);

        rvDownloadHistory.setLayoutManager(new LinearLayoutManager(this));
        historyAdapter = new DownloadHistoryAdapter(historyList, errorLog -> {
            ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            if (cm != null) {
                ClipData clip = ClipData.newPlainText("ErrorLog", errorLog);
                cm.setPrimaryClip(clip);
                Toast.makeText(this, "📋 لاگ خطا کپی شد!", Toast.LENGTH_SHORT).show();
            }
        });
        rvDownloadHistory.setAdapter(historyAdapter);
    }

    private void setupListeners() {
        btnPasteLink.setOnClickListener(v -> pasteFromClipboard());

        btnDownload.setOnClickListener(v -> {
            String link = etDownloadLink.getText() != null ? etDownloadLink.getText().toString().trim() : "";
            if (link.isEmpty()) {
                Toast.makeText(this, "⚠️ لطفا آدرس لینک را در کادر بالا وارد کنید!", Toast.LENGTH_SHORT).show();
                return;
            }
            processDownloadLink(link);
            etDownloadLink.setText("");
        });

        btnToggleNotification.setOnClickListener(v -> {
            Intent intent = new Intent(this, ClipboardService.class);
            if (ClipboardService.isRunning) {
                intent.setAction(ClipboardService.ACTION_STOP);
                stopService(intent);
                Toast.makeText(this, "🔴 سرویس پس‌زمینه متوقف شد", Toast.LENGTH_SHORT).show();
            } else {
                intent.setAction(ClipboardService.ACTION_START);
                ContextCompat.startForegroundService(this, intent);
                Toast.makeText(this, "🟢 سرویس پس‌زمینه فعال گردید!", Toast.LENGTH_SHORT).show();
            }
            mainHandler.postDelayed(this::updateNotificationBtnUI, 500);
        });

        btnConfigBackupRestore.setOnClickListener(v -> showConfigDialog());

        btnClearHistory.setOnClickListener(v -> {
            SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
            prefs.edit().remove("restricted_download_history").apply();
            loadHistory();
            Toast.makeText(this, "🗑️ تاریخچه پاکسازی شد", Toast.LENGTH_SHORT).show();
        });
    }

    private void pasteFromClipboard() {
        ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (cm != null && cm.hasPrimaryClip() && cm.getPrimaryClip().getItemCount() > 0) {
            CharSequence text = cm.getPrimaryClip().getItemAt(0).getText();
            if (text != null && text.length() > 0) {
                etDownloadLink.setText(text.toString().trim());
                Toast.makeText(this, "📋 متن چسبانده شد!", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "⚠️ کلیپ‌بورد خالی است", Toast.LENGTH_SHORT).show();
            }
        } else {
            Toast.makeText(this, "⚠️ کلیپ‌بورد خالی است", Toast.LENGTH_SHORT).show();
        }
    }

    private void pasteAndDownload() {
        ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (cm != null && cm.hasPrimaryClip() && cm.getPrimaryClip().getItemCount() > 0) {
            CharSequence text = cm.getPrimaryClip().getItemAt(0).getText();
            if (text != null && text.length() > 0) {
                String link = text.toString().trim();
                etDownloadLink.setText(link);
                processDownloadLink(link);
                etDownloadLink.setText("");
            }
        }
    }

    private void processDownloadLink(String link) {
        boolean isNew = registerUniqueLink(link);
        String historyId = addDownloadHistoryItem(link, "⏳ در حال ارسال به گیت‌هاب...");
        dispatchToGitHub(link, historyId);
    }

    private boolean registerUniqueLink(String link) {
        if (uniqueLinks.add(link)) {
            SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
            JSONArray array = new JSONArray();
            for (String l : uniqueLinks) array.put(l);
            prefs.edit().putString("restricted_unique_download_links", array.toString()).apply();
            updateUniqueCountUI();
            return true;
        }
        return false;
    }

    private void updateUniqueCountUI() {
        tvUniqueCount.setText(String.format(Locale.getDefault(), "%d", uniqueLinks.size()));
    }

    private String addDownloadHistoryItem(String link, String statusText) {
        String id = "dl_" + System.currentTimeMillis();
        String timestamp = new SimpleDateFormat("yyyy/MM/dd - HH:mm:ss", Locale.getDefault()).format(new Date());

        DownloadHistoryItem item = new DownloadHistoryItem(id, link, timestamp, "in_progress", statusText);
        historyList.add(0, item);
        saveHistory();
        renderHistoryUI();
        return id;
    }

    private void updateHistoryItemStatus(String id, String status, String statusText, String errorLog) {
        for (DownloadHistoryItem item : historyList) {
            if (item.id.equals(id) || item.link.equals(id)) {
                item.status = status;
                item.statusText = statusText;
                if (errorLog != null) item.errorLog = errorLog;
                break;
            }
        }
        saveHistory();
        renderHistoryUI();
    }

    private void saveHistory() {
        SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
        JSONArray array = new JSONArray();
        try {
            int limit = Math.min(historyList.size(), 50);
            for (int i = 0; i < limit; i++) {
                DownloadHistoryItem item = historyList.get(i);
                JSONObject obj = new JSONObject();
                obj.put("id", item.id);
                obj.put("link", item.link);
                obj.put("timestamp", item.timestamp);
                obj.put("status", item.status);
                obj.put("statusText", item.statusText);
                if (item.errorLog != null) obj.put("errorLog", item.errorLog);
                array.put(obj);
            }
            prefs.edit().putString("restricted_download_history", array.toString()).apply();
        } catch (Exception ignored) {}
    }

    private void loadHistory() {
        historyList.clear();
        SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
        String raw = prefs.getString("restricted_download_history", "[]");
        try {
            JSONArray array = new JSONArray(raw);
            for (int i = 0; i < array.length(); i++) {
                JSONObject obj = array.getJSONObject(i);
                DownloadHistoryItem item = new DownloadHistoryItem(
                        obj.optString("id", "dl_" + i),
                        obj.optString("link", ""),
                        obj.optString("timestamp", ""),
                        obj.optString("status", "in_progress"),
                        obj.optString("statusText", "")
                );
                if (obj.has("errorLog")) item.errorLog = obj.getString("errorLog");
                historyList.add(item);
            }
        } catch (Exception ignored) {}
        renderHistoryUI();
    }

    private void renderHistoryUI() {
        if (historyList.isEmpty()) {
            rvDownloadHistory.setVisibility(View.GONE);
            tvEmptyHistory.setVisibility(View.VISIBLE);
        } else {
            rvDownloadHistory.setVisibility(View.VISIBLE);
            tvEmptyHistory.setVisibility(View.GONE);
            historyAdapter.updateData(historyList);
        }
    }

    private void loadSavedData() {
        SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
        String rawUnique = prefs.getString("restricted_unique_download_links", "[]");
        try {
            JSONArray array = new JSONArray(rawUnique);
            for (int i = 0; i < array.length(); i++) {
                uniqueLinks.add(array.getString(i));
            }
        } catch (Exception ignored) {}
        updateUniqueCountUI();
        loadHistory();
    }

    private void dispatchToGitHub(String link, String historyId) {
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
            Toast.makeText(this, "⚠️ توکن گیت‌هاب تنظیم نشده است! تنظیمات را بررسی کنید.", Toast.LENGTH_LONG).show();
            updateHistoryItemStatus(historyId, "failed", "❌ توکن گیت‌هاب خالی است", "لطفاً توکن دسترسی PAT را در بخش تنظیمات وارد کنید.");
            return;
        }

        String tgApiId = prefs.getString("restricted_bot_tgApiId", "").trim();
        String tgApiHash = prefs.getString("restricted_bot_tgApiHash", "").trim();
        String tgBotToken = prefs.getString("restricted_bot_tgBotToken", "").trim();
        String tgSession = prefs.getString("restricted_bot_tgSession", "").trim();
        String tgOwner = prefs.getString("restricted_bot_tgOwner", "").trim();

        String apiUrl = "https://api.github.com/repos/" + fullRepo + "/actions/workflows/restricted_bot.yml/dispatches";

        try {
            JSONObject inputs = new JSONObject();
            inputs.put("TELEGRAM_LINK", link);
            inputs.put("API_ID", tgApiId);
            inputs.put("API_HASH", tgApiHash);
            inputs.put("BOT_TOKEN", tgBotToken);
            inputs.put("SESSION_STRING", tgSession);
            inputs.put("OWNER_ID", tgOwner);

            JSONObject payload = new JSONObject();
            payload.put("ref", ghBranch);
            payload.put("inputs", inputs);

            RequestBody body = RequestBody.create(payload.toString(), MediaType.parse("application/json; charset=utf-8"));
            Request request = new Request.Builder()
                    .url(apiUrl)
                    .addHeader("Authorization", "Bearer " + ghToken)
                    .addHeader("Accept", "application/vnd.github.v3+json")
                    .post(body)
                    .build();

            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    mainHandler.post(() -> {
                        Toast.makeText(MainActivity.this, "❌ خطا در ارسال به گیت‌هاب: " + e.getMessage(), Toast.LENGTH_LONG).show();
                        updateHistoryItemStatus(historyId, "failed", "❌ خطا در اتصال شبکه", e.getMessage());
                    });
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    int code = response.code();
                    mainHandler.post(() -> {
                        if (response.isSuccessful() || code == 204) {
                            Toast.makeText(MainActivity.this, "✅ لینک با موفقیت به گیت‌هاب ارسال شد 🚀", Toast.LENGTH_SHORT).show();
                            updateHistoryItemStatus(historyId, "completed", "ارسال به گیت‌هاب انجام شد 📥", null);
                        } else {
                            String msg = "پاسخ گیت‌هاب کد " + code;
                            Toast.makeText(MainActivity.this, "⚠️ " + msg, Toast.LENGTH_LONG).show();
                            updateHistoryItemStatus(historyId, "failed", "❌ " + msg, "کد پاسخ HTTP گیت‌هاب: " + code);
                        }
                    });
                    response.close();
                }
            });
        } catch (Exception e) {
            updateHistoryItemStatus(historyId, "failed", "❌ خطای برنامه", e.getMessage());
        }
    }

    private void checkServerStatus() {
        SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);
        final String fullRepo = NotificationInputReceiver.getFullRepoPath(prefs);
        String rawToken = prefs.getString("restricted_bot_ghToken", "");
        if (rawToken == null || rawToken.trim().isEmpty()) {
            rawToken = prefs.getString("restricted_bot_ghPat", "");
        }

        if (rawToken == null || rawToken.trim().isEmpty()) {
            tvServerStatus.setText("تنظیمات گیت‌هاب خالی است");
            tvServerStatus.setTextColor(0xFFEF4444);
            return;
        }

        String url = "https://api.github.com/repos/" + fullRepo + "/actions/runs?per_page=1";
        Request request = new Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer " + rawToken.trim())
                .addHeader("Accept", "application/vnd.github.v3+json")
                .get()
                .build();

        httpClient.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                mainHandler.post(() -> {
                    tvServerStatus.setText("خطای شبکه ❌");
                    tvServerStatus.setTextColor(0xFFEF4444);
                });
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful() && response.body() != null) {
                    try {
                        String bodyStr = response.body().string();
                        JSONObject data = new JSONObject(bodyStr);
                        JSONArray runs = data.optJSONArray("workflow_runs");
                        if (runs != null && runs.length() > 0) {
                            JSONObject run = runs.getJSONObject(0);
                            String status = run.optString("status");
                            String conclusion = run.optString("conclusion");

                            mainHandler.post(() -> {
                                if ("completed".equals(status)) {
                                    if ("success".equals(conclusion)) {
                                        tvServerStatus.setText("آماده به کار (موتور فعال) ✅");
                                        tvServerStatus.setTextColor(0xFF16A34A);
                                    } else {
                                        tvServerStatus.setText("آخرین اجرا ناموفق ❌");
                                        tvServerStatus.setTextColor(0xFFEF4444);
                                    }
                                } else if ("in_progress".equals(status)) {
                                    tvServerStatus.setText("در حال دانلود / پردازش ⚡");
                                    tvServerStatus.setTextColor(0xFF0284C7);
                                } else {
                                    tvServerStatus.setText("در صف انتظار ⏳");
                                    tvServerStatus.setTextColor(0xFFF59E0B);
                                }
                            });
                        }
                    } catch (Exception ignored) {}
                }
                response.close();
            }
        });
    }

    private void updateNotificationBtnUI() {
        if (ClipboardService.isRunning) {
            btnToggleNotification.setText("⚡ وضعیت اعلان: فعال 🟢");
            btnToggleNotification.setTextColor(0xFF16A34A);
        } else {
            btnToggleNotification.setText("⚡ وضعیت اعلان: غیرفعال 🔴");
            btnToggleNotification.setTextColor(0xFFEF4444);
        }
    }

    private void showConfigDialog() {
        SharedPreferences prefs = getSharedPreferences("restricted_bot_prefs", MODE_PRIVATE);

        JSONObject cfg = new JSONObject();
        try {
            cfg.put("ghOwner", prefs.getString("restricted_bot_ghOwner", ""));
            cfg.put("ghRepo", prefs.getString("restricted_bot_ghRepo", ""));
            cfg.put("ghPat", prefs.getString("restricted_bot_ghPat", ""));
            cfg.put("ghBranch", prefs.getString("restricted_bot_ghBranch", "100"));
            cfg.put("tgApiId", prefs.getString("restricted_bot_tgApiId", ""));
            cfg.put("tgApiHash", prefs.getString("restricted_bot_tgApiHash", ""));
            cfg.put("tgBotToken", prefs.getString("restricted_bot_tgBotToken", ""));
            cfg.put("tgSession", prefs.getString("restricted_bot_tgSession", ""));
            cfg.put("tgOwner", prefs.getString("restricted_bot_tgOwner", ""));
        } catch (Exception ignored) {}

        EditText etConfig = new EditText(this);
        etConfig.setText(cfg.toString());
        etConfig.setMaxLines(8);

        new AlertDialog.Builder(this)
                .setTitle("⚙️ مدیریت بکاپ تنظیمات")
                .setMessage("می‌توانید JSON کانفیگ را کپی کنید یا متن بکاپ جدید را وارد کرده و بازیابی کنید:")
                .setView(etConfig)
                .setPositiveButton("💾 بازیابی تنظیمات", (dialog, which) -> {
                    String input = etConfig.getText().toString().trim();
                    if (!input.isEmpty()) {
                        try {
                            JSONObject json = new JSONObject(input);
                            SharedPreferences.Editor editor = prefs.edit();

                            if (json.has("ghOwner")) editor.putString("restricted_bot_ghOwner", json.getString("ghOwner").trim());
                            if (json.has("ghRepo")) editor.putString("restricted_bot_ghRepo", json.getString("ghRepo").trim());
                            if (json.has("ghPat")) editor.putString("restricted_bot_ghPat", json.getString("ghPat").trim());
                            if (json.has("ghBranch")) editor.putString("restricted_bot_ghBranch", json.getString("ghBranch").trim());
                            if (json.has("tgApiId")) editor.putString("restricted_bot_tgApiId", json.getString("tgApiId").trim());
                            if (json.has("tgApiHash")) editor.putString("restricted_bot_tgApiHash", json.getString("tgApiHash").trim());
                            if (json.has("tgBotToken")) editor.putString("restricted_bot_tgBotToken", json.getString("tgBotToken").trim());
                            if (json.has("tgSession")) editor.putString("restricted_bot_tgSession", json.getString("tgSession").trim());
                            if (json.has("tgOwner")) editor.putString("restricted_bot_tgOwner", json.getString("tgOwner").trim());

                            editor.apply();
                            Toast.makeText(this, "✅ تنظیمات بازیابی شد!", Toast.LENGTH_SHORT).show();
                            checkServerStatus();
                        } catch (Exception e) {
                            Toast.makeText(this, "❌ فرمت JSON معتبر نیست", Toast.LENGTH_SHORT).show();
                        }
                    }
                })
                .setNeutralButton("📋 کپی به حافظه", (dialog, which) -> {
                    ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                    if (cm != null) {
                        cm.setPrimaryClip(ClipData.newPlainText("ConfigBackup", cfg.toString()));
                        Toast.makeText(this, "📋 بکاپ تنظیمات در کلیپ‌بورد کپی شد!", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton("بستن", null)
                .show();
    }

    private void checkPermissionsAndStartService() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(
                        this,
                        new String[]{Manifest.permission.POST_NOTIFICATIONS},
                        PERMISSION_REQUEST_CODE
                );
            } else {
                startClipboardService();
            }
        } else {
            startClipboardService();
        }
    }

    private void startClipboardService() {
        Intent serviceIntent = new Intent(this, ClipboardService.class);
        serviceIntent.setAction(ClipboardService.ACTION_START);
        ContextCompat.startForegroundService(this, serviceIntent);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == PERMISSION_REQUEST_CODE) {
            startClipboardService();
        }
    }
}
