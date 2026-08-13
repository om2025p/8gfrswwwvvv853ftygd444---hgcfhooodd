# Search plugin for Telegram deep search directly from bot chat
import os
import asyncio
from .. import bot as Drone
from .. import userbot, Bot, AUTH
from telethon import events
from pyrogram.raw.functions.contacts import Search
from pyrogram.tl.types import InputPeerUser

def expand_persian_query(query):
    queries = [query]

    # 1. Handle "هام" suffix (e.g., عکسهام -> عکس, عکس هام, عکسهایم, عکس های من)
    if query.endswith("هام") and len(query) > 3:
        base = query[:-3]
        queries.extend([
            f"{base} هام",
            f"{base}هایم",
            f"{base} هایم",
            f"{base}های من",
            f"{base} های من",
            f"{base}ام",
            f"{base} ام"
        ])
    # 2. Handle "ام" suffix (e.g., عکسام -> عکس, عکسهام, عکس های من)
    elif query.endswith("ام") and len(query) > 2 and not query.endswith("هام"):
        base = query[:-2]
        queries.extend([
            f"{base} ام",
            f"{base}هام",
            f"{base} هام",
            f"{base}هایم",
            f"{base} هایم",
            f"{base}های من",
            f"{base} های من"
        ])
    # 3. Handle "هایم" suffix (e.g., عکسهایم -> عکس, عکسهام, عکس های من)
    elif query.endswith("هایم") and len(query) > 4:
        base = query[:-4]
        queries.extend([
            f"{base} هایم",
            f"{base}هام",
            f"{base} هام",
            f"{base}های من",
            f"{base} های من",
            f"{base}ام",
            f"{base} ام"
        ])
    # 4. Handle "های من" suffix (e.g., عکس های من -> عکسهام)
    elif "های من" in query:
        base = query.replace("های من", "").strip()
        queries.extend([
            f"{base}های من",
            f"{base}هام",
            f"{base} هام",
            f"{base}هایم",
            f"{base} هایم",
            f"{base}ام",
            f"{base} ام"
        ])
    # 5. Handle "هایم" with space "هایم"
    elif " هایم" in query:
        base = query.replace(" هایم", "").strip()
        queries.extend([
            f"{base}هایم",
            f"{base}هام",
            f"{base} هام",
            f"{base}های من",
            f"{base} های من",
            f"{base}ام",
            f"{base} ام"
        ])

    seen = set()
    unique_queries = []
    for q in queries:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            unique_queries.append(q_clean)

    return unique_queries

@Drone.on(events.NewMessage(incoming=True, pattern=r'/search(?:\s+(.+))?'))
async def telegram_search(event):
    if not event.is_private:
        return

    # Check authorization if AUTH is set
    if AUTH and event.sender_id != AUTH:
        return await event.reply("⚠️ شما مجاز به استفاده از این ربات نیستید! 🛡️")

    query = event.pattern_match.group(1)
    if not query:
        return await event.reply("⚠️ لطفاً کلمه مورد نظر برای جستجو را وارد کنید.\nمثال: `/search عکس`")

    query = query.strip()
    msg = await event.reply(f"🔎 *در حال جستجوی عمیق و ترکیبی کلمه «{query}» در سرورهای تلگرام...*\n\n🕒 لطفا صبور باشید...")

    try:
        # Ensure userbot is connected
        if not getattr(userbot, 'is_connected', False):
            print("Starting userbot inside direct search plugin...")
            res = userbot.start()
            import inspect
            if inspect.iscoroutine(res):
                await res

        expanded_queries = expand_persian_query(query)
        channels = []
        seen_usernames = set()

        for q_term in expanded_queries:
            try:
                found = await userbot.invoke(Search(q=q_term, limit=1000))
                if found and hasattr(found, 'chats'):
                    for chat in found.chats:
                        username = getattr(chat, 'username', None)
                        if username and username.lower() not in seen_usernames:
                            seen_usernames.add(username.lower())
                            title = getattr(chat, 'title', "بدون عنوان")
                            members = getattr(chat, 'participants_count', None)
                            channels.append((title, username, members))
            except Exception as e_search:
                print(f"Search variation '{q_term}' contacts.Search failed: {e_search}")

            try:
                async for message in userbot.search_global_messages(query=q_term, limit=300):
                    if message.chat and getattr(message.chat, 'username', None):
                        username = getattr(message.chat, 'username')
                        if username and username.lower() not in seen_usernames:
                            seen_usernames.add(username.lower())
                            title = getattr(message.chat, 'title', "بدون عنوان")
                            members = getattr(message.chat, 'participants_count', None) or getattr(message.chat, 'members_count', None)
                            channels.append((title, username, members))
            except Exception as e_msg_search:
                print(f"Search variation '{q_term}' search_global_messages failed: {e_msg_search}")

            await asyncio.sleep(0.5)

        if not channels:
            await msg.edit(f"❌ *رئیس بزرگ، هیچ کانال عمومی برای عبارت «{query}» در تلگرام یافت نشد!*")
            return

        # Format and send results in chunks
        response_text = f"🎯 *نتایج جستجوی رسمی تلگرام برای «{query}» (یافت شده: {len(channels)} کانال):*\n\n"
        chunk_num = 1
        for i, (title, username, members) in enumerate(channels, 1):
            members_str = f" ({members:,} عضو)" if members is not None else ""
            line = f"{i}. 📣 *{title}*\n   🔗 شناسه: @{username}{members_str}\n   👉 [ورود به کانال](https://t.me/{username})\n\n"

            if len(response_text) + len(line) > 3900:
                if chunk_num == 1:
                    await msg.edit(response_text, link_preview=False)
                else:
                    await event.reply(response_text, link_preview=False)
                response_text = f"🎯 *ادامه نتایج جستجو برای «{query}» (بخش {chunk_num + 1}):*\n\n"
                chunk_num += 1
            response_text += line

        if response_text:
            if chunk_num == 1:
                await msg.edit(response_text, link_preview=False)
            else:
                await event.reply(response_text, link_preview=False)

        await event.reply("✅ *جستجوی عمیق تلگرام با موفقیت کامل شد!*")

    except Exception as e:
        print(f"Error during execution of direct search: {e}")
        try:
            await msg.edit(f"❌ *خطا در اجرای جستجوی عمیق تلگرام:*\n`{str(e)}`")
        except:
            pass
