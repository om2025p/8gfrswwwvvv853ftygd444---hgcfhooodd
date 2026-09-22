/**
 * Cloudflare Worker for Tabdeal Wallet Aggregation, Tether Valuation,
 * 24h Official World Standard Automated Snapshots (00:00 UTC Cron),
 * and Dual-Method Percentage Averages Database.
 */

const MANTLE_DB_URL = "https://mantledb.sh/v2/emarat-tabdeal-wallet-v1/global_history";

// Helper: Get Accurate USDT/IRT price in Toman with multi-source fallback
async function getUsdtIrtPrice() {
  let price = 0;

  // 1. Tabdeal 24hr ticker
  try {
    const res = await fetch("https://api1.tabdeal.org/r/api/v1/ticker/24hr?symbol=USDT_IRT", {
      headers: { "Accept": "application/json" }
    });
    if (res.ok) {
      const data = await res.json();
      if (data && (data.lastPrice || data.askPrice || data.bidPrice)) {
        price = parseFloat(data.lastPrice || data.askPrice || data.bidPrice) || 0;
      }
    }
  } catch (e) {}

  // 2. Tabdeal trades USDT_IRT
  if (!price) {
    try {
      const res = await fetch("https://api1.tabdeal.org/r/api/v1/trades?symbol=USDT_IRT&limit=1", {
        headers: { "Accept": "application/json" }
      });
      if (res.ok) {
        const trades = await res.json();
        if (Array.isArray(trades) && trades[0] && trades[0].price) {
          price = parseFloat(trades[0].price) || 0;
        }
      }
    } catch (e) {}
  }

  // 3. Tabdeal trades USDTIRT
  if (!price) {
    try {
      const res = await fetch("https://api1.tabdeal.org/r/api/v1/trades?symbol=USDTIRT&limit=1", {
        headers: { "Accept": "application/json" }
      });
      if (res.ok) {
        const trades = await res.json();
        if (Array.isArray(trades) && trades[0] && trades[0].price) {
          price = parseFloat(trades[0].price) || 0;
        }
      }
    } catch (e) {}
  }

  // 4. Nobitex fallback
  if (!price) {
    try {
      const res = await fetch("https://api.nobitex.ir/v2/trades/USDTIRT");
      if (res.ok) {
        const data = await res.json();
        if (data && data.trades && data.trades[0] && data.trades[0].price) {
          price = parseFloat(data.trades[0].price) || 0;
        }
      }
    } catch (e) {}
  }

  // 5. Wallex fallback
  if (!price) {
    try {
      const res = await fetch("https://api.wallex.ir/v1/currencies/stats");
      if (res.ok) {
        const data = await res.json();
        if (data && data.result && data.result.currencies && data.result.currencies.USDT) {
          price = parseFloat(data.result.currencies.USDT.price_toman || data.result.currencies.USDT.latest_price) || 0;
        }
      }
    } catch (e) {}
  }

  // Convert Rial to Toman if returned price is in Rials (> 300,000)
  if (price > 300000) {
    price = price / 10;
  }

  // Sanity check for realistic Tether Toman price (e.g. between 30,000 and 250,000)
  if (price < 30000 || price > 250000) {
    price = 91500; // Standard fallback rate
  }

  return Math.round(price);
}

