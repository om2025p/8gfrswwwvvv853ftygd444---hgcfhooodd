/* ساختار بکاپ: app/YYYY/MM/week-NN/YYYY.MM.DD/app_backup.json + _updates.json */
(function () {
    'use strict';

    /* Intl دقیق‌ترین است؛ الگوریتم فقط پشتیبان برای مرورگرهای قدیمی. */
    function jalaliIntl(d) {
        try {
            var f = new Intl.DateTimeFormat('en-US-u-ca-persian', {
                year: 'numeric', month: 'numeric', day: 'numeric',
                timeZone: 'Asia/Tehran'
            });
            var parts = f.formatToParts(d), out = {};
            for (var i = 0; i < parts.length; i++) out[parts[i].type] = parts[i].value;
            var y = parseInt(out.year, 10), m = parseInt(out.month, 10), dd = parseInt(out.day, 10);
            if (y > 1200 && y < 1700 && m >= 1 && m <= 12 && dd >= 1 && dd <= 31) {
                return { y: y, m: m, d: dd };
            }
        } catch (e) {}
        return null;
    }

    function jalaliAlgo(d) {
        var g_y = d.getFullYear(), g_m = d.getMonth() + 1, g_d = d.getDate();
        var gdim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        var jdim = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29];
        if ((g_y % 4 === 0 && g_y % 100 !== 0) || (g_y % 400 === 0)) gdim[1] = 29;
        var gy = g_y - 1600, gm = g_m - 1, gd = g_d - 1;
        var gdn = 365 * gy + Math.floor((gy + 3) / 4) - Math.floor((gy + 99) / 100) + Math.floor((gy + 399) / 400);
        for (var i = 0; i < gm; ++i) gdn += gdim[i];
        gdn += gd;
        var jdn = gdn - 79;
        var jnp = Math.floor(jdn / 12053);
        jdn %= 12053;
        var jy = 979 + 33 * jnp + 4 * Math.floor(jdn / 1461);
        jdn %= 1461;
        if (jdn >= 366) {
            jy += Math.floor((jdn - 1) / 365);
            jdn = (jdn - 1) % 365;
        }
        var jm = 0;
        while (jm < 11 && jdn >= jdim[jm]) { jdn -= jdim[jm]; jm++; }
        return { y: jy, m: jm + 1, d: jdn + 1 };
    }

    function jalali(date) {
        var d = date || new Date();
        return jalaliIntl(d) || jalaliAlgo(d);
    }

    function pad(n) { return n < 10 ? '0' + n : '' + n; }

    function weekOfMonth(day) { return Math.min(5, Math.floor((day - 1) / 7) + 1); }

    /* gold4/1405/08/week-05/1405.08.29 */
    function dayFolder(appId, date) {
        var j = jalali(date);
        return [appId, j.y, pad(j.m), 'week-' + pad(weekOfMonth(j.d)),
                j.y + '.' + pad(j.m) + '.' + pad(j.d)].join('/');
    }

    /* gold4/1405/08/week-05/1405.08.29/gold4_backup.json */
    function build(appId, date, baseName) {
        var name = (baseName || (appId + '_backup')).replace(/\.json$/i, '');
        return dayFolder(appId, date) + '/' + name + '.json';
    }

    /* .../_updates.json — لاگ ساعت هر به‌روزرسانی */
    function updatesPath(appId, date) {
        return dayFolder(appId, date) + '/_updates.json';
    }

    function clock(date) {
        var d = date || new Date();
        return pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    }

    /* شمارش به‌روزرسانی‌های یک روز */
    function countUpdates(list) {
        return Array.isArray(list) ? list.length : 0;
    }

    /* خلاصهٔ هفته از روی مسیرها */
    function summarize(paths) {
        var out = {};
        (paths || []).forEach(function (p) {
            var m = /^([^/]+)\/(\d{4})\/(\d{2})\/(week-\d{2})\/(\d{4}\.\d{2}\.\d{2})\//.exec(p);
            if (!m) return;
            var key = m[2] + '/' + m[3] + '/' + m[4];
            out[key] = (out[key] || 0) + 1;
        });
        return out;
    }

    /* ثبت یک به‌روزرسانی در _updates.json (خواندن → افزودن → نوشتن) */
    function recordUpdate(appId, repo, token, branch, date) {
        branch = branch || 'main';
        var path = updatesPath(appId, date);
        var url = 'https://api.github.com/repos/' + repo + '/contents/' + path;
        var headers = {
            Authorization: token.indexOf('github_pat_') === 0 ? 'Bearer ' + token : 'token ' + token,
            Accept: 'application/vnd.github.v3+json'
        };
        return fetch(url + '?ref=' + encodeURIComponent(branch), { headers: headers })
            .then(function (r) { return r.status === 200 ? r.json() : null; })
            .then(function (existing) {
                var sha = existing && existing.sha;
                var list = [];
                if (existing && existing.content) {
                    try {
                        list = JSON.parse(decodeURIComponent(escape(atob(existing.content.replace(/\s/g, '')))));
                    } catch (e) { list = []; }
                }
                if (!Array.isArray(list)) list = [];
                list.push(clock(date));
                var body = {
                    message: 'ثبت به‌روزرسانی ' + appId + ' - ' + clock(date),
                    content: btoa(unescape(encodeURIComponent(JSON.stringify(list)))),
                    branch: branch
                };
                if (sha) body.sha = sha;
                return fetch(url, {
                    method: 'PUT',
                    headers: Object.assign({ 'Content-Type': 'application/json' }, headers),
                    body: JSON.stringify(body)
                });
            })
            .then(function (r) { return { success: r.ok }; })
            .catch(function (e) { return { success: false, message: e.message }; });
    }

    window.EmaratBackupPath = {
        jalali: jalali,
        dayFolder: dayFolder,
        build: build,
        updatesPath: updatesPath,
        clock: clock,
        countUpdates: countUpdates,
        summarize: summarize,
        recordUpdate: recordUpdate,
        weekOfMonth: weekOfMonth
    };
})();
