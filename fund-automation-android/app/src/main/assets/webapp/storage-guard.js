/**
 * Emarat Storage Guard — لایهٔ ذخیرهٔ ایمن برای localStorage
 *
 * چرا لازم است: وقتی حافظهٔ مرورگر پر می‌شود، localStorage.setItem
 * استثنای QuotaExceededError می‌دهد و اگر گرفته نشود، ذخیره بی‌صدا
 * شکست می‌خورد؛ در حالی که کلیدهای دیگر همان batch با موفقیت نوشته
 * می‌شوند و داده نیمه‌کاره و ناسازگار باقی می‌ماند.
 *
 * استفاده:
 *   EmaratStorage.safeSet(key, value)
 *   EmaratStorage.safeSetBatch({ key1: v1, key2: v2 })   // اتمی
 *   EmaratStorage.migrate('old', 'new')
 */
(function () {
    'use strict';

    if (window.EmaratStorage) return;

    var TOAST_ID = 'emarat-storage-toast';
    var TOAST_MS = 7000;

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

    function usageBytes() {
        var total = 0;
        for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            var v = localStorage.getItem(k);
            total += (k ? k.length : 0) + (v ? v.length : 0);
        }
        return total * 2; // UTF-16
    }

    function usageMB() {
        return Math.round((usageBytes() / 1048576) * 100) / 100;
    }

    function biggestKeys(limit) {
        var rows = [];
        for (var i = 0; i < localStorage.length; i++) {
            var k = localStorage.key(i);
            var v = localStorage.getItem(k) || '';
            rows.push({ key: k, mb: Math.round((v.length * 2 / 1048576) * 100) / 100 });
        }
        rows.sort(function (a, b) { return b.mb - a.mb; });
        return rows.slice(0, limit || 8);
    }

    function toast(html, kind) {
        try {
            var el = document.getElementById(TOAST_ID);
            if (el) el.parentNode.removeChild(el);
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
        } catch (e) {
            /* اگر حتی toast هم نشد، سکوت بهتر از کرش است */
        }
    }

    function quotaMessage(failedKey, extra) {
        var top = biggestKeys(4)
            .filter(function (r) { return r.mb >= 0.05; })
            .map(function (r) { return '• ' + r.key + ' — ' + r.mb + ' مگابایت'; })
            .join('<br>');
        return (
            '⚠️ <b>حافظهٔ مرورگر پر است — این تغییر ذخیره نشد</b><br>' +
            'مصرف فعلی: <b>' + usageMB() + ' مگابایت</b>' +
            (failedKey ? ' · کلید: <code>' + failedKey + '</code>' : '') +
            (top ? '<br><br>بزرگ‌ترین بخش‌های حافظه:<br>' + top : '') +
            '<br><br>برای آزادسازی، از «جعبهٔ نجات» یا پاک‌کردن داده‌های اضافی استفاده کنید.' +
            (extra ? '<br><small>' + extra + '</small>' : '')
        );
    }

    /**
     * نوشتن یک کلید با گرفتن خطا. مقدار غیر رشته‌ای به JSON تبدیل نمی‌شود؛
     * فراخوان باید رشته بدهد (هم‌راستا با رفتار خود localStorage).
     */
    function safeSet(key, value) {
        try {
            localStorage.setItem(key, value);
            return { ok: true };
        } catch (err) {
            if (isQuotaError(err)) {
                toast(quotaMessage(key), 'err');
                return { ok: false, error: 'quota', key: key, message: String(err.message || err) };
            }
            toast('⚠️ خطای ذخیره‌سازی: ' + (err && err.name ? err.name : 'ناشناخته'), 'err');
            return { ok: false, error: 'other', key: key, message: String(err && err.message || err) };
        }
    }

    /**
     * نوشتن گروهی اتمی: یا همهٔ کلیدها ذخیره می‌شوند، یا هیچ‌کدام.
     * در صورت شکست، مقادیر قبلی کلیدهای نوشته‌شده بازگردانده می‌شوند تا
     * داده هرگز نیمه‌کاره نماند.
     */
    function safeSetBatch(map) {
        var keys = Object.keys(map || {});
        if (!keys.length) return { ok: true };

        var previous = {};
        for (var i = 0; i < keys.length; i++) {
            previous[keys[i]] = localStorage.getItem(keys[i]);
        }

        var written = [];
        for (var j = 0; j < keys.length; j++) {
            var k = keys[j];
            try {
                localStorage.setItem(k, map[k]);
                written.push(k);
            } catch (err) {
                for (var w = written.length - 1; w >= 0; w--) {
                    try {
                        if (previous[written[w]] === null) localStorage.removeItem(written[w]);
                        else localStorage.setItem(written[w], previous[written[w]]);
                    } catch (e) { /* بازگردانی بهترین تلاش است */ }
                }
                if (isQuotaError(err)) {
                    toast(quotaMessage(k), 'err');
                    return { ok: false, error: 'quota', key: k, rolledBack: written.length, message: String(err.message || err) };
                }
                toast('⚠️ خطای ذخیره‌سازی در «' + k + '»: ' + (err && err.name ? err.name : 'ناشناخته'), 'err');
                return { ok: false, error: 'other', key: k, rolledBack: written.length, message: String(err && err.message || err) };
            }
        }
        return { ok: true };
    }

    function safeRemove(key) {
        try {
            localStorage.removeItem(key);
            return { ok: true };
        } catch (err) {
            return { ok: false, error: 'other', key: key, message: String(err && err.message || err) };
        }
    }

    /**
     * مقدارهای «خالی‌نما» نباید مانع مهاجرت شوند. اگر اپ یک‌بار با وضعیت
     * خالی لود شده باشد (مثلاً beforeunload وضعیت درون‌حافظهٔ تهی را نوشته
     * باشد)، کلید جدید مقدار "[]" یا "{}" می‌گیرد و مقایسهٔ سادهٔ «پر بودن»
     * مهاجرت را برای همیشه بلاک می‌کند و دادهٔ قدیمی گم می‌شود.
     */
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

    /**
     * انتقال یک کلید قدیمی به کلید جدید، فقط اگر کلید جدید خالی باشد.
     * دادهٔ موجود در کلید جدید هرگز بازنویسی نمی‌شود.
     */
    function migrate(oldKey, newKey, opts) {
        opts = opts || {};
        try {
            var existing = localStorage.getItem(newKey);
            var targetHasData = existing !== null && !isEmptyish(existing);
            if (targetHasData && !opts.overwrite) {
                return { ok: true, skipped: true, reason: 'target-not-empty' };
            }
            var raw = localStorage.getItem(oldKey);
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

    /**
     * مهاجرت گروهی؛ هر جفت [oldKey, newKey] جداگانه بررسی می‌شود.
     */
    function migrateAll(pairs, opts) {
        var out = [];
        for (var i = 0; i < pairs.length; i++) {
            out.push({ pair: pairs[i], result: migrate(pairs[i][0], pairs[i][1], opts) });
        }
        return out;
    }

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

    /**
     * اگر مصرف از حد بحرانی گذشت، یک‌بار در هر نشست هشدار می‌دهد.
     * عمداً از setInterval استفاده نمی‌شود (قانون کارایی اسکرول).
     */
    function warnIfCritical() {
        try {
            if (sessionStorage.getItem('emarat_storage_warned') === '1') return;
            var h = health();
            if (!h.critical) return;
            sessionStorage.setItem('emarat_storage_warned', '1');
            toast(
                '⚠️ <b>حافظهٔ مرورگر تقریباً پر است</b><br>' +
                'مصرف: <b>' + h.usedMB + ' از ' + h.quotaMB + ' مگابایت</b> (' + h.percent + '٪)<br>' +
                'ممکن است ثبت‌های جدید ذخیره نشوند. با «جعبهٔ نجات» بکاپ بگیرید و داده‌های اضافی را پاک کنید.',
                'err'
            );
        } catch (e) { /* بی‌اثر */ }
    }

    window.EmaratStorage = {
        safeSet: safeSet,
        safeSetBatch: safeSetBatch,
        safeRemove: safeRemove,
        migrate: migrate,
        migrateAll: migrateAll,
        health: health,
        usageMB: usageMB,
        biggestKeys: biggestKeys,
        isQuotaError: isQuotaError,
        warnIfCritical: warnIfCritical,
        toast: toast
    };
})();
