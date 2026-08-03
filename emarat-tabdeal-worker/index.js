/**
 * Cloudflare Worker for Tabdeal Wallet Aggregation and Valuation
 *
 * This worker securely queries Spot, Funding, and Futures accounts on Tabdeal,
 * signs requests using HMAC-SHA256 with keys stored safely in its environment,
 * calculates total asset values in Toman (IRT) and Tether (USDT), and handles CORS.
 */

export default {
  async fetch(request, env, ctx) {
    // CORS configuration
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

    // Endpoint: POST /set-keys
    // Updates worker environment variables using user's Cloudflare Token if requested
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

        // We call Cloudflare API to update secrets individually using the official /secrets endpoint
        const scriptName = "emarat-tabdeal-worker";
        const baseCfUrl = `https://api.cloudflare.com/client/v4/accounts/${cfAccountId}/workers/scripts/${scriptName}/secrets`;

        // Function to update an individual secret
        const updateSecret = async (name, text) => {
          return fetch(baseCfUrl, {
            method: "PUT",
            headers: {
              "Authorization": `Bearer ${cfToken}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              name: name,
              text: text,
              type: "secret_text"
            })
          });
        };

        // Update TABDEAL_API_KEY and TABDEAL_API_SECRET in parallel
        const [resKey, resSecret] = await Promise.all([
          updateSecret("TABDEAL_API_KEY", apiKey),
          updateSecret("TABDEAL_API_SECRET", apiSecret)
        ]);

        if (!resKey.ok || !resSecret.ok) {
          const errKeyText = !resKey.ok ? await resKey.text() : "";
          const errSecText = !resSecret.ok ? await resSecret.text() : "";
          return new Response(JSON.stringify({
            error: `Failed to update secrets on Cloudflare. Key error: ${errKeyText || "None"}. Secret error: ${errSecText || "None"}`
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

    // Endpoint: GET /balance
    if (url.pathname === "/balance") {
      const apiKey = env.TABDEAL_API_KEY;
      const apiSecret = env.TABDEAL_API_SECRET;

      if (!apiKey || !apiSecret) {
        return new Response(JSON.stringify({ error: "API_KEYS_NOT_CONFIGURED" }), {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      try {
        // Sign query function
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

        // 1. Fetch Spot balances
        let spotAssets = [];
        try {
          const spotRes = await fetchSigned("https://api1.tabdeal.org/r/api/v1/account");
          if (spotRes.ok) {
            const data = await spotRes.json();
            if (data && data.balances) {
              spotAssets = data.balances.map(b => ({
                asset: b.asset,
                free: parseFloat(b.free) || 0,
                freeze: parseFloat(b.freeze) || 0,
              })).filter(b => (b.free + b.freeze) > 0);
            }
          } else {
            console.error("Spot API failed:", await spotRes.text());
          }
        } catch (e) {
          console.error("Error fetching spot balance:", e);
        }

        // 2. Fetch Futures balances (Note: Funding is already merged within Spot API on Tabdeal, hence omitted to prevent double valuation)
        let futuresAssets = [];
        try {
          const futuresRes = await fetchSigned("https://api1.tabdeal.org/r/fapi/v3/account");
          if (futuresRes.ok) {
            const data = await futuresRes.json();
            if (data && data.assets) {
              futuresAssets = data.assets.map(b => {
                const marginBal = parseFloat(b.marginBalance) || parseFloat(b.walletBalance) || 0;
                return {
                  asset: b.asset,
                  free: marginBal,
                  freeze: 0,
                };
              }).filter(b => b.free > 0);
            }
          } else {
            console.error("Futures API failed:", await futuresRes.text());
          }
        } catch (e) {
          console.error("Error fetching futures balance:", e);
        }

        // Merge all assets by symbol name
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

        // 4. Pricing service: Get prices in Toman (IRT) and calculate total valuation
        // A. Get USDTIRT price first from Tabdeal (as key multiplier)
        let usdtIrtPrice = 61500; // conservative fallback
        try {
          const usdtIrtRes = await fetch("https://api1.tabdeal.org/r/api/v1/trades?symbol=USDTIRT&limit=1");
          if (usdtIrtRes.ok) {
            const trades = await usdtIrtRes.json();
            if (trades && trades[0] && trades[0].price) {
              usdtIrtPrice = parseFloat(trades[0].price) || usdtIrtPrice;
            }
          }
        } catch (e) {
          console.error("Error fetching USDTIRT price:", e);
        }

        // B. Query prices for each asset in parallel
        const finalAssets = await Promise.all(uniqueAssets.map(async (assetItem) => {
          const sym = assetItem.asset;
          let priceIrt = 0;
          let pricingSource = "mock";

          if (sym === "IRT" || sym === "TOMAN") {
            priceIrt = 1;
            pricingSource = "fixed";
          } else if (sym === "USDT" || sym === "TETHER") {
            priceIrt = usdtIrtPrice;
            pricingSource = "tabdeal";
          } else {
            // Try Tabdeal direct price first
            try {
              const tabdealPriceRes = await fetch(`https://api1.tabdeal.org/r/api/v1/trades?symbol=${sym}IRT&limit=1`);
              if (tabdealPriceRes.ok) {
                const trades = await tabdealPriceRes.json();
                if (trades && trades[0] && trades[0].price) {
                  priceIrt = parseFloat(trades[0].price) || 0;
                  pricingSource = "tabdeal";
                }
              }
            } catch (e) {}

            // Fallback to Binance USD price * USDT_IRT_price if Direct IRT price failed
            if (priceIrt === 0) {
              try {
                const binanceRes = await fetch(`https://api.binance.com/api/v3/ticker/price?symbol=${sym}USDT`);
                if (binanceRes.ok) {
                  const bdata = await binanceRes.json();
                  if (bdata && bdata.price) {
                    const priceUsd = parseFloat(bdata.price) || 0;
                    priceIrt = priceUsd * usdtIrtPrice;
                    pricingSource = "binance_fallback";
                  }
                }
              } catch (e) {}
            }
          }

          // Fallbacks for main assets if both APIs failed
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

        // Calculate total valuations
        let totalIrt = 0;
        let totalUsdt = 0;

        finalAssets.forEach(a => {
          totalIrt += a.value_irt;
          totalUsdt += a.value_usdt;
        });

        return new Response(JSON.stringify({
          success: true,
          timestamp: Date.now(),
          total_irt: totalIrt,
          total_usdt: totalUsdt,
          usdt_irt_price: usdtIrtPrice,
          assets: finalAssets
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

    // Default route: instructions
    return new Response(
      "Emarat Tabdeal Wallet CF Worker is Active and Secure! Use GET /balance to fetch your wallet balance, or POST /set-keys to configure your keys.",
      { headers: { "Content-Type": "text/plain", ...corsHeaders } }
    );
  }
};
