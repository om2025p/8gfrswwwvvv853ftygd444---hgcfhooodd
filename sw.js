const CACHE_NAME = 'emarat-portal-v106';
const ASSETS = [
  './tree-samples/m1.html',
  './tree-samples/m2.html',
  './tree-samples/m3.html',
  './tree-samples/m4.html',
  './tree-samples/m5.html',
  './tree-samples/m6.html',
  './tree-samples/shared.js',

  './',
  './index.html',
  './manifest.json',
  './cloud-sync.js',
  './storage-guard.js',
  './refresh-button.js',
  './price-import.js',
  './usage-tracker.js',
  // Usage App
  './usage/index.html',
  './usage/manifest.json',
  './usage/icon-192.png',
  './usage/icon-512.png',
  './usage/icon-192-maskable.png',
  './usage/icon-512-maskable.png',
  './usage/apple-touch-icon.png',
  './usage/favicon.ico',
  // Rescue App (full backup tool)
  './rescue/index.html',
  './rescue/manifest.json',
  './rescue/icon-192.png',
  './rescue/icon-512.png',
  './rescue/icon-192-maskable.png',
  './rescue/icon-512-maskable.png',
  './rescue/apple-touch-icon.png',
  './rescue/favicon.ico',
  './icon-192.png',
  './icon-512.png',
  './icon-192-maskable.png',
  './icon-512-maskable.png',
  './apple-touch-icon.png',
  './favicon.ico',
  // Detective App
  './detective/index.html',
  './detective/manifest.json',
  './detective/icon-192.png',
  './detective/icon-512.png',
  './detective/icon-192-maskable.png',
  './detective/icon-512-maskable.png',
  './detective/favicon.ico',
  // Monitor App
  './monitor/index.html',
  './monitor/assets/monitor-update-celebration.svg',
  './monitor/manifest.json',
  './monitor/icon-192.png',
  './monitor/icon-512.png',
  './monitor/icon-192-maskable.png',
  './monitor/icon-512-maskable.png',
  // Gym App
  './gym/index.html',
  './gym/manifest.json',
  './gym/icon-192.png',
  './gym/icon-512.png',
  './gym/icon-192-maskable.png',
  './gym/icon-512-maskable.png',
  './gym/apple-touch-icon.png',
  './gym/favicon.ico',
  // Gold App
  './gold/index.html',
  './gold/calculator.html',
  './gold/percent.html',
  './gold/growth.html',
  './gold/manifest.json',
  './gold/icon-192.png',
  './gold/icon-512.png',
  './gold/icon-192-maskable.png',
  './gold/icon-512-maskable.png',
  './gold/apple-touch-icon.png',
  './gold/favicon.ico',
  // Gold 2 App
  './gold2/index.html',
  './gold2/calculator.html',
  './gold2/percent.html',
  './gold2/manifest.json',
  './gold2/icon-192.png',
  './gold2/icon-512.png',
  './gold2/icon-192-maskable.png',
  './gold2/icon-512-maskable.png',
  './gold2/apple-touch-icon.png',
  './gold2/favicon.ico',
  // Gold 3 App
  './gold3/index.html',
  './gold3/calculator.html',
  './gold3/percent.html',
  './gold3/price.html',
  './gold3/growth.html',
  './gold3/manifest.json',
  './gold3/icon-192.png',
  './gold3/icon-512.png',
  './gold3/icon-192-maskable.png',
  './gold3/icon-512-maskable.png',
  './gold3/apple-touch-icon.png',
  './gold3/favicon.ico',
  // Gold 4 App
  './gold4/index.html',
  './gold4/calculator.html',
  './gold4/percent.html',
  './gold4/manifest.json',
  './gold4/icon-192.png',
  './gold4/icon-512.png',
  './gold4/icon-192-maskable.png',
  './gold4/icon-512-maskable.png',
  './gold4/apple-touch-icon.png',
  './gold4/favicon.ico',
  // Gold 5 App
  './gold5/index.html',
  './gold5/calculator.html',
  './gold5/percent.html',
  './gold5/price.html',
  './gold5/growth.html',
  './gold5/manifest.json',
  './gold5/icon-192.png',
  './gold5/icon-512.png',
  './gold5/icon-192-maskable.png',
  './gold5/icon-512-maskable.png',
  './gold5/apple-touch-icon.png',
  './gold5/favicon.ico',
  // Gold 6 App (Cement Kian)
  './gold6/index.html',
  './gold6/calculator.html',
  './gold6/percent.html',
  './gold6/price.html',
  './gold6/growth.html',
  './gold6/manifest.json',
  './gold6/icon-192.png',
  './gold6/icon-512.png',
  './gold6/icon-192-maskable.png',
  './gold6/icon-512-maskable.png',
  './gold6/apple-touch-icon.png',
  './gold6/favicon.ico',
  // Gold 7 App (Ahang Kian)
  './gold7/index.html',
  './gold7/calculator.html',
  './gold7/percent.html',
  './gold7/price.html',
  './gold7/manifest.json',
  './gold7/icon-192.png',
  './gold7/icon-512.png',
  './gold7/icon-192-maskable.png',
  './gold7/icon-512-maskable.png',
  './gold7/apple-touch-icon.png',
  './gold7/favicon.ico',
  // Gold 8 App (Pharma Kian / Darouno)
  './gold8/index.html',
  './gold8/calculator.html',
  './gold8/percent.html',
  './gold8/price.html',
  './gold8/growth.html',
  './gold8/manifest.json',
  './gold8/icon-192.png',
  './gold8/icon-512.png',
  './gold8/icon-192-maskable.png',
  './gold8/icon-512-maskable.png',
  './gold8/apple-touch-icon.png',
  './gold8/favicon.ico',
  './gold9/index.html',
  './gold9/calculator.html',
  './gold9/percent.html',
  './gold9/price.html',
  './gold9/growth.html',
  './gold9/manifest.json',
  './gold9/icon-192.png',
  './gold9/icon-512.png',
  './gold9/icon-192-maskable.png',
  './gold9/icon-512-maskable.png',
  './gold9/apple-touch-icon.png',
  './gold9/favicon.ico',
  './gold9/baharan_bg.jpg',
  './gold9/baharan_bg.webp',
  './gold9/assets/a01.png',
  './gold9/assets/a01@2x.png',
  './gold9/assets/a02.png',
  './gold9/assets/a02@2x.png',
  './gold9/assets/a03.png',
  './gold9/assets/a03@2x.png',
  './gold9/assets/a04.png',
  './gold9/assets/a04@2x.png',
  './gold9/assets/a05.png',
  './gold9/assets/a05@2x.png',
  './gold9/assets/a06.png',
  './gold9/assets/a06@2x.png',
  './gold9/assets/a07.png',
  './gold9/assets/a07@2x.png',
  './gold9/assets/a08.png',
  './gold9/assets/a08@2x.png',
  './gold9/assets/a09.png',
  './gold9/assets/a09@2x.png',
  './gold9/assets/a10.png',
  './gold9/assets/a10@2x.png',
  './gold9/assets/a11.png',
  './gold9/assets/a11@2x.png',
  './gold9/assets/a12.png',
  './gold9/assets/a12@2x.png',
  './gold9/assets/b01.webp',
  './gold9/assets/b02.webp',
  './gold9/assets/b03.webp',
  './gold9/assets/b04.webp',
  './gold9/assets/b05.webp',
  './gold9/assets/b06.webp',
  './gold9/assets/b07.webp',
  './gold9/assets/b08.webp',
  './gold9/assets/b09.webp',
  // Profit Calculator
  './profit-calculator/index.html',
  './profit-calculator/calc1.html',
  './profit-calculator/calc2.html',
  './profit-calculator/total.html',
  './profit-calculator/manifest.json',
  './profit-calculator/icon-192.png',
  './profit-calculator/icon-512.png',
  './profit-calculator/icon-192-maskable.png',
  './profit-calculator/icon-512-maskable.png',
  './profit-calculator/apple-touch-icon.png',
  './profit-calculator/favicon.ico',
  // Skincare App
  './skincare/index.html',
  './skincare/manifest.json',
  './skincare/icon-192.png',
  './skincare/icon-512.png',
  './skincare/icon-192-maskable.png',
  './skincare/icon-512-maskable.png',
  // AI Chat App
  './ai-chat/index.html',
  './ai-chat/manifest.json',
  './ai-chat/icon-192.png',
  './ai-chat/icon-512.png',
  './ai-chat/icon-192-maskable.png',
  './ai-chat/icon-512-maskable.png',
  './ai-chat/apple-touch-icon.png',
  './ai-chat/favicon.ico',
  './ai-chat/worker.js',
  // Tabdeal App
  './tabdeal/index.html',
  './tabdeal/manifest.json',
  './tabdeal/icon-192.png',
  './tabdeal/icon-512.png',
  './tabdeal/icon-192-maskable.png',
  './tabdeal/icon-512-maskable.png',
  // Simple Chat App
  './simple-chat/index.html',
  './simple-chat/manifest.json',
  './simple-chat/icon-192.png',
  './simple-chat/icon-512.png',
  './simple-chat/icon-192-maskable.png',
  './simple-chat/icon-512-maskable.png',
  './simple-chat/apple-touch-icon.png',
  './simple-chat/favicon.ico',
  // Vault App
  './vault/index.html',
  './vault/manifest.json',
  './vault/icon-192.png',
  './vault/icon-512.png',
  './vault/icon-192-maskable.png',
  './vault/icon-512-maskable.png',
  './vault/apple-touch-icon.png',
  './vault/favicon.ico',
  // Restricted Bot PWA
  './restricted/index.html',
  './restricted/manifest.json',
  './restricted/icon-192.png',
  './restricted/icon-512.png',
  './restricted/icon-192-maskable.png',
  './restricted/icon-512-maskable.png',
  './restricted/favicon.ico',
  // Family Tree App
  './family/index.html',
  './family-lab/index.html',
  './family/manifest.json',
  './family/icon-192.png',
  './family/icon-512.png',
  './family/icon-192-maskable.png',
  './family/icon-512-maskable.png',
  // Family app: local Persian fonts (Vazirmatn + Naskh), no CDN
  './vendor/vazirmatn/fonts.css',
  './vendor/vazirmatn/fonts/Vazirmatn-Regular.woff2',
  './vendor/vazirmatn/fonts/Vazirmatn-Medium.woff2',
  './vendor/vazirmatn/fonts/Vazirmatn-Bold.woff2',
  './vendor/vazirmatn/fonts/NotoNaskhArabic-Regular.woff2',
  './vendor/vazirmatn/fonts/NotoNaskhArabic-Bold.woff2',
  // Monthly Deposit App
  './monthly-deposit/index.html',
  './monthly-deposit/manifest.json',
  './monthly-deposit/icon-192.png',
  './monthly-deposit/icon-512.png',
  './monthly-deposit/icon-192-maskable.png',
  './monthly-deposit/icon-512-maskable.png',
  './monthly-deposit/apple-touch-icon.png',
  './monthly-deposit/favicon.ico',
  // Peace App (ثبت آرامش)
  './peace/index.html',
  './peace/manifest.json',
  './peace/icon-192.png',
  './peace/icon-512.png',
  './peace/icon-192-maskable.png',
  './peace/icon-512-maskable.png',
  './peace/apple-touch-icon.png',
  './peace/favicon.ico',
  // Yandex App (جستجوگر عکس)
  './yandex/index.html',
  './yandex/manifest.json',
  './yandex/icon-192.png',
  './yandex/icon-512.png',
  './yandex/icon-192-maskable.png',
  './yandex/icon-512-maskable.png',
  './yandex/apple-touch-icon.png',
  './yandex/favicon.ico',
  // HTML Viewer App (نمایشگر کد)
  './html-viewer/index.html',
  './html-viewer/manifest.json',
  './html-viewer/icon-192.png',
  './html-viewer/icon-512.png',
  './html-viewer/icon-192-maskable.png',
  './html-viewer/icon-512-maskable.png',
  './html-viewer/apple-touch-icon.png',
  './html-viewer/favicon.ico',
  // Funds Webview App (WWW.com)
  './funds/index.html',
  './funds/manifest.json',
  './funds/icon-192.png',
  './funds/icon-512.png',
  './funds/icon-192-maskable.png',
  './funds/icon-512-maskable.png',
  './funds/apple-touch-icon.png',
  './funds/favicon.ico',
  // Clipboard Saver App (کلیپ بورد)
  './clipboard/index.html',
  './clipboard/manifest.json',
  './clipboard/icon-192.png',
  './clipboard/icon-512.png',
  './clipboard/icon-192-maskable.png',
  './clipboard/icon-512-maskable.png',
  './clipboard/apple-touch-icon.png',
  './clipboard/favicon.ico',
  // Jules Agent App (دستیار اتوماسیون جولز)
  './jules-agent/index.html',
  './jules-agent/manifest.json',
  './jules-agent/icon-192.png',
  './jules-agent/icon-512.png',
  './jules-agent/apple-touch-icon.png',
  // Jules Bot Telegram App (ربات تلگرام عامل جولز)
  './jules-bot/index.html',
  './jules-bot/manifest.json',
  './jules-bot/icon-192.png',
  './jules-bot/icon-512.png',
  // Liquidity App (محاسبه نقدشوندگی)
  './liquidity/index.html',
  './liquidity/manifest.json',
  './liquidity/icon-192.png',
  './liquidity/icon-512.png',
  './liquidity/icon-192-maskable.png',
  './liquidity/icon-512-maskable.png',
  './liquidity/apple-touch-icon.png',
  './liquidity/favicon.ico',
  // AI Image Enhancer App (ارتقای کیفیت عکس)
  './image-enhancer/index.html',
  './image-enhancer/manifest.json',
  './image-enhancer/icon-192.png',
  './image-enhancer/icon-512.png',
  './image-enhancer/icon-192-maskable.png',
  './image-enhancer/icon-512-maskable.png',
  './image-enhancer/apple-touch-icon.png',
  // Daily Report App (گزارش روز عمارت)
  './daily-report/index.html',
  './daily-report/manifest.json',
  './daily-report/icon-192.png',
  './daily-report/icon-512.png',
  './daily-report/icon-192-maskable.png',
  './daily-report/icon-512-maskable.png',
  './daily-report/apple-touch-icon.png',
  './daily-report/favicon.ico',
  // Emarat 1-Tap Sync App
  './sync/index.html',
  './sync/manifest.json',
  './sync/icon-192.png',
  './sync/icon-512.png',
  // کتابخانه‌های محلی (بدون CDN مسدود) — Font Awesome، JSZip، فونت Inter
  './vendor/fontawesome/css/all.min.css',
  './vendor/fontawesome/webfonts/fa-brands-400.woff2',
  './vendor/fontawesome/webfonts/fa-regular-400.woff2',
  './vendor/fontawesome/webfonts/fa-solid-900.woff2',
  './vendor/fontawesome/webfonts/fa-v4compatibility.woff2',
  './vendor/jszip/jszip.min.js',
  './price-import.js',
  './refresh-button.js',
  './vendor/inter/inter.css',
  './vendor/inter/fonts/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2',
  './vendor/inter/fonts/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa25L7SUc.woff2',
  // Second Brain App (مغز دوم)
  './second-brain/index.html',
  './second-brain/styles.css',
  './second-brain/app.js',
  './second-brain/manifest.json',
  './second-brain/icon-192.png',
  './second-brain/icon-512.png',
  './second-brain/icon-192-maskable.png',
  './second-brain/icon-512-maskable.png',
  './second-brain/apple-touch-icon.png',
  './second-brain/favicon.ico',
  './second-brain/vendor/dompurify/purify.min.js',
  './second-brain/vendor/marked/marked.umd.js',
  './second-brain/vendor/hljs/highlight.min.js',
  './second-brain/vendor/hljs/kotlin.min.js',
  './second-brain/vendor/hljs/github-dark.min.css',
  './second-brain/vendor/hljs/github.min.css',
  './second-brain/vendor/chartjs/chart.umd.min.js',
  './second-brain/vendor/katex/katex.min.js',
  './second-brain/vendor/katex/katex.min.css',
  './second-brain/vendor/katex/fonts/KaTeX_AMS-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Caligraphic-Bold.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Caligraphic-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Fraktur-Bold.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Fraktur-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Main-Bold.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Main-BoldItalic.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Main-Italic.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Main-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Math-BoldItalic.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Math-Italic.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_SansSerif-Bold.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_SansSerif-Italic.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_SansSerif-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Script-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Size1-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Size2-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Size3-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Size4-Regular.woff2',
  './second-brain/vendor/katex/fonts/KaTeX_Typewriter-Regular.woff2',
  './second-brain/vendor/pdfjs/pdf.min.mjs',
  './second-brain/vendor/pdfjs/pdf.worker.min.mjs'
];

