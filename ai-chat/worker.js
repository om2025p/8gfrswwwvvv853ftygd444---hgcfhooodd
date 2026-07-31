/**
 * Cloudflare Worker Proxy for Google Gemini API
 *
 * This worker acts as a secure, CORS-enabled reverse proxy to route Gemini Flash API requests
 * directly from your browser without needing a VPN.
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
    // Replace the proxy hostname with Google's API endpoint
    url.hostname = "generativelanguage.googleapis.com";

    // Create a new request based on the original request
    const modifiedRequest = new Request(url, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      redirect: request.redirect,
    });

    try {
      // Fetch from Google's Gemini API
      const response = await fetch(modifiedRequest);

      // Create a modified response to allow CORS
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
