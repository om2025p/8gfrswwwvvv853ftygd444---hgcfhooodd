/**
 * Emarat Storage Guard v2 — لایهٔ ذخیرهٔ ایمن + حافظهٔ قدرتمند مرورگر
 *
 * دو مشکل را حل می‌کند:
 *
 * ۱) سهمیهٔ localStorage فقط حدود ۱۰ مگابایت است و بین همهٔ اپ‌های یک
 *    origin مشترک است. وقتی پر شود، setItem استثنا می‌دهد و اگر گرفته
 *    نشود ذخیره بی‌صدا شکست می‌خورد.
 *
 * ۲) اپ‌هایی که یک کلید را می‌خوانند و اپ دیگری نامش را عوض کرده، کور
 *    می‌شوند (رگرسیون مهاجرت کلید gold).
 *
 * راه‌حل:
 *   • هر نوشتن در localStorage به‌طور خودکار در IndexedDB آینه می‌شود
 *     (حافظهٔ قدرتمند: سهمیه‌اش صدها مگابایت تا چند گیگابایت است).
 *   • اگر localStorage پر باشد، داده در IndexedDB می‌ماند و در بارگذاری
 *     بعدی خودکار به localStorage برگردانده می‌شود.
 *   • آینهٔ کلید: هر نوشتن روی کلید اصلی، کلید سازگاری قدیمی را هم
 *     به‌روز می‌کند تا خواننده‌های قدیمی کور نشوند.
 *
 * API:
 *   EmaratStorage.safeSet(key, value)
 *   EmaratStorage.safeSetBatch({ k1: v1, k2: v2 })
 *   EmaratStorage.migrate(oldKey, newKey)
 *   EmaratStorage.registerMirror(masterKey, mirrorKey)
 *   EmaratStorage.healMirrors()
 *   EmaratStorage.health()          // وضعیت localStorage
 *   EmaratStorage.power()           // وضعیت حافظهٔ قدرتمند
 *   EmaratStorage.shadowHeal()      // بازیابی از IndexedDB
 */
