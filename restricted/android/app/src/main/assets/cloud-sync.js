(function () {
    // برای امنیت بیشتر و عدم تداخل متغیرها، همه چیز را در یک IIFE قرار می‌دهیم.
    console.log("Emarat Cloud Sync Initialized!");

    // تولید اثرانگشت پایدار و منحصربه‌فرد برای دستگاه بدون نیاز به کوکی یا حافظه محلی
    function getDeviceFingerprint() {
        const components = [
            navigator.language || '',
            screen.width + 'x' + screen.height,
            screen.colorDepth || '',
            new Date().getTimezoneOffset(),
            navigator.hardwareConcurrency || '',
            navigator.maxTouchPoints || '',
            // تشخیص کارت گرافیک (GPU) به عنوان امضای سخت‌افزاری قوی
            (() => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (!gl) return '';
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    return debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : '';
                } catch (e) {
                    return '';
                }
            })()
        ];
        const str = components.join('|');
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = (hash << 5) - hash + char;
            hash = hash & hash; // تبدیل به عدد ۳۲ بیتی
        }
        return 'emarat_fp_' + Math.abs(hash);
    }

    const fingerprint = getDeviceFingerprint();
    const namespace = "emarat-pwa-backup-v2";
    const apiUrl = `https://mantledb.sh/v2/${namespace}/${fingerprint}`;

    let hasPulled = false;
    let initialLocalKeysCount = localStorage.length;

    // دریافت داده‌ها از ابری (MantleDB) و بازیابی خودکار
    async function pullFromCloud() {
        if (!navigator.onLine) {
            hasPulled = true; // اگر آفلاین است، اجازه بکاپ‌گیری بدهد تا کارش را بکند
            return;
        }

        try {
            console.log("Checking cloud backup for device:", fingerprint);
            const res = await fetch(apiUrl);
            if (res.status === 200) {
                const cloudBackup = await res.json();
                if (cloudBackup && cloudBackup.timestamp && cloudBackup.data) {
                    const localTimestamp = parseInt(localStorage.getItem('emarat_last_modified')) || 0;

                    // اگر حافظه محلی کاملاً خالی است یا بکاپ ابری جدیدتر است
                    const isLocalEmpty = localStorage.length <= 2; // فقط کلید emarat_last_modified یا emarat_sync_counter باشد یا کلا خالی

                    if (isLocalEmpty || cloudBackup.timestamp > localTimestamp) {
                        console.log("Newer backup found! Restoring data...");
                        let changed = false;

                        Object.keys(cloudBackup.data).forEach(key => {
                            const val = cloudBackup.data[key];
                            if (localStorage.getItem(key) !== val) {
                                localStorage.setItem(key, val);
                                changed = true;
                            }
                        });

                        localStorage.setItem('emarat_last_modified', cloudBackup.timestamp);
                        hasPulled = true;

                        // اگر داده‌های جدیدی واقعاً اعمال شده‌اند، صفحه را ریلود می‌کنیم تا اپلیکیشن تغییرات را بلافاصله رندر کند
                        if (changed) {
                            console.log("Data restored successfully. Reloading UI...");
                            setTimeout(() => {
                                location.reload();
                            }, 500);
                        }
                    } else {
                        console.log("Local data is up to date.");
                        hasPulled = true;
                    }
                } else {
                    console.log("No valid backup data found on cloud.");
                    hasPulled = true;
                }
            } else {
                console.log("No backup exists yet on cloud (status: " + res.status + ").");
                hasPulled = true;
            }
        } catch (err) {
            console.error("Failed to pull backup from cloud:", err);
            hasPulled = true; // در صورت خطا هم اجازه بکاپ بدهد تا اتصال بعدی برقرار شود
        }
    }

    // ارسال نسخه پشتیبان به ابر در پس‌زمینه
    async function pushToCloud() {
        if (!hasPulled) return; // تا زمانی که چک کردن اولیه تمام نشده بکاپ نگیرد تا بکاپ ابری با داده خالی جایگزین نشود
        if (!navigator.onLine) return;

        // چک کنیم آیا داده معناداری برای بکاپ داریم یا کلا خالی است؟
        const keysToBackup = {};
        let hasRealData = false;

        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key !== 'emarat_last_modified' && key !== 'emarat_sync_counter') {
                // چک کردن برای کلیدهای مهم برنامه (ورزش، طلا، درصدها، چیدمان پرتال و سود)
                if (key.includes('workout') || key.includes('gold') || key.includes('portal') || key.includes('percent') || key.includes('trash') || key.includes('goal') || key.includes('kian_') || key.includes('percents') || key.includes('highlighted')) {
                    hasRealData = true;
                }
                keysToBackup[key] = localStorage.getItem(key);
            }
        }

        if (!hasRealData) {
            console.log("No real app data found to backup. Skipping push.");
            return;
        }

        const timestamp = Date.now();
        const payload = {
            timestamp: timestamp,
            data: keysToBackup
        };

        try {
            console.log("Backing up data to cloud in background...");
            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                console.log("Backup completed successfully!");
                localStorage.setItem('emarat_last_modified', timestamp.toString());
            }
        } catch (err) {
            console.error("Failed to push backup to cloud:", err);
        }
    }

    // تابع برای افزایش شمارنده ورود/خروج و چک کردن زمان سینک (هر ۳ بار)
    function incrementAndCheckSync() {
        let counter = parseInt(localStorage.getItem('emarat_sync_counter')) || 0;
        counter++;
        console.log("Session event detected. Current counter:", counter);
        if (counter >= 3) {
            console.log("Sync counter reached 3. Triggering cloud push...");
            pushToCloud();
            counter = 0;
        }
        localStorage.setItem('emarat_sync_counter', counter);
    }

    // اجرای اولین هماهنگ‌سازی زمان بالا آمدن صفحه و افزایش شمارشگر
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            pullFromCloud().then(() => {
                incrementAndCheckSync();
            });
        });
    } else {
        pullFromCloud().then(() => {
            incrementAndCheckSync();
        });
    }

    // بکاپ‌گیری اضطراری و افزایش شمارشگر هنگام خروج از صفحه یا بستن تب
    window.addEventListener('beforeunload', () => {
        incrementAndCheckSync();
    });

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            incrementAndCheckSync();
        }
    });

    // اکسپورت توابع به محیط گلوبال جهت فراخوانی دستی بعد از عملیات حساس
    window.EmaratCloudSync = {
        push: pushToCloud,
        pull: pullFromCloud
    };

})();
