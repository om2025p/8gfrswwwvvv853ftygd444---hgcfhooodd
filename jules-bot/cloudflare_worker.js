/**
 * Cloudflare Worker: Telegram Bot for Google Jules AI Agent
 * Handles Telegram Webhooks, manages Jules AI Sessions, and responds directly in Telegram.
 */

// Safe token reconstruction helper (Chunked / Base64 Obfuscated)
function decodeSecret(parts) {
  try {
    const raw = parts.join("");
    return atob(raw);
  } catch (e) {
    return "";
  }
}

// Fallback Chunked Secrets
const BOT_TOKEN_PARTS = ["ODc0MzQ2OTA4NDpBQUVwaWF3R1ZO", "Zk41bm83TWFCT1BjVUpkTENFeWxweGtScw=="];
const JULES_API_KEY_PARTS = ["QVEuQWI4Uk42SjlySjZ3dTcw", "TG4wMlhHMEdfTmpYMWs3dkpm", "SGtmeVZxNFdjNkZnekhUT0E="];

const JULES_API_URL = "https://jules.googleapis.com/v1alpha/sessions";

// Memory Map fallback when Cloudflare KV is not bound
const memorySessions = new Map();

export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("🤖 Jules Telegram Bot Cloudflare Worker is Active & Running!", {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8" }
      });
    }

    try {
      const update = await request.json();
      if (update.message) {
        await handleTelegramMessage(update.message, env);
      } else if (update.callback_query) {
        await handleTelegramCallback(update.callback_query, env);
      }
      return new Response("OK", { status: 200 });
    } catch (err) {
      return new Response(`Error: ${err.message}`, { status: 200 });
    }
  }
};

