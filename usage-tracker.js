/*!
 * ردیاب استفادهٔ عمارت — زمان و تعداد باز شدن هر اپ را می‌شمارد.
 *
 * استفاده: <script src="../usage-tracker.js" data-app="gold9"></script>
 * اگر data-app نباشد، نام از مسیر استخراج می‌شود.
 *
 * آمار روزانه جمع می‌شود (نه هر باز/بسته جداگانه) تا فایل بکاپ سبک بماند:
 *   { "gold9": { "2026-11-19": { "ms": 1820000, "opens": 4 } } }
 *
 * داخل iframe غیرفعال است تا دوبار شمرده نشود.
 * به localStorage کلیدهای دیگر هیچ دستی نمی‌زند.
 */
(function () {
  'use strict';

  if (window.top !== window.self) return;
  if (window.__emaratUsageMounted) return;
  window.__emaratUsageMounted = true;

  var STORE_KEY = 'emarat_usage_stats';
  var MIN_MS = 3000;
  var HEARTBEAT_MS = 15000;

  var script = document.currentScript;
  var appId = (script && script.getAttribute('data-app')) || '';

  function detectApp() {
    if (appId) return appId;
    var path = location.pathname.replace(/\/index\.html?$/, '/');
    var parts = path.split('/').filter(Boolean);
    if (!parts.length) return 'portal';
    var last = parts[parts.length - 1];
    if (last.indexOf('.') !== -1) {
      if (parts.length > 1) last = parts[parts.length - 2];
      else return 'portal';
    }
    return last || 'portal';
  }

  appId = detectApp();

  function todayKey() {
    var d = new Date();
    var m = d.getMonth() + 1;
    var day = d.getDate();
    return d.getFullYear() + '-' + (m < 10 ? '0' + m : m) + '-' + (day < 10 ? '0' + day : day);
  }

  function readStats() {
    try {
      var raw = localStorage.getItem(STORE_KEY);
      var parsed = raw ? JSON.parse(raw) : null;
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch (e) {
      return {};
    }
  }

  function writeStats(stats) {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(stats));
      return true;
    } catch (e) {
      return false;
    }
  }

  function bump(msDelta, openDelta) {
    var stats = readStats();
    var day = todayKey();
    if (!stats[appId]) stats[appId] = {};
    var rec = stats[appId][day] || { ms: 0, opens: 0 };
    rec.ms = Math.max(0, Math.round((rec.ms || 0) + msDelta));
    rec.opens = Math.max(0, (rec.opens || 0) + openDelta);
    stats[appId][day] = rec;
    writeStats(stats);
    return stats;
  }

  var sessionStart = Date.now();
  var flushed = 0;
  var closed = false;

  // بعضی اپ‌ها (مثل cloud-sync) خودشان صفحه را رفرش می‌کنند. آن رفرش یک
  // «باز شدن» تازه نیست، وگرنه هر بازدید دو بار شمرده می‌شود.
  var OPEN_DEDUPE_MS = 8000;
  var openKey = 'emr_usage_open_' + appId;
  var counted = false;
  try {
    var lastOpen = parseInt(sessionStorage.getItem(openKey), 10) || 0;
    if (!lastOpen || Date.now() - lastOpen > OPEN_DEDUPE_MS) counted = true;
    sessionStorage.setItem(openKey, String(Date.now()));
  } catch (e) {
    counted = true;
  }
  if (counted) bump(0, 1);

  function flush() {
    if (closed) return;
    var elapsed = Date.now() - sessionStart - flushed;
    if (elapsed <= 0) return;
    flushed += elapsed;
    if (elapsed < MIN_MS) return;
    bump(elapsed, 0);
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') {
      flush();
      sessionStart = Date.now();
      flushed = 0;
    } else {
      sessionStart = Date.now();
      flushed = 0;
    }
  });

  window.addEventListener('pagehide', flush);
  window.addEventListener('beforeunload', flush);
  setInterval(function () {
    if (document.visibilityState === 'visible') flush();
  }, HEARTBEAT_MS);

  // ---------- بکاپ خودکار گیت‌هاب (ادغام دوطرفه، هرگز جایگزینی کور) ----------
  var BACKUP_FILE = 'usage/usage_backup.json';
  var LAST_UP_KEY = 'emarat_usage_last_upload';
  var MIN_GAP_MS = 10 * 60 * 1000;
  var syncTimer = null;

  function mergeStats(a, b) {
    var out = {};
    [a, b].forEach(function (src) {
      if (!src || typeof src !== 'object') return;
      Object.keys(src).forEach(function (app) {
        if (!out[app]) out[app] = {};
        Object.keys(src[app] || {}).forEach(function (day) {
          var cur = out[app][day] || { ms: 0, opens: 0 };
          var inc = src[app][day] || {};
          out[app][day] = {
            ms: Math.max(cur.ms || 0, inc.ms || 0),
            opens: Math.max(cur.opens || 0, inc.opens || 0)
          };
        });
      });
    });
    return out;
  }

  function ghConfig() {
    return {
      token: localStorage.getItem('github_backup_token') || '',
      repo: localStorage.getItem('github_backup_repo') || '',
      branch: localStorage.getItem('github_backup_branch') || 'main',
      path: localStorage.getItem('github_backup_filepath') || BACKUP_FILE
    };
  }

  function b64(str) {
    return btoa(unescape(encodeURIComponent(str)));
  }

  function uploadUsageToGitHub() {
    var cfg = ghConfig();
    if (!cfg.token || !cfg.repo) return Promise.resolve({ success: false, message: 'تنظیمات گیت‌هاب کامل نیست.' });

    var path = cfg.path;
    if (window.EmaratBackupPath) {
      path = window.EmaratBackupPath.build('usage', new Date(), 'usage_backup');
    } else if (path.endsWith('/')) {
      path += 'usage_backup.json';
    }
    var url = 'https://api.github.com/repos/' + cfg.repo + '/contents/' + path;
    var headers = { Authorization: 'token ' + cfg.token, Accept: 'application/vnd.github.v3+json' };
    var local = readStats();
    var sha = null;

    return fetch(url + '?ref=' + encodeURIComponent(cfg.branch), { headers: headers, cache: 'no-store' })
      .then(function (res) {
        if (res.status !== 200) return null;
        return res.json();
      })
      .then(function (info) {
        var remote = {};
        if (info && info.content) {
          sha = info.sha;
          try {
            remote = JSON.parse(decodeURIComponent(escape(atob(info.content.replace(/\s/g, ''))))) || {};
          } catch (e) { remote = {}; }
        }
        var merged = mergeStats(remote, local);
        var body = {
          message: 'بکاپ آمار استفاده — ' + new Date().toLocaleString('fa-IR'),
          content: b64(JSON.stringify(merged, null, 2)),
          branch: cfg.branch
        };
        if (sha) body.sha = sha;
        return fetch(url, {
          method: 'PUT',
          headers: Object.assign({}, headers, { 'Content-Type': 'application/json' }),
          body: JSON.stringify(body)
        });
      })
      .then(function (res) {
        return res && res.ok ? { success: true } : { success: false, message: 'خطا در آپلود' };
      })
      .catch(function (err) {
        return { success: false, message: err.message };
      });
  }

  function scheduleBackup() {
    var cfg = ghConfig();
    if (!cfg.token || !cfg.repo) return;
    // هر باز شدن صفحه یک «باز شدن» تازه ثبت می‌کند؛ اگر هر بار آپلود کنیم،
    // مخزن با کامیت‌های بی‌مورد پر می‌شود. پس حداقل ۱۰ دقیقه فاصله می‌گذاریم.
    var last = parseInt(localStorage.getItem(LAST_UP_KEY), 10) || 0;
    if (Date.now() - last < MIN_GAP_MS) return;
    if (syncTimer) clearTimeout(syncTimer);
    syncTimer = setTimeout(function () {
      if (navigator.onLine === false) return;
      uploadUsageToGitHub().then(function (res) {
        if (res && res.success) localStorage.setItem(LAST_UP_KEY, String(Date.now()));
      });
    }, 15000);
  }

  var rawBump = bump;
  bump = function (msDelta, openDelta) {
    var stats = rawBump(msDelta, openDelta);
    scheduleBackup();
    return stats;
  };

  window.EmaratUsage = {
    appId: appId,
    read: readStats,
    write: writeStats,
    flush: flush,
    key: STORE_KEY,
    merge: mergeStats,
    uploadToGitHub: uploadUsageToGitHub
  };
})();
