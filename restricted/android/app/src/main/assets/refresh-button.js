/*!
 * دکمهٔ «به‌روزرسانی» عمارت — از زیر لبهٔ صفحه بیرون می‌آید.
 *
 * رفتار: دکمه کاملاً زیر صفحه پنهان است و با اسکرول جابه‌جا نمی‌شود
 * (position:fixed). وقتی کاربر در کف صفحه یک اسکرول اضافه به پایین بزند،
 * دکمه از زیر لبه سُر می‌خورد بالا و چند ثانیه بعد خودش برمی‌گردد.
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
    '.emr-rb{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;',
    'display:flex;justify-content:center;align-items:flex-end;pointer-events:none;',
    'padding-bottom:calc(6px + env(safe-area-inset-bottom,0px));',
    'transform:translate3d(0,110%,0);',
    'transition:transform .32s cubic-bezier(.22,.9,.3,1);will-change:transform}',
    '.emr-rb.open{transform:translate3d(0,0,0)}',
    '.emr-rb-btn{pointer-events:auto;cursor:pointer;opacity:.92;',
    'background:rgba(18,24,38,.94);color:#dbeafe;border:1px solid rgba(255,255,255,.22);',
    'border-radius:999px;padding:8px 15px;font-size:.68rem;font-weight:700;line-height:1;',
    'white-space:nowrap;box-shadow:0 6px 20px rgba(0,0,0,.4);',
    'backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);user-select:none;',
    'font-family:Tahoma,"Segoe UI",sans-serif;transition:opacity .18s,background .18s,transform .18s}',
    '.emr-rb-btn:hover,.emr-rb-btn:focus-visible{opacity:1;background:rgba(26,34,52,.98);transform:translateY(-1px)}',
    '.emr-rb-btn.busy{cursor:progress;color:#ffe9a8;border-color:rgba(255,214,102,.55)}',
    '.emr-rb-btn.confirm{color:#ffd9a8;border-color:rgba(255,178,122,.7);background:rgba(74,44,12,.95)}',
    '.emr-rb:not(.open) .emr-rb-btn{box-shadow:none;backdrop-filter:none;-webkit-backdrop-filter:none}'
  ].join('');

  function el(tag, cls) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    return n;
  }

  var REVEAL_MS = 5000;

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

    root.appendChild(btn);
    document.body.appendChild(root);

    var version = '';
    var confirmTimer = null;
    var hideTimer = null;
    var busy = false;
    var pending = false;

    function label(text) {
      btn.textContent = text;
    }

    function idleLabel() {
      return version ? '🔄 به‌روزرسانی · ' + version : '🔄 به‌روزرسانی';
    }

    // ---------- نمایش / پنهان‌سازی ----------
    function show() {
      root.classList.add('open');
      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(function () {
        if (!busy && !pending) root.classList.remove('open');
      }, REVEAL_MS);
    }

    function hide() {
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      root.classList.remove('open');
    }

    // ---------- تشخیص «کف صفحه» ----------
    function scrollRoot() {
      return document.scrollingElement || document.documentElement;
    }

    function isDocRoot(n) {
      return n === scrollRoot() || n === document.documentElement || n === document.body;
    }

    function canScroll(n) {
      if (!n) return false;
      if (isDocRoot(n)) {
        return document.documentElement.scrollHeight - window.innerHeight > 4;
      }
      return n.scrollHeight - n.clientHeight > 4;
    }

    function atBottom(n) {
      if (!n) return true;
      if (isDocRoot(n)) {
        var vh = window.innerHeight || document.documentElement.clientHeight;
        return window.scrollY + vh >= document.documentElement.scrollHeight - 3;
      }
      return n.scrollTop + n.clientHeight >= n.scrollHeight - 3;
    }

    // نزدیک‌ترین ظرف اسکرول‌شونده به عنصر زیر اشاره‌گر
    function scrollableFrom(target) {
      var n = target && target.nodeType === 1 ? target : null;
      while (n && n !== document.body && n !== document.documentElement) {
        var st = window.getComputedStyle(n);
        if (/(auto|scroll|overlay)/.test(st.overflowY) && canScroll(n)) return n;
        n = n.parentElement;
      }
      return scrollRoot();
    }

    // ---------- باز کردن با اسکرول اضافه در کف ----------
    var bottomHits = 0;

    function tryReveal(target, direction) {
      if (direction !== 'down') { bottomHits = 0; return; }
      var sc = scrollableFrom(target);

      if (!canScroll(sc)) {
        // صفحه اصلاً اسکرول ندارد: هر اسکرول رو به پایین دکمه را بیرون می‌آورد
        show();
        return;
      }
      if (atBottom(sc)) {
        bottomHits++;
        if (bottomHits >= 2) show();
      } else {
        bottomHits = 0;
      }
    }

    window.addEventListener('wheel', function (e) {
      tryReveal(e.target, e.deltaY > 0 ? 'down' : 'up');
    }, { passive: true });

    var touchY = null;

    window.addEventListener('touchstart', function (e) {
      touchY = e.touches && e.touches[0] ? e.touches[0].clientY : null;
      bottomHits = 0;
    }, { passive: true });

    window.addEventListener('touchmove', function (e) {
      if (touchY === null || !e.touches || !e.touches[0]) return;
      var y = e.touches[0].clientY;
      var dy = touchY - y;            // مثبت = انگشت به بالا (اسکرول به پایین)
      touchY = y;
      if (Math.abs(dy) < 2) return;
      var t = e.target;
      if (!t || t.nodeType !== 1) {
        t = document.elementFromPoint(e.touches[0].clientX, e.touches[0].clientY);
      }
      tryReveal(t, dy > 0 ? 'down' : 'up');
    }, { passive: true });

    window.addEventListener('touchend', function () {
      touchY = null;
      bottomHits = 0;
    }, { passive: true });

    window.addEventListener('scroll', function () {
      if (!root.classList.contains('open')) bottomHits = 0;
    }, { passive: true });

    // ---------- صفحاتی که محتوا را داخل iframe نشان می‌دهند ----------
    // مثل gold9: صفحهٔ بیرونی اسکرول ندارد و همهٔ اسکرول داخل iframe رخ می‌دهد.
    // پس همان شنود را داخل iframe‌های هم‌دامنه هم نصب می‌کنیم و اگر آن‌ها به کف
    // رسیدند، به همین صفحه پیام می‌دهند.
    var boundFrames = [];

    var IFRAME_HOOK = [
      '(function(){',
      'if(window.__emrRbHook)return;window.__emrRbHook=1;',
      'var hits=0;',
      'function atBot(){var d=document.documentElement;',
      'return (window.scrollY||window.pageYOffset||0)+window.innerHeight>=d.scrollHeight-3}',
      'function canSc(){return document.documentElement.scrollHeight-window.innerHeight>4}',
      'function send(){try{parent.postMessage({__emrRb:1},"*")}catch(e){}}',
      'function onDown(){',
      '  if(!canSc()){send();return}',
      '  if(atBot()){hits++;if(hits>=2)send()}else{hits=0}',
      '}',
      'window.addEventListener("wheel",function(e){',
      '  if(e.deltaY>0)onDown();else hits=0;',
      '},{passive:true});',
      'var ty=null;',
      'window.addEventListener("touchstart",function(e){',
      '  ty=e.touches&&e.touches[0]?e.touches[0].clientY:null;hits=0;',
      '},{passive:true});',
      'window.addEventListener("touchmove",function(e){',
      '  if(ty===null||!e.touches||!e.touches[0])return;',
      '  var y=e.touches[0].clientY,dy=ty-y;ty=y;',
      '  if(Math.abs(dy)<2)return;',
      '  if(dy>0)onDown();else hits=0;',
      '},{passive:true});',
      'window.addEventListener("touchend",function(){ty=null;hits=0},{passive:true});',
      '})();'
    ].join('\n');

    function bindFrames() {
      var frames = document.querySelectorAll('iframe');
      for (var i = 0; i < frames.length; i++) {
        var f = frames[i];
        if (boundFrames.indexOf(f) !== -1) continue;
        boundFrames.push(f);
        try {
          var d = f.contentDocument;
          if (!d || !d.documentElement) continue;
          var s = d.createElement('script');
          s.textContent = IFRAME_HOOK;
          d.documentElement.appendChild(s);
        } catch (e) {}
      }
    }

    window.addEventListener('message', function (e) {
      if (e.data && e.data.__emrRb === 1) show();
    }, false);

    bindFrames();
    setTimeout(bindFrames, 1200);
    setTimeout(bindFrames, 3000);
    setInterval(bindFrames, 4000);

    // ---------- نسخه ----------
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

    // ---------- دو مرحله‌ای ----------
    function resetConfirm() {
      if (confirmTimer) { clearTimeout(confirmTimer); confirmTimer = null; }
      pending = false;
      btn.classList.remove('confirm');
      label(idleLabel());
      if (root.classList.contains('open')) show();
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
      show();

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

    window.addEventListener('resize', function () {
      if (root.classList.contains('open')) show();
    });

    showVersion();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
