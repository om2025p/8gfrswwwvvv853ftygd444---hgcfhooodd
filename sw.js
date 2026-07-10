const CACHE_NAME = 'emarat-portal-v7';
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
  './profit-calculator/favicon.ico'
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

// استراتژی Cache First برای لود آفلاین
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
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
