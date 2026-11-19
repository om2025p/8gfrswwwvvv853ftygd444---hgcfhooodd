/*!
 * ورود قیمت ابطال از فایل اکسل سایت — مشترک بین اپ‌های ثبت درصد ۳ تا ۹
 *
 * قانون: فقط «کپی عدد». هیچ تقسیم/ضرب/مرکب‌سازی انجام نمی‌شود.
 * ستون انتخابی: ستونی از سرستون که هم «قیمت» دارد و هم «ابطال»
 * (یا «NAV ابطال»؛ «ابظال» غلط تایپی رایج فایل‌های سایت هم پذیرفته می‌شود).
 *
 * وابستگی: JSZip (vendor/jszip/jszip.min.js) — آفلاین، بدون CDN.
 * استفاده:
 *   EmaratPriceImport.mount({ storageKey, getPrices, savePrices, accent });
 */
(function () {
  'use strict';

  var FA_DIGITS = {
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
  };

  function toEnDigits(s) {
    return String(s == null ? '' : s).replace(/[۰-۹٠-٩]/g, function (m) { return FA_DIGITS[m] || m; });
  }

  /* نیم‌فاصله و نویسه‌های کنترلی RTL تطبیق واژه‌ها را می‌شکنند */
  function clean(s) {
    return toEnDigits(s)
      .replace(/[\u200b-\u200f\u202a-\u202e\u2066-\u2069]/g, '')
      .replace(/\u00a0/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function hasEbtal(text) {
    return /ابطال|ابظال/.test(text);
  }

  function parseNumber(raw) {
    if (raw == null) return NaN;
    if (typeof raw === 'number') return raw;
    var s = clean(raw).replace(/[,\u066c\u060c\s]/g, '').replace(/[^0-9.\-]/g, '');
    if (!s || s === '-' || s === '.') return NaN;
    var n = parseFloat(s);
    return isNaN(n) ? NaN : n;
  }

  /* YYYY.MM.DD برای مقایسهٔ رشته‌ای؛ ورودی ۱۴۰۵/۰۸/۲۶ یا 1405-8-26 */
  function normDate(raw) {
    var s = clean(raw);
    var m = s.match(/^(\d{4})[\/\.\-](\d{1,2})[\/\.\-](\d{1,2})$/);
    if (!m) return '';
    var y = +m[1], mo = +m[2], d = +m[3];
    if (y < 1300 || y > 1500 || mo < 1 || mo > 12 || d < 1 || d > 31) return '';
    return y + '.' + (mo < 10 ? '0' : '') + mo + '.' + (d < 10 ? '0' : '') + d;
  }

  /* ---------------- خواندن xlsx با JSZip ---------------- */

  function readSharedStrings(zip) {
    var f = zip.file('xl/sharedStrings.xml');
    if (!f) return Promise.resolve([]);
    return f.async('string').then(function (xml) {
      var doc = new DOMParser().parseFromString(xml, 'application/xml');
      var sis = doc.getElementsByTagName('si');
      var out = [];
      for (var i = 0; i < sis.length; i++) {
        var ts = sis[i].getElementsByTagName('t');
        var buf = '';
        for (var j = 0; j < ts.length; j++) buf += ts[j].textContent;
        out.push(buf);
      }
      return out;
    });
  }

  function readSheetNames(zip) {
    var f = zip.file('xl/workbook.xml');
    if (!f) return Promise.resolve([]);
    return f.async('string').then(function (xml) {
      var doc = new DOMParser().parseFromString(xml, 'application/xml');
      var sheets = doc.getElementsByTagName('sheet');
      var out = [];
      for (var i = 0; i < sheets.length; i++) out.push(sheets[i].getAttribute('name') || '');
      return out;
    });
  }

  function colIndex(ref) {
    var letters = String(ref || '').replace(/[0-9]/g, '');
    var n = 0;
    for (var i = 0; i < letters.length; i++) n = n * 26 + (letters.charCodeAt(i) - 64);
    return n - 1;
  }

  function parseSheet(zip, path, shared) {
    return zip.file(path).async('string').then(function (xml) {
      var doc = new DOMParser().parseFromString(xml, 'application/xml');
      var rowNodes = doc.getElementsByTagName('row');
      var rows = [];
      for (var r = 0; r < rowNodes.length; r++) {
        var cells = [];
        var cNodes = rowNodes[r].getElementsByTagName('c');
        for (var c = 0; c < cNodes.length; c++) {
          var node = cNodes[c];
          var idx = colIndex(node.getAttribute('r'));
          var t = node.getAttribute('t');
          var val = '';
          if (t === 's') {
            var v = node.getElementsByTagName('v')[0];
            val = v ? (shared[parseInt(v.textContent, 10)] || '') : '';
          } else if (t === 'inlineStr') {
            var ts = node.getElementsByTagName('t');
            for (var k = 0; k < ts.length; k++) val += ts[k].textContent;
          } else {
            var vn = node.getElementsByTagName('v')[0];
            val = vn ? vn.textContent : '';
          }
          cells[idx >= 0 ? idx : cells.length] = val;
        }
        rows.push(cells);
      }
      return rows;
    });
  }

  function readWorkbook(file) {
    return file.arrayBuffer().then(function (buf) {
      return JSZip.loadAsync(buf);
    }).then(function (zip) {
      return Promise.all([readSharedStrings(zip), readSheetNames(zip)]).then(function (res) {
        var shared = res[0], names = res[1];
        var paths = Object.keys(zip.files)
          .filter(function (p) { return /^xl\/worksheets\/sheet\d+\.xml$/.test(p); })
          .sort(function (a, b) {
            return parseInt(a.match(/sheet(\d+)/)[1], 10) - parseInt(b.match(/sheet(\d+)/)[1], 10);
          });
        return paths.reduce(function (chain, p, i) {
          return chain.then(function (acc) {
            return parseSheet(zip, p, shared).then(function (rows) {
              acc.push({ name: names[i] || ('Sheet' + (i + 1)), rows: rows });
              return acc;
            });
          });
        }, Promise.resolve([]));
      });
    });
  }

  /* ---------------- تشخیص ستون ---------------- */

  function detectColumns(rows) {
    var headerIdx = -1;
    for (var i = 0; i < Math.min(rows.length, 15); i++) {
      if (/تاریخ/.test(clean(rows[i].join(' ')))) { headerIdx = i; break; }
    }
    if (headerIdx < 0) return null;

    var header = rows[headerIdx].map(clean);
    var dateCol = -1, priceCol = -1, i, h;

    for (i = 0; i < header.length; i++) {
      if (dateCol < 0 && /تاریخ/.test(header[i])) dateCol = i;
    }
    /* اولویت ۱: «قیمت» + «ابطال» → قیمت ابطال واحد ممتاز */
    for (i = 0; i < header.length; i++) {
      h = header[i];
      if (h && i !== dateCol && /قیمت/.test(h) && hasEbtal(h)) { priceCol = i; break; }
    }
    /* اولویت ۲: «NAV» + «ابطال» → NAV ابطال */
    if (priceCol < 0) {
      for (i = 0; i < header.length; i++) {
        h = header[i];
        if (h && i !== dateCol && /NAV/i.test(h) && hasEbtal(h)) { priceCol = i; break; }
      }
    }
    /* اولویت ۳: هر ستون ابطال، به‌شرط اینکه «ارزش/تعداد/بازدهی» نباشد */
    if (priceCol < 0) {
      for (i = 0; i < header.length; i++) {
        h = header[i];
        if (h && i !== dateCol && hasEbtal(h) && !/ارزش|تعداد|بازدهی/.test(h)) { priceCol = i; break; }
      }
    }
    return { headerIdx: headerIdx, dateCol: dateCol, priceCol: priceCol, header: header };
  }

  function extractRows(rows, cols) {
    var out = [];
    for (var i = cols.headerIdx + 1; i < rows.length; i++) {
      var row = rows[i];
      if (!row) continue;
      var date = normDate(row[cols.dateCol]);
      if (!date) continue;
      var rawPrice = cols.priceCol >= 0 ? row[cols.priceCol] : '';
      var price = parseNumber(rawPrice);
      out.push({
        date: date,
        rawPrice: clean(rawPrice),
        price: isNaN(price) ? null : price
      });
    }
    return out;
  }

  /* ---------------- مقایسه با دادهٔ موجود ---------------- */

  function lastSavedDate(existing) {
    var max = '';
    for (var i = 0; i < existing.length; i++) {
      var d = normDate(existing[i] && existing[i].date);
      if (d && d > max) max = d;
    }
    return max;
  }

  function classify(extracted, existing) {
    var byDate = {};
    for (var i = 0; i < existing.length; i++) {
      var d = normDate(existing[i] && existing[i].date);
      if (d) byDate[d] = existing[i];
    }
    var last = lastSavedDate(existing);
    return extracted.map(function (r) {
      var status;
      if (r.price == null) status = 'invalid';
      else if (byDate[r.date]) status = 'duplicate';
      else if (last && r.date <= last) status = 'old';
      else status = 'new';
      var old = byDate[r.date];
      return {
        date: r.date,
        price: r.price,
        rawPrice: r.rawPrice,
        status: status,
        oldPrice: old && typeof old.price === 'number' ? old.price : null
      };
    });
  }

  /* اختلاف مقیاس (ریال در برابر تومان) فقط هشدار است، نه تبدیل */
  function unitMismatch(rows, existing) {
    var fileVals = rows.filter(function (r) { return r.price != null; }).map(function (r) { return r.price; });
    var oldVals = existing.map(function (p) { return p && p.price; })
      .filter(function (v) { return typeof v === 'number' && v > 0; });
    if (!fileVals.length || !oldVals.length) return null;
    function median(a) {
      var s = a.slice().sort(function (x, y) { return x - y; });
      return s[Math.floor(s.length / 2)];
    }
    var mf = median(fileVals), mo = median(oldVals);
    if (!mf || !mo) return null;
    var ratio = mf / mo;
    if (ratio > 8) return { ratio: ratio, direction: 'bigger' };
    if (ratio < 0.125) return { ratio: ratio, direction: 'smaller' };
    return null;
  }

  /* ---------------- استایل (تم از متغیرهای صفحه ارث می‌برد) ---------------- */

  var STYLE_ID = 'pi-styles';
  var STYLE = [
    '.pi-card{margin-bottom:16px}',
    '.pi-head{display:flex;align-items:center;justify-content:space-between;gap:8px;cursor:pointer;',
    'background:var(--pi-head-bg,rgba(0,0,0,.22));border:1px solid var(--pi-border,rgba(255,255,255,.18));',
    'border-radius:10px;padding:10px 12px;user-select:none}',
    '.pi-head b{font-size:.9rem;color:var(--pi-accent,currentColor)}',
    '.pi-head .pi-arrow{transition:.2s;color:var(--pi-accent,currentColor)}',
    '.pi-card.open .pi-arrow{transform:rotate(180deg)}',
    '.pi-body{display:none;padding:12px 2px 2px}',
    '.pi-card.open .pi-body{display:block}',
    '.pi-drop{border:2px dashed var(--pi-border,rgba(255,255,255,.25));border-radius:14px;padding:20px;',
    'text-align:center;background:var(--pi-drop-bg,rgba(0,0,0,.2));cursor:pointer;transition:.15s;',
    'font-size:.8rem;line-height:1.9}',
    '.pi-drop.hot{border-color:var(--pi-accent,currentColor);background:var(--pi-hot-bg,rgba(255,255,255,.08))}',
    '.pi-drop b{color:var(--pi-accent,currentColor)}',
    '.pi-file{display:none}',
    '.pi-hint{font-size:.68rem;opacity:.85;margin-top:8px;line-height:1.8}',
    '.pi-summary{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}',
    '.pi-pill{font-size:.72rem;padding:4px 10px;border-radius:20px;',
    'border:1px solid var(--pi-border,rgba(255,255,255,.2));background:rgba(0,0,0,.18)}',
    '.pi-pill.new{color:#6bffb0;border-color:#2f8f6d}',
    '.pi-pill.dup{color:#f9e45b;border-color:#8f7f2f}',
    '.pi-pill.old{color:#ffb27a;border-color:#8f5f2f}',
    '.pi-pill.bad{color:#ff9a8b;border-color:#8f3f3f}',
    '.pi-tw{margin-top:10px;max-height:260px;overflow:auto;border-radius:10px;',
    'border:1px solid var(--pi-border,rgba(255,255,255,.2))}',
    '.pi-table{width:100%;border-collapse:collapse;font-size:.72rem;font-family:monospace}',
    '.pi-table th{position:sticky;top:0;background:var(--pi-accent,#2fba9b);color:var(--pi-accent-fg,#06251f);',
    'padding:6px 4px;font-size:.68rem}',
    '.pi-table td{padding:5px 4px;text-align:center;border-bottom:1px solid rgba(255,255,255,.12);',
    'white-space:nowrap}',
    '.pi-table tr.is-new td{background:rgba(43,143,109,.16)}',
    '.pi-table tr.is-dup td{color:#c9c07a}',
    '.pi-table tr.is-old td{color:#c99a7a}',
    '.pi-table tr.is-bad td{color:#e08a7a}',
    '.pi-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}',
    '.pi-btn{background:var(--pi-accent,#2fba9b);border:none;border-radius:30px;padding:9px 16px;',
    'font-weight:bold;font-size:.8rem;color:var(--pi-accent-fg,#06251f);cursor:pointer;font-family:inherit}',
    '.pi-btn:disabled{opacity:.45;cursor:not-allowed}',
    '.pi-btn.ghost{background:transparent;border:1px solid var(--pi-border,rgba(255,255,255,.3));',
    'color:inherit}',
    '.pi-note{font-size:.68rem;opacity:.9;margin-top:10px;line-height:1.9}',
    '.pi-warn{font-size:.72rem;color:#ffd479;background:rgba(120,90,10,.35);border:1px solid #8f7f2f;',
    'border-radius:10px;padding:8px 10px;margin-top:10px;line-height:1.8}',
    '.pi-ok{font-size:.75rem;color:#6bffb0;margin-top:10px;line-height:1.8}'
  ].join('');

  var LABEL = {
    new: '🟢 جدید',
    duplicate: '🟡 قبلاً ثبت شده',
    old: '🟠 قدیمی‌تر از آخرین ثبت',
    invalid: '🔴 بدون قیمت معتبر'
  };
  var CLS = { new: 'is-new', duplicate: 'is-dup', old: 'is-old', invalid: 'is-bad' };

  function el(tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function mount(opts) {
    var cfg = opts || {};
    var container = cfg.container || document.querySelector('.container') || document.body;
    var defaultHint = 'فقط ستون «قیمت … ابطال» خوانده می‌شود؛ عدد همان‌طور که در فایل است کپی می‌شود.';

    if (!document.getElementById(STYLE_ID)) {
      var style = document.createElement('style');
      style.id = STYLE_ID;
      style.textContent = STYLE;
      document.head.appendChild(style);
    }

    var card = el('div', 'card pi-card');
    card.innerHTML =
      '<div class="pi-head">' +
        '<b>📥 ورود قیمت ابطال از فایل سایت</b>' +
        '<span class="pi-arrow">▼</span>' +
      '</div>' +
      '<div class="pi-body">' +
        '<div class="pi-drop" id="piDrop">' +
          '<b>فایل اکسل سایت را اینجا رها کن</b><br>' +
          '<span style="font-size:.72rem;opacity:.85">یا برای انتخاب کلیک کن (xlsx)</span>' +
        '</div>' +
        '<input type="file" id="piFile" class="pi-file" accept=".xlsx">' +
        '<div class="pi-hint" id="piHint">' + defaultHint + '</div>' +
        '<div id="piResult"></div>' +
      '</div>';

    if (cfg.accent) card.style.setProperty('--pi-accent', cfg.accent);
    if (cfg.accentFg) card.style.setProperty('--pi-accent-fg', cfg.accentFg);

    container.appendChild(card);

    var drop = card.querySelector('#piDrop');
    var fileInput = card.querySelector('#piFile');
    var hint = card.querySelector('#piHint');
    var result = card.querySelector('#piResult');
    var current = null;

    card.querySelector('.pi-head').addEventListener('click', function () {
      card.classList.toggle('open');
    });

    drop.addEventListener('click', function () { fileInput.click(); });
    ['dragenter', 'dragover'].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('hot'); });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('hot'); });
    });
    drop.addEventListener('drop', function (e) {
      var f = e.dataTransfer.files && e.dataTransfer.files[0];
      if (f) handleFile(f);
    });
    fileInput.addEventListener('change', function (e) {
      var f = e.target.files && e.target.files[0];
      if (f) handleFile(f);
      e.target.value = '';
    });

    function getExisting() {
      if (typeof cfg.getPrices === 'function') {
        try { return cfg.getPrices() || []; } catch (err) { return []; }
      }
      try { return JSON.parse(localStorage.getItem(cfg.storageKey) || '[]') || []; }
      catch (err) { return []; }
    }

    function persist(list) {
      if (typeof cfg.savePrices === 'function') return cfg.savePrices(list);
      localStorage.setItem(cfg.storageKey, JSON.stringify(list));
      if (typeof window.renderAll === 'function') window.renderAll();
    }

    function renderError(msg) {
      result.innerHTML = '';
      result.appendChild(el('div', 'pi-warn', '⚠️ ' + msg));
    }

    function handleFile(file) {
      if (!/\.xlsx$/i.test(file.name)) {
        renderError('فقط فایل xlsx پشتیبانی می‌شود. (فایل csv را با اکسل ذخیره کن)');
        return;
      }
      if (typeof JSZip === 'undefined') {
        renderError('کتابخانهٔ خواندن اکسل بارگذاری نشده است (vendor/jszip).');
        return;
      }
      hint.textContent = '⏳ در حال خواندن فایل…';
      result.innerHTML = '';

      readWorkbook(file).then(function (book) {
        var picked = null, cols = null;
        for (var i = 0; i < book.length; i++) {
          var c = detectColumns(book[i].rows);
          if (c && c.priceCol >= 0 && c.dateCol >= 0) { picked = book[i]; cols = c; break; }
        }
        if (!picked) {
          hint.textContent = '—';
          renderError('در این فایل ستون «قیمت … ابطال» پیدا نشد. فایل‌هایی که فقط درصد بازدهی دارند قابل استفاده نیستند.');
          return;
        }
        var extracted = extractRows(picked.rows, cols);
        if (!extracted.length) {
          hint.textContent = '—';
          renderError('هیچ ردیف معتبری (تاریخ + قیمت) در فایل پیدا نشد.');
          return;
        }
        current = {
          file: file.name,
          sheet: picked.name,
          cols: cols,
          rows: classify(extracted, getExisting())
        };
        hint.textContent = '📄 ' + file.name + ' — شیت: ' + picked.name;
        renderResult();
      }).catch(function (err) {
        hint.textContent = '—';
        renderError('خواندن فایل ناموفق بود: ' + (err && err.message ? err.message : err));
      });
    }

    function renderResult() {
      result.innerHTML = '';
      if (!current) return;

      var counts = { new: 0, duplicate: 0, old: 0, invalid: 0 };
      current.rows.forEach(function (r) { counts[r.status]++; });

      var priceName = current.cols.header[current.cols.priceCol] || 'قیمت';
      var existing = getExisting();

      result.appendChild(el('div', 'pi-note',
        '🔎 ستون انتخاب‌شده: <b>' + priceName + '</b><br>' +
        '📅 آخرین تاریخ ثبت‌شدهٔ تو: <b>' + (lastSavedDate(existing) || '—') + '</b>'));

      var mismatch = unitMismatch(current.rows, existing);
      if (mismatch) {
        result.appendChild(el('div', 'pi-warn',
          '⚠️ اعداد این فایل حدوداً <b>' + Math.round(mismatch.ratio) + ' برابر</b> ' +
          (mismatch.direction === 'bigger' ? 'بزرگ‌تر' : 'کوچک‌تر') +
          ' از قیمت‌های ثبت‌شدهٔ تو هستند (احتمالاً ریال در برابر تومان). ' +
          'طبق خواستهٔ تو عدد دست‌کاری نمی‌شود؛ فقط بدان که نمودار یک پله می‌گیرد.'));
      }

      var sum = el('div', 'pi-summary');
      sum.appendChild(el('span', 'pi-pill new', '🟢 جدید: ' + counts.new));
      sum.appendChild(el('span', 'pi-pill dup', '🟡 تکراری: ' + counts.duplicate));
      sum.appendChild(el('span', 'pi-pill old', '🟠 قدیمی: ' + counts.old));
      sum.appendChild(el('span', 'pi-pill bad', '🔴 نامعتبر: ' + counts.invalid));
      result.appendChild(sum);

      var tw = el('div', 'pi-tw');
      var table = el('table', 'pi-table');
      table.innerHTML = '<thead><tr><th>تاریخ</th><th>' + priceName + '</th><th>وضعیت</th></tr></thead>';
      var tbody = el('tbody');
      current.rows.slice().sort(function (a, b) { return a.date.localeCompare(b.date); })
        .forEach(function (r) {
          var tr = el('tr', CLS[r.status]);
          var priceCell = r.price == null ? (r.rawPrice || '—') : r.price.toLocaleString('en-US');
          if (r.status === 'duplicate' && r.oldPrice != null && r.oldPrice !== r.price) {
            priceCell += ' <span style="color:#f9e45b;font-size:.62rem">(ثبت‌شده: ' +
              r.oldPrice.toLocaleString('en-US') + ')</span>';
          }
          tr.innerHTML = '<td>' + r.date + '</td><td>' + priceCell + '</td><td>' +
            LABEL[r.status] + '</td>';
          tbody.appendChild(tr);
        });
      table.appendChild(tbody);
      tw.appendChild(table);
      result.appendChild(tw);

      var actions = el('div', 'pi-actions');
      var applyBtn = el('button', 'pi-btn', '✅ ثبت ' + counts.new + ' ردیف جدید');
      applyBtn.disabled = counts.new === 0;
      var cancelBtn = el('button', 'pi-btn ghost', 'انصراف');
      actions.appendChild(applyBtn);
      actions.appendChild(cancelBtn);
      result.appendChild(actions);

      cancelBtn.addEventListener('click', function () {
        current = null;
        result.innerHTML = '';
        hint.textContent = defaultHint;
      });

      applyBtn.addEventListener('click', function () {
        var base = getExisting();
        var added = [];
        current.rows.forEach(function (r) {
          if (r.status !== 'new') return;
          added.push({
            id: Date.now() + added.length,
            date: r.date,
            timestamp: new Date().toISOString(),
            price: r.price,
            source: 'excel-import'
          });
        });
        if (!added.length) return;

        var merged = base.concat(added);
        merged.sort(function (a, b) {
          return normDate(a.date).localeCompare(normDate(b.date)) ||
            (new Date(a.timestamp) - new Date(b.timestamp));
        });
        persist(merged);

        hint.textContent = '✅ ' + added.length + ' قیمت از فایل ثبت شد.';
        result.innerHTML = '';
        result.appendChild(el('div', 'pi-ok',
          '✅ <b>' + added.length + '</b> قیمت جدید از فایل ثبت شد.'));
        current = null;
        if (typeof window.showMessage === 'function') {
          window.showMessage('✅ ' + added.length + ' قیمت از فایل ثبت شد');
        }
      });
    }
  }

  window.EmaratPriceImport = {
    mount: mount,
    _internal: {
      normDate: normDate,
      parseNumber: parseNumber,
      detectColumns: detectColumns,
      extractRows: extractRows,
      classify: classify,
      unitMismatch: unitMismatch,
      readWorkbook: readWorkbook,
      lastSavedDate: lastSavedDate
    }
  };
})();
