/**
 * Cloudflare Worker: 24/7 Always-Online Relay for Emarat Download Shield Bot
 * Receives Telegram Webhook updates & triggers GitHub Actions workflow instantly.
 */

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("Emarat Download Shield Cloudflare Worker is Live!", { status: 200 });
    }

    try {
      const update = await request.json();
      if (!update || !update.message) {
        return new Response("OK", { status: 200 });
      }

      const message = update.message;
      const chatId = message.chat ? message.chat.id : null;
      const text = message.text || "";

      if (!chatId || !text) {
        return new Response("OK", { status: 200 });
      }

      // Check for links in message
      const linkRegex = /(https?:\/\/[^\s]+)/g;
      const matches = text.match(linkRegex);

      if (matches && matches.length > 0) {
        const targetLink = matches[0];
        const botToken = env.BOT_TOKEN;
        const ghPat = env.GH_PAT;
        const ghRepo = env.GH_REPO || "user/repo"; // format: owner/repo
        const ghBranch = env.GH_BRANCH || "75";

        // 1. Send immediate Persian live log to Telegram User Chat
        const tgApiUrl = `https://api.telegram.org/bot${botToken}/sendMessage`;
        await fetch(tgApiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: chatId,
            text: `⚡ *درخواست دانلود شما با موفقیت در سیستم کلودفلر ۲۴ ساعته ثبت شد!*\n\n🔗 *لینک:* \`${targetLink}\`\n\n🕒 *وضعیت:* در حال اتصال و بیدار کردن موتور دانلود ابری گیت‌هاب... 🚀`,
            parse_mode: "Markdown"
          })
        });

        // 2. Trigger GitHub Actions Workflow via Workflow Dispatch
        if (ghPat && ghRepo) {
          const ghApiUrl = `https://api.github.com/repos/${ghRepo}/actions/workflows/restricted_bot.yml/dispatches`;
          await fetch(ghApiUrl, {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${ghPat}`,
              "Accept": "application/vnd.github+json",
              "User-Agent": "Cloudflare-Worker-EmaratBot",
              "X-GitHub-Api-Version": "2022-11-28"
            },
            body: JSON.stringify({
              ref: ghBranch,
              inputs: {
                TELEGRAM_LINK: targetLink,
                OWNER_ID: String(chatId)
              }
            })
          });
        }
      }

      return new Response("OK", { status: 200 });
    } catch (err) {
      return new Response(`Worker Error: ${err.message}`, { status: 200 });
    }
  }
};
