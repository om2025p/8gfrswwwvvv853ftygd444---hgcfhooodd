/* Shared growth statistics for the liquidity growth pages. */
(function (global) {
    'use strict';

    function sortHistory(data) {
        return [...(data || [])].sort(function (a, b) {
            const da = String(a.date || a.d || '');
            const db = String(b.date || b.d || '');
            return da.localeCompare(db);
        });
    }

    function calcAvgGrowth(data) {
        if (!data || data.length < 2) return null;

        const sorted = sortHistory(data);
        const growthPercents = [];
        let positiveCount = 0;
        let negativeCount = 0;

        for (let i = 1; i < sorted.length; i++) {
            const prevPrice = Number(sorted[i - 1].pc) || 0;
            const currPrice = Number(sorted[i].pc) || 0;
            if (prevPrice > 0 && currPrice > 0) {
                const growth = ((currPrice - prevPrice) / prevPrice) * 100;
                growthPercents.push(growth);
                if (growth > 0) positiveCount++;
                else if (growth < 0) negativeCount++;
            }
        }

        if (growthPercents.length === 0) return null;

        const avgSimple = growthPercents.reduce(function (sum, value) { return sum + value; }, 0) / growthPercents.length;
        const firstPrice = Number(sorted[0].pc) || 0;
        const lastPrice = Number(sorted[sorted.length - 1].pc) || 0;

        return {
            avgSimple: avgSimple,
            totalGrowth: firstPrice > 0 ? ((lastPrice - firstPrice) / firstPrice) * 100 : 0,
            positiveCount: positiveCount,
            negativeCount: negativeCount,
            totalDays: growthPercents.length,
            firstPrice: firstPrice,
            lastPrice: lastPrice
        };
    }

    function calcAvgGrowthLastN(data, n) {
        if (!data || data.length < 2) return null;
        const sorted = sortHistory(data);
        return calcAvgGrowth(sorted.slice(-n - 1));
    }

    const PERIODS = [
        { key: 'week', label: 'هفته اخیر', days: 5 },
        { key: 'm1', label: '۱ ماه اخیر', days: 22 },
        { key: 'm2', label: '۲ ماه اخیر', days: 44 },
        { key: 'm3', label: '۳ ماه اخیر', days: 66 },
        { key: 'm6', label: '۶ ماه اخیر', days: 132 },
        { key: 'y1', label: '۱ سال اخیر', days: 250 },
        { key: 'all', label: 'همه', days: null }
    ];

    function periodResult(data, period) {
        if (!period || period.days == null) return calcAvgGrowth(data);
        return calcAvgGrowthLastN(data, period.days);
    }

    function buildTrendSeries(data, period) {
        if (!data || data.length < 2) return null;

        const sorted = sortHistory(data);
        const recent = period && period.days != null ? sorted.slice(-period.days - 1) : sorted;
        const stats = calcAvgGrowth(recent);
        if (!stats) return null;

        const growths = [];
        for (let i = 1; i < recent.length; i++) {
            const prevPrice = Number(recent[i - 1].pc) || 0;
            const currPrice = Number(recent[i].pc) || 0;
            if (prevPrice > 0 && currPrice > 0) {
                growths.push({
                    date: String(recent[i].date || recent[i].d || ''),
                    price: currPrice,
                    growth: ((currPrice - prevPrice) / prevPrice) * 100
                });
            }
        }

        const rolling = [];
        const windowSize = 7;
        for (let i = 0; i < growths.length; i++) {
            const start = Math.max(0, i - windowSize + 1);
            let sum = 0;
            for (let j = start; j <= i; j++) sum += growths[j].growth;
            rolling.push(sum / (i - start + 1));
        }

        return {
            sorted: sorted,
            recent: recent,
            growths: growths,
            rolling: rolling,
            stats: stats
        };
    }

    global.GrowthStats = {
        sortHistory: sortHistory,
        calcAvgGrowth: calcAvgGrowth,
        calcAvgGrowthLastN: calcAvgGrowthLastN,
        PERIODS: PERIODS,
        periodResult: periodResult,
        buildTrendSeries: buildTrendSeries
    };
})(window);
