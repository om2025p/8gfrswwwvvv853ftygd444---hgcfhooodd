/* دکمهٔ پاک کردن کش نمادها — کش را از localStorage و آینهٔ IndexedDB
   پاک می‌کند، ولی به داده‌های ذخیره‌شده (نمادها، درصدها، تنظیمات) دست نمی‌زند. */
(function () {
    'use strict';

    var CACHE_KEY = 'symbolsCache';
    var STORE_DB = 'emarat_power_store';
    var STORE = 'kv';

    function cacheBytes() {
        try { return (localStorage.getItem(CACHE_KEY) || '').length; } catch (e) { return 0; }
    }

    /* storage-guard فقط localStorage را پاک می‌کند؛ اگر آینه بماند،
       shadowHeal همان کش را برمی‌گرداند. */
    function shadowDelete(key) {
        return new Promise(function (resolve) {
            try {
                if (!window.indexedDB) return resolve(false);
                var req = indexedDB.open(STORE_DB, 1);
                req.onupgradeneeded = function (e) {
                    var db = e.target.result;
                    if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
                };
                req.onsuccess = function (e) {
                    var db = e.target.result;
                    try {
                        if (!db.objectStoreNames.contains(STORE)) { db.close(); return resolve(false); }
                        var tx = db.transaction(STORE, 'readwrite');
                        tx.objectStore(STORE).delete(key);
                        tx.oncomplete = function () { db.close(); resolve(true); };
                        tx.onerror = function () { db.close(); resolve(false); };
                    } catch (err) { db.close(); resolve(false); }
                };
                req.onerror = function () { resolve(false); };
            } catch (e) { resolve(false); }
        });
    }

    function clear() {
        var before = cacheBytes();
        if (!before) {
            alert('کشی برای پاک کردن نیست.');
            return Promise.resolve(0);
        }
        var mb = (before / 1048576).toFixed(1);
        var ok = confirm('کش نمادها ' + mb + ' مگابایت است.\nپاک شود؟\n\n' +
            'داده‌های ذخیره‌شده، درصدها و نمادهای انتخابی دست نمی‌خورند.');
        if (!ok) return Promise.resolve(0);

        try { localStorage.removeItem(CACHE_KEY); } catch (e) {}

        return shadowDelete(CACHE_KEY).then(function () {
            var freed = Math.max(0, before - cacheBytes());
            alert('✅ کش پاک شد — ' + (freed / 1048576).toFixed(2) + ' مگابایت آزاد شد.\n' +
                '(با اولین باز شدن صفحهٔ رشد، از نو ساخته می‌شود.)');
            return freed;
        });
    }

    window.LiquidityCache = { clear: clear, size: cacheBytes };

    document.addEventListener('click', function (e) {
        var el = e.target && e.target.closest ? e.target.closest('[data-clear-cache]') : null;
        if (!el) return;
        e.preventDefault();
        if (el.disabled) return;
        el.disabled = true;
        clear().then(function () { el.disabled = false; });
    });
})();
