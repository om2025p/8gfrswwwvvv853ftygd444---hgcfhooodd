/* ==========================================================================
   مغز دوم — معماری ماژولار کلاینت هوش مصنوعی با پشتیبانی کامل آفلاین از ابزارها
   بخش‌های منطقی: StorageManager, ErrorManager, SettingsManager,
   SystemPromptManager, ConversationManager, OpenRouterClient, StreamingManager,
   CodeRenderer, JSONRenderer, ChartRenderer, MarkdownRenderer,
   ComposerManager, AppController
   ========================================================================== */
(function () {
  'use strict';

  /* ---------- توابع کمکی عمومی ---------- */
  const $ = (id) => document.getElementById(id);

  function uid(prefix = 'id') {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      return `${prefix}_${window.crypto.randomUUID()}`;
    }
    return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
  }

  function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function safeUrl(url) {
    try {
      const parsed = new URL(String(url).trim(), window.location.href);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        return parsed.href;
      }
    } catch (_) {}
    return '';
  }

  function formatDuration(ms) {
    if (!Number.isFinite(ms) || ms < 0) return '';
    if (ms < 1000) return `${Math.round(ms)} ms`;
    return `${(ms / 1000).toFixed(1)} s`;
  }

  function formatTimeFa(ts) {
    try {
      return new Date(ts).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
    } catch (_) {
      return '';
    }
  }

  function downloadBlob(content, filename, mimeType = 'text/plain;charset=utf-8') {
    const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 150);
  }

  async function copyToClipboard(text) {
    const val = String(text ?? '');
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(val);
      return true;
    }
    const ta = document.createElement('textarea');
    ta.value = val;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    if (!ok) throw new Error('COPY_FAILED');
    return true;
  }

  /* ==========================================================================
     1. ErrorManager — مدیریت خطاهای شبکه، سرویس، کتابخانه و حافظه
     ========================================================================== */
  class ErrorManager {
    static toast(message, type = 'info', duration = 3200) {
      const container = $('toastContainer');
      if (!container) return;
      const el = document.createElement('div');
      el.className = `toast ${type}`;
      el.textContent = message;
      container.appendChild(el);
      setTimeout(() => {
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 220);
      }, duration);
    }

    static formatApiError(status, bodyText) {
      let detail = '';
      try {
        const parsed = JSON.parse(bodyText);
        detail = parsed?.error?.message || parsed?.message || '';
      } catch (_) {
        detail = (bodyText || '').slice(0, 180);
      }

      if (!navigator.onLine) {
        return 'اتصال اینترنت شما قطع است. لطفاً شبکه را بررسی کنید (نوشته شما محفوظ ماند).';
      }
      if (status === 401) {
        return 'کلید دسترسی نامعتبر یا منقضی است (کد ۴۰۱). لطفاً کلید خود را در تنظیمات بررسی کنید.';
      }
      if (status === 402) {
        return 'اعتبار حساب کاربری شما کافی نیست (کد ۴۰۲). می‌توانید از فهرست مدل‌های رایگان استفاده کنید.';
      }
      if (status === 403) {
        return 'دسترسی به این مدل یا سرویس مجاز نیست (کد ۴۰۳).' + (detail ? ` (${detail})` : '');
      }
      if (status === 404) {
        return 'مدل انتخاب‌شده یافت نشد یا نامعتبر است (کد ۴۰۴). مدل دیگری انتخاب کنید.';
      }
      if (status === 429) {
        return 'محدودیت تعداد درخواست در دقیقه (کد ۴۲۹). چند لحظه صبر کرده و دوباره تلاش کنید.';
      }
      if (status >= 500) {
        return `خطای موقت در سرور سرویس‌دهنده (کد ${status}). لطفاً کمی بعد دوباره امتحان کنید.`;
      }
      if (status === 400 && /token|context|length/i.test(detail)) {
        return `طول متن از ظرفیت مجاز مدل بیشتر است: ${detail}`;
      }
      return `خطا در ارتباط با سرویس (کد ${status || 'نامشخص'}): ${detail || 'پاسخ نامعتبر دریافت شد.'}`;
    }

    static formatNetworkError(err) {
      if (err?.name === 'AbortError') {
        return 'تولید پاسخ به دستور شما متوقف شد.';
      }
      if (!navigator.onLine) {
        return 'اینترنت دستگاه قطع شده است. نوشته شما در کادر باقی ماند.';
      }
      const msg = String(err?.message || '');
      if (/Failed to fetch|NetworkError|Load failed|ERR_NAME_NOT_RESOLVED/i.test(msg)) {
        return 'برقراری ارتباط با سرور ممکن نشد (احتمالاً خطای DNS، فیلتر یا قطع شبکه).';
      }
      return msg || 'خطای پیش‌بینی‌نشده در ارسال درخواست رخ داد.';
    }
  }

  /* ==========================================================================
     2. StorageManager — مدیریت ذخیره‌سازی امن در IndexedDB و LocalStorage
     ========================================================================== */
  class StorageManager {
    constructor() {
      this.dbName = 'SecondBrainDB';
      this.dbVersion = 1;
      this.db = null;
      this.memoryFallback = new Map();
    }

    async init() {
      if (!('indexedDB' in window)) {
        ErrorManager.toast('مرورگر از پایگاه داده پیشرفته پشتیبانی نمی‌کند؛ حالت حافظه موقت فعال شد.', 'err');
        return;
      }
      return new Promise((resolve) => {
        try {
          const req = indexedDB.open(this.dbName, this.dbVersion);
          req.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('conversations')) {
              db.createObjectStore('conversations', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains('secrets')) {
              db.createObjectStore('secrets', { keyPath: 'key' });
            }
            if (!db.objectStoreNames.contains('presets')) {
              db.createObjectStore('presets', { keyPath: 'id' });
            }
          };
          req.onsuccess = (e) => {
            this.db = e.target.result;
            resolve();
          };
          req.onerror = () => {
            ErrorManager.toast('خطا در باز کردن پایگاه داده محلی مرورگر.', 'err');
            resolve();
          };
        } catch (_) {
          resolve();
        }
      });
    }

    async put(storeName, value) {
      if (!this.db) {
        this.memoryFallback.set(`${storeName}:${value.id || value.key}`, value);
        return;
      }
      return new Promise((resolve, reject) => {
        try {
          const tx = this.db.transaction(storeName, 'readwrite');
          tx.objectStore(storeName).put(value);
          tx.oncomplete = () => resolve();
          tx.onerror = () => reject(tx.error);
        } catch (err) {
          reject(err);
        }
      });
    }

    async get(storeName, key) {
      if (!this.db) {
        return this.memoryFallback.get(`${storeName}:${key}`) || null;
      }
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction(storeName, 'readonly');
          const req = tx.objectStore(storeName).get(key);
          req.onsuccess = () => resolve(req.result || null);
          req.onerror = () => resolve(null);
        } catch (_) {
          resolve(null);
        }
      });
    }

    async getAll(storeName) {
      if (!this.db) {
        const res = [];
        for (const [k, v] of this.memoryFallback.entries()) {
          if (k.startsWith(`${storeName}:`)) res.push(v);
        }
        return res;
      }
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction(storeName, 'readonly');
          const req = tx.objectStore(storeName).getAll();
          req.onsuccess = () => resolve(req.result || []);
          req.onerror = () => resolve([]);
        } catch (_) {
          resolve([]);
        }
      });
    }

    async delete(storeName, key) {
      if (!this.db) {
        this.memoryFallback.delete(`${storeName}:${key}`);
        return;
      }
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction(storeName, 'readwrite');
          tx.objectStore(storeName).delete(key);
          tx.oncomplete = () => resolve();
          tx.onerror = () => resolve();
        } catch (_) {
          resolve();
        }
      });
    }

    async clearStore(storeName) {
      if (!this.db) {
        for (const k of [...this.memoryFallback.keys()]) {
          if (k.startsWith(`${storeName}:`)) this.memoryFallback.delete(k);
        }
        return;
      }
      return new Promise((resolve) => {
        try {
          const tx = this.db.transaction(storeName, 'readwrite');
          tx.objectStore(storeName).clear();
          tx.oncomplete = () => resolve();
          tx.onerror = () => resolve();
        } catch (_) {
          resolve();
        }
      });
    }

    getLocal(key, fallback = null) {
      try {
        const raw = localStorage.getItem(key);
        return raw !== null ? JSON.parse(raw) : fallback;
      } catch (_) {
        return fallback;
      }
    }

    setLocal(key, val) {
      try {
        localStorage.setItem(key, JSON.stringify(val));
      } catch (_) {
        ErrorManager.toast('حافظه تنظیمات مرورگر پر یا مسدود است.', 'err');
      }
    }
  }

  /* ==========================================================================
     3. SettingsManager — تنظیمات مدل، تم مهربان با چشم، فونت و مدل‌های رایگان
     ========================================================================== */
  const FREE_CURATED_MODELS = [
    { id: 'openrouter/free', name: 'مسیریاب هوشمند مدل‌های رایگان (خودکار)', isFree: true, context_length: 128000 },
    { id: 'google/gemini-2.0-flash-exp:free', name: 'جمنای ۲ فلش آزمایشی (رایگان)', isFree: true, context_length: 1048576 },
    { id: 'meta-llama/llama-3.3-70b-instruct:free', name: 'لاما ۳.۳ ۷۰ میلیارد (رایگان)', isFree: true, context_length: 131072 },
    { id: 'deepseek/deepseek-r1:free', name: 'دیپ‌سیک R1 استدلالگر (رایگان)', isFree: true, context_length: 163840 },
    { id: 'qwen/qwen-2.5-72b-instruct:free', name: 'کوئن ۲.۵ ۷۲ میلیارد (رایگان)', isFree: true, context_length: 32768 },
    { id: 'mistralai/mistral-small-3.1-24b-instruct:free', name: 'میسترال اسمال ۳.۱ ۲۴ میلیارد (رایگان)', isFree: true, context_length: 96000 },
    { id: 'google/gemini-2.5-flash', name: 'جمنای ۲.۵ فلش (اقتصادی و سریع)', isFree: false, context_length: 1048576 }
  ];

  class SettingsManager {
    constructor(storage) {
      this.storage = storage;
      this.STORAGE_KEY = 'sb_settings_v1';
      this.MODELS_CACHE_KEY = 'sb_models_cache_v1';
      this.apiKey = '';
      this.defaults = {
        baseUrl: 'https://openrouter.ai/api/v1',
        modelId: 'google/gemini-2.0-flash-exp:free',
        maxTokens: 4096,
        temperature: 0.7,
        topP: 1.0,
        frequencyPenalty: 0,
        presencePenalty: 0,
        contextLimit: 20,
        streaming: true,
        webSearchEnabled: false,
        theme: 'dark',
        fontFamily: "'Vazirmatn', system-ui, Tahoma, sans-serif",
        fontSize: 15,
        codeTheme: 'auto',
        richMarkdown: true,
        underlineAndCallouts: true,
        freeModelsOnly: true
      };
      this.data = { ...this.defaults };
      this.models = [...FREE_CURATED_MODELS];
    }

    async load() {
      const saved = this.storage.getLocal(this.STORAGE_KEY, null);
      if (saved && typeof saved === 'object') {
        this.data = { ...this.defaults, ...saved };
      }
      const cachedModels = this.storage.getLocal(this.MODELS_CACHE_KEY, null);
      if (Array.isArray(cachedModels) && cachedModels.length > 0) {
        this.mergeModels(cachedModels);
      }
      const secretRec = await this.storage.get('secrets', 'openrouter_api_key');
      this.apiKey = secretRec && typeof secretRec.value === 'string' ? secretRec.value : '';
      this.applyVisualSettings();
    }

    save() {
      this.storage.setLocal(this.STORAGE_KEY, this.data);
      this.applyVisualSettings();
    }

    async setApiKey(key) {
      this.apiKey = String(key || '').trim();
      if (this.apiKey) {
        await this.storage.put('secrets', { key: 'openrouter_api_key', value: this.apiKey });
      } else {
        await this.storage.delete('secrets', 'openrouter_api_key');
      }
    }

    normalizeModelId(rawId) {
      let id = String(rawId || '').trim();
      if (id.startsWith('openrouter/') && id !== 'openrouter/free' && id !== 'openrouter/auto') {
        id = id.slice('openrouter/'.length);
      }
      return id;
    }

    mergeModels(remoteList) {
      const map = new Map();
      for (const m of FREE_CURATED_MODELS) {
        map.set(m.id, m);
      }
      for (const item of remoteList) {
        if (!item || !item.id) continue;
        const pPrompt = Number(item.pricing?.prompt ?? item.promptPrice ?? -1);
        const pComp = Number(item.pricing?.completion ?? item.completionPrice ?? -1);
        const isFree = item.isFree === true ||
          item.id.endsWith(':free') ||
          item.id === 'openrouter/free' ||
          (pPrompt === 0 && pComp === 0);
        map.set(item.id, {
          id: item.id,
          name: item.name || item.id,
          isFree,
          context_length: item.context_length || 0
        });
      }
      this.models = Array.from(map.values()).sort((a, b) => {
        if (a.isFree !== b.isFree) return a.isFree ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
    }

    cacheModels(list) {
      this.mergeModels(list);
      this.storage.setLocal(this.MODELS_CACHE_KEY, this.models.slice(0, 350));
    }

    applyVisualSettings() {
      const theme = this.data.theme === 'light' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', theme);
      const metaTheme = $('metaThemeColor');
      if (metaTheme) {
        metaTheme.setAttribute('content', theme === 'light' ? '#f3efe6' : '#121417');
      }
      document.documentElement.style.setProperty('--sb-font', this.data.fontFamily || this.defaults.fontFamily);
      const size = Math.min(22, Math.max(12, Number(this.data.fontSize) || 15));
      document.documentElement.style.setProperty('--sb-font-size', `${size}px`);

      const hljsLink = $('hljsThemeLink');
      if (hljsLink) {
        const effectiveCodeTheme = this.data.codeTheme === 'auto' ? theme : this.data.codeTheme;
        hljsLink.setAttribute(
          'href',
          effectiveCodeTheme === 'light'
            ? './vendor/hljs/github.min.css'
            : './vendor/hljs/github-dark.min.css'
        );
      }
    }
  }

  /* ==========================================================================
     4. SystemPromptManager — مدیریت مستقل دستورالعمل پایه سامانه
     ========================================================================== */
  const SMART_DEFAULT_SYSTEM_PROMPT = `تو «مغز دوم» هستی؛ یک دستیار هوشمند، دقیق، ساختاریافته و فارسی‌زبان.
تمام ابزارهای قالب‌بندی و نمایش پیشرفته این سامانه در اختیار توست تا پاسخ‌هایت را بسیار خوانا، دقیق و کاربردی ارائه دهی:
1. نگارش فارسی روان، صحیح و خوش‌خوان بنویس و جهت طبیعی متن فارسی و بخش‌های فنی انگلیسی را درست نگه دار.
2. پاسخ‌های ساختاریافته را با تیترهای روشن (Heading) و فهرست‌های منظم، خط‌خورده (~~...~~)، نقل‌قول (>) و پیوندهای معتبر بخش‌بندی کن؛ از پاسخ‌های شلوغ و بی‌ساختار بپرهیز.
3. برای نکات کلیدی از **ضخیم**، برای *تأکید ظریف* از کج، برای مهم‌ترین واژه‌ها از زیرخط ++این متن++ یا <u>این متن</u> و برای برجسته‌سازی از ==این متن== استفاده کن (به‌اندازه و متعادل).
4. برای مقایسه‌ها از جدول مارک‌داون مرتب استفاده کن، اما برای سؤال‌های ساده جدول یا نمودار غیرضروری نساز.
5. تمام کدهای برنامه‌نویسی را فقط در بلوک کد با نام دقیق زبان قرار بده و داده‌های ساخت‌یافته را در بلوک \`\`\`json بنویس تا به شکل درخت تعاملی نمایش داده شوند.
6. فرمول‌های ریاضی را با نگارش استاندارد لاتک ($...$ برای درون‌خطی و $$...$$ برای بلوکی) بنویس.
7. هرگاه داده عددی مناسب نمودار بود، از بلوک \`\`\`chart با ساختار JSON شامل فیلدهای type و title و labels و datasets استفاده کن.
8. در موارد لازم از بلوک‌های اطلاعاتی ویژه پلتفرم استفاده کن: :::info، :::note، :::success، :::warning، :::error، :::important، :::tip، :::summary، :::steps، :::compare، :::progress، :::status، :::timeline و :::stats.
9. متناسب با نیاز واقعی سؤال، بهترین و ساده‌ترین قالب پاسخ را برگزین.`;

  class SystemPromptManager {
    constructor(storage) {
      this.storage = storage;
      this.KEY = 'sb_system_prompt_v1';
      this.state = {
        enabled: true,
        globalPrompt: SMART_DEFAULT_SYSTEM_PROMPT
      };
      this.presets = [];
    }

    async load() {
      const saved = this.storage.getLocal(this.KEY, null);
      if (saved && typeof saved === 'object') {
        this.state.enabled = saved.enabled !== false;
        this.state.globalPrompt = typeof saved.globalPrompt === 'string'
          ? saved.globalPrompt
          : SMART_DEFAULT_SYSTEM_PROMPT;
      }
      this.presets = await this.storage.getAll('presets');
      if (this.presets.length === 0) {
        const defPreset = {
          id: 'preset_default',
          title: 'پیش‌فرض هوشمند مغز دوم',
          content: SMART_DEFAULT_SYSTEM_PROMPT,
          updatedAt: Date.now()
        };
        this.presets.push(defPreset);
        await this.storage.put('presets', defPreset);
      }
    }

    save() {
      this.storage.setLocal(this.KEY, this.state);
    }

    getEffectivePrompt(conversation) {
      if (!this.state.enabled) return '';
      if (conversation && typeof conversation.systemPrompt === 'string' && conversation.systemPrompt.trim()) {
        return conversation.systemPrompt.trim();
      }
      return (this.state.globalPrompt || '').trim();
    }

    async savePreset(title, content) {
      const preset = {
        id: uid('preset'),
        title: (title || 'نسخه سفارشی').trim(),
        content: String(content || ''),
        updatedAt: Date.now()
      };
      this.presets.unshift(preset);
      await this.storage.put('presets', preset);
      return preset;
    }

    async deletePreset(id) {
      this.presets = this.presets.filter((p) => p.id !== id);
      await this.storage.delete('presets', id);
    }

    resetDefault() {
      this.state.globalPrompt = SMART_DEFAULT_SYSTEM_PROMPT;
      this.save();
      return SMART_DEFAULT_SYSTEM_PROMPT;
    }
  }

  /* ==========================================================================
     5. ConversationManager — مدیریت چند گفت‌وگو، تاریخچه و پشتیبان JSON
     ========================================================================== */
  class ConversationManager {
    constructor(storage) {
      this.storage = storage;
      this.ACTIVE_KEY = 'sb_active_conv_id';
      this.conversations = [];
      this.activeId = null;
    }

    async load() {
      const list = await this.storage.getAll('conversations');
      this.conversations = (Array.isArray(list) ? list : [])
        .filter((c) => c && c.id && Array.isArray(c.messages))
        .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));

      const savedActive = this.storage.getLocal(this.ACTIVE_KEY, null);
      if (savedActive && this.conversations.some((c) => c.id === savedActive)) {
        this.activeId = savedActive;
      } else if (this.conversations.length > 0) {
        this.activeId = this.conversations[0].id;
      } else {
        await this.createConversation('گفت‌وگوی جدید');
      }
    }

    getActive() {
      return this.conversations.find((c) => c.id === this.activeId) || null;
    }

    setActive(id) {
      if (this.conversations.some((c) => c.id === id)) {
        this.activeId = id;
        this.storage.setLocal(this.ACTIVE_KEY, id);
      }
    }

    async createConversation(title = 'گفت‌وگوی جدید') {
      const conv = {
        id: uid('conv'),
        title,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        systemPrompt: '',
        messages: []
      };
      this.conversations.unshift(conv);
      this.activeId = conv.id;
      this.storage.setLocal(this.ACTIVE_KEY, conv.id);
      await this.storage.put('conversations', conv);
      return conv;
    }

    async saveConversation(conv) {
      if (!conv) return;
      conv.updatedAt = Date.now();
      this.conversations.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
      await this.storage.put('conversations', conv);
    }

    async deleteConversation(id) {
      this.conversations = this.conversations.filter((c) => c.id !== id);
      await this.storage.delete('conversations', id);
      if (this.activeId === id) {
        if (this.conversations.length > 0) {
          this.setActive(this.conversations[0].id);
        } else {
          await this.createConversation('گفت‌وگوی جدید');
        }
      }
    }

    async clearAll() {
      this.conversations = [];
      await this.storage.clearStore('conversations');
      await this.createConversation('گفت‌وگوی جدید');
    }

    buildApiMessages(conv, systemPromptText, contextLimit) {
      const limit = Math.max(1, Number(contextLimit) || 20);
      const cleanMsgs = conv.messages
        .filter((m) => (m.role === 'user' || m.role === 'assistant') && (m.content || '').trim())
        .slice(-limit)
        .map((m) => {
          let finalContent = m.content;
          if (m.role === 'user' && Array.isArray(m.attachments) && m.attachments.length > 0) {
            const filesBlock = m.attachments
              .map((f) => `\n\n[فایل پیوست: ${f.name}]\n\`\`\`\n${f.text}\n\`\`\``)
              .join('');
            finalContent = `${finalContent}${filesBlock}`;
          }
          return { role: m.role, content: finalContent };
        });

      const payload = [];
      if (systemPromptText) {
        payload.push({ role: 'system', content: systemPromptText });
      }
      return payload.concat(cleanMsgs);
    }

    exportAllJson() {
      return JSON.stringify(
        {
          app: 'second-brain',
          version: 1,
          exportedAt: new Date().toISOString(),
          conversations: this.conversations
        },
        null,
        2
      );
    }

    async importJson(rawText) {
      let parsed;
      try {
        parsed = JSON.parse(rawText);
      } catch (_) {
        throw new Error('فایل JSON معتبر نیست.');
      }
      const list = Array.isArray(parsed)
        ? parsed
        : Array.isArray(parsed?.conversations)
          ? parsed.conversations
          : null;
      if (!list) {
        throw new Error('ساختار پشتیبان با فرمت مغز دوم هم‌خوانی ندارد.');
      }
      let importedCount = 0;
      for (const item of list) {
        if (!item || typeof item !== 'object' || !Array.isArray(item.messages)) continue;
        const conv = {
          id: uid('conv'),
          title: String(item.title || 'گفت‌وگوی بازیابی‌شده').slice(0, 120),
          createdAt: Number(item.createdAt) || Date.now(),
          updatedAt: Number(item.updatedAt) || Date.now(),
          systemPrompt: typeof item.systemPrompt === 'string' ? item.systemPrompt : '',
          messages: item.messages
            .filter((m) => m && (m.role === 'user' || m.role === 'assistant') && typeof m.content === 'string')
            .map((m) => ({
              id: m.id || uid('msg'),
              role: m.role,
              content: m.content,
              createdAt: Number(m.createdAt) || Date.now(),
              durationMs: Number(m.durationMs) || 0,
              model: m.model || '',
              attachments: Array.isArray(m.attachments) ? m.attachments : [],
              citations: Array.isArray(m.citations) ? m.citations : []
            }))
        };
        this.conversations.unshift(conv);
        await this.storage.put('conversations', conv);
        importedCount++;
      }
      if (importedCount === 0) {
        throw new Error('هیچ گفت‌وگوی معتبری در فایل یافت نشد.');
      }
      this.conversations.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
      this.setActive(this.conversations[0].id);
      return importedCount;
    }
  }

  /* ==========================================================================
     6. OpenRouterClient — ارتباط واقعی با OpenRouter و مدیریت دسترسی وب
     ========================================================================== */
  class OpenRouterClient {
    constructor(settingsManager) {
      this.settings = settingsManager;
    }

    getBaseUrl() {
      const raw = (this.settings.data.baseUrl || 'https://openrouter.ai/api/v1').trim();
      return raw.replace(/\/+$/, '');
    }

    async fetchModels() {
      const url = `${this.getBaseUrl()}/models`;
      const headers = { Accept: 'application/json' };
      if (this.settings.apiKey) {
        headers.Authorization = `Bearer ${this.settings.apiKey}`;
      }
      const res = await fetch(url, { method: 'GET', headers });
      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(ErrorManager.formatApiError(res.status, text));
      }
      const json = await res.json();
      const list = Array.isArray(json?.data) ? json.data : [];
      this.settings.cacheModels(list);
      return this.settings.models;
    }

    async createChatRequest(messages, abortSignal) {
      const key = this.settings.apiKey;
      if (!key) {
        throw new Error('NO_API_KEY');
      }

      const d = this.settings.data;
      const modelId = this.settings.normalizeModelId(d.modelId);
      if (!modelId) {
        throw new Error('شناسه مدل انتخاب نشده است.');
      }

      const body = {
        model: modelId,
        messages,
        stream: Boolean(d.streaming),
        max_tokens: Number(d.maxTokens) || 4096,
        temperature: Number(d.temperature ?? 0.7),
        top_p: Number(d.topP ?? 1),
        frequency_penalty: Number(d.frequencyPenalty ?? 0),
        presence_penalty: Number(d.presencePenalty ?? 0)
      };

      if (d.webSearchEnabled) {
        body.plugins = [{ id: 'web', max_results: 5 }];
      }

      const res = await fetch(`${this.getBaseUrl()}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${key}`,
          'HTTP-Referer': window.location.origin,
          'X-Title': 'مغز دوم'
        },
        body: JSON.stringify(body),
        signal: abortSignal
      });

      if (!res.ok) {
        const errText = await res.text().catch(() => '');
        throw new Error(ErrorManager.formatApiError(res.status, errText));
      }

      return res;
    }
  }

  /* ==========================================================================
     7. StreamingManager — پردازش دقیق SSE بدون تکرار و با حفظ متن هنگام توقف
     ========================================================================== */
  class StreamingManager {
    extractCitations(obj, targetMap) {
      const anns = obj?.annotations || obj?.delta?.annotations || obj?.message?.annotations;
      if (!Array.isArray(anns)) return;
      for (const a of anns) {
        const cite = a?.url_citation || a;
        const href = safeUrl(cite?.url);
        if (href && !targetMap.has(href)) {
          targetMap.set(href, {
            url: href,
            title: String(cite?.title || href).slice(0, 90)
          });
        }
      }
    }

    async consumeResponse(res, isStream, onDelta, signal) {
      const citationsMap = new Map();
      let fullText = '';

      if (!isStream) {
        const json = await res.json();
        const choice = json?.choices?.[0];
        if (!choice) throw new Error('پاسخی از مدل دریافت نشد.');
        fullText = String(choice?.message?.content || '');
        this.extractCitations(choice.message, citationsMap);
        return { text: fullText, citations: Array.from(citationsMap.values()) };
      }

      if (!res.body || typeof res.body.getReader !== 'function') {
        const json = await res.json();
        fullText = String(json?.choices?.[0]?.message?.content || '');
        return { text: fullText, citations: [] };
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let pendingRender = false;
      let finishFlag = false;

      const scheduleRender = () => {
        if (pendingRender) return;
        pendingRender = true;
        requestAnimationFrame(() => {
          pendingRender = false;
          onDelta(fullText, Array.from(citationsMap.values()));
        });
      };

      try {
        while (true) {
          if (signal?.aborted) break;
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split(/\r?\n/);
          buffer = lines.pop() || '';

          for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line || line.startsWith(':')) continue;
            if (!line.startsWith('data:')) continue;

            const payload = line.slice(5).trim();
            if (payload === '[DONE]') {
              finishFlag = true;
              break;
            }

            let parsed;
            try {
              parsed = JSON.parse(payload);
            } catch (_) {
              continue;
            }

            if (parsed?.error) {
              throw new Error(parsed.error.message || 'خطا هنگام دریافت جریان زنده پاسخ.');
            }

            const choice = parsed?.choices?.[0];
            if (!choice) continue;

            this.extractCitations(choice, citationsMap);

            const deltaText = choice?.delta?.content;
            if (typeof deltaText === 'string' && deltaText.length > 0) {
              fullText += deltaText;
              scheduleRender();
            }
          }

          if (finishFlag) break;
        }
      } finally {
        try {
          reader.releaseLock();
        } catch (_) {}
      }

      onDelta(fullText, Array.from(citationsMap.values()));
      return { text: fullText, citations: Array.from(citationsMap.values()) };
    }
  }

  /* ==========================================================================
     8. CodeRenderer — رنگ‌آمیزی کد، شماره خطوط، کپی و بازوبسته‌شدن
     ========================================================================== */
  class CodeRenderer {
    static renderCodeCard(codeText, langRaw) {
      const lang = (langRaw || 'text').toLowerCase().replace(/[^a-z0-9_+#-]/g, '');
      const card = document.createElement('div');
      card.className = 'code-card';

      const head = document.createElement('div');
      head.className = 'code-card-head';

      const langBadge = document.createElement('span');
      langBadge.className = 'code-lang';
      langBadge.textContent = lang || 'text';

      const btns = document.createElement('div');
      btns.className = 'code-card-btns';

      const btnCollapse = document.createElement('button');
      btnCollapse.type = 'button';
      btnCollapse.className = 'mini-btn';
      btnCollapse.textContent = 'جمع کردن';
      btnCollapse.onclick = () => {
        const collapsed = card.classList.toggle('collapsed');
        btnCollapse.textContent = collapsed ? 'باز کردن' : 'جمع کردن';
      };

      const btnCopy = document.createElement('button');
      btnCopy.type = 'button';
      btnCopy.className = 'mini-btn';
      btnCopy.textContent = 'کپی کد';
      btnCopy.onclick = async () => {
        try {
          await copyToClipboard(codeText);
          btnCopy.textContent = 'کپی شد ✓';
          setTimeout(() => { btnCopy.textContent = 'کپی کد'; }, 1500);
        } catch (_) {
          ErrorManager.toast('کپی انجام نشد.', 'err');
        }
      };

      const btnCopyAll = document.createElement('button');
      btnCopyAll.type = 'button';
      btnCopyAll.className = 'mini-btn';
      btnCopyAll.textContent = 'کپی با قالب';
      btnCopyAll.onclick = async () => {
        try {
          await copyToClipboard(`\`\`\`${lang}\n${codeText}\n\`\`\``);
          btnCopyAll.textContent = 'کپی شد ✓';
          setTimeout(() => { btnCopyAll.textContent = 'کپی با قالب'; }, 1500);
        } catch (_) {
          ErrorManager.toast('کپی انجام نشد.', 'err');
        }
      };

      btns.append(btnCollapse, btnCopy, btnCopyAll);
      head.append(langBadge, btns);

      const body = document.createElement('div');
      body.className = 'code-card-body';

      let highlightedHtml = '';
      if (window.hljs) {
        try {
          if (lang && window.hljs.getLanguage(lang)) {
            highlightedHtml = window.hljs.highlight(codeText, { language: lang, ignoreIllegals: true }).value;
          } else {
            highlightedHtml = window.hljs.highlightAuto(codeText).value;
          }
        } catch (_) {
          highlightedHtml = escapeHtml(codeText);
        }
      } else {
        highlightedHtml = escapeHtml(codeText);
      }

      const lines = highlightedHtml.split('\n');
      if (lines.length > 1 && lines[lines.length - 1] === '') lines.pop();

      const linesTable = document.createElement('div');
      linesTable.className = 'code-lines';

      for (let i = 0; i < lines.length; i++) {
        const row = document.createElement('div');
        row.className = 'code-line';

        const num = document.createElement('span');
        num.className = 'line-num';
        num.textContent = String(i + 1);

        const codeCell = document.createElement('span');
        codeCell.className = 'line-code';
        codeCell.innerHTML = lines[i] || ' ';

        row.append(num, codeCell);
        linesTable.appendChild(row);
      }

      body.appendChild(linesTable);
      card.append(head, body);
      return card;
    }
  }

  /* ==========================================================================
     9. JSONRenderer — درخت تعاملی با مدیریت خطا، بازوبسته‌شدن و کپی خام
     ========================================================================== */
  class JSONRenderer {
    static buildTreeNode(keyName, val, depth = 0) {
      const wrap = document.createElement('div');
      wrap.className = 'json-node';

      const isArr = Array.isArray(val);
      const isObj = val !== null && typeof val === 'object' && !isArr;

      if (!isArr && !isObj) {
        if (keyName !== null) {
          const kSpan = document.createElement('span');
          kSpan.className = 'json-k';
          kSpan.textContent = `"${keyName}"`;
          wrap.appendChild(kSpan);
          wrap.appendChild(document.createTextNode(': '));
        }
        const vSpan = document.createElement('span');
        if (typeof val === 'string') {
          vSpan.className = 'json-s';
          vSpan.textContent = `"${val}"`;
        } else if (typeof val === 'number') {
          vSpan.className = 'json-n';
          vSpan.textContent = String(val);
        } else if (typeof val === 'boolean') {
          vSpan.className = 'json-b';
          vSpan.textContent = String(val);
        } else {
          vSpan.className = 'json-null';
          vSpan.textContent = 'null';
        }
        wrap.appendChild(vSpan);
        return wrap;
      }

      const entries = isArr ? val : Object.entries(val);
      const count = isArr ? val.length : entries.length;

      const details = document.createElement('details');
      details.open = depth < 2;

      const summary = document.createElement('summary');
      const arrow = document.createElement('span');
      arrow.className = 'json-toggle-arrow';
      arrow.textContent = details.open ? '▾' : '▸';
      details.addEventListener('toggle', () => {
        arrow.textContent = details.open ? '▾' : '▸';
      });
      summary.appendChild(arrow);

      if (keyName !== null) {
        const kSpan = document.createElement('span');
        kSpan.className = 'json-k';
        kSpan.textContent = `"${keyName}"`;
        summary.appendChild(kSpan);
        summary.appendChild(document.createTextNode(': '));
      }

      const bracketInfo = document.createElement('span');
      bracketInfo.style.color = 'var(--text-muted)';
      bracketInfo.textContent = isArr ? `[ ${count} مورد ]` : `{ ${count} کلید }`;
      summary.appendChild(bracketInfo);

      const children = document.createElement('div');
      children.className = 'json-children';

      if (isArr) {
        for (let i = 0; i < val.length; i++) {
          children.appendChild(this.buildTreeNode(String(i), val[i], depth + 1));
        }
      } else {
        for (const [k, v] of entries) {
          children.appendChild(this.buildTreeNode(k, v, depth + 1));
        }
      }

      details.append(summary, children);
      wrap.appendChild(details);
      return wrap;
    }

    static renderJsonCard(rawText) {
      const card = document.createElement('div');
      card.className = 'code-card';

      const head = document.createElement('div');
      head.className = 'code-card-head';

      const langBadge = document.createElement('span');
      langBadge.className = 'code-lang';
      langBadge.textContent = 'JSON';

      const btns = document.createElement('div');
      btns.className = 'code-card-btns';

      let parsed = null;
      let parseErr = '';
      try {
        parsed = JSON.parse(rawText);
      } catch (e) {
        parseErr = e.message || 'ساختار نامعتبر';
      }

      const treeWrap = document.createElement('div');
      treeWrap.className = 'json-tree-wrap';

      if (!parseErr) {
        const btnExpandAll = document.createElement('button');
        btnExpandAll.type = 'button';
        btnExpandAll.className = 'mini-btn';
        btnExpandAll.textContent = 'باز کردن همه';
        btnExpandAll.onclick = () => {
          treeWrap.querySelectorAll('details').forEach((d) => { d.open = true; });
        };

        const btnCollapseAll = document.createElement('button');
        btnCollapseAll.type = 'button';
        btnCollapseAll.className = 'mini-btn';
        btnCollapseAll.textContent = 'بستن همه';
        btnCollapseAll.onclick = () => {
          treeWrap.querySelectorAll('details').forEach((d) => { d.open = false; });
        };

        btns.append(btnExpandAll, btnCollapseAll);
      }

      const btnCopyRaw = document.createElement('button');
      btnCopyRaw.type = 'button';
      btnCopyRaw.className = 'mini-btn';
      btnCopyRaw.textContent = 'کپی خام';
      btnCopyRaw.onclick = async () => {
        try {
          await copyToClipboard(parseErr ? rawText : JSON.stringify(parsed, null, 2));
          btnCopyRaw.textContent = 'کپی شد ✓';
          setTimeout(() => { btnCopyRaw.textContent = 'کپی خام'; }, 1500);
        } catch (_) {}
      };
      btns.appendChild(btnCopyRaw);

      head.append(langBadge, btns);
      card.appendChild(head);

      if (parseErr) {
        const errBox = document.createElement('div');
        errBox.className = 'json-err-banner';
        errBox.textContent = `خطای ساختاری در JSON: ${parseErr}`;
        card.appendChild(errBox);
        const fallback = CodeRenderer.renderCodeCard(rawText, 'json');
        card.appendChild(fallback.querySelector('.code-card-body'));
      } else {
        treeWrap.appendChild(this.buildTreeNode(null, parsed, 0));
        card.appendChild(treeWrap);
      }

      return card;
    }
  }

  /* ==========================================================================
     10. ChartRenderer — نمودارهای تعاملی با دانلود تصویر، داده خام و مدیریت خطا
     ========================================================================== */
  class ChartRenderer {
    static activeCharts = new Set();

    static destroyAll() {
      for (const ch of this.activeCharts) {
        try { ch.destroy(); } catch (_) {}
      }
      this.activeCharts.clear();
    }

    static renderChartCard(rawJson) {
      const card = document.createElement('div');
      card.className = 'chart-card';

      let spec;
      try {
        spec = JSON.parse(rawJson);
      } catch (e) {
        card.innerHTML = `<div class="msg-error-box">داده نمودار معتبر نیست: ${escapeHtml(e.message)}</div>`;
        return card;
      }

      if (!spec || typeof spec !== 'object' || !Array.isArray(spec.datasets)) {
        if (!spec?.data || !Array.isArray(spec.data.datasets)) {
          card.innerHTML = `<div class="msg-error-box">ساختار نمودار کامل نیست (فیلدهای labels و datasets نیاز است).</div>`;
          return card;
        }
      }

      const rawType = String(spec.type || 'bar').toLowerCase();
      const isArea = rawType === 'area';
      const chartType = isArea ? 'line' : (['bar', 'line', 'pie', 'doughnut', 'scatter'].includes(rawType) ? rawType : 'bar');
      const titleText = String(spec.title || 'نمودار تحلیلی');
      const labels = spec.labels || spec.data?.labels || [];
      const rawDatasets = spec.datasets || spec.data?.datasets || [];

      const palette = ['#4fd1c5', '#38bdf8', '#a78bfa', '#fbbf24', '#f87171', '#34d399', '#fb923c'];
      const datasets = rawDatasets.map((ds, idx) => {
        const col = palette[idx % palette.length];
        const multiColors = (chartType === 'pie' || chartType === 'doughnut')
          ? (Array.isArray(ds.data) ? ds.data.map((_, i) => palette[i % palette.length]) : palette)
          : col;
        return {
          ...ds,
          label: ds.label || `سری ${idx + 1}`,
          backgroundColor: ds.backgroundColor || (isArea ? 'rgba(79, 209, 197, 0.22)' : multiColors),
          borderColor: ds.borderColor || (chartType === 'pie' || chartType === 'doughnut' ? 'transparent' : col),
          borderWidth: ds.borderWidth ?? 2,
          fill: isArea ? true : Boolean(ds.fill),
          tension: ds.tension ?? 0.28
        };
      });

      const head = document.createElement('div');
      head.className = 'chart-head';

      const titleEl = document.createElement('span');
      titleEl.className = 'chart-title';
      titleEl.textContent = titleText;

      const btns = document.createElement('div');
      btns.className = 'table-toolbar-btns';

      const btnPng = document.createElement('button');
      btnPng.type = 'button';
      btnPng.className = 'mini-btn';
      btnPng.textContent = 'دانلود PNG';

      const btnToggleData = document.createElement('button');
      btnToggleData.type = 'button';
      btnToggleData.className = 'mini-btn';
      btnToggleData.textContent = 'نمایش داده‌ها';

      const btnCopyData = document.createElement('button');
      btnCopyData.type = 'button';
      btnCopyData.className = 'mini-btn';
      btnCopyData.textContent = 'کپی داده‌ها';

      btns.append(btnPng, btnToggleData, btnCopyData);
      head.append(titleEl, btns);
      card.appendChild(head);

      const rawPre = document.createElement('pre');
      rawPre.className = 'chart-raw-data';
      rawPre.textContent = JSON.stringify(spec, null, 2);

      btnToggleData.onclick = () => {
        const open = rawPre.classList.toggle('open');
        btnToggleData.textContent = open ? 'بستن داده‌ها' : 'نمایش داده‌ها';
      };

      btnCopyData.onclick = async () => {
        try {
          await copyToClipboard(JSON.stringify(spec, null, 2));
          btnCopyData.textContent = 'کپی شد ✓';
          setTimeout(() => { btnCopyData.textContent = 'کپی داده‌ها'; }, 1400);
        } catch (_) {}
      };

      if (!window.Chart) {
        const fallback = document.createElement('div');
        fallback.className = 'msg-error-box';
        fallback.textContent = 'کتابخانه نمودارساز بارگذاری نشده است؛ داده‌های خام در دسترس هستند.';
        rawPre.classList.add('open');
        card.append(fallback, rawPre);
        return card;
      }

      const canvasWrap = document.createElement('div');
      canvasWrap.className = 'chart-canvas-wrap';
      const canvas = document.createElement('canvas');
      canvasWrap.appendChild(canvas);
      card.append(canvasWrap, rawPre);

      const cs = getComputedStyle(document.documentElement);
      const tickColor = cs.getPropertyValue('--chart-tick').trim() || '#9aa3b2';
      const gridColor = cs.getPropertyValue('--chart-grid').trim() || 'rgba(255,255,255,0.08)';
      const isRadial = chartType === 'pie' || chartType === 'doughnut';

      try {
        const chart = new window.Chart(canvas.getContext('2d'), {
          type: chartType,
          data: { labels, datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { labels: { color: tickColor } },
              tooltip: { enabled: true }
            },
            scales: isRadial ? {} : {
              x: { ticks: { color: tickColor }, grid: { color: gridColor } },
              y: { ticks: { color: tickColor }, grid: { color: gridColor } }
            }
          }
        });
        this.activeCharts.add(chart);
        btnPng.onclick = () => {
          const url = canvas.toDataURL('image/png');
          const a = document.createElement('a');
          a.href = url;
          a.download = `chart-${Date.now()}.png`;
          a.click();
        };
      } catch (err) {
        canvasWrap.innerHTML = `<div class="msg-error-box">خطا در رسم نمودار: ${escapeHtml(err.message)}</div>`;
      }

      return card;
    }
  }

  /* ==========================================================================
     11. MarkdownRenderer — رندر پیشرفته Markdown، زیرخط، جدول، فرمول، کد و جعبه‌ها
     ========================================================================== */
  class MarkdownRenderer {
    constructor(settingsManager) {
      this.settings = settingsManager;
    }

    renderInto(container, markdownText, isStreaming = false) {
      const raw = String(markdownText ?? '');

      if (!this.settings.data.richMarkdown) {
        container.innerHTML = '';
        const p = document.createElement('p');
        p.style.whiteSpace = 'pre-wrap';
        p.textContent = raw;
        container.appendChild(p);
        return;
      }

      const placeholders = [];
      const hold = (kind, data) => {
        const idx = placeholders.length;
        placeholders.push({ kind, data });
        return `@@SB_HOLD_${idx}@@`;
      };

      // ۱) محافظت از بلوک‌های کد/نمودار/JSON
      let text = raw.replace(/```([a-zA-Z0-9_+#-]*)\r?\n([\s\S]*?)```/g, (_, lang, body) => {
        const l = (lang || '').toLowerCase();
        if (l === 'chart' || l === 'chartjs') {
          return hold('chart', body.trim());
        }
        if (l === 'json') {
          return hold('json', body.trim());
        }
        return hold('code', { lang: l, body });
      });

      // ۲) محافظت از کدهای خطی قبل از پردازش فرمول و زیرخط
      text = text.replace(/`([^`\n]+)`/g, (m) => hold('inlinecode', m));

      // ۳) محافظت از فرمول‌های بلوکی و خطی LaTeX
      text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, eq) => hold('math_block', eq.trim()));
      text = text.replace(/\\\[([\s\S]+?)\\\]/g, (_, eq) => hold('math_block', eq.trim()));
      text = text.replace(/\\\((.+?)\\\)/g, (_, eq) => hold('math_inline', eq.trim()));
      text = text.replace(/(^|[^\\$])\$([^\s$](?:[^$\n]*?[^\s$])?)\$/g, (_, pre, eq) => `${pre}${hold('math_inline', eq.trim())}`);

      // ۴) تبدیل ۱۳ نوع بلوک اطلاعاتی ویژه (:::type ... :::)
      if (this.settings.data.underlineAndCallouts) {
        const boxTitles = {
          info: 'ℹ️ اطلاعات',
          note: 'ℹ️ یادداشت',
          success: '✅ موفقیت',
          warning: '⚠️ هشدار',
          error: '⛔ خطا',
          important: '📌 نکته مهم',
          tip: '💡 ترفند و پیشنهاد',
          summary: '📝 جمع‌بندی',
          steps: '🪜 راهنمای گام‌به‌گام',
          compare: '⚖️ مقایسه',
          comparison: '⚖️ مقایسه',
          progress: '📊 وضعیت پیشرفت',
          status: '🟢 وضعیت',
          timeline: '🕒 خط زمانی',
          stats: '📈 کارت‌های آمار'
        };
        text = text.replace(/^:::(info|note|success|warning|error|important|tip|summary|steps|compare|comparison|progress|status|timeline|stats)(?:[ \t]+([^\n]*))?\r?\n([\s\S]*?)^:::[ \t]*$/gm,
          (_, typeRaw, customTitle, inner) => {
            const type = typeRaw === 'comparison' ? 'compare' : typeRaw;
            const title = (customTitle || boxTitles[type] || type).trim();
            return hold('callout', { type, title, inner: inner.trim() });
          }
        );

        // ۵) پشتیبانی از ++زیرخط++ و ==هایلایت==
        text = text.replace(/\+\+([^\n+]+?)\+\+/g, (_, inner) => `<u class="sb-underline">${inner}</u>`);
        text = text.replace(/==([^\n=]+?)==/g, (_, inner) => `<mark>${inner}</mark>`);
      }

      const parseMd = (mdStr) => {
        if (window.marked && typeof window.marked.parse === 'function') {
          return window.marked.parse(mdStr, { gfm: true, breaks: true });
        }
        return `<p style="white-space:pre-wrap">${escapeHtml(mdStr)}</p>`;
      };

      let html = parseMd(text);

      // جایگذاری calloutها بعد از پارس داخلی خودشان
      html = html.replace(/@@SB_HOLD_(\d+)@@/g, (full, idxStr) => {
        const item = placeholders[Number(idxStr)];
        if (!item) return full;
        if (item.kind === 'inlinecode') {
          const codeBody = item.data.slice(1, -1);
          return `<code>${escapeHtml(codeBody)}</code>`;
        }
        if (item.kind === 'callout') {
          const innerHtml = parseMd(item.data.inner);
          let extra = '';
          if (item.data.type === 'progress') {
            const pctMatch = item.data.inner.match(/(\d{1,3})\s*%/);
            const pct = pctMatch ? Math.min(100, Math.max(0, Number(pctMatch[1]))) : 65;
            extra = `<div class="prog-track"><div class="prog-fill" style="width:${pct}%"></div></div>`;
          } else if (item.data.type === 'status') {
            extra = `<div style="margin-top:4px"><span class="status-pill">${escapeHtml(item.data.title)}</span></div>`;
          }
          if (item.data.type === 'stats') {
            const lines = item.data.inner.split(/\r?\n/).map((l) => l.replace(/^[-*]\s*/, '').trim()).filter(Boolean);
            const cards = lines.map((l) => {
              const parts = l.split(':');
              const k = (parts[0] || l).trim();
              const v = (parts.slice(1).join(':') || '—').trim();
              return `<div class="sb-stat-item"><div class="sb-stat-label">${escapeHtml(k)}</div><div class="sb-stat-val tech-num">${escapeHtml(v)}</div></div>`;
            }).join('');
            return `<div class="sb-callout stats"><div class="sb-callout-title">${escapeHtml(item.data.title)}</div><div class="sb-stats-grid">${cards}</div></div>`;
          }
          return `<div class="sb-callout ${item.data.type}"><div class="sb-callout-title">${escapeHtml(item.data.title)}</div><div class="sb-callout-body">${innerHtml}${extra}</div></div>`;
        }
        return full;
      });

      // پاک‌سازی امنیتی با DOMPurify (جلوگیری کامل از XSS)
      if (window.DOMPurify && typeof window.DOMPurify.sanitize === 'function') {
        html = window.DOMPurify.sanitize(html, {
          ALLOWED_TAGS: [
            'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'del', 'mark', 'code', 'pre',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'hr',
            'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'span', 'input'
          ],
          ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'style', 'type', 'checked', 'disabled', 'dir'],
          ALLOW_DATA_ATTR: false
        });
      }

      container.innerHTML = html;

      // امن‌سازی تمام لینک‌ها
      container.querySelectorAll('a').forEach((a) => {
        const cleanHref = safeUrl(a.getAttribute('href'));
        if (!cleanHref) {
          a.replaceWith(document.createTextNode(a.textContent || ''));
        } else {
          a.setAttribute('href', cleanHref);
          a.setAttribute('target', '_blank');
          a.setAttribute('rel', 'noopener noreferrer');
        }
      });

      // جایگزینی placeholderهای تعاملی (کد، جیسون، نمودار، ریاضی)
      this.hydratePlaceholders(container, placeholders);

      // ارتقای جدول‌ها با اسکرول موبایل و دکمه‌های کپی/خروجی واقعی
      this.enhanceTables(container);

      // تنظیم جهت خودکار پاراگراف‌ها برای فارسی و انگلیسی هم‌زمان
      container.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, blockquote').forEach((el) => {
        if (!el.getAttribute('dir')) el.setAttribute('dir', 'auto');
      });

      if (isStreaming) {
        const cur = document.createElement('span');
        cur.className = 'typing-cursor';
        container.appendChild(cur);
      }
    }

    hydratePlaceholders(root, placeholders) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      const nodes = [];
      let n;
      while ((n = walker.nextNode())) {
        if (n.nodeValue && n.nodeValue.includes('@@SB_HOLD_')) {
          nodes.push(n);
        }
      }

      for (const textNode of nodes) {
        const parts = textNode.nodeValue.split(/(@@SB_HOLD_\d+@@)/g);
        const frag = document.createDocumentFragment();
        for (const part of parts) {
          const match = part.match(/^@@SB_HOLD_(\d+)@@$/);
          if (!match) {
            if (part) frag.appendChild(document.createTextNode(part));
            continue;
          }
          const item = placeholders[Number(match[1])];
          if (!item) continue;

          if (item.kind === 'code') {
            frag.appendChild(CodeRenderer.renderCodeCard(item.data.body, item.data.lang));
          } else if (item.kind === 'json') {
            frag.appendChild(JSONRenderer.renderJsonCard(item.data));
          } else if (item.kind === 'chart') {
            frag.appendChild(ChartRenderer.renderChartCard(item.data));
          } else if (item.kind === 'math_inline' || item.kind === 'math_block') {
            const isBlock = item.kind === 'math_block';
            const host = document.createElement(isBlock ? 'div' : 'span');
            if (isBlock) host.className = 'math-block-scroll';
            if (window.katex && typeof window.katex.render === 'function') {
              try {
                window.katex.render(item.data, host, {
                  displayMode: isBlock,
                  throwOnError: false,
                  strict: false
                });
              } catch (_) {
                host.className = 'katex-fallback';
                host.textContent = item.data;
              }
            } else {
              host.className = 'katex-fallback';
              host.textContent = item.data;
            }
            frag.appendChild(host);
          }
        }
        textNode.parentNode.replaceChild(frag, textNode);
      }
    }

    enhanceTables(root) {
      root.querySelectorAll('table').forEach((table) => {
        if (table.closest('.table-card')) return;
        const card = document.createElement('div');
        card.className = 'table-card';

        const rows = Array.from(table.querySelectorAll('tr')).map((tr) =>
          Array.from(tr.querySelectorAll('th, td')).map((cell) => cell.innerText.replace(/\s+/g, ' ').trim())
        );

        const toolbar = document.createElement('div');
        toolbar.className = 'table-toolbar';

        const meta = document.createElement('span');
        meta.className = 'tech-num';
        meta.textContent = `جدول (${rows.length} سطر)`;

        const btns = document.createElement('div');
        btns.className = 'table-toolbar-btns';

        const toTSV = () => rows.map((r) => r.join('\t')).join('\n');
        const toCSV = () => rows.map((r) => r.map((c) => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n');
        const toMarkdown = () => {
          if (rows.length === 0) return '';
          const head = `| ${rows[0].join(' | ')} |`;
          const sep = `| ${rows[0].map(() => '---').join(' | ')} |`;
          const body = rows.slice(1).map((r) => `| ${r.join(' | ')} |`).join('\n');
          return [head, sep, body].filter(Boolean).join('\n');
        };

        const addCopyBtn = (label, getter) => {
          const b = document.createElement('button');
          b.type = 'button';
          b.className = 'mini-btn';
          b.textContent = label;
          b.onclick = async () => {
            try {
              await copyToClipboard(getter());
              b.textContent = 'کپی شد ✓';
              setTimeout(() => { b.textContent = label; }, 1300);
            } catch (_) {}
          };
          btns.appendChild(b);
        };

        addCopyBtn('کپی جدول', toTSV);
        addCopyBtn('کپی TSV', toTSV);
        addCopyBtn('کپی Markdown', toMarkdown);

        const btnCsv = document.createElement('button');
        btnCsv.type = 'button';
        btnCsv.className = 'mini-btn';
        btnCsv.textContent = 'خروجی CSV';
        btnCsv.onclick = () => downloadBlob('\uFEFF' + toCSV(), `table-${Date.now()}.csv`, 'text/csv;charset=utf-8');
        btns.appendChild(btnCsv);

        toolbar.append(meta, btns);

        const scroll = document.createElement('div');
        scroll.className = 'table-scroll';

        table.parentNode.insertBefore(card, table);
        scroll.appendChild(table);
        card.append(toolbar, scroll);
      });
    }
  }

  /* ==========================================================================
     12. ComposerManager — کادر تایپ حرفه‌ای، قالب‌بندی زیرخط و آپلود PDF/متن
     ========================================================================== */
  class ComposerManager {
    constructor(app) {
      this.app = app;
      this.textarea = $('composerInput');
      this.pendingFiles = [];
      this.MAX_FILE_BYTES = 5 * 1024 * 1024;
      this.MAX_EXTRACTED_CHARS = 80000;
    }

    init() {
      this.textarea.addEventListener('input', () => this.autoResize());
      this.textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
          e.preventDefault();
          this.app.handleSend();
        }
      });

      $('btnAttachFile').addEventListener('click', () => $('fileUploadInput').click());
      $('fileUploadInput').addEventListener('change', (e) => this.handleFiles(e));

      // سازگاری با کیبورد مجازی اندروید و عدم پرش صفحه
      if (window.visualViewport) {
        const adjustViewport = () => {
          const shell = $('appShell');
          if (!shell) return;
          shell.style.height = `${window.visualViewport.height}px`;
          this.app.scrollToBottom();
        };
        window.visualViewport.addEventListener('resize', adjustViewport);
      }

      this.autoResize();
    }

    autoResize() {
      const ta = this.textarea;
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(170, Math.max(26, ta.scrollHeight))}px`;
      $('composerCountText').textContent = `${ta.value.length.toLocaleString('fa-IR')} کاراکتر`;
    }

    async handleFiles(e) {
      const files = Array.from(e.target.files || []);
      e.target.value = '';
      for (const file of files) {
        const ext = (file.name.split('.').pop() || '').toLowerCase();
        if (!['txt', 'md', 'json', 'csv', 'pdf'].includes(ext)) {
          ErrorManager.toast(`فرمت فایل «${file.name}» پشتیبانی نمی‌شود. فقط فایل‌های متنی، مارک‌داون، جیسون، جدول یا پی‌دی‌اف مجاز هستند.`, 'err', 4200);
          continue;
        }
        if (file.size > this.MAX_FILE_BYTES) {
          ErrorManager.toast(`حجم فایل «${file.name}» از ۵ مگابایت بیشتر است.`, 'err');
          continue;
        }
        try {
          let extracted = '';
          if (ext === 'pdf') {
            $('composerStatusText').textContent = `در حال خواندن فایل ${file.name}...`;
            extracted = await this.extractPdfText(file);
          } else {
            extracted = await file.text();
          }
          extracted = extracted.trim();
          if (!extracted) {
            ErrorManager.toast(`متنی از فایل «${file.name}» قابل استخراج نبود.`, 'err');
            continue;
          }
          if (extracted.length > this.MAX_EXTRACTED_CHARS) {
            extracted = extracted.slice(0, this.MAX_EXTRACTED_CHARS) + '\n... [ادامه به دلیل حجم بالا کوتاه شد]';
          }
          this.pendingFiles.push({ id: uid('file'), name: file.name, text: extracted });
          this.renderPendingFiles();
          ErrorManager.toast(`فایل «${file.name}» آماده پیوست شد.`, 'ok');
        } catch (err) {
          ErrorManager.toast(`خطا در خواندن فایل «${file.name}»: ${err.message}`, 'err', 4000);
        } finally {
          $('composerStatusText').textContent = 'آماده';
        }
      }
    }

    async extractPdfText(file) {
      let pdfjs;
      try {
        pdfjs = await import('./vendor/pdfjs/pdf.min.mjs');
      } catch (_) {
        throw new Error('ماژول خواندن پی‌دی‌اف در دسترس نیست.');
      }
      if (pdfjs.GlobalWorkerOptions) {
        pdfjs.GlobalWorkerOptions.workerSrc = './vendor/pdfjs/pdf.worker.min.mjs';
      }
      const buffer = await file.arrayBuffer();
      const doc = await pdfjs.getDocument({ data: new Uint8Array(buffer) }).promise;
      const pages = [];
      for (let i = 1; i <= doc.numPages; i++) {
        const page = await doc.getPage(i);
        const tc = await page.getTextContent();
        const pageStr = tc.items.map((it) => it.str || '').join(' ').trim();
        if (pageStr) pages.push(`--- صفحه ${i} ---\n${pageStr}`);
      }
      return pages.join('\n\n');
    }

    renderPendingFiles() {
      const box = $('pendingFiles');
      box.innerHTML = '';
      for (const f of this.pendingFiles) {
        const chip = document.createElement('span');
        chip.className = 'pending-file-chip';
        chip.innerHTML = `<span>📄 ${escapeHtml(f.name)}</span>`;
        const btnRm = document.createElement('button');
        btnRm.type = 'button';
        btnRm.textContent = '✕';
        btnRm.title = 'حذف پیوست';
        btnRm.onclick = () => {
          this.pendingFiles = this.pendingFiles.filter((x) => x.id !== f.id);
          this.renderPendingFiles();
        };
        chip.appendChild(btnRm);
        box.appendChild(chip);
      }
    }
  }

  /* ==========================================================================
     13. AppController — کنترل‌گر اصلی برنامه و هماهنگ‌کننده کل بخش‌ها
     ========================================================================== */
  class AppController {
    constructor() {
      this.storage = new StorageManager();
      this.settings = new SettingsManager(this.storage);
      this.systemPrompt = new SystemPromptManager(this.storage);
      this.conversations = new ConversationManager(this.storage);
      this.client = new OpenRouterClient(this.settings);
      this.streamer = new StreamingManager();
      this.markdown = new MarkdownRenderer(this.settings);
      this.composer = new ComposerManager(this);

      this.isGenerating = false;
      this.abortController = null;
    }

    async bootstrap() {
      await this.storage.init();
      await this.settings.load();
      await this.systemPrompt.load();
      await this.conversations.load();

      this.composer.init();
      this.bindUI();
      this.syncHeaderAndToggles();
      this.renderConversationList();
      this.renderActiveChat();

      // دریافت بی‌سروصدای فهرست مدل‌ها در پس‌زمینه وقتی آنلاین هستیم
      if (navigator.onLine) {
        this.client.fetchModels().then(() => {
          this.populateSettingsModelSelect();
        }).catch(() => {});
      }
    }

    bindUI() {
      // تغییر تم شب و روز
      $('btnThemeToggle').addEventListener('click', () => {
        this.settings.data.theme = this.settings.data.theme === 'dark' ? 'light' : 'dark';
        this.settings.save();
        this.syncHeaderAndToggles();
        this.renderActiveChat();
      });

      // کلید دسترسی مدل به اینترنت
      $('btnWebToggle').addEventListener('click', () => {
        this.settings.data.webSearchEnabled = !this.settings.data.webSearchEnabled;
        this.settings.save();
        this.syncHeaderAndToggles();
        ErrorManager.toast(
          this.settings.data.webSearchEnabled
            ? 'دسترسی مدل به جست‌وجوی اینترنت روشن شد.'
            : 'دسترسی مدل به اینترنت خاموش شد.',
          'info',
          2200
        );
      });

      // ارسال و توقف
      $('btnSendMsg').addEventListener('click', () => this.handleSend());
      $('btnStopMsg').addEventListener('click', () => this.stopGeneration());

      // کشوی گفت‌وگوها
      $('btnOpenDrawer').addEventListener('click', () => this.toggleDrawer(true));
      $('btnCloseDrawer').addEventListener('click', () => this.toggleDrawer(false));
      $('drawerBackdrop').addEventListener('click', () => this.toggleDrawer(false));

      $('btnNewChat').addEventListener('click', async () => {
        if (this.isGenerating) this.stopGeneration();
        await this.conversations.createConversation('گفت‌وگوی جدید');
        this.renderConversationList();
        this.renderActiveChat();
        this.toggleDrawer(false);
      });

      $('btnClearCurrentChat').addEventListener('click', async () => {
        const conv = this.conversations.getActive();
        if (!conv || conv.messages.length === 0) return;
        if (!window.confirm('آیا از پاک کردن تمام پیام‌های گفت‌وگوی جاری مطمئن هستید؟')) return;
        conv.messages = [];
        await this.conversations.saveConversation(conv);
        this.renderConversationList();
        this.renderActiveChat();
      });

      $('btnExportAllJson').addEventListener('click', () => {
        downloadBlob(this.conversations.exportAllJson(), `second-brain-backup-${Date.now()}.json`, 'application/json');
      });
      $('btnImportAllJson').addEventListener('click', () => $('importHistoryInput').click());
      $('importHistoryInput').addEventListener('change', async (e) => {
        const f = e.target.files?.[0];
        e.target.value = '';
        if (!f) return;
        try {
          const text = await f.text();
          const count = await this.conversations.importJson(text);
          this.renderConversationList();
          this.renderActiveChat();
          ErrorManager.toast(`${count} گفت‌وگو با موفقیت بازیابی شد.`, 'ok');
        } catch (err) {
          ErrorManager.toast(err.message, 'err');
        }
      });

      // انتخاب سریع مدل
      $('btnQuickModel').addEventListener('click', () => this.openQuickModelModal());
      $('quickModelSearch').addEventListener('input', () => this.renderQuickModelList());
      $('btnToggleFreeOnly').addEventListener('click', () => {
        this.settings.data.freeModelsOnly = !this.settings.data.freeModelsOnly;
        this.settings.save();
        this.renderQuickModelList();
      });
      $('btnRefreshModelsQuick').addEventListener('click', async () => {
        try {
          $('quickModelHint').textContent = 'در حال دریافت فهرست مدل‌ها از اوپن‌روتر...';
          await this.client.fetchModels();
          this.renderQuickModelList();
          this.populateSettingsModelSelect();
          $('quickModelHint').textContent = 'فهرست مدل‌ها به‌روزرسانی شد.';
        } catch (err) {
          $('quickModelHint').textContent = err.message;
        }
      });
      $('btnApplyManualModel').addEventListener('click', () => {
        const val = this.settings.normalizeModelId($('quickManualModelId').value);
        if (!val) return;
        this.settings.data.modelId = val;
        this.settings.save();
        this.syncHeaderAndToggles();
        this.closeModal('quickModelModal');
        ErrorManager.toast(`مدل فعال به ${val} تغییر یافت.`, 'ok');
      });

      // مودال دستورالعمل پایه (System Prompt)
      $('btnOpenSystemPrompt').addEventListener('click', () => this.openSystemPromptModal());
      $('spScopeSelect').addEventListener('change', () => this.loadSpScopeIntoEditor());
      $('spTextarea').addEventListener('input', () => {
        $('spCharCount').textContent = `${$('spTextarea').value.length.toLocaleString('fa-IR')} کاراکتر`;
      });
      $('btnSpCopy').addEventListener('click', async () => {
        try {
          await copyToClipboard($('spTextarea').value);
          ErrorManager.toast('دستورالعمل پایه کپی شد.', 'ok');
        } catch (_) {}
      });
      $('btnSpResetDefault').addEventListener('click', () => {
        $('spTextarea').value = SMART_DEFAULT_SYSTEM_PROMPT;
        $('spCharCount').textContent = `${SMART_DEFAULT_SYSTEM_PROMPT.length.toLocaleString('fa-IR')} کاراکتر`;
      });
      $('btnSpClear').addEventListener('click', () => {
        if (!window.confirm('آیا متن دستورالعمل پایه پاک شود؟')) return;
        $('spTextarea').value = '';
        $('spCharCount').textContent = '۰ کاراکتر';
      });
      $('btnSpSavePreset').addEventListener('click', async () => {
        const content = $('spTextarea').value.trim();
        if (!content) return;
        const title = window.prompt('نامی برای این نسخه از دستورالعمل وارد کنید:', 'نسخه سفارشی');
        if (title === null) return;
        await this.systemPrompt.savePreset(title, content);
        this.renderSpPresets();
        ErrorManager.toast('نسخه دستورالعمل ذخیره شد.', 'ok');
      });
      $('btnSpImportTxt').addEventListener('click', () => $('spImportFile').click());
      $('spImportFile').addEventListener('change', async (e) => {
        const file = e.target.files?.[0];
        e.target.value = '';
        if (!file) return;
        const txt = await file.text();
        let val = txt;
        if (file.name.toLowerCase().endsWith('.json')) {
          try {
            const parsed = JSON.parse(txt);
            val = parsed.systemPrompt || parsed.content || txt;
          } catch (_) {}
        }
        $('spTextarea').value = val;
        $('spCharCount').textContent = `${val.length.toLocaleString('fa-IR')} کاراکتر`;
      });
      $('btnSpExportTxt').addEventListener('click', () => {
        downloadBlob($('spTextarea').value, `system-prompt-${Date.now()}.txt`);
      });
      $('btnSpExportJson').addEventListener('click', () => {
        downloadBlob(JSON.stringify({ systemPrompt: $('spTextarea').value, enabled: $('spEnabledToggle').checked }, null, 2), `system-prompt-${Date.now()}.json`, 'application/json');
      });
      $('btnSpSave').addEventListener('click', async () => {
        this.systemPrompt.state.enabled = $('spEnabledToggle').checked;
        const scope = $('spScopeSelect').value;
        const text = $('spTextarea').value;
        if (scope === 'conversation') {
          const conv = this.conversations.getActive();
          if (conv) {
            conv.systemPrompt = text;
            await this.conversations.saveConversation(conv);
          }
        } else {
          this.systemPrompt.state.globalPrompt = text;
        }
        this.systemPrompt.save();
        this.syncHeaderAndToggles();
        this.closeModal('systemPromptModal');
        ErrorManager.toast('دستورالعمل پایه ذخیره شد.', 'ok');
      });

      // مودال تنظیمات پیشرفته
      $('btnOpenSettings').addEventListener('click', () => this.openSettingsModal());
      $('btnToggleKeyVis').addEventListener('click', () => {
        const inp = $('setApiKey');
        inp.type = inp.type === 'password' ? 'text' : 'password';
      });
      $('btnRemoveApiKey').addEventListener('click', async () => {
        if (!window.confirm('آیا کلید دسترسی از مرورگر حذف شود؟')) return;
        await this.settings.setApiKey('');
        $('setApiKey').value = '';
        this.syncHeaderAndToggles();
        ErrorManager.toast('کلید دسترسی حذف شد.', 'info');
      });
      $('btnFetchModels').addEventListener('click', async () => {
        try {
          $('btnFetchModels').textContent = 'در حال دریافت...';
          await this.client.fetchModels();
          this.populateSettingsModelSelect();
          ErrorManager.toast('فهرست مدل‌ها با موفقیت دریافت شد.', 'ok');
        } catch (err) {
          ErrorManager.toast(err.message, 'err');
        } finally {
          $('btnFetchModels').textContent = 'دریافت فهرست مدل‌ها';
        }
      });
      $('setModelSelect').addEventListener('change', (e) => {
        if (e.target.value) $('setModelId').value = e.target.value;
      });
      $('btnSaveSettings').addEventListener('click', async () => {
        await this.saveSettingsFromModal();
      });
      $('btnSetExportAll').addEventListener('click', () => {
        downloadBlob(this.conversations.exportAllJson(), `second-brain-backup-${Date.now()}.json`, 'application/json');
      });
      $('btnSetDeleteAll').addEventListener('click', async () => {
        if (!window.confirm('هشدار: تمام گفت‌وگوها و تاریخچه برای همیشه پاک می‌شوند. مطمئن هستید؟')) return;
        await this.conversations.clearAll();
        this.renderConversationList();
        this.renderActiveChat();
        this.closeModal('settingsModal');
        ErrorManager.toast('تمام تاریخچه پاک شد.', 'info');
      });

      // بستن مودال‌ها
      document.querySelectorAll('[data-close-modal]').forEach((btn) => {
        btn.addEventListener('click', () => this.closeModal(btn.dataset.closeModal));
      });
      document.querySelectorAll('.modal-backdrop').forEach((bd) => {
        bd.addEventListener('click', (e) => {
          if (e.target === bd) bd.classList.remove('open');
        });
      });
    }

    syncHeaderAndToggles() {
      const isDark = this.settings.data.theme !== 'light';
      $('btnThemeToggle').textContent = isDark ? '🌙' : '☀️';
      $('btnThemeToggle').title = isDark ? 'تغییر به تم روشن مهربان با چشم' : 'تغییر به تم تاریک مهربان با چشم';

      const modelId = this.settings.normalizeModelId(this.settings.data.modelId);
      $('activeModelLabel').textContent = modelId || 'مدلی انتخاب نشده';

      const dot = $('connDot');
      dot.className = 'conn-dot';
      if (this.isGenerating) {
        dot.classList.add('busy');
        dot.title = 'در حال دریافت پاسخ';
      } else if (!navigator.onLine) {
        dot.classList.add('err');
        dot.title = 'آفلاین';
      } else if (this.settings.apiKey) {
        dot.classList.add('ready');
        dot.title = 'آماده ارسال';
      }

      const webOn = Boolean(this.settings.data.webSearchEnabled);
      const webBtn = $('btnWebToggle');
      webBtn.classList.toggle('active', webOn);
      $('webToggleText').textContent = webOn ? 'اینترنت: روشن' : 'اینترنت: خاموش';

      const spBtn = $('btnOpenSystemPrompt');
      spBtn.classList.toggle('active-dot', Boolean(this.systemPrompt.state.enabled));
    }

    toggleDrawer(open) {
      $('convDrawer').classList.toggle('open', open);
      $('drawerBackdrop').classList.toggle('open', open);
    }

    openModal(id) {
      $(id).classList.add('open');
    }

    closeModal(id) {
      $(id).classList.remove('open');
    }

    openQuickModelModal() {
      $('quickManualModelId').value = this.settings.data.modelId || '';
      this.renderQuickModelList();
      this.openModal('quickModelModal');
    }

    renderQuickModelList() {
      const q = ($('quickModelSearch').value || '').trim().toLowerCase();
      const freeOnly = Boolean(this.settings.data.freeModelsOnly);
      const btnFree = $('btnToggleFreeOnly');
      btnFree.style.borderColor = freeOnly ? 'var(--accent)' : '';
      btnFree.style.color = freeOnly ? 'var(--accent)' : '';

      const listEl = $('quickModelList');
      listEl.innerHTML = '';

      const filtered = this.settings.models.filter((m) => {
        if (freeOnly && !m.isFree) return false;
        if (q && !m.id.toLowerCase().includes(q) && !m.name.toLowerCase().includes(q)) return false;
        return true;
      });

      if (filtered.length === 0) {
        listEl.innerHTML = '<div class="field-hint">مدلی با این شرط یافت نشد. فیلتر را تغییر دهید یا شناسه مدل را دستی وارد کنید.</div>';
        return;
      }

      for (const m of filtered.slice(0, 80)) {
        const row = document.createElement('div');
        row.className = 'preset-item';
        row.style.cursor = 'pointer';
        if (this.settings.normalizeModelId(this.settings.data.modelId) === m.id) {
          row.style.borderColor = 'var(--accent)';
        }

        const info = document.createElement('div');
        info.style.minWidth = '0';
        info.innerHTML = `<div style="font-weight:700; word-break:break-word">${escapeHtml(m.name)}</div>
          <div style="font-size:0.72rem; color:var(--text-muted); direction:ltr; text-align:right">${escapeHtml(m.id)}</div>`;

        const badge = document.createElement('span');
        badge.className = 'mini-btn';
        badge.style.flex = '0 0 auto';
        badge.textContent = m.isFree ? '🆓 رایگان' : 'اعتباری';

        row.append(info, badge);
        row.onclick = () => {
          this.settings.data.modelId = m.id;
          this.settings.save();
          this.syncHeaderAndToggles();
          this.closeModal('quickModelModal');
          ErrorManager.toast(`مدل فعال: ${m.id}`, 'ok');
        };
        listEl.appendChild(row);
      }
    }

    openSystemPromptModal() {
      $('spEnabledToggle').checked = Boolean(this.systemPrompt.state.enabled);
      $('spScopeSelect').value = 'global';
      this.loadSpScopeIntoEditor();
      this.renderSpPresets();
      this.openModal('systemPromptModal');
    }

    loadSpScopeIntoEditor() {
      const scope = $('spScopeSelect').value;
      const conv = this.conversations.getActive();
      const val = scope === 'conversation'
        ? (conv?.systemPrompt || '')
        : (this.systemPrompt.state.globalPrompt || '');
      $('spTextarea').value = val;
      $('spCharCount').textContent = `${val.length.toLocaleString('fa-IR')} کاراکتر`;
    }

    renderSpPresets() {
      const box = $('spPresetsList');
      box.innerHTML = '';
      for (const p of this.systemPrompt.presets) {
        const item = document.createElement('div');
        item.className = 'preset-item';
        const title = document.createElement('span');
        title.textContent = p.title;
        const btns = document.createElement('div');
        btns.style.display = 'flex';
        btns.style.gap = '4px';

        const btnUse = document.createElement('button');
        btnUse.type = 'button';
        btnUse.className = 'mini-btn';
        btnUse.textContent = 'استفاده';
        btnUse.onclick = () => {
          $('spTextarea').value = p.content;
          $('spCharCount').textContent = `${p.content.length.toLocaleString('fa-IR')} کاراکتر`;
        };
        btns.appendChild(btnUse);

        if (p.id !== 'preset_default') {
          const btnDel = document.createElement('button');
          btnDel.type = 'button';
          btnDel.className = 'mini-btn';
          btnDel.textContent = 'حذف';
          btnDel.onclick = async () => {
            await this.systemPrompt.deletePreset(p.id);
            this.renderSpPresets();
          };
          btns.appendChild(btnDel);
        }

        item.append(title, btns);
        box.appendChild(item);
      }
    }

    openSettingsModal() {
      const d = this.settings.data;
      $('setApiKey').value = this.settings.apiKey || '';
      $('setApiKey').type = 'password';
      $('setBaseUrl').value = d.baseUrl || 'https://openrouter.ai/api/v1';
      this.populateSettingsModelSelect();
      $('setModelId').value = d.modelId || '';
      $('setMaxTokens').value = d.maxTokens;
      $('setContextLimit').value = d.contextLimit;
      $('setTemperature').value = d.temperature;
      $('setTopP').value = d.topP;
      $('setFreqPenalty').value = d.frequencyPenalty;
      $('setPresPenalty').value = d.presencePenalty;
      $('setFontFamily').value = d.fontFamily;
      $('setFontSize').value = d.fontSize;
      $('setCodeTheme').value = d.codeTheme;
      $('setStreaming').checked = Boolean(d.streaming);
      $('setWebSearch').checked = Boolean(d.webSearchEnabled);
      $('setRichMarkdown').checked = Boolean(d.richMarkdown);
      $('setUnderlineAndCallouts').checked = Boolean(d.underlineAndCallouts);
      this.openModal('settingsModal');
    }

    populateSettingsModelSelect() {
      const sel = $('setModelSelect');
      if (!sel) return;
      sel.innerHTML = '';
      for (const m of this.settings.models) {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = `${m.isFree ? '🆓 ' : ''}${m.id}`;
        sel.appendChild(opt);
      }
      const norm = this.settings.normalizeModelId(this.settings.data.modelId);
      if (this.settings.models.some((m) => m.id === norm)) {
        sel.value = norm;
      }
    }

    async saveSettingsFromModal() {
      await this.settings.setApiKey($('setApiKey').value);
      const d = this.settings.data;
      d.baseUrl = $('setBaseUrl').value.trim() || 'https://openrouter.ai/api/v1';
      d.modelId = this.settings.normalizeModelId($('setModelId').value) || d.modelId;
      d.maxTokens = Math.max(64, Number($('setMaxTokens').value) || 4096);
      d.contextLimit = Math.max(1, Number($('setContextLimit').value) || 20);
      d.temperature = Math.min(2, Math.max(0, Number($('setTemperature').value)));
      d.topP = Math.min(1, Math.max(0, Number($('setTopP').value)));
      d.frequencyPenalty = Math.min(2, Math.max(-2, Number($('setFreqPenalty').value) || 0));
      d.presencePenalty = Math.min(2, Math.max(-2, Number($('setPresPenalty').value) || 0));
      d.fontFamily = $('setFontFamily').value;
      d.fontSize = Math.min(22, Math.max(12, Number($('setFontSize').value) || 15));
      d.codeTheme = $('setCodeTheme').value;
      d.streaming = $('setStreaming').checked;
      d.webSearchEnabled = $('setWebSearch').checked;
      d.richMarkdown = $('setRichMarkdown').checked;
      d.underlineAndCallouts = $('setUnderlineAndCallouts').checked;

      this.settings.save();
      this.syncHeaderAndToggles();
      this.renderActiveChat();
      this.closeModal('settingsModal');
      ErrorManager.toast('تنظیمات با موفقیت ذخیره شد.', 'ok');
    }

    renderConversationList() {
      const box = $('convList');
      box.innerHTML = '';
      for (const conv of this.conversations.conversations) {
        const item = document.createElement('div');
        item.className = `conv-item ${conv.id === this.conversations.activeId ? 'active' : ''}`;

        const info = document.createElement('div');
        info.className = 'conv-info';
        const ttl = document.createElement('div');
        ttl.className = 'conv-title';
        ttl.textContent = conv.title || 'گفت‌وگوی بدون عنوان';
        const sub = document.createElement('div');
        sub.className = 'conv-sub tech-num';
        sub.textContent = `${conv.messages.length} پیام`;
        info.append(ttl, sub);

        info.onclick = () => {
          if (this.isGenerating) this.stopGeneration();
          this.conversations.setActive(conv.id);
          this.renderConversationList();
          this.renderActiveChat();
          this.toggleDrawer(false);
        };

        const btns = document.createElement('div');
        btns.className = 'conv-btns';

        const btnRename = document.createElement('button');
        btnRename.type = 'button';
        btnRename.className = 'icon-btn';
        btnRename.style.width = '30px';
        btnRename.style.height = '30px';
        btnRename.textContent = '✏️';
        btnRename.title = 'تغییر عنوان';
        btnRename.onclick = async (e) => {
          e.stopPropagation();
          const newTitle = window.prompt('عنوان جدید گفت‌وگو:', conv.title);
          if (newTitle && newTitle.trim()) {
            conv.title = newTitle.trim().slice(0, 100);
            await this.conversations.saveConversation(conv);
            this.renderConversationList();
          }
        };

        const btnDel = document.createElement('button');
        btnDel.type = 'button';
        btnDel.className = 'icon-btn';
        btnDel.style.width = '30px';
        btnDel.style.height = '30px';
        btnDel.textContent = '🗑';
        btnDel.title = 'حذف گفت‌وگو';
        btnDel.onclick = async (e) => {
          e.stopPropagation();
          if (!window.confirm(`آیا گفت‌وگوی «${conv.title}» حذف شود؟`)) return;
          await this.conversations.deleteConversation(conv.id);
          this.renderConversationList();
          this.renderActiveChat();
        };

        btns.append(btnRename, btnDel);
        item.append(info, btns);
        box.appendChild(item);
      }
    }

    renderActiveChat() {
      ChartRenderer.destroyAll();
      const streamEl = $('chatStream');
      streamEl.innerHTML = '';
      const conv = this.conversations.getActive();
      if (!conv) return;

      if (conv.messages.length === 0) {
        const welcome = document.createElement('div');
        welcome.className = 'empty-welcome';
        welcome.innerHTML = `
          <img src="icon-192.png" alt="مغز دوم">
          <h2>به مغز دوم خوش آمدید</h2>
          <p>مدل رایگان یا دلخواه خود را از بالا برگزینید، در صورت نیاز کلید دسترسی خود را در تنظیمات ثبت کنید و گفت‌وگو را آغاز کنید.</p>
        `;
        const chips = document.createElement('div');
        chips.className = 'quick-chips';
        const starters = [
          'یک جدول مقایسه بساز و نکات مهم را با زیرخط و جعبه خلاصه مشخص کن',
          'یک نمودار میله‌ای نمونه با داده واقعی رسم کن',
          'تست فرمول انتگرال ریاضی و قطعه کد پایتون',
          'تنظیم کلید دسترسی اوپن‌روتر'
        ];
        starters.forEach((txt, idx) => {
          const c = document.createElement('button');
          c.type = 'button';
          c.className = 'quick-chip';
          c.textContent = txt;
          c.onclick = () => {
            if (idx === 3) {
              this.openSettingsModal();
              return;
            }
            this.composer.textarea.value = txt;
            this.composer.autoResize();
            this.composer.textarea.focus();
          };
          chips.appendChild(c);
        });
        welcome.appendChild(chips);
        streamEl.appendChild(welcome);
        return;
      }

      for (const msg of conv.messages) {
        streamEl.appendChild(this.createMessageElement(msg));
      }
      this.scrollToBottom();
    }

    createMessageElement(msg, isStreaming = false) {
      const row = document.createElement('article');
      row.className = `msg-row ${msg.role}`;
      row.dataset.msgId = msg.id;

      const card = document.createElement('div');
      card.className = 'msg-card';

      const head = document.createElement('div');
      head.className = 'msg-header';

      const roleSpan = document.createElement('span');
      roleSpan.className = 'msg-role';
      roleSpan.textContent = msg.role === 'user' ? 'شما' : `مغز دوم${msg.model ? ` · ${msg.model}` : ''}`;

      const metaSpan = document.createElement('span');
      metaSpan.className = 'msg-meta tech-num';
      const timeStr = msg.createdAt ? formatTimeFa(msg.createdAt) : '';
      const durStr = msg.durationMs ? formatDuration(msg.durationMs) : '';
      metaSpan.textContent = [timeStr, durStr].filter(Boolean).join(' · ');

      head.append(roleSpan, metaSpan);
      card.appendChild(head);

      if (Array.isArray(msg.attachments) && msg.attachments.length > 0) {
        const attBox = document.createElement('div');
        attBox.className = 'msg-attachments';
        for (const a of msg.attachments) {
          const b = document.createElement('span');
          b.className = 'attach-badge';
          b.textContent = `📄 ${a.name}`;
          attBox.appendChild(b);
        }
        card.appendChild(attBox);
      }

      const bodyEl = document.createElement('div');
      bodyEl.className = 'msg-body';
      bodyEl.setAttribute('dir', 'auto');
      if (msg.role === 'user') {
        const plain = document.createElement('div');
        plain.className = 'user-plain-body';
        plain.setAttribute('dir', 'auto');
        plain.textContent = msg.content || '';
        bodyEl.appendChild(plain);
      } else {
        this.markdown.renderInto(bodyEl, msg.content, isStreaming);
      }
      card.appendChild(bodyEl);

      if (Array.isArray(msg.citations) && msg.citations.length > 0) {
        const citeBox = document.createElement('div');
        citeBox.className = 'citations-box';
        citeBox.innerHTML = '<div class="citations-title">🌐 منابع وب استفاده‌شده:</div>';
        const list = document.createElement('div');
        list.className = 'citations-list';
        for (const c of msg.citations) {
          const href = safeUrl(c.url);
          if (!href) continue;
          const a = document.createElement('a');
          a.className = 'citation-chip';
          a.href = href;
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.textContent = c.title || href;
          list.appendChild(a);
        }
        citeBox.appendChild(list);
        card.appendChild(citeBox);
      }

      if (msg.error) {
        const errEl = document.createElement('div');
        errEl.className = 'msg-error-box';
        errEl.textContent = msg.error;
        card.appendChild(errEl);
      }

      if (!isStreaming) {
        card.appendChild(this.buildMessageActions(msg, bodyEl));
      }

      row.appendChild(card);
      return row;
    }

    buildMessageActions(msg, bodyEl) {
      const bar = document.createElement('div');
      bar.className = 'msg-actions';

      const addBtn = (label, fn) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'msg-act-btn';
        b.textContent = label;
        b.onclick = fn;
        bar.appendChild(b);
      };

      if (msg.role === 'assistant') {
        addBtn('کپی پاسخ', async () => {
          try {
            await copyToClipboard(bodyEl.innerText || msg.content);
            ErrorManager.toast('متن پاسخ کپی شد.', 'ok');
          } catch (_) {}
        });
        addBtn('کپی مارک‌داون', async () => {
          try {
            await copyToClipboard(msg.content);
            ErrorManager.toast('متن خام مارک‌داون کپی شد.', 'ok');
          } catch (_) {}
        });
        addBtn('تولید مجدد', () => this.regenerateFrom(msg.id));
        addBtn('ادامه پاسخ', () => this.continueFrom(msg.id));
        addBtn('دانلود متن', () => downloadBlob(bodyEl.innerText || msg.content, `response-${Date.now()}.txt`));
        addBtn('دانلود مارک‌داون', () => downloadBlob(msg.content, `response-${Date.now()}.md`, 'text/markdown;charset=utf-8'));
      } else {
        addBtn('ویرایش', () => this.openInlineUserEdit(msg.id, bodyEl));
        addBtn('ارسال مجدد', () => this.resendUserMessage(msg.id));
        addBtn('کپی', async () => {
          try {
            await copyToClipboard(msg.content);
            ErrorManager.toast('پیام کپی شد.', 'ok');
          } catch (_) {}
        });
      }

      return bar;
    }

    openInlineUserEdit(msgId, bodyEl) {
      if (this.isGenerating) return;
      const conv = this.conversations.getActive();
      const msg = conv?.messages.find((m) => m.id === msgId);
      if (!msg) return;

      bodyEl.innerHTML = '';
      const box = document.createElement('div');
      box.className = 'edit-msg-box';
      const ta = document.createElement('textarea');
      ta.value = msg.content;
      ta.dir = 'auto';

      const row = document.createElement('div');
      row.style.display = 'flex';
      row.style.gap = '6px';

      const btnSaveSend = document.createElement('button');
      btnSaveSend.type = 'button';
      btnSaveSend.className = 'primary-btn';
      btnSaveSend.textContent = 'ذخیره و ارسال مجدد';
      btnSaveSend.onclick = async () => {
        const nextText = ta.value.trim();
        if (!nextText) return;
        const idx = conv.messages.findIndex((m) => m.id === msgId);
        if (idx === -1) return;
        conv.messages[idx].content = nextText;
        conv.messages = conv.messages.slice(0, idx + 1);
        await this.conversations.saveConversation(conv);
        this.renderActiveChat();
        await this.executeCompletion(conv);
      };

      const btnCancel = document.createElement('button');
      btnCancel.type = 'button';
      btnCancel.className = 'secondary-btn';
      btnCancel.textContent = 'انصراف';
      btnCancel.onclick = () => this.renderActiveChat();

      row.append(btnSaveSend, btnCancel);
      box.append(ta, row);
      bodyEl.appendChild(box);
      ta.focus();
    }

    async resendUserMessage(msgId) {
      if (this.isGenerating) return;
      const conv = this.conversations.getActive();
      const idx = conv?.messages.findIndex((m) => m.id === msgId) ?? -1;
      if (idx === -1) return;
      conv.messages = conv.messages.slice(0, idx + 1);
      await this.conversations.saveConversation(conv);
      this.renderActiveChat();
      await this.executeCompletion(conv);
    }

    async regenerateFrom(assistantMsgId) {
      if (this.isGenerating) return;
      const conv = this.conversations.getActive();
      const idx = conv?.messages.findIndex((m) => m.id === assistantMsgId) ?? -1;
      if (idx === -1) return;
      conv.messages = conv.messages.slice(0, idx);
      await this.conversations.saveConversation(conv);
      this.renderActiveChat();
      await this.executeCompletion(conv);
    }

    async continueFrom(assistantMsgId) {
      if (this.isGenerating) return;
      const conv = this.conversations.getActive();
      const target = conv?.messages.find((m) => m.id === assistantMsgId);
      if (!target || !target.content) return;

      const idx = conv.messages.findIndex((m) => m.id === assistantMsgId);
      conv.messages = conv.messages.slice(0, idx + 1);
      conv.messages.push({
        id: uid('msg'),
        role: 'user',
        content: 'لطفاً دقیقاً از ادامه آخرین جمله پاسخ قبلی‌ات بدون تکرار مطالب قبل ادامه بده.',
        createdAt: Date.now()
      });
      await this.conversations.saveConversation(conv);
      this.renderActiveChat();
      await this.executeCompletion(conv);
    }

    async handleSend() {
      if (this.isGenerating) return;
      const text = this.composer.textarea.value.trim();
      const attachments = [...this.composer.pendingFiles];
      if (!text && attachments.length === 0) return;

      if (!this.settings.apiKey) {
        ErrorManager.toast('لطفاً ابتدا کلید دسترسی اوپن‌روتر را در تنظیمات وارد کنید.', 'err', 4000);
        this.openSettingsModal();
        return;
      }

      const conv = this.conversations.getActive();
      if (!conv) return;

      const userMsg = {
        id: uid('msg'),
        role: 'user',
        content: text || 'لطفاً فایل پیوست را بررسی کن.',
        attachments,
        createdAt: Date.now()
      };

      if (conv.messages.length === 0) {
        conv.title = (text || attachments[0]?.name || 'گفت‌وگوی جدید').replace(/\s+/g, ' ').slice(0, 48);
      }

      // پاک کردن موقت ورودی فقط پس از افزودن به گفتگو (در خطای API بازگردانده می‌شود)
      const draftBackup = this.composer.textarea.value;
      const filesBackup = [...this.composer.pendingFiles];

      conv.messages.push(userMsg);
      await this.conversations.saveConversation(conv);

      this.composer.textarea.value = '';
      this.composer.pendingFiles = [];
      this.composer.renderPendingFiles();
      this.composer.autoResize();

      this.renderConversationList();
      this.renderActiveChat();

      const ok = await this.executeCompletion(conv);
      if (!ok && conv.messages[conv.messages.length - 1]?.role === 'user') {
        // در صورت شکست کامل پیش از دریافت پاسخ، نوشته کاربر حفظ و بازیابی می‌شود
        conv.messages.pop();
        await this.conversations.saveConversation(conv);
        this.composer.textarea.value = draftBackup;
        this.composer.pendingFiles = filesBackup;
        this.composer.renderPendingFiles();
        this.composer.autoResize();
        this.renderActiveChat();
      }
    }

    async executeCompletion(conv) {
      this.isGenerating = true;
      this.abortController = new AbortController();
      $('btnSendMsg').hidden = true;
      $('btnStopMsg').hidden = false;
      $('composerStatusText').textContent = this.settings.data.webSearchEnabled
        ? 'در حال جست‌وجو در وب و تولید پاسخ...'
        : 'در حال دریافت پاسخ از مدل...';
      this.syncHeaderAndToggles();

      const startTime = performance.now();
      const assistantMsg = {
        id: uid('msg'),
        role: 'assistant',
        content: '',
        model: this.settings.normalizeModelId(this.settings.data.modelId),
        createdAt: Date.now(),
        durationMs: 0,
        citations: [],
        error: ''
      };

      const streamEl = $('chatStream');
      const liveNode = this.createMessageElement(assistantMsg, true);
      streamEl.appendChild(liveNode);
      const liveBody = liveNode.querySelector('.msg-body');
      this.scrollToBottom();

      let receivedAnyToken = false;
      try {
        const spText = this.systemPrompt.getEffectivePrompt(conv);
        const apiMessages = this.conversations.buildApiMessages(conv, spText, this.settings.data.contextLimit);
        const res = await this.client.createChatRequest(apiMessages, this.abortController.signal);

        const result = await this.streamer.consumeResponse(
          res,
          Boolean(this.settings.data.streaming),
          (partialText, citations) => {
            if (partialText) receivedAnyToken = true;
            assistantMsg.content = partialText;
            assistantMsg.citations = citations;
            this.markdown.renderInto(liveBody, partialText, true);
            this.scrollToBottom();
          },
          this.abortController.signal
        );

        assistantMsg.content = result.text;
        assistantMsg.citations = result.citations;
        assistantMsg.durationMs = Math.round(performance.now() - startTime);

        if (!assistantMsg.content.trim()) {
          assistantMsg.error = 'پاسخ خالی از مدل دریافت شد.';
        }

        conv.messages.push(assistantMsg);
        await this.conversations.saveConversation(conv);
        this.renderConversationList();
        this.renderActiveChat();
        return true;
      } catch (err) {
        const isAbort = err?.name === 'AbortError';
        const friendly = isAbort
          ? 'تولید پاسخ متوقف شد.'
          : (err?.message === 'NO_API_KEY'
            ? 'کلید دسترسی وارد نشده است.'
            : ErrorManager.formatNetworkError(err));

        if (receivedAnyToken && assistantMsg.content.trim()) {
          assistantMsg.durationMs = Math.round(performance.now() - startTime);
          assistantMsg.error = friendly;
          conv.messages.push(assistantMsg);
          await this.conversations.saveConversation(conv);
          this.renderActiveChat();
          ErrorManager.toast(friendly, 'info', 3500);
          return true;
        }

        liveNode.remove();
        ErrorManager.toast(friendly, 'err', 4500);
        return false;
      } finally {
        this.isGenerating = false;
        this.abortController = null;
        $('btnSendMsg').hidden = false;
        $('btnStopMsg').hidden = true;
        $('composerStatusText').textContent = 'آماده';
        this.syncHeaderAndToggles();
      }
    }

    stopGeneration() {
      if (this.abortController) {
        this.abortController.abort();
      }
    }

    scrollToBottom() {
      const vp = $('chatViewport');
      if (!vp) return;
      vp.scrollTop = vp.scrollHeight;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    const app = new AppController();
    window.SecondBrainApp = app;
    app.bootstrap();
  });
})();
