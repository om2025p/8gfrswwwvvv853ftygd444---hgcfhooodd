/**
 * Cloudflare Worker: 24/7 Always-Online Relay for Emarat Download Shield Bot
 * Receives Telegram Webhook updates & triggers GitHub Actions workflow instantly.
 */

addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
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
      const botToken = typeof BOT_TOKEN !== "undefined" ? BOT_TOKEN : "";
      const ghPat = typeof GH_PAT !== "undefined" ? GH_PAT : "";
      const ghRepo = typeof GH_REPO !== "undefined" ? GH_REPO : "";
      const ghBranch = typeof GH_BRANCH !== "undefined" ? GH_BRANCH : "80";

      // Send status message to user informing how many links were queued
      if (botToken) {
        const tgApiUrl = `https://api.telegram.org/bot${botToken}/sendMessage`;
        const queueText = matches.length === 1
          ? `⚡ *لینک شما در سیستم صف ۲۴ ساعته قرار گرفت!*\n\n🔗 *لینک:* \`${matches[0]}\`\n\n🕒 *وضعیت:* در حال استخراج و بیدار کردن موتور دانلود ابری گیت‌هاب... 🚀`
          : `⚡ *تعداد ${matches.length} لینک شناسایی شد و به صف دانلود افزوده‌شدند!* 📋\n\n🕒 *وضعیت:* ربات به ترتیب نوبت تمام فایل‌ها را استخراج کرده و به پی‌وی و کانال ارسال می‌کند. 🚀`;

        await fetch(tgApiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            chat_id: chatId,
            text: queueText,
            parse_mode: "Markdown"
          })
        });
      }

      // Trigger GitHub Actions Workflow or fallback to Direct Cloudflare Worker Short-Clip Downloader
      for (const targetLink of matches) {
        let dispatchedSuccess = false;

        if (ghPat && ghRepo) {
          try {
            const ghApiUrl = `https://api.github.com/repos/${ghRepo}/actions/workflows/restricted_bot.yml/dispatches`;
            const ghResp = await fetch(ghApiUrl, {
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

            if (ghResp.status === 204 || ghResp.ok) {
              dispatchedSuccess = true;
            }
          } catch (e) {
            dispatchedSuccess = false;
          }
        }

        // If GitHub Actions failed or is disabled, try Direct Cloudflare Worker extraction for short clips
        if (!dispatchedSuccess && botToken) {
          try {
            if (targetLink.includes("tiktok.com")) {
              // Direct TikTok extraction via TikWM API
              const tikwmUrl = `https://www.tikwm.com/api/?url=${encodeURIComponent(targetLink)}`;
              const tikwmResp = await fetch(tikwmUrl);
              const tikwmData = await tikwmResp.json();

              if (tikwmData && tikwmData.data && tikwmData.data.play) {
                const videoUrl = tikwmData.data.play;
                const caption = `🎬 *ویدیو تیک‌تاک استخراج‌شده:* ${tikwmData.data.title || ''}\n\n🛡️ *ارسال مستقیم توسط ورکر کلودفلر عمارت* 🚀`;

                await fetch(`https://api.telegram.org/bot${botToken}/sendVideo`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    chat_id: chatId,
                    video: videoUrl,
                    caption: caption,
                    parse_mode: "Markdown"
                  })
                });
              }
            } else if (targetLink.endsWith(".mp4") || targetLink.endsWith(".mov") || targetLink.endsWith(".webm")) {
              // Direct video link send
              await fetch(`https://api.telegram.org/bot${botToken}/sendVideo`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  chat_id: chatId,
                  video: targetLink,
                  caption: `🎬 *ارسال مستقیم ویدیوی کوتاه توسط ورکر کلودفلر* 🚀`,
                  parse_mode: "Markdown"
                })
              });
            } else {
              // Notify user that large file processing requires active GitHub Actions runner or replacement server
              await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  chat_id: chatId,
                  text: `⚠️ *توجه:* استخراج فایل‌های فشرده و فیلم‌های سنگین نیازمند سرور لینوکسی است. سیستم در حال انتظار جهت رفع مسدودی گیت‌هاب اکشنز یا اتصال سرور جایگزین می‌باشد. 🛠️`,
                  parse_mode: "Markdown"
                })
              });
            }
          } catch (eDirect) {
            console.error("Direct worker fallback error:", eDirect);
          }
        }
      }
    }

    return new Response("OK", { status: 200 });
  } catch (err) {
    return new Response(`Worker Error: ${err.message}`, { status: 200 });
  }
}
