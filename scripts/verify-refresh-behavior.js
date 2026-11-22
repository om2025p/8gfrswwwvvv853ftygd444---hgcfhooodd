/**
 * بازرس رفتاری دکمهٔ به‌روزرسانی (Puppeteer).
 * قانون اساسی: پیش‌فرض پنهان، fixed، فقط با اسکرول اضافه در کف باز شود.
 *
 * اجرا:  node scripts/verify-refresh-behavior.js [BASE_URL]
 */
function loadPuppeteer() {
  const paths = ['puppeteer-core', '/tmp/pptest/node_modules/puppeteer-core'];
  for (const p of paths) {
    try { return require(p); } catch (e) {}
  }
  console.error('puppeteer-core نصب نیست. اجرا کن: npm i puppeteer-core');
  process.exit(2);
}

const puppeteer = loadPuppeteer();

const BASE = process.argv[2] || 'http://127.0.0.1:12099';
const PAGES = ['index.html', 'monitor/index.html', 'gold9/index.html', 'gold10/index.html'];
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function state(page) {
  return page.evaluate(() => {
    const root = document.querySelector('#emr-rb-root');
    const btn = document.querySelector('.emr-rb-btn');
    if (!root || !btn) return { mounted: false };
    const r = btn.getBoundingClientRect();
    return {
      mounted: true,
      open: root.classList.contains('open'),
      position: getComputedStyle(root).position,
      hidden: r.top >= window.innerHeight - 1,
      top: Math.round(r.top),
      count: document.querySelectorAll('.emr-rb-btn').length,
    };
  });
}

async function checkPage(browser, path) {
  const page = await browser.newPage();
  await page.setViewport({ width: 390, height: 745 });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message.split('\n')[0]));
  const result = { page: path, failures: [], errors };

  try {
    await page.goto(`${BASE}/${path}`, { waitUntil: 'load', timeout: 45000 });
    await page.waitForFunction(() => !!document.querySelector('#emr-rb-root'), { timeout: 10000 });
    await sleep(1200);

    const initial = await state(page);
    if (!initial.mounted) result.failures.push('دکمه mount نشد');
    if (initial.count !== 1) result.failures.push(`تعداد دکمه ${initial.count} (باید ۱)`);
    if (initial.position !== 'fixed') result.failures.push(`position=${initial.position} (باید fixed)`);
    if (!initial.hidden) result.failures.push('پیش‌فرض پنهان نیست');

    // ظرف اسکرول: خود صفحه یا iframe فعال
    const frame = page.frames().find(f => /percent|calculator|price|growth/.test(f.url())) || null;
    const scroller = frame || page;

    await scroller.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await sleep(400);
    const atBottom = await state(page);
    if (atBottom.open) result.failures.push('فقط با رسیدن به کف نباید باز شود');

    const rect = await page.evaluate(() => {
      const b = document.querySelector('.emr-rb-btn').getBoundingClientRect();
      return { x: Math.round(window.innerWidth / 2), y: Math.round(window.innerHeight / 2) };
    });
    await page.mouse.move(rect.x, rect.y);
    await page.mouse.wheel({ deltaY: 120 });
    await sleep(150);
    await page.mouse.wheel({ deltaY: 120 });
    await sleep(800);

    const revealed = await state(page);
    if (!revealed.open) result.failures.push('با ۲ اسکرول اضافه در کف باز نشد');

    if (revealed.open) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await sleep(600);
      const afterScroll = await state(page);
      if (Math.abs(afterScroll.top - revealed.top) > 1) {
        result.failures.push('با اسکرول جابه‌جا شد (باید ثابت بماند)');
      }
    }

    result.revealedTop = revealed.top;
  } catch (e) {
    result.failures.push(`خطا: ${e.message.split('\n')[0]}`);
  } finally {
    await page.close();
  }
  return result;
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || '/usr/bin/chromium',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
  });

  const results = [];
  for (const p of PAGES) results.push(await checkPage(browser, p));
  await browser.close();

  let failed = 0;
  for (const r of results) {
    if (r.failures.length) {
      failed++;
      console.log(`❌ ${r.page}`);
      r.failures.forEach(f => console.log(`     - ${f}`));
    } else {
      console.log(`✅ ${r.page}  (top=${r.revealedTop})`);
    }
    r.errors.forEach(e => console.log(`     ⚠️ JS: ${e}`));
  }

  console.log(failed ? `\n${failed} صفحه رد شد.` : '\n✅ رفتار دکمه در همهٔ صفحات مطابق قانون است.');
  process.exit(failed ? 1 : 0);
})();
