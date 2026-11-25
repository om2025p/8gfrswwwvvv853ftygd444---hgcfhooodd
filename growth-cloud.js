/* بکاپ ابری تب «مدیریت رشد» — محافظ ضد گم‌شدن داده
   ------------------------------------------------------------------
   چرا این فایل ساخته شد: جدول تب چهارم در IndexedDB (GrowthDB_*) است و
   هیچ بکاپی نداشت. با پاک شدن دادهٔ سایت، درصدها از گیت‌هاب برمی‌گشتند
   ولی رشد برای همیشه می‌رفت.

   قواعد امنیتی (تغییرناپذیر):
   ۱. هیچ ردیفی از نسخهٔ ابری حذف نمی‌شود؛ ادغام همیشه «اجتماع» است.
   ۲. اگر خواندن ابری شکست بخورد، آپلود انجام نمی‌شود (تا ابر پاک نشود).
   ۳. اگر محلی خالی باشد و ابر پر، محلی از ابر پر می‌شود — نه برعکس.
   ۴. توکن فقط از localStorage خوانده می‌شود (بدون hardcode).
*/
(function () {
  'use strict';
  if (window.__EmaratGrowthCloudLoaded) return;
  window.__EmaratGrowthCloudLoaded = true;

  var APP = (document.currentScript && document.currentScript.dataset && document.currentScript.dataset.app) || '';
  if (!APP) return;

  var PATH = 'growth/' + APP + '_growth_backup.json';
  var DEBOUNCE_MS = 4000;
  var LAST_KEY = 'emarat_growth_last_upload_' + APP;

  var timer = null;
  var busy = false;
  var pending = false;

  function cfg() {
    return {
      token: localStorage.getItem('github_backup_token') || '',
      repo: localStorage.getItem('github_backup_repo') || '',
      branch: localStorage.getItem('github_backup_branch') || 'main'
    };
  }
  function configured() { var c = cfg(); return !!(c.token && c.repo); }

  function b64enc(s) { return btoa(unescape(encodeURIComponent(s))); }
  function b64dec(s) { return decodeURIComponent(escape(atob(String(s).replace(/\s/g, '')))); }

  function isBlank(r) {
    return !r || (!r.unitPrice && !r.amount && !r.date && !r.quantity && !r.desc && !r.note);
  }
  function keyOf(r) {
    if (r && r.id) return 'id:' + r.id;
    return 'h:' + [r && r.date, r && r.unitPrice, r && r.amount, r && r.quantity].join('|');
  }

  function merge(remote, local) {
    var map = new Map();
    function add(r) { if (!isBlank(r)) map.set(keyOf(r), r); }
    ((remote && remote.rows) || []).forEach(add);
    ((local && local.rows) || []).forEach(add);
    return {
      app: APP,
      version: 1,
      updatedAt: new Date().toISOString(),
      capital: (local && local.capital) || (remote && remote.capital) || '',
      rows: Array.from(map.values())
    };
  }
  function signature(o) { return JSON.stringify({ rows: (o && o.rows) || [], capital: (o && o.capital) || '' }); }

  async function readLocal() {
    var rows = [], capital = '';
    try { if (typeof getAllRows === 'function') rows = (await getAllRows()) || []; } catch (e) {}
    try { if (typeof loadCapital === 'function') capital = (await loadCapital()) || ''; } catch (e) {}
    return { rows: rows.filter(function (r) { return !isBlank(r); }), capital: capital };
  }

  async function fetchRemote() {
    var c = cfg();
    if (!c.token || !c.repo) return { ok: false, reason: 'no-config' };
    var url = 'https://api.github.com/repos/' + c.repo + '/contents/' + PATH + '?ref=' + c.branch;
    try {
      var res = await fetch(url, {
        headers: { Authorization: 'token ' + c.token, Accept: 'application/vnd.github.v3+json' },
        cache: 'no-store'
      });
      if (res.status === 404) return { ok: true, exists: false, sha: null, data: null };
      if (!res.ok) return { ok: false, reason: 'http-' + res.status };
      var j = await res.json();
      var parsed = null;
      try { parsed = JSON.parse(b64dec(j.content || '')); } catch (e) { return { ok: false, reason: 'bad-json' }; }
      return { ok: true, exists: true, sha: j.sha, data: parsed };
    } catch (e) {
      return { ok: false, reason: 'network' };
    }
  }

  async function putRemote(text, sha, message) {
    var c = cfg();
    var url = 'https://api.github.com/repos/' + c.repo + '/contents/' + PATH;
    var body = { message: message, content: b64enc(text), branch: c.branch };
    if (sha) body.sha = sha;
    try {
      var res = await fetch(url, {
        method: 'PUT',
        headers: { Authorization: 'token ' + c.token, Accept: 'application/vnd.github.v3+json', 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      return res.ok;
    } catch (e) {
      return false;
    }
  }

  async function pushNow(opts) {
    opts = opts || {};
    if (!configured()) {
      if (opts.manual) toast('⚙️ توکن و مخزن گیت‌هاب تنظیم نشده است', 'warn');
      return false;
    }
    if (busy) { pending = true; return false; }
    busy = true;
    try {
      var local = await readLocal();
      var rem = await fetchRemote();
      if (!rem.ok) {
        if (opts.manual) toast('📡 خواندن بکاپ ابری ممکن نشد (' + rem.reason + ') — چیزی آپلود نشد', 'warn');
        return false;
      }
      var merged = merge(rem.data, local);
      if (rem.data && signature(rem.data) === signature(merged) && !opts.force) {
        if (opts.manual) toast('☁️ بکاپ ابری به‌روز است (' + merged.rows.length + ' ردیف)', 'ok');
        return true;
      }
      var ok = await putRemote(JSON.stringify(merged, null, 2), rem.sha,
        'بکاپ رشد ' + APP + ' — ' + new Date().toLocaleString('fa-IR'));
      if (ok) {
        localStorage.setItem(LAST_KEY, String(Date.now()));
        if (opts.manual) toast('☁️ ' + merged.rows.length + ' ردیف در گیت‌هاب ذخیره شد', 'ok');
      } else if (opts.manual) {
        toast('❌ آپلود نشد (خطای گیت‌هاب)', 'warn');
      }
      return ok;
    } finally {
      busy = false;
      if (pending) { pending = false; setTimeout(function () { pushNow({}); }, 1500); }
    }
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(function () { pushNow({}); }, DEBOUNCE_MS);
  }

  async function importRows(rows) {
    var clean = (rows || []).filter(function (r) { return !isBlank(r); });
    if (!clean.length) return 0;
    try {
      if (typeof db !== 'undefined' && db && db.objectStoreNames.contains('rows')) {
        await new Promise(function (resolve, reject) {
          var tx = db.transaction('rows', 'readwrite');
          var st = tx.objectStore('rows');
          st.clear();
          clean.forEach(function (r) { st.put(r); });
          tx.oncomplete = resolve;
          tx.onerror = function () { reject(tx.error); };
        });
        return clean.length;
      }
    } catch (e) {}
    if (typeof clearAllRows === 'function') { try { await clearAllRows(); } catch (e) {} }
    for (var i = 0; i < clean.length; i++) {
      if (typeof addRowToDB === 'function') { try { await addRowToDB(clean[i]); } catch (e) {} }
    }
    return clean.length;
  }

  async function pullNow(opts) {
    opts = opts || {};
    if (!configured()) {
      if (opts.manual) toast('⚙️ توکن و مخزن گیت‌هاب تنظیم نشده است', 'warn');
      return false;
    }
    var rem = await fetchRemote();
    if (!rem.ok) { if (opts.manual) toast('📡 خواندن بکاپ ابری ممکن نشد (' + rem.reason + ')', 'warn'); return false; }
    if (!rem.data || !(rem.data.rows || []).length) {
      if (opts.manual) toast('☁️ بکاپ ابری خالی است', 'warn');
      return false;
    }
    var local = await readLocal();
    if (local.rows.length > 0 && !opts.force) {
      if (opts.manual) toast('ℹ️ دادهٔ محلی موجود است — بازنویسی انجام نشد', 'warn');
      return false;
    }
    var n = await importRows(rem.data.rows);
    if (!n) return false;
    if (rem.data.capital && typeof saveCapital === 'function') {
      try { await saveCapital(rem.data.capital); } catch (e) {}
    }
    toast('⬇️ ' + n + ' ردیف از بکاپ ابری بازگردانده شد', 'ok');
    setTimeout(function () { location.reload(); }, 900);
    return true;
  }

  function toast(msg, kind) {
    try {
      var el = document.getElementById('__growthCloudToast');
      if (!el) {
        el = document.createElement('div');
        el.id = '__growthCloudToast';
        el.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:24px;z-index:2147483000;' +
          'padding:10px 16px;border-radius:12px;font:13px/1.6 Vazirmatn,Tahoma,sans-serif;color:#fff;' +
          'max-width:86vw;text-align:center;box-shadow:0 6px 22px rgba(0,0,0,.45);transition:opacity .25s';
        document.body.appendChild(el);
      }
      el.textContent = msg;
      el.style.background = kind === 'ok' ? '#2f7d32' : (kind === 'warn' ? '#8c2b20' : '#3a3a3a');
      el.style.opacity = '1';
      clearTimeout(el._t);
      el._t = setTimeout(function () { el.style.opacity = '0'; }, 3200);
    } catch (e) {}
  }

  function addMenuItems() {
    var menu = document.getElementById('dropdownMenu');
    if (!menu || menu.querySelector('[data-growth-cloud]')) return;
    var b1 = document.createElement('button');
    b1.className = 'dropdown-item';
    b1.type = 'button';
    b1.setAttribute('data-growth-cloud', 'push');
    b1.textContent = '☁️ بکاپ ابری فوری';
    b1.addEventListener('click', function () { pushNow({ manual: true, force: true }); });
    var b2 = document.createElement('button');
    b2.className = 'dropdown-item';
    b2.type = 'button';
    b2.setAttribute('data-growth-cloud', 'pull');
    b2.textContent = '⬇️ بازیابی از بکاپ ابری';
    b2.addEventListener('click', function () {
      if (confirm('دادهٔ محلی با بکاپ ابری جایگزین شود؟\n(اگر دادهٔ محلی دارید، ابتدا بکاپ بگیرید)')) {
        pullNow({ manual: true, force: true });
      }
    });
    menu.appendChild(b1);
    menu.appendChild(b2);
  }

  function wrapWriters() {
    ['updateRowInDB', 'addRowToDB', 'deleteRowFromDB', 'clearAllRows', 'saveCapital'].forEach(function (name) {
      var orig = window[name];
      if (typeof orig !== 'function' || orig.__cloudWrapped) return;
      var wrapped = function () {
        var out = orig.apply(this, arguments);
        Promise.resolve(out).then(schedule, schedule);
        return out;
      };
      wrapped.__cloudWrapped = true;
      try { window[name] = wrapped; } catch (e) {}
    });
  }

  function wrapRestoreGuard() {
    var orig = window.restoreData;
    if (typeof orig !== 'function' || orig.__guardWrapped) return;
    var wrapped = async function (file) {
      try {
        var text = await file.text();
        var data = JSON.parse(text);
        var tag = String(data && data.app || '');
        if (tag && tag !== 'GrowthDB_' + APP && tag !== 'GrowthDB') {
          var other = tag.replace('GrowthDB_', '');
          if (!confirm('⚠️ این فایل بکاپ «' + other + '» است، نه «' + APP + '».\n' +
            'بازیابی، جدول فعلی را پاک می‌کند. ادامه می‌دهید؟')) {
            return;
          }
        }
      } catch (e) {}
      var out = await orig.call(this, file);
      schedule();
      return out;
    };
    wrapped.__guardWrapped = true;
    try { window.restoreData = wrapped; } catch (e) {}
  }

  function boot() {
    addMenuItems();
    wrapWriters();
    wrapRestoreGuard();
    // اگر محلی خالی و ابری پر است، خودکار بازگردان (هدف: هرگز گم نشود)
    if (configured()) {
      setTimeout(function () { pullNow({}); }, 1200);
      setTimeout(function () { schedule(); }, 2500);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.EmaratGrowthCloud = {
    app: APP,
    path: PATH,
    push: function () { return pushNow({ manual: true, force: true }); },
    pull: function () { return pullNow({ manual: true, force: true }); },
    schedule: schedule,
    _internal: { merge: merge, keyOf: keyOf, isBlank: isBlank, signature: signature }
  };
})();
