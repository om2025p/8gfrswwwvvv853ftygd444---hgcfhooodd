/*!
 * اسکرول محترم برای اپ‌های چت عمارت.
 *
 * مشکل: در حین استریم پاسخ، هر توکن اسکرول اجباری به پایین می‌داد و کاربر
 * نمی‌توانست متن قبلی را بخواند.
 *
 * رفتار: تا وقتی کاربر در «کف» صفحه است، اسکرول خودکار انجام می‌شود. به‌محض
 * اینکه کاربر خودش رو به بالا اسکرول کند، اسکرول خودکار خاموش می‌شود و فقط
 * با برگشت به کف (یا دکمهٔ «پیام جدید») دوباره روشن می‌شود.
 *
 * استفاده:
 *   EmaratAutoScroll.attach(document.getElementById('chatViewport'));
 *   EmaratAutoScroll.toBottom();          // اسکرول محترم
 *   EmaratAutoScroll.toBottom(true);      // اسکرول اجباری (ارسال پیام خود کاربر)
 */
(function () {
  'use strict';

  if (window.__emaratAutoScrollLoaded) return;
  window.__emaratAutoScrollLoaded = true;

  var NEAR_BOTTOM_PX = 80;
  var RELEASE_PX = 140;
  var BTN_ID = 'emr-scroll-down';
  var STYLE_ID = 'emr-scroll-down-styles';

  var vp = null;
  var btn = null;
  var userScrolledAway = false;
  var rafPending = false;
  var touchStartY = null;
  var streaming = false;

  var CSS = [
    '#' + BTN_ID + '{position:absolute;left:50%;transform:translateX(-50%) translateY(14px);',
    'bottom:var(--emr-rb-offset,16px);z-index:40;display:flex;align-items:center;gap:7px;',
    'min-height:44px;padding:9px 16px;border:1px solid var(--border,#2a3f5a);border-radius:999px;',
    'background:var(--card-bg,#12263d);color:var(--text-head,#e8eef7);',
    'font:600 0.82rem/1.2 inherit;cursor:pointer;opacity:0;pointer-events:none;',
    'transition:opacity .22s ease,transform .22s ease;',
    'box-shadow:0 8px 24px rgba(0,0,0,.42);-webkit-tap-highlight-color:transparent}',
    '#' + BTN_ID + '.show{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0)}',
    '#' + BTN_ID + ' .cnt{background:var(--primary,#38bdf8);color:#04121f;',
    'border-radius:999px;padding:2px 7px;font-size:.72rem;font-weight:800}',
    '@media (prefers-reduced-motion:reduce){#' + BTN_ID + '{transition:none}}',
    // در حین استریم، انیمیشن smooth فقط کشمکش می‌سازد؛ اسکرول باید فوری باشد
    '.emr-streaming{scroll-behavior:auto !important}'
  ].join('');

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var st = document.createElement('style');
    st.id = STYLE_ID;
    st.textContent = CSS;
    (document.head || document.documentElement).appendChild(st);
  }

  function isNearBottom() {
    if (!vp) return true;
    var gap = vp.scrollHeight - vp.scrollTop - vp.clientHeight;
    return gap <= NEAR_BOTTOM_PX;
  }

  function showBtn(on, count) {
    if (!btn) return;
    if (on) placeBtn();
    btn.classList.toggle('show', Boolean(on));
    var c = btn.querySelector('.cnt');
    if (!c) return;
    if (count && count > 0) {
      c.textContent = String(count).replace(/\d/g, function (d) {
        return '۰۱۲۳۴۵۶۷۸۹'[+d];
      });
      c.hidden = false;
    } else {
      c.hidden = true;
    }
  }

  /**
   * دکمه باید درست بالای نوار ارسال بنشیند، نه روی آن.
   * ارتفاع composer از پایین ظرف تا بالای آن اندازه‌گیری می‌شود.
   */
  function placeBtn() {
    if (!btn || !vp) return;
    var host = vp.parentElement;
    if (!host) return;
    var hostRect = host.getBoundingClientRect();
    var offset = 16;
    // اولین خواهر/برادر بعد از ظرف گفتگو که پایین صفحه است (نوار ارسال)
    var sib = vp.nextElementSibling;
    while (sib) {
      var sr = sib.getBoundingClientRect();
      if (sr.height > 0 && sr.height < hostRect.height * 0.7) {
        offset = Math.round(hostRect.bottom - sr.top) + 10;
        break;
      }
      sib = sib.nextElementSibling;
    }
    btn.style.setProperty('--emr-rb-offset', offset + 'px');
  }

  function buildBtn() {
    if (btn || !vp) return;
    var host = vp.parentElement;
    if (!host) return;
    if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
    btn = document.createElement('button');
    btn.id = BTN_ID;
    btn.type = 'button';
    btn.setAttribute('aria-label', 'رفتن به آخرین پیام');
    btn.innerHTML = '<span>⬇️</span><span>پیام جدید</span><span class="cnt" hidden></span>';
    btn.addEventListener('click', function () {
      toBottom(true);
      showBtn(false);
    });
    host.appendChild(btn);
  }

  function flush() {
    rafPending = false;
    if (!vp) return;
    vp.scrollTop = vp.scrollHeight;
  }

  /**
   * اسکرول به پایین.
   * @param {boolean} [force] اگر true باشد، حتی اگر کاربر بالا رفته هم اسکرول می‌کند.
   */
  function toBottom(force) {
    if (!vp) return;
    if (!force && userScrolledAway) {
      showBtn(true);
      return;
    }
    if (force) {
      userScrolledAway = false;
      showBtn(false);
    }
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(flush);
  }

  function onScroll() {
    if (!vp) return;
    var gap = vp.scrollHeight - vp.scrollTop - vp.clientHeight;
    if (gap <= NEAR_BOTTOM_PX) {
      userScrolledAway = false;
      showBtn(false);
    } else if (gap > RELEASE_PX) {
      userScrolledAway = true;
      if (streaming) showBtn(true);
    }
  }

  /**
   * @param {HTMLElement} el ظرف اسکرول‌شوندهٔ گفتگو
   */
  function attach(el) {
    if (!el || el === vp) return;
    vp = el;
    injectStyle();
    buildBtn();
    vp.addEventListener('scroll', onScroll, { passive: true });

    vp.addEventListener(
      'wheel',
      function (e) {
        if (e.deltaY < 0 && !isNearBottom()) {
          userScrolledAway = true;
          if (streaming) showBtn(true);
        }
      },
      { passive: true }
    );

    vp.addEventListener(
      'touchstart',
      function (e) {
        touchStartY = e.touches && e.touches[0] ? e.touches[0].clientY : null;
      },
      { passive: true }
    );

    vp.addEventListener(
      'touchmove',
      function (e) {
        if (touchStartY === null || !e.touches || !e.touches[0]) return;
        var dy = e.touches[0].clientY - touchStartY;
        if (dy > 6 && !isNearBottom()) {
          userScrolledAway = true;
          if (streaming) showBtn(true);
        }
      },
      { passive: true }
    );

    vp.addEventListener('touchend', function () { touchStartY = null; }, { passive: true });
    window.addEventListener('resize', function () { if (btn) placeBtn(); }, { passive: true });
  }

  /** هنگام شروع استریم: حالت پایین‌بودن را تازه کن */
  function beginStream() {
    streaming = true;
    if (vp) vp.classList.add('emr-streaming');
    if (isNearBottom()) {
      userScrolledAway = false;
      showBtn(false);
    }
  }

  function endStream() {
    streaming = false;
    if (vp) vp.classList.remove('emr-streaming');
    if (!userScrolledAway) showBtn(false);
  }

  window.EmaratAutoScroll = {
    attach: attach,
    toBottom: toBottom,
    beginStream: beginStream,
    endStream: endStream,
    isNearBottom: isNearBottom,
    isUserAway: function () { return userScrolledAway; },
    _setAway: function (v) { userScrolledAway = Boolean(v); showBtn(Boolean(v)); }
  };
})();
