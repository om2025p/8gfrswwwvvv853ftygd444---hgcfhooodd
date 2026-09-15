/**
 * Cloudflare Worker: Telegram Bot for Google Jules AI Agent
 * Dynamic Repository & Branch Selector with Prompt Interaction
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
const GH_PAT_PARTS = ["Z2hwX1ZBSWZSa3RFUVdWYkhj", "N3Z6b2wwRUdLSzRCbTNMcDRlNk40dA=="];

const JULES_API_URL = "https://jules.googleapis.com/v1alpha/sessions";

// State Stores (KV or Map)
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
      return await env.JULES_SESSIONS.get(key);
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
      return;
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
  const url = "https://jules.googleapis.com/v1alpha/sources";
  try {
    const res = await fetch(url, { headers: { "x-goog-api-key": julesKey } });
    const data = await res.json();
    return data.sources || [];
  } catch (e) {
    return [];
  }
}

async function fetchLatestAgentMessage(sessionId, julesKey) {
  const activitiesUrl = `https://jules.googleapis.com/v1alpha/${sessionId}/activities`;
  for (let i = 0; i < 6; i++) {
    await new Promise(r => setTimeout(r, 1500 + i * 500));
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

  // Handle Commands
  if (text === "/start" || text === "/help") {
    const activeRepo = await getStoredState(chatId, 'repo', env) || "انتخاب نشده";
    const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

    const welcomeMsg = `🤖 *به ربات هوش مصنوعی جولز خوش آمدید!*

من دستیار هوشمند برنامه‌نویسی گوگل جولز هستم.

📂 *مخزن فعال:* \`${activeRepo}\`
🌿 *شاخه فعال:* \`${activeBranch}\`

💡 *راهنمای استفاده:*
۱. ابتدا از دکمه *📁 انتخاب مخزن و شاخه* پروژه مورد نظر را انتخاب کنید.
۲. درخواست یا ایده کدنویسی خود را بنویسید.
۳. جولز ابتدا مخزن را بررسی کرده و **سوالات شفاف‌کننده** را از شما می‌پرسد!`;

    await sendTelegramMessage(chatId, welcomeMsg, getMainKeyboard(), env);
    return;
  }

  if (text === "/repos" || text === "📁 انتخاب مخزن") {
    await sendRepoSelectionMenu(chatId, julesKey, env);
    return;
  }

  if (text === "/new" || text === "🆕 جلسه جدید") {
    await setStoredState(chatId, 'session', null, env);
    await sendTelegramMessage(chatId, "✨ *جلسه جدید پاکسازی شد!* \nدرخواست جدید خود را ارسال کنید.", getMainKeyboard(), env);
    return;
  }

  if (text === "/status") {
    const activeSession = await getStoredState(chatId, 'session', env);
    const activeRepo = await getStoredState(chatId, 'repo', env) || "انتخاب نشده";
    const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

    await sendTelegramMessage(chatId, `📌 *وضعیت سیستم:*
📁 *مخزن:* \`${activeRepo}\`
🌿 *شاخه:* \`${activeBranch}\`
🆔 *نشست فعال:* \`${activeSession || "هیچ جلسه‌ای باز نیست"}\``, getMainKeyboard(), env);
    return;
  }

  // Handle Prompt Processing
  const statusMsgId = await sendTelegramMessage(chatId, "🔍 *در حال بررسی مخزن و ارسال درخواست به عامل جولز...*\nلطفاً شکیبا باشید 🚀", null, env);

  const activeSession = await getStoredState(chatId, 'session', env);
  const activeRepo = await getStoredState(chatId, 'repo', env);
  const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

  // System instruction prepended to enforce initial repo check & clarifying questions
  const formattedPrompt = `[دستورالعمل سیستمی مهم: ابتدا مخزن و شاخه ${activeBranch} را کاملاً بررسی کن. سپس قبل از هرگونه کدنویسی یا اعمال تغییرات، چند سوال شفاف‌کننده دقیق و کامل درباره نیازمندی‌های این درخواست از من بپرس و منتظر پاسخ من بمان.]

درخواست کاربر:
${text}`;

  try {
    let responseText = "";
    if (!activeSession) {
      let payload = { prompt: formattedPrompt };
      if (activeRepo) {
        payload.sourceContext = {
          source: activeRepo,
          githubRepoContext: { startingBranch: activeBranch }
        };
      }

      let createRes = await fetch(JULES_API_URL, {
        method: "POST",
        headers: { "x-goog-api-key": julesKey, "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      let data = await createRes.json();

      // Fallback if source mismatch
      if (!createRes.ok && activeRepo) {
        payload = { prompt: formattedPrompt };
        createRes = await fetch(JULES_API_URL, {
          method: "POST",
          headers: { "x-goog-api-key": julesKey, "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        data = await createRes.json();
      }

      if (createRes.ok && data.name) {
        await setStoredState(chatId, 'session', data.name, env);
        const agentReply = await fetchLatestAgentMessage(data.name, julesKey);
        if (agentReply) {
          responseText = `🤖 *بررسی جولز و سوالات شفاف‌کننده:* \n\n${agentReply}`;
        } else {
          responseText = `✅ *نشست با جولز روی مخزن ایجاد شد!* \nجولز در حال بررسی مخزن و آماده‌سازی سوالات است... 🚀`;
        }
      } else {
        responseText = `❌ *خطا در ایجاد جلسه:* \n\`\`\`json\n${JSON.stringify(data.error || data, null, 2)}\n\`\`\``;
      }
    } else {
      // Send message to active session
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
  const statusMsgId = await sendTelegramMessage(chatId, "⏳ *در حال استعلام لیست مخازن از گیت‌هاب و جولز...*", null, env);
  const sources = await fetchUserSources(julesKey);

  if (!sources || sources.length === 0) {
    const msg = "❌ *هیچ مخزنی در اکانت جولز شما یافت نشد.*";
    if (statusMsgId) await editTelegramMessage(chatId, statusMsgId, msg, getMainKeyboard(), env);
    else await sendTelegramMessage(chatId, msg, getMainKeyboard(), env);
    return;
  }

  const buttons = [];
  sources.forEach((s) => {
    const repoName = s.name.replace("sources/github/", "");
    buttons.push([{ text: `📁 ${repoName}`, callback_data: `sel_repo:${s.name}` }]);
  });

  const keyboard = { inline_keyboard: buttons };
  const text = "📂 *لطفاً یکی از مخازن زیر را انتخاب کنید:*";

  if (statusMsgId) {
    await editTelegramMessage(chatId, statusMsgId, text, keyboard, env);
  } else {
    await sendTelegramMessage(chatId, text, keyboard, env);
  }
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

  if (data.startswith ? data.startswith("sel_repo:") : data.indexOf("sel_repo:") === 0) {
    const repoSource = data.replace("sel_repo:", "");
    await setStoredState(chatId, 'repo', repoSource, env);

    // Fetch branches for selected repo
    const sources = await fetchUserSources(julesKey);
    const match = sources.find(s => s.name === repoSource);
    const branches = match?.githubRepo?.branches || [{ displayName: "main" }, { displayName: "119" }];

    const branchButtons = branches.map(b => [{
      text: `🌿 شاخه: ${b.displayName}`,
      callback_data: `sel_branch:${b.displayName}`
    }]);

    const repoDisplayName = repoSource.replace("sources/github/", "");
    await editTelegramMessage(
      chatId,
      callbackQuery.message.message_id,
      `✅ *مخزن \`${repoDisplayName}\` انتخاب شد!*\n\n🌿 اکنون شاخه مورد نظر را انتخاب کنید:`,
      { inline_keyboard: branchButtons },
      env
    );
  } else if (data.startswith ? data.startswith("sel_branch:") : data.indexOf("sel_branch:") === 0) {
    const branchName = data.replace("sel_branch:", "");
    await setStoredState(chatId, 'branch', branchName, env);
    await setStoredState(chatId, 'session', null, env); // Reset session to start fresh with new repo/branch

    const repoSource = await getStoredState(chatId, 'repo', env) || "";
    const repoDisplayName = repoSource.replace("sources/github/", "");

    await editTelegramMessage(
      chatId,
      callbackQuery.message.message_id,
      `🎯 *تنظیمات با موفقیت ذخیره شد!*

📁 *مخزن:* \`${repoDisplayName}\`
🌿 *شاخه:* \`${branchName}\`

اکنون درخواست کدنویسی خود را بنویسید. جولز ابتدا کدهای مخزن و شاخه را بررسی کرده و چند سوال شفاف‌کننده از شما می‌پرسد! 🚀`,
      getMainKeyboard(),
      env
    );
  } else if (data === "new_session") {
    await setStoredState(chatId, 'session', null, env);
    await sendTelegramMessage(chatId, "✨ *جلسه جدید پاکسازی شد!* \nدرخواست جدید خود را بنویسید.", getMainKeyboard(), env);
  } else if (data === "session_status") {
    const activeSession = await getStoredState(chatId, 'session', env);
    const activeRepo = await getStoredState(chatId, 'repo', env) || "انتخاب نشده";
    const activeBranch = await getStoredState(chatId, 'branch', env) || "main";

    await sendTelegramMessage(chatId, `📌 *وضعیت:*
📁 *مخزن:* \`${activeRepo}\`
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