// منابع حیاتی: نبودشان یعنی صفحه سفید. باید قبل از هر چیز و به‌صورت قطعی کش شوند.
const CRITICAL_ASSETS = [
  './',
  './index.html',
  './sw.js',
  './manifest.json',
  './cloud-sync.js',
  './storage-guard.js',
  './second-brain/icon-192.png'
];

// نصب سرویس ورکر و کش کردن تمام منابع عمارت و زیرمجموعه‌ها
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      // منابع حیاتی باید کامل کش شوند؛ در غیر این صورت نصب شکست می‌خورد و
      // سرویس‌ورکر و کش سالم قبلی دست‌نخورده باقی می‌ماند (جلوگیری از صفحه سفید).
      await Promise.all(CRITICAL_ASSETS.map((asset) => cache.add(asset)));
      // بقیه منابع اختیاری‌اند؛ خطای یکی نباید کل نصب را خراب کند.
      await Promise.allSettled(
        ASSETS.filter((asset) => !CRITICAL_ASSETS.includes(asset)).map((asset) =>
          cache.add(asset).catch((err) => console.warn('Skipped asset:', asset, err))
        )
      );
    }).then(() => self.skipWaiting())
  );
});

// فعال‌سازی و پاکسازی کش‌های قدیمی
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// استراتژی Stale-While-Revalidate برای لود فوق‌سریع همراه با به‌روزرسانی پس‌زمینه
self.addEventListener('fetch', (event) => {
  // فقط درخواست‌های GET با پروتکل‌های محلی کنترل می‌شوند
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  // کش کردن فقط برای مبدا خود برنامه (فایل‌های محلی)
  if (url.origin !== self.location.origin) {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          // در پس‌زمینه شبکه را آپدیت کن
          fetch(event.request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(event.request, networkResponse.clone());
            }
          }).catch(() => {});
          return cachedResponse;
        }

        // اگر در کش نبود، مستقیماً از شبکه دریافت کن و در کش قرار بده
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            cache.put(event.request, networkResponse.clone());
          }
          return networkResponse;
        }).catch(() => {
          // حالت آفلاین: برای درخواست‌های صفحه، پرتال کش‌شده را برگردان تا صفحه سفید/ارور نبینی
          if (event.request.mode === 'navigate') {
            return cache.match('./index.html').then((fallback) => fallback || cache.match('./'));
          }
          return Response.error();
        });
      });
    })
  );
});