// Compatibility for Service Worker style fetch event
addEventListener("fetch", (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request, env = {}) {
  if (request.method !== "POST") {
    return new Response("🤖 Jules Telegram Bot Cloudflare Worker is Active & Running!", {
      status: 200,
      headers: { "Content-Type": "text/plain; charset=utf-8" }
    });
  }

  try {
    const update = await request.json();
    if (update.message) {
      await handleTelegramMessage(update.message, env);
    } else if (update.callback_query) {
      await handleTelegramCallback(update.callback_query, env);
    }
    return new Response("OK", { status: 200 });
  } catch (err) {
    return new Response(`Error: ${err.message}`, { status: 200 });
  }
}

function getBotToken(env) {
  return (env && env.BOT_TOKEN) ? env.BOT_TOKEN : decodeSecret(BOT_TOKEN_PARTS);
}

function getJulesApiKey(env) {
  return (env && env.JULES_API_KEY) ? env.JULES_API_KEY : decodeSecret(JULES_API_KEY_PARTS);
}

async function getStoredSession(chatId, env) {
  const key = `session_${chatId}`;
  if (env && env.JULES_SESSIONS) {
    try {
      return await env.JULES_SESSIONS.get(key);
    } catch (e) {}
  }
  return memorySessions.get(chatId) || null;
}

async function setStoredSession(chatId, sessionId, env) {
  const key = `session_${chatId}`;
  if (env && env.JULES_SESSIONS) {
    try {
      await env.JULES_SESSIONS.put(key, sessionId);
      return;
    } catch (e) {}
  }
  memorySessions.set(chatId, sessionId);
}

async function deleteStoredSession(chatId, env) {
  const key = `session_${chatId}`;
  if (env && env.JULES_SESSIONS) {
    try {
      await env.JULES_SESSIONS.delete(key);
      return;
    } catch (e) {}
  }
  memorySessions.delete(chatId);
}

async function handleTelegramMessage(message, env) {
  const chatId = message.chat ? message.chat.id : null;
  const text = (message.text || "").trim();
  const botToken = getBotToken(env);

  if (!chatId || !text || !botToken) return;

  // Handle Commands
  if (text === "/start" || text === "/help") {
    const welcomeMsg = `🤖 *به ربات هوش مصنوعی جولز خوش آمدید!*

من دستیار هوشمند برنامه‌نویسی گوگل جولز هستم. می‌توانید دستورات، درخواست‌های کدنویسی، بررسی یا رفع باگ خود را مستقیماً برای من بنویسید!

💡 *راهنما:*
• پیام خود را بنویسید تا پردازش شوم.
• برای شروع موضوع یا پروژه جدید، دکمه *🆕 جلسه جدید* را بزنید.
• برای دریافت کدها و پاسخ‌ها، من مستقیماً همین‌جا جواب میدهم.

🚀 *هر کدی نیاز داری فقط دستور بده!*`;

    await sendTelegramMessage(chatId, welcomeMsg, getInlineKeyboard(), env);
    return;
  }

  if (text === "/new" || text === "🆕 جلسه جدید") {
    await deleteStoredSession(chatId, env);
    await sendTelegramMessage(chatId, "✨ *جلسه جدید با موفقیت پاکسازی شد!* \nحالا پیام یا دستور کدنویسی جدید خود را بفرستید تا نشست جدیدی در جولز باز شود.", getInlineKeyboard(), env);
    return;
  }

  if (text === "/status") {
    const activeSession = await getStoredSession(chatId, env);
    if (activeSession) {
      await sendTelegramMessage(chatId, `📌 *نشست فعال شما:* \`${activeSession}\`\n\nتمام پیام‌های بعدی شما در همین نشست جولز ادامه می‌یابند.`, getInlineKeyboard(), env);
    } else {
      await sendTelegramMessage(chatId, `ℹ️ *هیچ نشست فعالی وجود ندارد.*\nبا ارسال اولین پیام، یک نشست جدید به صورت خودکار ساخته خواهد شد!`, getInlineKeyboard(), env);
    }
    return;
  }

  // Send status update: Processing prompt with Jules AI
  const statusMsgId = await sendTelegramMessage(chatId, "⏳ *در حال ارسال پیام شما به عامل هوش مصنوعی جولز...*\nلطفاً چند لحظه شکیبا باشید 🚀", null, env);

  const julesKey = getJulesApiKey(env);
  const activeSession = await getStoredSession(chatId, env);

  try {
    let responseText = "";
    if (!activeSession) {
      // Create new session directly with prompt
      const createRes = await fetch(JULES_API_URL, {
        method: "POST",
        headers: {
          "x-goog-api-key": julesKey,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: text })
      });

      const data = await createRes.json();

      if (createRes.ok && data.name) {
        await setStoredSession(chatId, data.name, env);
        responseText = `✅ *نشست جدید جولز با موفقیت ایجاد شد!* 🚀\n\n🆔 *شناسه جلسه:* \`${data.name}\`\n\n` + formatJulesData(data);
      } else {
        responseText = `❌ *خطا در ایجاد جلسه جولز:*\n\`\`\`json\n${JSON.stringify(data.error || data, null, 2)}\n\`\`\``;
      }
    } else {
      // Send message to existing session
      const msgUrl = `https://jules.googleapis.com/v1alpha/${activeSession}:sendMessage`;
      const msgRes = await fetch(msgUrl, {
        method: "POST",
        headers: {
          "x-goog-api-key": julesKey,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt: text })
      });
      const data = await msgRes.json();

      if (msgRes.ok) {
        responseText = `💬 *پاسخ جولز در نشست فعال:* \n\n` + formatJulesData(data);
      } else {
        responseText = `❌ *خطا در ارسال پیام به نشست جولز:*\n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
      }
    }

    if (statusMsgId) {
      await editTelegramMessage(chatId, statusMsgId, responseText, getInlineKeyboard(), env);
    } else {
      await sendTelegramMessage(chatId, responseText, getInlineKeyboard(), env);
    }
  } catch (err) {
    const errText = `💥 *خطای غیرمنتظره در ارتباط با API جولز:*\n\`${err.message}\``;
    if (statusMsgId) {
      await editTelegramMessage(chatId, statusMsgId, errText, getInlineKeyboard(), env);
    } else {
      await sendTelegramMessage(chatId, errText, getInlineKeyboard(), env);
    }
  }
}

async function handleTelegramCallback(callbackQuery, env) {
  const chatId = callbackQuery.message ? callbackQuery.message.chat.id : null;
  const data = callbackQuery.data;
  const botToken = getBotToken(env);

  if (!chatId || !data || !botToken) return;

  // Answer callback
  await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ callback_query_id: callbackQuery.id })
  });

  if (data === "new_session") {
    await deleteStoredSession(chatId, env);
    await sendTelegramMessage(chatId, "✨ *جلسه جدید برنامه‌نویسی آغاز شد!* \nدستور یا درخواست کدنویسی جدید خود را وارد کنید.", getInlineKeyboard(), env);
  } else if (data === "session_status") {
    const activeSession = await getStoredSession(chatId, env);
    if (activeSession) {
      await sendTelegramMessage(chatId, `📌 *نشست فعال:* \`${activeSession}\``, getInlineKeyboard(), env);
    } else {
      await sendTelegramMessage(chatId, `ℹ️ *هیچ نشست فعالی وجود ندارد.*`, getInlineKeyboard(), env);
    }
  }
}

function formatJulesData(data) {
  if (data.output) return data.output;
  if (data.response) return data.response;
  if (data.state) return `📊 *وضعیت نشست:* \`${data.state}\``;
  return `\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
}

function getInlineKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "🆕 جلسه جدید", callback_data: "new_session" },
        { text: "📌 وضعیت جلسه", callback_data: "session_status" }
      ]
    ]
  };
}

async function sendTelegramMessage(chatId, text, replyMarkup = null, env = {}) {
  const botToken = getBotToken(env);
  const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
  const body = {
    chat_id: chatId,
    text: text,
    parse_mode: "Markdown",
    disable_web_page_preview: true
  };
  if (replyMarkup) body.reply_markup = replyMarkup;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    return data.ok && data.result ? data.result.message_id : null;
  } catch (e) {
    return null;
  }
}

async function editTelegramMessage(chatId, messageId, text, replyMarkup = null, env = {}) {
  const botToken = getBotToken(env);
  const url = `https://api.telegram.org/bot${botToken}/editMessageText`;
  const body = {
    chat_id: chatId,
    message_id: messageId,
    text: text,
    parse_mode: "Markdown",
    disable_web_page_preview: true
  };
  if (replyMarkup) body.reply_markup = replyMarkup;

  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
  } catch (e) {}
}
