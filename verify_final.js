const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.cwd() + '/index.html');
  await page.waitForTimeout(1000); // Wait for animations
  await page.screenshot({ path: '/home/jules/verification/final_portal.png' });

  const cards = await page.$$('.app-card');
  console.log('Number of app cards:', cards.length);

  await browser.close();
})();