(function () {
    'use strict';

    if (window.EmaratStorage && window.EmaratStorage.__v >= 2) return;

    var TOAST_ID = 'emarat-storage-toast';
    var TOAST_MS = 7000;

    var DB_NAME = 'emarat_power_store';
    var DB_VER = 1;
    var STORE = 'kv';

    var nativeSetItem = null;
    var nativeGetItem = null;
    var nativeRemoveItem = null;
    try {
        nativeSetItem = Storage.prototype.setItem;
        nativeGetItem = Storage.prototype.getItem;
        nativeRemoveItem = Storage.prototype.removeItem;
    } catch (e) { /* بی‌اثر */ }

    function rawSet(k, v) {
        if (nativeSetItem) nativeSetItem.call(localStorage, k, v);
        else localStorage.setItem(k, v);
    }
    function rawGet(k) {
        if (nativeGetItem) return nativeGetItem.call(localStorage, k);
        return localStorage.getItem(k);
    }
    function rawRemove(k) {
        if (nativeRemoveItem) nativeRemoveItem.call(localStorage, k);
        else localStorage.removeItem(k);
    }

    function isQuotaError(err) {
        if (!err) return false;
        return (
            err.name === 'QuotaExceededError' ||
            err.name === 'NS_ERROR_DOM_QUOTA_REACHED' ||
            err.code === 22 ||
            err.code === 1014 ||
            /quota/i.test(String(err.message || ''))
        );
    }

    /* ------------------------------------------------------------------ */
    /*  حافظهٔ قدرتمند — IndexedDB                                         */
    /* ------------------------------------------------------------------ */

    var _db = null;
    var _dbFailed = false;

    function openDB() {
        if (_db) return Promise.resolve(_db);
        if (_dbFailed) return Promise.resolve(null);
        return new Promise(function (resolve) {
            try {
                if (!window.indexedDB) { _dbFailed = true; return resolve(null); }
                var req = indexedDB.open(DB_NAME, DB_VER);
                req.onupgradeneeded = function (e) {
                    var db = e.target.result;
                    if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE);
                };
                req.onsuccess = function (e) { _db = e.target.result; resolve(_db); };
                req.onerror = function () { _dbFailed = true; resolve(null); };
                req.onblocked = function () { _dbFailed = true; resolve(null); };
            } catch (e) {
                _dbFailed = true;
                resolve(null);
            }
        });
    }

    /**
     * هر مقدار با مهر زمانی ذخیره می‌شود تا هنگام بازیابی بتوانیم تشخیص
     * دهیم کدام نسخه تازه‌تر است. بدون این، سایهٔ قدیمی روی دادهٔ تازه
     * می‌نشیند و همان باگ «چهار ماه عقب» را می‌سازد.
     */
    function shadowPut(key, value) {
        openDB().then(function (db) {
            if (!db) return;
            try {
                var tx = db.transaction(STORE, 'readwrite');
                tx.objectStore(STORE).put({ v: String(value), t: Date.now() }, String(key));
            } catch (e) { /* بی‌اثر */ }
        }).catch(function () {});
    }

    function shadowPutMany(map) {
        openDB().then(function (db) {
            if (!db) return;
            try {
                var tx = db.transaction(STORE, 'readwrite');
                var os = tx.objectStore(STORE);
                var now = Date.now();
                Object.keys(map || {}).forEach(function (k) {
                    os.put({ v: String(map[k]), t: now }, String(k));
                });
            } catch (e) { /* بی‌اثر */ }
        }).catch(function () {});
    }

    function unwrapShadow(row) {
        if (row === null || row === undefined) return null;
        if (typeof row === 'object' && row !== null && 'v' in row) {
            return { value: row.v, at: row.t || 0 };
        }
        // سازگاری با نسخهٔ ۱ که رشتهٔ خام ذخیره می‌کرد
        return { value: String(row), at: 0 };
    }

    function shadowGet(key) {
        return openDB().then(function (db) {
            if (!db) return null;
            return new Promise(function (resolve) {
                try {
                    var tx = db.transaction(STORE, 'readonly');
                    var r = tx.objectStore(STORE).get(String(key));
                    r.onsuccess = function () {
                        var u = unwrapShadow(r.result === undefined ? null : r.result);
                        resolve(u ? u.value : null);
                    };
                    r.onerror = function () { resolve(null); };
                } catch (e) { resolve(null); }
            });
        }).catch(function () { return null; });
    }

    function shadowAll() {
        return openDB().then(function (db) {
            if (!db) return {};
            return new Promise(function (resolve) {
                try {
                    var tx = db.transaction(STORE, 'readonly');
                    var os = tx.objectStore(STORE);
                    var out = {};
                    var keys = null, vals = null;
                    function done() {
                        if (keys && vals) {
                            for (var i = 0; i < keys.length; i++) out[keys[i]] = vals[i];
                            resolve(out);
                        }
                    }
                    var kr = os.getAllKeys();
                    var vr = os.getAll();
                    kr.onsuccess = function () { keys = kr.result; done(); };
                    vr.onsuccess = function () { vals = vr.result; done(); };
                    kr.onerror = function () { resolve({}); };
                    vr.onerror = function () { resolve({}); };
                } catch (e) { resolve({}); }
            });
        }).catch(function () { return {}; });
    }

    function shadowCount() {
        return openDB().then(function (db) {
            if (!db) return 0;
            return new Promise(function (resolve) {
                try {
                    var tx = db.transaction(STORE, 'readonly');
                    var r = tx.objectStore(STORE).count();
                    r.onsuccess = function () { resolve(r.result || 0); };
                    r.onerror = function () { resolve(0); };
                } catch (e) { resolve(0); }
            });
        }).catch(function () { return 0; });
    }

    /* ------------------------------------------------------------------ */
    /*  اندازه‌گیری و پیام                                                */
    /* ------------------------------------------------------------------ */

    function usageBytes() {
        var total = 0;
        for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            var v = rawGet(k);
            total += (k ? k.length : 0) + (v ? v.length : 0);
        }
        return total * 2;
    }

    function usageMB() {
        return Math.round((usageBytes() / 1048576) * 100) / 100;
    }

    function biggestKeys(limit) {
        var rows = [];
        for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            var v = rawGet(k) || '';
            rows.push({ key: k, mb: Math.round((v.length * 2 / 1048576) * 100) / 100 });
        }
        rows.sort(function (a, b) { return b.mb - a.mb; });
        return rows.slice(0, limit || 8);
    }

    function toast(html, kind) {
        try {
            var el = document.getElementById(TOAST_ID);
            if (el && el.parentNode) el.parentNode.removeChild(el);
            el = document.createElement('div');
            el.id = TOAST_ID;
            el.setAttribute('dir', 'rtl');
            el.style.cssText = [
                'position:fixed', 'z-index:2147483001',
                'left:12px', 'right:12px', 'bottom:12px',
                'max-width:560px', 'margin:0 auto',
                'padding:14px 16px', 'border-radius:14px',
                'font-family:inherit', 'font-size:14px', 'line-height:1.9',
                'color:#fff', 'text-align:right',
                'box-shadow:0 10px 34px rgba(0,0,0,.45)',
                'background:' + (kind === 'ok' ? '#1f6b3a' : '#8c2b20'),
                'border:1px solid ' + (kind === 'ok' ? '#2f9e57' : '#c0392b')
            ].join(';');
            el.innerHTML = html;
            document.body.appendChild(el);
            setTimeout(function () {
                if (el && el.parentNode) el.parentNode.removeChild(el);
            }, TOAST_MS);
        } catch (e) { /* سکوت بهتر از کرش */ }
    }

    function quotaMessage(failedKey, extra) {
        var top = biggestKeys(4)
            .filter(function (r) { return r.mb >= 0.05; })
            .map(function (r) { return '• ' + r.key + ' — ' + r.mb + ' مگابایت'; })
            .join('<br>');
        return (
            '⚠️ <b>حافظهٔ معمولی پر است — ولی داده از دست نرفت</b><br>' +
            'این تغییر در <b>حافظهٔ قدرتمند</b> (IndexedDB) ذخیره شد و در بارگذاری بعدی برمی‌گردد.<br>' +
            'مصرف فعلی: <b>' + usageMB() + ' مگابایت</b>' +
            (failedKey ? ' · کلید: <code>' + failedKey + '</code>' : '') +
            (top ? '<br><br>بزرگ‌ترین بخش‌های حافظه:<br>' + top : '') +
            (extra ? '<br><small>' + extra + '</small>' : '')
        );
    }

    /* ------------------------------------------------------------------ */
    /*  نوشتن ایمن                                                         */
    /* ------------------------------------------------------------------ */

    function safeSet(key, value) {
        try {
            rawSet(key, value);
            shadowPut(key, value);
            return { ok: true };
        } catch (err) {
            shadowPut(key, value);
            if (isQuotaError(err)) {
                if (!safeSet._warned) {
                    safeSet._warned = true;
                    toast(quotaMessage(key), 'err');
                }
                return { ok: false, error: 'quota', key: key, inShadow: true, message: String(err.message || err) };
            }
            toast('⚠️ خطای ذخیره‌سازی: ' + (err && err.name ? err.name : 'ناشناخته'), 'err');
            return { ok: false, error: 'other', key: key, inShadow: true, message: String(err && err.message || err) };
        }
    }

    function safeSetBatch(map) {
        var keys = Object.keys(map || {});
        if (!keys.length) return { ok: true };

        var previous = {};
        for (var i = 0; i < keys.length; i++) previous[keys[i]] = rawGet(keys[i]);

        var written = [];
        for (var j = 0; j < keys.length; j++) {
            var k = keys[j];
            try {
                rawSet(k, map[k]);
                written.push(k);
            } catch (err) {
                for (var w = written.length - 1; w >= 0; w--) {
                    try {
                        if (previous[written[w]] === null) rawRemove(written[w]);
                        else rawSet(written[w], previous[written[w]]);
                    } catch (e) { /* بازگردانی بهترین تلاش */ }
                }
                shadowPutMany(map);
                if (isQuotaError(err)) {
                    if (!safeSetBatch._warned) {
                        safeSetBatch._warned = true;
                        toast(quotaMessage(k), 'err');
                    }
                    return { ok: false, error: 'quota', key: k, rolledBack: written.length, inShadow: true, message: String(err.message || err) };
                }
                toast('⚠️ خطای ذخیره‌سازی در «' + k + '»: ' + (err && err.name ? err.name : 'ناشناخته'), 'err');
                return { ok: false, error: 'other', key: k, rolledBack: written.length, inShadow: true, message: String(err && err.message || err) };
            }
        }
        shadowPutMany(map);
        return { ok: true };
    }

    function safeRemove(key) {
        try {
            rawRemove(key);
            return { ok: true };
        } catch (err) {
            return { ok: false, error: 'other', key: key, message: String(err && err.message || err) };
        }
    }

    function isEmptyish(raw) {
        if (raw === null || raw === undefined) return true;
        var t = String(raw).trim();
        if (t === '' || t === 'null' || t === 'undefined' || t === '[]' || t === '{}' || t === '""') return true;
        try {
            var v = JSON.parse(t);
            if (v === null) return true;
            if (Array.isArray(v)) return v.length === 0;
            if (typeof v === 'object') return Object.keys(v).length === 0;
        } catch (e) { /* مقدار غیر JSON را پر در نظر بگیر */ }
        return false;
    }

    function migrate(oldKey, newKey, opts) {
        opts = opts || {};
        try {
            var existing = rawGet(newKey);
            var targetHasData = existing !== null && !isEmptyish(existing);
            if (targetHasData && !opts.overwrite) {
                return { ok: true, skipped: true, reason: 'target-not-empty' };
            }
            var raw = rawGet(oldKey);
            if (raw === null) return { ok: true, skipped: true, reason: 'source-missing' };
            if (isEmptyish(raw)) return { ok: true, skipped: true, reason: 'source-empty' };

            var value = raw;
            if (typeof opts.transform === 'function') {
                value = opts.transform(raw);
                if (value === null || value === undefined) {
                    return { ok: false, error: 'transform', key: oldKey };
                }
            }

            var res = safeSet(newKey, value);
            if (!res.ok) return res;
            if (!opts.keepOld) safeRemove(oldKey);
            return { ok: true, migrated: true, bytes: value.length };
        } catch (err) {
            return { ok: false, error: 'other', key: oldKey, message: String(err && err.message || err) };
        }
    }

    function migrateAll(pairs, opts) {
        var out = [];
        for (var i = 0; i < pairs.length; i++) {
            out.push({ pair: pairs[i], result: migrate(pairs[i][0], pairs[i][1], opts) });
        }
        return out;
    }

    /* ------------------------------------------------------------------ */
    /*  آینهٔ کلید — سازگاری بین نام قدیم و جدید                            */
    /* ------------------------------------------------------------------ */

    var MIRRORS = {};

    /**
     * اعلام می‌کند کلید masterKey مرجع است و mirrorKey باید همیشه با آن
     * هم‌ارز بماند. خواننده‌های قدیمی که mirrorKey را می‌خوانند کور نمی‌شوند.
     */
    function registerMirror(masterKey, mirrorKey) {
        if (!masterKey || !mirrorKey || masterKey === mirrorKey) return;
        if (!MIRRORS[masterKey]) MIRRORS[masterKey] = [];
        if (MIRRORS[masterKey].indexOf(mirrorKey) === -1) MIRRORS[masterKey].push(mirrorKey);
    }

    function mirrorsOf(key) {
        return MIRRORS[key] || [];
    }

    /**
     * نوشتن روی کلید اصلی + همهٔ آینه‌هایش.
     */
    function setWithMirrors(masterKey, value) {
        var res = safeSet(masterKey, value);
        if (!res.ok) return res;
        var ms = mirrorsOf(masterKey);
        for (var i = 0; i < ms.length; i++) safeSet(ms[i], value);
        return res;
    }

    function batchWithMirrors(map) {
        var full = {};
        Object.keys(map).forEach(function (k) {
            full[k] = map[k];
            var ms = mirrorsOf(k);
            for (var i = 0; i < ms.length; i++) full[ms[i]] = map[k];
        });
        return safeSetBatch(full);
    }

    /**
     * اگر یک طرف آینه خالی و طرف دیگر پر است، خالی را پر می‌کند.
     * هرگز دادهٔ موجود را بازنویسی نمی‌کند.
     */
    function healMirrors() {
        var healed = [];
        Object.keys(MIRRORS).forEach(function (master) {
            var mRaw = rawGet(master);
            var masterEmpty = mRaw === null || isEmptyish(mRaw);
            MIRRORS[master].forEach(function (mirror) {
                var kRaw = rawGet(mirror);
                var mirrorEmpty = kRaw === null || isEmptyish(kRaw);
                if (masterEmpty && !mirrorEmpty) {
                    if (safeSet(master, kRaw).ok) healed.push(master + ' ← ' + mirror);
                } else if (!masterEmpty && mirrorEmpty) {
                    if (safeSet(mirror, mRaw).ok) healed.push(mirror + ' ← ' + master);
                }
            });
        });
        return healed;
    }

    /* ------------------------------------------------------------------ */
    /*  بازیابی از حافظهٔ قدرتمند                                          */
    /* ------------------------------------------------------------------ */

    /**
     * بازگردانی از سایه فقط وقتی که localStorage خالی باشد. چون هر نوشتن
     * محلی سایه را به‌روز می‌کند، سایه هرگز از localStorage عقب‌تر نیست؛
     * ولی اگر خالی بودن موقتی باشد (اپ تازه لود شده و هنوز ننوشته)،
     * سایه همان آخرین وضعیت معتبر است.
     */
    function shadowHeal(opts) {
        opts = opts || {};
        return shadowAll().then(function (all) {
            var healed = [], skipped = [];
            Object.keys(all).forEach(function (k) {
                if (opts.only && opts.only.indexOf(k) === -1) return;
                var u = unwrapShadow(all[k]);
                if (!u) return;
                // سایهٔ خالی چیزی برای بازگرداندن ندارد
                if (isEmptyish(u.value)) return;
                var local = null;
                try { local = rawGet(k); } catch (e) { return; }
                // فقط کلیدِ کاملاً غایب بازگردانده می‌شود. کلید موجود ولی
                // خالی («[]») نشانهٔ وضعیت واقعی اپ است و نباید دست بخورد.
                if (local === null) {
                    var res = safeSet(k, u.value);
                    if (res.ok) healed.push(k);
                    else skipped.push(k);
                }
            });
            return { healed: healed, skipped: skipped };
        });
    }

    function power() {
        return shadowCount().then(function (n) {
            return {
                engine: 'IndexedDB',
                dbName: DB_NAME,
                keys: n,
                available: n > 0 || !!_db,
                localStorageMB: usageMB()
            };
        });
    }

    /* ------------------------------------------------------------------ */
    /*  وضعیت سلامت                                                       */
    /* ------------------------------------------------------------------ */

    function health() {
        var used = usageMB();
        var ratio = used / 9.92;
        return {
            usedMB: used,
            quotaMB: 9.92,
            percent: Math.round(ratio * 100),
            critical: ratio >= 0.9,
            warning: ratio >= 0.75,
            biggest: biggestKeys(10)
        };
    }

    function warnIfCritical() {
        try {
            if (sessionStorage.getItem('emarat_storage_warned') === '1') return;
            var h = health();
            if (!h.critical) return;
            sessionStorage.setItem('emarat_storage_warned', '1');
            toast(
                '⚠️ <b>حافظهٔ معمولی تقریباً پر است</b><br>' +
                'مصرف: <b>' + h.usedMB + ' از ' + h.quotaMB + ' مگابایت</b> (' + h.percent + '٪)<br>' +
                'داده‌های جدید در حافظهٔ قدرتمند ذخیره می‌شوند و از دست نمی‌روند، ' +
                'ولی برای آزادسازی با «جعبهٔ نجات» بکاپ بگیرید.',
                'err'
            );
        } catch (e) { /* بی‌اثر */ }
    }

    /* ------------------------------------------------------------------ */
    /*  هوک سراسری: هر نوشتن در localStorage در IndexedDB آینه می‌شود      */
    /* ------------------------------------------------------------------ */

    function installWriteHook() {
        if (installWriteHook._done) return;
        installWriteHook._done = true;
        try {
            localStorage.setItem = function (k, v) {
                try {
                    rawSet(k, v);
                    shadowPut(k, v);
                } catch (err) {
                    shadowPut(k, v);
                    if (isQuotaError(err)) {
                        if (!installWriteHook._warned) {
                            installWriteHook._warned = true;
                            toast(quotaMessage(k), 'err');
                        }
                        return; // داده در حافظهٔ قدرتمند محفوظ است
                    }
                    throw err;
                }
            };
        } catch (e) { /* بعضی مرورگرها اجازهٔ بازنویسی نمی‌دهند */ }
    }

    /**
     * اگر localStorage خالی شده ولی IndexedDB داده دارد، یک‌بار بازگردانی
     * می‌کند و صفحه را تازه می‌کند تا اپ داده را ببیند.
     */
    /**
     * بازگردانی خودکار در بارگذاری. فقط کلیدهایی که کاملاً غایب‌اند برمی‌گردند
     * و رفرش فقط وقتی رخ می‌دهد که واقعاً داده‌ای نجات یافته باشد — وگرنه
     * هر بازدید یک رفرش بی‌دلیل می‌گرفت.
     */
    function autoHealOnLoad() {
        try {
            if (sessionStorage.getItem('emarat_heal_done') === '1') return;
            sessionStorage.setItem('emarat_heal_done', '1');
        } catch (e) { return; }
        shadowHeal().then(function (r) {
            if (!r.healed.length) return;
            toast(
                '♻️ <b>داده‌ها از حافظهٔ قدرتمند بازیابی شد</b><br>' +
                r.healed.length + ' کلید بازگردانده شد. صفحه به‌روزرسانی می‌شود…',
                'ok'
            );
            setTimeout(function () { try { location.reload(); } catch (e) {} }, 2000);
        }).catch(function () {});
    }

    window.EmaratStorage = {
        __v: 2,
        safeSet: safeSet,
        safeSetBatch: safeSetBatch,
        safeRemove: safeRemove,
        migrate: migrate,
        migrateAll: migrateAll,
        registerMirror: registerMirror,
        mirrorsOf: mirrorsOf,
        setWithMirrors: setWithMirrors,
        batchWithMirrors: batchWithMirrors,
        healMirrors: healMirrors,
        shadowPut: shadowPut,
        shadowPutMany: shadowPutMany,
        shadowGet: shadowGet,
        shadowAll: shadowAll,
        shadowHeal: shadowHeal,
        shadowCount: shadowCount,
        power: power,
        health: health,
        usageMB: usageMB,
        biggestKeys: biggestKeys,
        isQuotaError: isQuotaError,
        isEmptyish: isEmptyish,
        warnIfCritical: warnIfCritical,
        toast: toast,
        autoHealOnLoad: autoHealOnLoad
    };

    installWriteHook();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            autoHealOnLoad();
            warnIfCritical();
        });
    } else {
        autoHealOnLoad();
        warnIfCritical();
    }
})();