// Helpers for Date & Time Formatting
function getJalaliDateStr(ts = Date.now()) {
  try {
    return new Intl.DateTimeFormat('fa-IR-u-nu-latn', {
      timeZone: 'Asia/Tehran',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(new Date(ts));
  } catch(e) {
    return new Date(ts).toISOString().split('T')[0];
  }
}

function getGregorianDateStr(ts = Date.now()) {
  try {
    return new Date(ts).toISOString().split('T')[0];
  } catch(e) {
    return "";
  }
}

function getTimeStr(ts = Date.now()) {
  try {
    return new Intl.DateTimeFormat('fa-IR-u-nu-latn', {
      timeZone: 'Asia/Tehran',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(new Date(ts));
  } catch(e) {
    return "";
  }
}

// Cloud Database Pull / Push (MantleDB & Cloudflare KV)
async function pullCloudHistory(env) {
  let history = [];
  if (env && env.TABDEAL_KV) {
    try {
      const kvData = await env.TABDEAL_KV.get("tabdeal_history_v1", "json");
      if (Array.isArray(kvData) && kvData.length > 0) {
        return kvData;
      }
    } catch (e) {}
  }

  try {
    const res = await fetch(MANTLE_DB_URL);
    if (res.ok) {
      const data = await res.json();
      if (data && Array.isArray(data.history)) {
        history = data.history;
      } else if (Array.isArray(data)) {
        history = data;
      }
    }
  } catch (e) {}

  return history;
}

async function pushCloudHistory(env, history) {
  if (env && env.TABDEAL_KV) {
    try {
      await env.TABDEAL_KV.put("tabdeal_history_v1", JSON.stringify(history));
    } catch (e) {}
  }

  try {
    await fetch(MANTLE_DB_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        timestamp: Date.now(),
        updated_at: new Date().toISOString(),
        history: history
      })
    });
  } catch (e) {}
}

// Recalculate Dual-Method Percentage Averages and update History
function processHistoryWithAverages(historyRaw, currentIrt, currentUsdt, usdtPrice, source = "user_visit") {
  let history = Array.isArray(historyRaw) ? [...historyRaw] : [];
  const now = Date.now();
  const jalaliToday = getJalaliDateStr(now);
  const gregorianToday = getGregorianDateStr(now);
  const timeToday = getTimeStr(now);

  const snapshotObj = {
    timestamp: now,
    date_str_jalali: jalaliToday,
    date_str_gregorian: gregorianToday,
    time_str: timeToday,
    total_irt: Math.round(currentIrt),
    total_usdt: parseFloat(currentUsdt.toFixed(2)),
    usdt_irt_price: usdtPrice,
    recorded_by: source
  };

  if (history.length === 0) {
    history.push(snapshotObj);
  } else {
    const lastEntry = history[history.length - 1];
    if (lastEntry.date_str_jalali === jalaliToday) {
      lastEntry.total_irt = Math.round(currentIrt);
      lastEntry.total_usdt = parseFloat(currentUsdt.toFixed(2));
      lastEntry.usdt_irt_price = usdtPrice;
      lastEntry.timestamp = now;
      lastEntry.time_str = timeToday;
      lastEntry.recorded_by = source;
    } else {
      history.push(snapshotObj);
    }
  }

  if (history.length > 365) {
    history = history.slice(-365);
  }

  let cumulativeSum = 0;
  for (let i = 0; i < history.length; i++) {
    const item = history[i];
    if (i === 0) {
      item.percent_24h = 0.00;
      item.avg_cumulative_to_now = 0.00;
    } else {
      const prev = history[i - 1];
      let pct = 0;
      if (prev.total_irt > 0) {
        pct = ((item.total_irt - prev.total_irt) / prev.total_irt) * 100;
      }
      item.percent_24h = parseFloat(pct.toFixed(2));
      cumulativeSum += item.percent_24h;

      item.avg_cumulative_to_now = parseFloat((cumulativeSum / i).toFixed(2));
    }
  }

  const totalDaysCount = history.length - 1;
  const overallAvg = totalDaysCount > 0 ? parseFloat((cumulativeSum / totalDaysCount).toFixed(2)) : 0.00;

  for (let i = 0; i < history.length; i++) {
    history[i].avg_overall_percent = overallAvg;
  }

  return { history, overallAvg, latestPct: history[history.length - 1].percent_24h };
}

// Fetch balances from Tabdeal and compute valuations
async function fetchBalanceAndValuation(env) {
  const apiKey = env.TABDEAL_API_KEY;
  const apiSecret = env.TABDEAL_API_SECRET;

  if (!apiKey || !apiSecret) {
    throw new Error("API_KEYS_NOT_CONFIGURED");
  }

  const hmacSha256 = async (secret, message) => {
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      "raw",
      encoder.encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["sign"]
    );
    const sig = await crypto.subtle.sign("HMAC", key, encoder.encode(message));
    return Array.from(new Uint8Array(sig))
      .map(b => b.toString(16).padStart(2, "0"))
      .join("");
  };

  const fetchSigned = async (baseUrl) => {
    const timestamp = Date.now();
    const queryString = `timestamp=${timestamp}`;
    const signature = await hmacSha256(apiSecret, queryString);
    const fullUrl = `${baseUrl}?${queryString}&signature=${signature}`;
    return fetch(fullUrl, {
      headers: {
        "X-MBX-APIKEY": apiKey,
        "Accept": "application/json"
      }
    });
  };

  // 1. Spot balances (including free, locked, freeze, and frozen amounts)
  let spotAssets = [];
  try {
    const spotRes = await fetchSigned("https://api1.tabdeal.org/r/api/v1/account");
    if (spotRes.ok) {
      const data = await spotRes.json();
      if (data && data.balances) {
        spotAssets = data.balances.map(b => {
          const free = parseFloat(b.free) || 0;
          const freeze = parseFloat(b.freeze) || parseFloat(b.locked) || parseFloat(b.frozen) || parseFloat(b.borrowed) || 0;
          return {
            asset: b.asset,
            free: free,
            freeze: freeze,
          };
        }).filter(b => (b.free + b.freeze) > 0);
      }
    }
  } catch (e) {}

  // 2. Futures balances
  let futuresAssets = [];
  try {
    const futuresRes = await fetchSigned("https://api1.tabdeal.org/r/fapi/v3/account");
    if (futuresRes.ok) {
      const data = await futuresRes.json();
      if (data && data.assets) {
        futuresAssets = data.assets.map(b => {
          const walletBal = parseFloat(b.walletBalance) || 0;
          const marginBal = parseFloat(b.marginBalance) || 0;
          const crossBal = parseFloat(b.crossWalletBalance) || 0;
          const unPnl = parseFloat(b.unrealizedProfit) || parseFloat(b.unrealizedPnl) || 0;
          const totalAmt = Math.max(walletBal, marginBal, crossBal) + unPnl;
          return {
            asset: b.asset,
            free: totalAmt > 0 ? totalAmt : 0,
            freeze: 0,
          };
        }).filter(b => b.free > 0);
      }
    }
  } catch (e) {}

  // Fallback to v2/v1 Futures if v3 returned empty
  if (futuresAssets.length === 0) {
    try {
      const futuresRes = await fetchSigned("https://api1.tabdeal.org/r/fapi/v2/account");
      if (futuresRes.ok) {
        const data = await futuresRes.json();
        if (data && data.assets) {
          futuresAssets = data.assets.map(b => {
            const walletBal = parseFloat(b.walletBalance) || 0;
            const marginBal = parseFloat(b.marginBalance) || 0;
            const unPnl = parseFloat(b.unrealizedProfit) || 0;
            const totalAmt = Math.max(walletBal, marginBal) + unPnl;
            return {
              asset: b.asset,
              free: totalAmt > 0 ? totalAmt : 0,
              freeze: 0,
            };
          }).filter(b => b.free > 0);
        }
      }
    } catch (e) {}
  }

  // Merge assets
  const mergedMap = new Map();
  const addAsset = (item, type) => {
    const symbol = item.asset.toUpperCase();
    const totalAmt = item.free + item.freeze;
    if (totalAmt <= 0) return;

    if (!mergedMap.has(symbol)) {
      mergedMap.set(symbol, {
        asset: symbol,
        total: 0,
        spot: 0,
        futures: 0
      });
    }
    const existing = mergedMap.get(symbol);
    existing.total += totalAmt;
    existing[type] += totalAmt;
  };

  spotAssets.forEach(a => addAsset(a, "spot"));
  futuresAssets.forEach(a => addAsset(a, "futures"));

  const uniqueAssets = Array.from(mergedMap.values());

  // Get accurate Tether price
  const usdtIrtPrice = await getUsdtIrtPrice();

  // Price each asset
  const finalAssets = await Promise.all(uniqueAssets.map(async (assetItem) => {
    const sym = assetItem.asset;
    let priceIrt = 0;

    if (sym === "IRT" || sym === "TOMAN") {
      priceIrt = 1;
    } else if (sym === "USDT" || sym === "TETHER") {
      priceIrt = usdtIrtPrice;
    } else {
      try {
        const tabdealPriceRes = await fetch(`https://api1.tabdeal.org/r/api/v1/trades?symbol=${sym}IRT&limit=1`);
        if (tabdealPriceRes.ok) {
          const trades = await tabdealPriceRes.json();
          if (trades && trades[0] && trades[0].price) {
            priceIrt = parseFloat(trades[0].price) || 0;
          }
        }
      } catch (e) {}

      if (priceIrt === 0) {
        try {
          const binanceRes = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${sym}USDT`);
          if (binanceRes.ok) {
            const bdata = await binanceRes.json();
            if (bdata && bdata.price) {
              const priceUsd = parseFloat(bdata.price) || 0;
              priceIrt = priceUsd * usdtIrtPrice;
            }
          }
        } catch (e) {}
      }
    }

    if (priceIrt === 0) {
      if (sym === "BTC") priceIrt = 98000 * usdtIrtPrice;
      else if (sym === "ETH") priceIrt = 3300 * usdtIrtPrice;
      else if (sym === "SOL") priceIrt = 180 * usdtIrtPrice;
    }

    const valueIrt = assetItem.total * priceIrt;
    const valueUsdt = valueIrt / usdtIrtPrice;

    return {
      ...assetItem,
      price_irt: priceIrt,
      value_irt: valueIrt,
      value_usdt: valueUsdt
    };
  }));

  let totalIrt = 0;
  let totalUsdt = 0;

  finalAssets.forEach(a => {
    totalIrt += a.value_irt;
    totalUsdt += a.value_usdt;
  });

  return {
    totalIrt,
    totalUsdt,
    usdtIrtPrice,
    assets: finalAssets
  };
}

export default {
  // Scheduled Cron Event (00:00 UTC Official World Standard Trading Time)
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async () => {
      try {
        const valuation = await fetchBalanceAndValuation(env);
        const currentHistory = await pullCloudHistory(env);
        const { history } = processHistoryWithAverages(
          currentHistory,
          valuation.totalIrt,
          valuation.totalUsdt,
          valuation.usdtIrtPrice,
          "auto_cron_00utc"
        );
        await pushCloudHistory(env, history);
      } catch (e) {
        console.error("Cron snapshot failed:", e);
      }
    })());
  },

  async fetch(request, env, ctx) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-Cloudflare-Token",
      "Access-Control-Max-Age": "86400",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    // POST /set-keys
    if (url.pathname === "/set-keys" && request.method === "POST") {
      try {
        const body = await request.json();
        const { apiKey, apiSecret, cfToken, cfAccountId } = body;

        if (!apiKey || !apiSecret || !cfToken || !cfAccountId) {
          return new Response(JSON.stringify({ error: "Missing parameters" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        const scriptName = "emarat-tabdeal-worker";
        const baseCfUrl = `https://api.cloudflare.com/client/v4/accounts/${cfAccountId}/workers/scripts/${scriptName}/secrets`;

        const updateSecret = async (name, text) => {
          return fetch(baseCfUrl, {
            method: "PUT",
            headers: {
              "Authorization": `Bearer ${cfToken}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ name, text, type: "secret_text" })
          });
        };

        const [resKey, resSecret] = await Promise.all([
          updateSecret("TABDEAL_API_KEY", apiKey),
          updateSecret("TABDEAL_API_SECRET", apiSecret)
        ]);

        if (!resKey.ok || !resSecret.ok) {
          const errKeyText = !resKey.ok ? await resKey.text() : "";
          const errSecText = !resSecret.ok ? await resSecret.text() : "";
          return new Response(JSON.stringify({
            error: `Failed to update secrets on Cloudflare. Key error: ${errKeyText}. Secret error: ${errSecText}`
          }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        return new Response(JSON.stringify({ success: true }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    // GET /history
    if (url.pathname === "/history") {
      try {
        const history = await pullCloudHistory(env);
        return new Response(JSON.stringify({ success: true, history }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    // GET /record-snapshot (manual or external cron trigger)
    if (url.pathname === "/record-snapshot") {
      try {
        const valuation = await fetchBalanceAndValuation(env);
        const currentHistory = await pullCloudHistory(env);
        const { history, overallAvg, latestPct } = processHistoryWithAverages(
          currentHistory,
          valuation.totalIrt,
          valuation.totalUsdt,
          valuation.usdtIrtPrice,
          "manual_snapshot_api"
        );
        await pushCloudHistory(env, history);

        return new Response(JSON.stringify({
          success: true,
          timestamp: Date.now(),
          total_irt: valuation.totalIrt,
          total_usdt: valuation.totalUsdt,
          usdt_irt_price: valuation.usdtIrtPrice,
          latest_24h_percent: latestPct,
          overall_avg_percent: overallAvg,
          history
        }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    // GET /balance
    if (url.pathname === "/balance") {
      try {
        const valuation = await fetchBalanceAndValuation(env);
        const currentHistory = await pullCloudHistory(env);
        const { history, overallAvg, latestPct } = processHistoryWithAverages(
          currentHistory,
          valuation.totalIrt,
          valuation.totalUsdt,
          valuation.usdtIrtPrice,
          "user_visit"
        );

        // Sync to cloud database asynchronously
        ctx.waitUntil(pushCloudHistory(env, history));

        return new Response(JSON.stringify({
          success: true,
          timestamp: Date.now(),
          total_irt: valuation.totalIrt,
          total_usdt: valuation.totalUsdt,
          usdt_irt_price: valuation.usdtIrtPrice,
          latest_24h_percent: latestPct,
          overall_avg_percent: overallAvg,
          assets: valuation.assets,
          history
        }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });

      } catch (err) {
        if (err.message === "API_KEYS_NOT_CONFIGURED") {
          return new Response(JSON.stringify({ error: "API_KEYS_NOT_CONFIGURED" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }
        return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }
    }

    return new Response(
      "Emarat Tabdeal Wallet Worker Active! Supports GET /balance, GET /history, GET /record-snapshot, and 00:00 UTC Scheduled Auto Cron.",
      { headers: { "Content-Type": "text/plain", ...corsHeaders } }
    );
  }
};