// مدیریت اعلان‌ها (برای یادآوری تمرین، دانلود سریع و نوار وضعیت)
self.addEventListener('notificationclick', (event) => {
  const notification = event.notification;
  const action = event.action;
  const replyText = event.reply; // کادر متنی ورودی تایپ/پیست شده در اعلان نوار وضعیت

  // اگر اکشن چسباندن یا ارسال مستقیم نبود، اعلان بسته می‌شود
  if (action !== 'paste_download' && action !== 'direct_submit') {
    notification.close();
  }

  const baseUrl = new URL('/restricted/index.html', self.location.origin).href;
  const actionUrl = new URL('/restricted/index.html?action=paste_download', self.location.origin).href;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      let matchingClient = null;
      for (const client of clientList) {
        if (client.url.includes('/restricted/')) {
          matchingClient = client;
          break;
        }
      }

      if (action === 'direct_submit' && replyText) {
        const directUrl = new URL('/restricted/index.html?action=direct_submit&link=' + encodeURIComponent(replyText), self.location.origin).href;
        if (matchingClient) {
          return matchingClient.focus().then(() => {
            matchingClient.postMessage({ action: 'DIRECT_SUBMIT_LINK', link: replyText });
          });
        } else if (clients.openWindow) {
          return clients.openWindow(directUrl);
        }
      } else if (action === 'paste_download') {
        if (matchingClient) {
          return matchingClient.focus().then(() => {
            matchingClient.postMessage({ action: 'PASTE_AND_DOWNLOAD' });
          });
        } else if (clients.openWindow) {
          return clients.openWindow(actionUrl);
        }
      } else {
        if (matchingClient) {
          return matchingClient.focus();
        } else if (clients.openWindow) {
          return clients.openWindow(baseUrl);
        }
      }
    })
  );
});