/**
 * Cloudflare Worker: Telegram Bot for Google Jules AI Agent
 * Dynamic Repository & Branch Selector with Fast Memory Caching & Callback Data Compression
 */

function decodeSecret(parts) {
  try {
    return atob(parts.join(""));
  } catch (e) {
    return "";
  }
}

// Fallback Chunked Secrets
const BOT_TOKEN_PARTS = ["ODc0MzQ2OTA4NDpBQUVwaWF3R1ZO", "Zk41bm83TWFCT1BjVUpkTENFeWxweGtScw=="];
const JULES_API_KEY_PARTS = ["QVEuQWI4Uk42SjlySjZ3dTcw", "TG4wMlhHMEdfTmpYMWs3dkpm", "SGtmeVZxNFdjNkZnekhUT0E="];

const JULES_API_URL = "https://jules.googleapis.com/v1alpha/sessions";

// Fast Global Sources Cache
let cachedSources = null;
let lastCacheTime = 0;

// State Stores
const userSessions = new Map();
const userSelectedRepo = new Map();
const userSelectedBranch = new Map();

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

async function getStoredState(chatId, keyPrefix, env) {
  const key = `${keyPrefix}_${chatId}`;
  if (env && env.JULES_SESSIONS) {
    try {
      const val = await env.JULES_SESSIONS.get(key);
      if (val) return val;
    } catch (e) {}
  }
  if (keyPrefix === 'session') return userSessions.get(chatId) || null;
  if (keyPrefix === 'repo') return userSelectedRepo.get(chatId) || null;
  if (keyPrefix === 'branch') return userSelectedBranch.get(chatId) || null;
  return null;
}

async function setStoredState(chatId, keyPrefix, value, env) {
  const key = `${keyPrefix}_${chatId}`;
  if (env && env.JULES_SESSIONS) {
    try {
      if (value === null) await env.JULES_SESSIONS.delete(key);
      else await env.JULES_SESSIONS.put(key, value);
    } catch (e) {}
  }
  if (keyPrefix === 'session') {
    if (value === null) userSessions.delete(chatId);
    else userSessions.set(chatId, value);
  }
  if (keyPrefix === 'repo') {
    if (value === null) userSelectedRepo.delete(chatId);
    else userSelectedRepo.set(chatId, value);
  }
  if (keyPrefix === 'branch') {
    if (value === null) userSelectedBranch.delete(chatId);
    else userSelectedBranch.set(chatId, value);
  }
}

async function fetchUserSources(julesKey) {
  const now = Date.now();
  if (cachedSources && (now - lastCacheTime < 300000)) {
    return cachedSources;
  }

  const url = "https://jules.googleapis.com/v1alpha/sources";
  try {
    const res = await fetch(url, { headers: { "x-goog-api-key": julesKey } });
    const data = await res.json();
    if (data && data.sources) {
      cachedSources = data.sources;
      lastCacheTime = now;
      return cachedSources;
    }
    return [];
  } catch (e) {
    return cachedSources || [];
  }
}

async function fetchLatestAgentMessage(sessionId, julesKey) {
  const activitiesUrl = `https://jules.googleapis.com/v1alpha/${sessionId}/activities`;
  for (let i = 0; i < 4; i++) {
    await new Promise(r => setTimeout(r, 1000));
    try {
      const res = await fetch(activitiesUrl, {
        headers: { "x-goog-api-key": julesKey }
      });
      const data = await res.json();
      if (data && data.activities && Array.isArray(data.activities)) {
        const agentActs = data.activities.filter(a => a.originator === "agent" || a.agentMessaged);
        if (agentActs.length > 0) {
          const lastAct = agentActs[agentActs.length - 1];
          if (lastAct.agentMessaged && lastAct.agentMessaged.agentMessage) {
            return lastAct.agentMessaged.agentMessage;
          }
        }
      }
    } catch (e) {}
  }
  return null;
}

