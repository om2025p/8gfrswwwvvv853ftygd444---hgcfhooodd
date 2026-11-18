/*
 * جایگزین بی‌اثر برای cloud-sync.js داخل اپ اندروید.
 *
 * اپ اندروید طبق طراحی، Local-First است و از MantleDB / همگام‌سازی ابری
 * استفاده نمی‌کند؛ پس این فایل هیچ درخواست شبکه‌ای نمی‌فرستد. وجود آن فقط
 * برای جلوگیری از خطای ۴۰۴ در صفحاتی است که `<script src="../cloud-sync.js">`
 * دارند. فایل اصلی مخزن دست‌نخورده باقی می‌ماند.
 */
(function () {
  if (window.EmaratCloudSync) return;
  window.EmaratCloudSync = {
    push: function () {},
    pull: function () {},
    init: function () {},
    isEnabled: function () { return false; }
  };
})();
