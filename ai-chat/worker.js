/**
 * Cloudflare Worker Proxy for Google Gemini API and Live Web Search
 *
 * This worker acts as a secure, CORS-enabled reverse proxy to route Gemini API requests
 * directly from your browser without needing a VPN, and provides a powerful keyless Web Search API.
 *
 * How to deploy:
 * 1. Go to Cloudflare Dashboard -> Workers & Pages -> Create Application -> Create Worker.
 * 2. Copy and paste this code into the Cloudflare Worker editor.
 * 3. Deploy it!
 * 4. Paste your Worker's URL (e.g. https://your-worker-name.your-subdomain.workers.dev)
 *    in the Smart Assistant settings under "آدرس مسیردهی کلودفلر".
 */

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight (OPTIONS) requests
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, X-goog-api-key, Authorization",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    const url = new URL(request.url);

    // Endpoint for Live Web Search
    if (url.pathname === "/search" || url.pathname.endsWith("/search")) {
      const query = url.searchParams.get("q");
      if (!query) {
        return new Response(JSON.stringify({ error: "Query parameter 'q' is required." }), {
          status: 400,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          }
        });
      }

      try {
        const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
        const searchRes = await fetch(searchUrl, {
          headers: {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"
          }
        });

        if (!searchRes.ok) {
          return new Response(JSON.stringify({ error: "Failed to fetch search results from DuckDuckGo" }), {
            status: 502,
            headers: {
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*",
            }
          });
        }

        const htmlContent = await searchRes.text();
        const results = [];

        // Custom lightweight HTML block splitter for DuckDuckGo
        const blocks = htmlContent.split('class="result__body"');
        for (let i = 1; i < blocks.length; i++) {
          const block = blocks[i];

          const hrefMatch = block.match(/class="result__a"\s+href="([^"]+)"/);
          const titleMatch = block.match(/class="result__a"[^>]*>([\s\S]*?)<\/a>/);
          const snippetMatch = block.match(/class="result__snippet"[^>]*>([\s\S]*?)<\/div>/);

          if (hrefMatch && titleMatch) {
            let link = hrefMatch[1];
            if (link.includes("uddg=")) {
              const uddg = link.split("uddg=")[1];
              link = decodeURIComponent(uddg.split("&")[0]);
            }

            const title = titleMatch[1].replace(/<[^>]+>/g, "").trim();
            const snippet = snippetMatch ? snippetMatch[1].replace(/<[^>]+>/g, "").trim() : "";

            results.push({
              title: title,
              link: link,
              snippet: snippet
            });
          }

          if (results.length >= 7) break; // Limit to top 7 web results for context window size
        }

        return new Response(JSON.stringify({ results }), {
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          }
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: "Web search parsing failed: " + err.message }), {
          status: 500,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
          }
        });
      }
    }

    // Default: Proxy to Google's Gemini API endpoint
    url.hostname = "generativelanguage.googleapis.com";

    const modifiedRequest = new Request(url, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: request.redirect,
    });

    try {
      const response = await fetch(modifiedRequest);

      const modifiedResponse = new Response(response.body, response);
      modifiedResponse.headers.set("Access-Control-Allow-Origin", "*");
      modifiedResponse.headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
      modifiedResponse.headers.set("Access-Control-Allow-Headers", "Content-Type, X-goog-api-key, Authorization");

      return modifiedResponse;
    } catch (error) {
      return new Response(JSON.stringify({ error: "Failed to fetch from Gemini API via proxy: " + error.message }), {
        status: 502,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }
  },
};
