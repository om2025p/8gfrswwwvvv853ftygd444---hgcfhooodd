/*!
 * دکمهٔ «به‌روزرسانی» عمارت — نیم‌شفاف، پایین‌وسط، با هاور پدیدار می‌شود.
 *
 * کاری که می‌کند: کش سرویس‌ورکر و فایل‌های کهنه را پاک می‌کند و صفحه را
 * با نسخهٔ تازهٔ سایت دوباره بالا می‌آورد. به localStorage/IndexedDB
 * دست نمی‌زند، پس درصدها و تاریخچه سالم می‌مانند.
 *
 * استفاده: <script src="../refresh-button.js"></script>
 * داخل iframe خودکار غیرفعال می‌شود تا دکمه دوبار نیاید.
 */
(function () {
  'use strict';

  if (window.top !== window.self) return;
  if (window.__emaratRefreshMounted) return;
  window.__emaratRefreshMounted = true;

  var SELF_SRC = (document.currentScript && document.currentScript.src) || '';
  var SW_URL = SELF_SRC ? new URL('sw.js', SELF_SRC).href : null;

  var STYLE_ID = 'emr-rb-styles';
  var CSS = [
    '.emr-rb{position:fixed;left:50%;bottom:0;transform:translateX(-50%);z-index:2147483000;',
    'display:flex;flex-direction:column;align-items:center;pointer-events:none;',
    'font-family:Tahoma,"Segoe UI",sans-serif;padding-bottom:env(safe-area-inset-bottom,0)}',
    '.emr-rb-btn{pointer-events:auto;cursor:pointer;opacity:.20;',
    'transform:translateY(7px) scale(.95);transition:opacity .22s ease,transform .22s ease,background .22s ease;',
    'background:rgba(18,24,38,.82);color:#dbeafe;border:1px solid rgba(255,255,255,.20);',
    'border-radius:999px;padding:6px 13px;font-size:.66rem;font-weight:700;line-height:1;',
    'white-space:nowrap;margin-bottom:7px;box-shadow:0 4px 14px rgba(0,0,0,.28);',
    'backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);user-select:none}',
    '.emr-rb:hover .emr-rb-btn,.emr-rb.show .emr-rb-btn,.emr-rb-btn:focus-visible{',
    'opacity:1;transform:translateY(0) scale(1);background:rgba(26,34,52,.95)}',
    '.emr-rb-btn.busy{opacity:1;transform:translateY(0) scale(1);cursor:progress;',
    'color:#ffe9a8;border-color:rgba(255,214,102,.55)}',
    '.emr-rb-btn.confirm{opacity:1;transform:translateY(0) scale(1);cursor:pointer;',
    'color:#ffd9a8;border-color:rgba(255,178,122,.7);background:rgba(74,44,12,.92)}',
    '.emr-rb-zone{pointer-events:auto;width:132px;height:26px;cursor:pointer}',
    '.emr-rb.lifted{bottom:74px}'
  ].join('');

  function el(tag, cls) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    return n;
  }

  function mount() {
    if (document.getElementById('emr-rb-root')) return;

    if (!document.getElementById(STYLE_ID)) {
      var style = document.createElement('style');
      style.id = STYLE_ID;
      style.textContent = CSS;
      document.head.appendChild(style);
    }

    var root = el('div', 'emr-rb');
    root.id = 'emr-rb-root';

    var btn = el('button', 'emr-rb-btn');
    btn.type = 'button';
    btn.textContent = '🔄 به‌روزرسانی';
    btn.title = 'دریافت نسخهٔ تازهٔ سایت';

    var zone = el('div', 'emr-rb-zone');
    zone.setAttribute('aria-hidden', 'true');

    root.appendChild(btn);
    root.appendChild(zone);
    document.body.appendChild(root);

    var version = '';
    var confirmTimer = null;
    var busy = false;
    var pending = false;

    function label(text) {
      btn.textContent = text;
    }

    function idleLabel() {
      return version ? '🔄 به‌روزرسانی · ' + version : '🔄 به‌روزرسانی';
    }

    function showVersion() {
      if (!SW_URL) return;
      fetch(SW_URL, { cache: 'no-store' })
        .then(function (r) { return r.ok ? r.text() : ''; })
        .then(function (txt) {
          var m = txt && txt.match(/CACHE_NAME\s*=\s*['"]([^'"]+)['"]/);
          if (!m) return;
          version = (m[1].match(/v\d+$/) || [m[1]])[0];
          if (!busy && !pending) label(idleLabel());
        })
        .catch(function () {});
    }

    function resetConfirm() {
      if (confirmTimer) { clearTimeout(confirmTimer); confirmTimer = null; }
      pending = false;
      btn.classList.remove('confirm');
      label(idleLabel());
    }

    function hardRefresh() {
      if (busy) return;
      busy = true;
      btn.classList.remove('confirm');
      btn.classList.add('busy');
      label('⏳ در حال به‌روزرسانی…');

      var jobs = [];

      try {
        if (window.caches && caches.keys) {
          jobs.push(caches.keys().then(function (keys) {
            return Promise.all(keys.map(function (k) { return caches.delete(k); }));
          }));
        }
      } catch (e) {}

      try {
        if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
          jobs.push(navigator.serviceWorker.getRegistrations().then(function (regs) {
            return Promise.all(regs.map(function (r) { return r.unregister(); }));
          }));
        }
      } catch (e) {}

      Promise.all(jobs).catch(function () {}).then(function () {
        var u = new URL(location.href);
        u.searchParams.set('_r', String(Date.now()));
        location.replace(u.href);
      });
    }

    btn.addEventListener('click', function () {
      if (busy) return;

      if (!pending) {
        if (navigator.onLine === false) {
          label('📡 اینترنت قطع است');
          setTimeout(resetConfirm, 2200);
          return;
        }
        pending = true;
        btn.classList.add('confirm');
        label('⚠️ مطمئنی؟ دوباره بزن');
        confirmTimer = setTimeout(resetConfirm, 3500);
        return;
      }

      if (confirmTimer) { clearTimeout(confirmTimer); confirmTimer = null; }
      hardRefresh();
    });

    zone.addEventListener('click', function () {
      root.classList.add('show');
      setTimeout(function () { root.classList.remove('show'); }, 4000);
    });

    // اگر دکمه روی یک کنترل (نوار تایپ چت، دکمهٔ پایین صفحه و…) بیفتد، خودش بالا می‌رود.
    var CONTROLS = 'textarea,input,button,select,[contenteditable="true"]';

    function collides() {
      var r = btn.getBoundingClientRect();
      if (!r.width || !r.height) return false;
      var pad = 6;
      var nodes = document.querySelectorAll(CONTROLS);
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        if (root.contains(n)) continue;
        var b = n.getBoundingClientRect();
        if (b.width < 24 || b.height < 16) continue;
        var st = getComputedStyle(n);
        if (st.visibility === 'hidden' || st.display === 'none' || st.opacity === '0') continue;
        if (b.left < r.right + pad && b.right > r.left - pad &&
            b.top < r.bottom + pad && b.bottom > r.top - pad) return true;
      }
      return false;
    }

    function adjustPosition() {
      root.classList.remove('lifted');
      if (collides()) root.classList.add('lifted');
    }

    var adjustTimer = null;
    function scheduleAdjust() {
      if (adjustTimer) clearTimeout(adjustTimer);
      adjustTimer = setTimeout(adjustPosition, 120);
    }

    window.addEventListener('resize', scheduleAdjust);
    window.addEventListener('orientationchange', scheduleAdjust);
    document.addEventListener('transitionend', scheduleAdjust, true);
    setTimeout(adjustPosition, 60);
    setTimeout(adjustPosition, 900);
    setTimeout(adjustPosition, 2400);

    showVersion();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