async function handleTelegramMessage(message, env) {
  const chatId = message.chat ? message.chat.id : null;
  const text = (message.text || "").trim();
  const botToken = getBotToken(env);

  if (!chatId || !text || !botToken) return;

  const julesKey = getJulesApiKey(env);

  // Commands
  if (text === "/start" || text === "/help") {
    const activeRepo = await getStoredState(chatId, 'repo', env) || "انتخاب نشده ❌";
    const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

    const welcomeMsg = `🤖 *به ربات هوش مصنوعی جولز خوش آمدید!*

📁 *مخزن فعال:* \`${activeRepo.replace("sources/github/", "")}\`
🌿 *شاخه فعال:* \`${activeBranch}\`

💡 *راهنمای سریع:*
۱. ابتدا روی دکمه *📁 انتخاب مخزن* بزنید.
۲. درخواست یا سفارش کدنویسی خود را بفرستید.
۳. جولز ابتدا کدهای مخزن را تحلیل کرده و سوالات شفاف‌کننده از شما می‌پرسد!`;

    await sendTelegramMessage(chatId, welcomeMsg, getMainKeyboard(), env);
    return;
  }

  if (text === "/repos" || text === "📁 انتخاب مخزن") {
    await sendRepoSelectionMenu(chatId, julesKey, env);
    return;
  }

  if (text === "/new" || text === "🆕 جلسه جدید") {
    await setStoredState(chatId, 'session', null, env);
    await sendTelegramMessage(chatId, "✨ *جلسه جدید پاکسازی شد!* \nدرخواست یا ایده جدید خود را ارسال کنید.", getMainKeyboard(), env);
    return;
  }

  if (text === "/status") {
    const activeSession = await getStoredState(chatId, 'session', env);
    const activeRepo = await getStoredState(chatId, 'repo', env) || "انتخاب نشده ❌";
    const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

    await sendTelegramMessage(chatId, `📌 *وضعیت سیستم:*
📁 *مخزن:* \`${activeRepo.replace("sources/github/", "")}\`
🌿 *شاخه:* \`${activeBranch}\`
🆔 *نشست:* \`${activeSession || "بدون نشست"}\``, getMainKeyboard(), env);
    return;
  }

  // Ensure Repo selection
  const activeRepo = await getStoredState(chatId, 'repo', env);
  const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

  if (!activeRepo) {
    await sendTelegramMessage(chatId, "⚠️ *لطفاً ابتدا مخزن و شاخه پروژه را انتخاب کنید!*", null, env);
    await sendRepoSelectionMenu(chatId, julesKey, env);
    return;
  }

  // Handle Prompt Processing
  const statusMsgId = await sendTelegramMessage(chatId, `🔍 *در حال استخراج کدهای مخزن \`${activeRepo.replace("sources/github/", "")}\` (شاخه ${activeBranch})...*\nلطفاً چند لحظه شکیبا باشید 🚀`, null, env);

  const activeSession = await getStoredState(chatId, 'session', env);

  const formattedPrompt = `[دستورالعمل سیستمی مهم: ابتدا تمام کدهای مخزن و شاخه ${activeBranch} را کاملاً بررسی و تحلیل کن. سپس قبل از هرگونه تغییر یا کدنویسی، چند سوال شفاف‌کننده و دقیق درباره این درخواست از من بپرس و منتظر پاسخ من بمان.]

درخواست کاربر:
${text}`;

  try {
    let responseText = "";
    if (!activeSession) {
      let payload = {
        prompt: formattedPrompt,
        sourceContext: {
          source: activeRepo,
          githubRepoContext: { startingBranch: activeBranch }
        }
      };

      let createRes = await fetch(JULES_API_URL, {
        method: "POST",
        headers: { "x-goog-api-key": julesKey, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      let data = await createRes.json();

      if (createRes.ok && data.name) {
        await setStoredState(chatId, 'session', data.name, env);
        const agentReply = await fetchLatestAgentMessage(data.name, julesKey);
        if (agentReply) {
          responseText = `🤖 *بررسی اولیه جولز و سوالات شفاف‌کننده:* \n\n${agentReply}`;
        } else {
          responseText = `✅ *نشست جدید جولز روی مخزن ایجاد شد!* \n🆔 *شناسه جلسه:* \`${data.name}\`\n\nجولز در حال بررسی کدهاست و به‌زودی سوالات خود را مطرح خواهد کرد...`;
        }
      } else {
        responseText = `❌ *خطا در اتصال به مخزن انتخاب‌شده:*\n\`\`\`json\n${JSON.stringify(data.error || data, null, 2)}\n\`\`\``;
      }
    } else {
      const msgUrl = `https://jules.googleapis.com/v1alpha/${activeSession}:sendMessage`;
      const msgRes = await fetch(msgUrl, {
        method: "POST",
        headers: { "x-goog-api-key": julesKey, "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text })
      });

      if (msgRes.ok) {
        const agentReply = await fetchLatestAgentMessage(activeSession, julesKey);
        if (agentReply) {
          responseText = `🤖 *پاسخ جولز:* \n\n${agentReply}`;
        } else {
          responseText = `✅ *پاسخ شما ارسال شد.* جولز در حال تحلیل و پاسخ‌دهی است...`;
        }
      } else {
        const data = await msgRes.json();
        responseText = `❌ *خطا در ارسال پیام:* \n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
      }
    }

    if (statusMsgId) {
      await editTelegramMessage(chatId, statusMsgId, responseText, getMainKeyboard(), env);
    } else {
      await sendTelegramMessage(chatId, responseText, getMainKeyboard(), env);
    }
  } catch (err) {
    const errText = `💥 *خطا:* \`${err.message}\``;
    if (statusMsgId) {
      await editTelegramMessage(chatId, statusMsgId, errText, getMainKeyboard(), env);
    } else {
      await sendTelegramMessage(chatId, errText, getMainKeyboard(), env);
    }
  }
}

async function sendRepoSelectionMenu(chatId, julesKey, env) {
  const sources = await fetchUserSources(julesKey);

  if (!sources || sources.length === 0) {
    await sendTelegramMessage(chatId, "❌ *هیچ مخزنی در اکانت جولز شما یافت نشد.*", getMainKeyboard(), env);
    return;
  }

  // Use short indexed callback_data to strictly respect Telegram's 64-byte limit!
  const topSources = sources.slice(0, 10);
  const buttons = [];
  topSources.forEach((s, idx) => {
    const repoName = s.name.replace("sources/github/", "");
    buttons.push([{ text: `📁 ${repoName}`, callback_data: `r:${idx}` }]);
  });

  const keyboard = { inline_keyboard: buttons };
  const text = "📂 *لطفاً مخزن مورد نظر برای بررسی کدها را انتخاب کنید:*";

  await sendTelegramMessage(chatId, text, keyboard, env);
}

async function handleTelegramCallback(callbackQuery, env) {
  const chatId = callbackQuery.message ? callbackQuery.message.chat.id : null;
  const data = callbackQuery.data;
  const botToken = getBotToken(env);
  const julesKey = getJulesApiKey(env);

  if (!chatId || !data || !botToken) return;

  await fetch(`https://api.telegram.org/bot${botToken}/answerCallbackQuery`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ callback_query_id: callbackQuery.id })
  });

  if (data === "new_repo_select") {
    await sendRepoSelectionMenu(chatId, julesKey, env);
    return;
  }

  // Handle compressed repo index callback (e.g. r:0)
  if (data.indexOf("r:") === 0) {
    const repoIdx = parseInt(data.replace("r:", ""), 10);
    const sources = await fetchUserSources(julesKey);
    const selectedSource = sources[repoIdx];

    if (!selectedSource) {
      await sendTelegramMessage(chatId, "❌ *مخزن نامعتبر است.*", getMainKeyboard(), env);
      return;
    }

    await setStoredState(chatId, 'repo', selectedSource.name, env);

    const branches = selectedSource.githubRepo?.branches || [{ displayName: "main" }, { displayName: "119" }];

    // Use short branch index callback (e.g. b:0)
    const branchButtons = branches.slice(0, 8).map((b, idx) => [{
      text: `🌿 شاخه: ${b.displayName}`,
      callback_data: `b:${idx}`
    }]);

    const repoDisplayName = selectedSource.name.replace("sources/github/", "");
    await editTelegramMessage(
      chatId,
      callbackQuery.message.message_id,
      `✅ *مخزن \`${repoDisplayName}\` انتخاب شد!*\n\n🌿 اکنون شاخه مورد نظر خود را انتخاب کنید:`,
      { inline_keyboard: branchButtons },
      env
    );
  } else if (data.indexOf("b:") === 0) {
    const branchIdx = parseInt(data.replace("b:", ""), 10);
    const repoSource = await getStoredState(chatId, 'repo', env) || "";
    const sources = await fetchUserSources(julesKey);
    const selectedSource = sources.find(s => s.name === repoSource) || sources[0];

    const branches = selectedSource?.githubRepo?.branches || [{ displayName: "main" }, { displayName: "119" }];
    const selectedBranch = branches[branchIdx] ? branches[branchIdx].displayName : "main";

    await setStoredState(chatId, 'branch', selectedBranch, env);
    await setStoredState(chatId, 'session', null, env);

    const repoDisplayName = repoSource.replace("sources/github/", "");

    await editTelegramMessage(
      chatId,
      callbackQuery.message.message_id,
      `🎯 *تنظیمات با موفقیت انجام شد!*

📁 *مخزن:* \`${repoDisplayName}\`
🌿 *شاخه:* \`${selectedBranch}\`

اکنون درخواست کدنویسی خود را بفرستید. جولز ابتدا کدهای این مخزن را بررسی کرده و سوالات شفاف‌کننده از شما می‌پرسد! 🚀`,
      getMainKeyboard(),
      env
    );
  } else if (data === "new_session") {
    await setStoredState(chatId, 'session', null, env);
    await sendTelegramMessage(chatId, "✨ *جلسه جدید پاکسازی شد!* \nدرخواست جدید خود را بنویسید.", getMainKeyboard(), env);
  } else if (data === "session_status") {
    const activeSession = await getStoredState(chatId, 'session', env);
    const activeRepo = await getStoredState(chatId, 'repo', env) || "انتخاب نشده ❌";
    const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

    await sendTelegramMessage(chatId, `📌 *وضعیت فعلی سیستم:*
📁 *مخزن:* \`${activeRepo.replace("sources/github/", "")}\`
🌿 *شاخه:* \`${activeBranch}\`
🆔 *نشست:* \`${activeSession || "بدون نشست"}\``, getMainKeyboard(), env);
  }
}

function getMainKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: "📁 انتخاب مخزن", callback_data: "new_repo_select" },
        { text: "🆕 جلسه جدید", callback_data: "new_session" }
      ],
      [
        { text: "📌 وضعیت سیستم", callback_data: "session_status" }
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
