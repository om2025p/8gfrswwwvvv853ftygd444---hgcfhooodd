const CACHE_NAME = 'emarat-portal-v17';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './cloud-sync.js',
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
  './gold5/manifest.json',
  './gold5/icon-192.png',
  './gold5/icon-512.png',
  './gold5/icon-192-maskable.png',
  './gold5/icon-512-maskable.png',
  './gold5/apple-touch-icon.png',
  './gold5/favicon.ico',
  // Profit Calculator
  './profit-calculator/index.html',
  './profit-calculator/calc1.html',
  './profit-calculator/calc2.html',
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
  './simple-chat/favicon.ico'
];

// نصب سرویس ورکر و کش کردن تمام منابع عمارت و زیرمجموعه‌ها
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Caching all assets...');
      return cache.addAll(ASSETS);
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
        });
      });
    })
  );
});

// مدیریت اعلان‌ها (برای یادآوری تمرین و غیره)
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('./index.html')
  );
});
