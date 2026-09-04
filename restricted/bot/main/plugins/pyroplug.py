#Github.com-Vasusen-code

import asyncio, time, os, inspect, math

from .. import bot as Drone
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot

from pyrogram import Client, filters
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, PeerIdInvalid
from pyrogram.enums import MessageMediaType
from ethon.pyfunc import video_metadata
from ethon.telefunc import fast_upload
from telethon.tl.types import DocumentAttributeVideo
from telethon import events

def humanbytes(size):
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    dic_power_n = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power and n < 4:
        size /= power
        n += 1
    return f"{round(size, 2)} {dic_power_n[n]}B"

def thumbnail(sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    else:
        return None

async def safe_edit_msg_pyroplug(client, bot, sender, edit_id, text):
    if not edit_id or isinstance(edit_id, bool):
        try:
            return await bot.send_message(sender, text)
        except Exception:
            return None
    try:
        res = await client.edit_message_text(sender, edit_id, text)
        return res if res and not isinstance(res, bool) else edit_id
    except Exception as e:
        print(f"DEBUG: Pyroplug client.edit_message_text failed: {e}. Trying Telethon bot...")
        try:
            res = await bot.edit_message(sender, edit_id, text)
            return res if res and not isinstance(res, bool) else edit_id
        except Exception as e2:
            print(f"DEBUG: Pyroplug bot.edit_message failed: {e2}. Sending new message...")
            try:
                return await bot.send_message(sender, text)
            except Exception as e3:
                print(f"DEBUG: All pyroplug fallback edit methods failed: {e3}")
                return edit_id

async def safe_edit_object(msg_obj, text):
    if not msg_obj:
        return
    try:
        if hasattr(msg_obj, 'edit'):
            await msg_obj.edit(text)
        elif hasattr(msg_obj, 'edit_text'):
            await msg_obj.edit_text(text)
    except Exception as e:
        print(f"DEBUG: safe_edit_object failed: {e}")

async def safe_delete_object(msg_obj):
    if not msg_obj:
        return
    try:
        await msg_obj.delete()
    except Exception as e:
        print(f"DEBUG: safe_delete_object failed: {e}")

async def get_msg(userbot, client, bot, sender, edit_id, msg_link, i):

    """ userbot: PyrogramUserBot
    client: PyrogramBotClient
    bot: TelethonBotClient """

    print(f"DEBUG: Entering get_msg with msg_link: {msg_link}")

    # Redirect social media links (TikTok, Instagram, WhatsApp, etc.) directly to process_social_media_download
    from urllib.parse import urlparse
    parsed_domain = urlparse(msg_link.lower()).netloc
    if 't.me' not in parsed_domain and 'telegram.me' not in parsed_domain:
        from download_single import process_social_media_download
        return await process_social_media_download(msg_link, sender, edit_id)

    # Ensure Pyrogram and Telethon clients are started dynamically (attempt unconditionally to bypass stale states)
    for c_obj in [userbot, client]:
        if c_obj:
            name = getattr(c_obj, 'name', 'Client')
            try:
                # Use await on is_connected to support all environments securely
                is_conn = c_obj.is_connected
                if inspect.iscoroutine(is_conn):
                    is_conn = await is_conn

                print(f"DEBUG: Client {name} is_connected status: {is_conn}")
                if not is_conn:
                    print(f"DEBUG: Starting client {name} inside get_msg...")
                    res = c_obj.start()
                    if inspect.iscoroutine(res):
                        await res
                    print(f"DEBUG: Client {name} successfully started.")
            except (ConnectionError, OSError) as e:
                if "already" in str(e).lower():
                    print(f"DEBUG: Client {name} is already started in get_msg.")
                else:
                    print(f"DEBUG: Warning starting client {name} in get_msg: {e}")
            except Exception as e:
                if "already started" in str(e).lower() or "active" in str(e).lower():
                    pass
                else:
                    print(f"DEBUG: Error starting client {name} dynamically in get_msg: {e}")

    try:
        if bot and not bot.is_connected():
            print("DEBUG: Starting Telethon bot dynamically in get_msg...")
            res = bot.start()
            if inspect.iscoroutine(res):
                await res
            print("DEBUG: Telethon bot successfully started.")
    except Exception as e:
        print(f"DEBUG: Error starting Telethon bot in get_msg: {e}")

    edit = ""
    chat = ""
    round_message = False
    clean_link = msg_link.split("?")[0].rstrip("/")
    try:
        last_part = clean_link.split("/")[-1]
        msg_id = int(last_part) + int(i) if last_part and last_part.isdigit() else 0
    except Exception:
        msg_id = 0
    height, width, duration, thumb_path = 90, 90, 0, None

    print(f"DEBUG: Sanitized msg_id: {msg_id}")

    # CRITICAL BUG FIX: Use exact string presence check instead of 't.me/c/' or 't.me/b/' in msg_link
    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
        if 't.me/b/' in msg_link:
            chat = str(clean_link.split("/")[-2])
        else:
            chat = int('-100' + str(clean_link.split("/")[-2]))

        print(f"DEBUG: Link classified as PRIVATE/RESTRICTED. Chat extracted: {chat}")
        file = ""
        try:
            print(f"DEBUG: Getting message with ID {msg_id} from private chat {chat}...")
            msg = await userbot.get_messages(chat, msg_id)
            print(f"DEBUG: Message retrieved. Media type: {getattr(msg, 'media', None)}")

            if msg.media:
                if msg.media==MessageMediaType.WEB_PAGE:
                    edit = await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "Cloning.")
                    try:
                        await client.send_message(sender, msg.text.markdown)
                    except Exception:
                        await bot.send_message(sender, msg.text.markdown)
                    await safe_delete_object(edit)
                    return
            if not msg.media:
                if msg.text:
                    edit = await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "Cloning.")
                    try:
                        await client.send_message(sender, msg.text.markdown)
                    except Exception:
                        await bot.send_message(sender, msg.text.markdown)
                    await safe_delete_object(edit)
                    return
            edit = await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "Trying to Download.")
            file = await userbot.download_media(
                msg,
                progress=progress_for_pyrogram,
                progress_args=(
                    client,
                    "**DOWNLOADING:**\n",
                    edit,
                    time.time()
                )
            )
            print(f"DEBUG: Download completed. File path: {file}")
            await safe_edit_object(edit, 'Preparing to Upload!')
            caption = None
            if msg.caption is not None:
                caption = msg.caption
            if msg.media==MessageMediaType.VIDEO_NOTE:
                round_message = True
                print("DEBUG: Processing video note metadata...")
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                print(f'DEBUG: d: {duration}, w: {width}, h:{height}')
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video_note(
                    chat_id=sender,
                    video_note=file,
                    length=height, duration=duration,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        '**UPLOADING:**\n',
                        edit,
                        time.time()
                    )
                )
            elif msg.media==MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                print("DEBUG: Processing video metadata...")
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                print(f'DEBUG: d: {duration}, w: {width}, h:{height}')
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video(
                    chat_id=sender,
                    video=file,
                    caption=caption,
                    supports_streaming=True,
                    height=height, width=width, duration=duration,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        '**UPLOADING:**\n',
                        edit,
                        time.time()
                    )
                )

            elif msg.media==MessageMediaType.PHOTO or (hasattr(msg, 'photo') and msg.photo):
                await safe_edit_object(edit, "Uploading photo...")
                from download_single import send_media_to_destinations
                await send_media_to_destinations(file, caption, sender)
            else:
                thumb_path=thumbnail(sender)
                from download_single import send_media_to_destinations
                await send_media_to_destinations(file, caption, sender)
            try:
                os.remove(file)
                if os.path.isfile(file) == True:
                    os.remove(file)
            except Exception:
                pass
            await safe_delete_object(edit)
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid) as ce:
            print(f"DEBUG: Channel joining/permission error: {ce}")
            await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "Have you joined the channel?")
            return
        except PeerIdInvalid as pie:
            print(f"DEBUG: PeerIdInvalid error: {pie}")
            chat = clean_link.split("/")[-3]
            try:
                int(chat)
                new_link = f"t.me/c/{chat}/{msg_id}"
            except:
                new_link = f"t.me/b/{chat}/{msg_id}"
            return await get_msg(userbot, client, bot, sender, edit_id, msg_link, i)
        except Exception as e:
            print(f"DEBUG: Unhandled error in private downloader: {e}")
            if "messages.SendMedia" in str(e) \
            or "SaveBigFilePartRequest" in str(e) \
            or "SendMediaRequest" in str(e) \
            or "PeerIdInvalid" in str(type(e)) \
            or "peer" in str(e).lower() \
            or str(e) == "File size equals to 0 B":
                try:
                    if msg.media==MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                        UT = time.time()
                        uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                        attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height, round_message=round_message, supports_streaming=True)]
                        await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, attributes=attributes, force_document=False)
                    elif msg.media==MessageMediaType.VIDEO_NOTE:
                        uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                        attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height, round_message=round_message, supports_streaming=True)]
                        await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, attributes=attributes, force_document=False)
                    else:
                        UT = time.time()
                        uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                        await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, force_document=True)
                    if os.path.isfile(file) == True:
                        os.remove(file)
                except Exception as e:
                    print(e)
                    await safe_edit_msg_pyroplug(client, bot, sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
                    try:
                        os.remove(file)
                    except Exception:
                        return
                    return
            else:
                await safe_edit_msg_pyroplug(client, bot, sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
                try:
                    os.remove(file)
                except Exception:
                    return
                return
        try:
            os.remove(file)
            if os.path.isfile(file) == True:
                os.remove(file)
        except Exception:
            pass
        await safe_delete_object(edit)
    else:
        # Public Channel Link
        print(f"DEBUG: Link classified as PUBLIC. Chat extracted: {msg_link}")

        parts = [p for p in clean_link.split("/") if p]
        chat = parts[-2] if len(parts) >= 2 else clean_link.split("t.me")[1].split("/")[1]

        from download_single import send_media_to_destinations, safe_edit_message, safe_send_message

        edit = await safe_edit_message(sender, edit_id, f"📥 *در حال ارتباط با سرور و استخراج پست تلگرام از @{chat}...*")

        try:
            # Pre-resolve chat with userbot to populate peer cache
            if getattr(userbot, 'is_connected', False):
                try:
                    print(f"DEBUG: Pre-resolving chat @{chat} with userbot...")
                    await userbot.get_chat(chat)
                except Exception as e_gc:
                    print(f"DEBUG: userbot.get_chat(@{chat}) failed: {e_gc}")
                    try:
                        await userbot.join_chat(chat)
                        print(f"DEBUG: Successfully joined public channel @{chat}")
                    except Exception as e_jc:
                        print(f"DEBUG: userbot.join_chat(@{chat}) notice: {e_jc}")

            print(f"DEBUG: Fetching message {msg_id} from public channel {chat}...")
            msg = None
            try:
                msg = await asyncio.wait_for(userbot.get_messages(chat, msg_id), timeout=15)
            except Exception as e_ub:
                print(f"DEBUG: userbot.get_messages failed for public chat {chat}: {e_ub}")
                try:
                    if getattr(client, 'is_connected', False):
                        msg = await asyncio.wait_for(client.get_messages(chat, msg_id), timeout=15)
                except Exception as e_cl:
                    print(f"DEBUG: client.get_messages failed for public chat {chat}: {e_cl}")

            if not msg or getattr(msg, 'empty', True):
                print("DEBUG: Message was empty or unavailable.")
                await safe_edit_message(sender, edit, f"❌ *رئیس بزرگ، پیام یا محتوای مورد نظر در پست @{chat}/{msg_id} دریافت نشد یا حذف شده است.*")
                return

            if msg.media and msg.media != MessageMediaType.WEB_PAGE:
                edit = await safe_edit_message(sender, edit, f"⚡ *در حال دانلود محتوای رسانه‌ای پست @{chat}/{msg_id}...*")

                last_update = [0]
                start_time = time.time()

                async def custom_progress(current, total):
                    now = time.time()
                    if now - last_update[0] < 2.5 and current < total:
                        return
                    last_update[0] = now
                    diff = max(now - start_time, 0.1)
                    percentage = (current * 100 / total) if total > 0 else 0
                    speed = current / diff
                    filled = int(percentage // 10)
                    bar = "█" * filled + "░" * (10 - filled)
                    p_text = (
                        f"⬇️ *در حال دانلود محتوا از تلگرام...*\n\n"
                        f"🟢 `[{bar}] {round(percentage, 1)}%`\n"
                        f"📊 *حجم:* {humanbytes(current)} از {humanbytes(total)}\n"
                        f"🚀 *سرعت:* {humanbytes(speed)}/s"
                    )
                    await safe_edit_message(sender, edit, p_text)

                file = None
                try:
                    file = await asyncio.wait_for(userbot.download_media(msg, progress=custom_progress), timeout=180)
                except Exception as dl_ub_err:
                    print(f"DEBUG: userbot download_media failed: {dl_ub_err}. Trying client download_media...")
                    try:
                        if getattr(client, 'is_connected', False):
                            file = await asyncio.wait_for(client.download_media(msg, progress=custom_progress), timeout=180)
                    except Exception as dl_cl_err:
                        print(f"DEBUG: client download_media failed: {dl_cl_err}")

                if file and os.path.exists(file) and os.path.getsize(file) > 0:
                    await safe_edit_message(sender, edit, '⬆️ *فایل با موفقیت دانلود شد. در حال ارسال به چت شما...*')
                    caption = msg.caption if msg.caption is not None else None
                    await send_media_to_destinations(file, caption, sender)
                    try:
                        os.remove(file)
                    except Exception:
                        pass
                    await safe_edit_message(sender, edit, "✅ *دانلود و ارسال فایل با موفقیت پایان یافت!*")
                else:
                    await safe_edit_message(sender, edit, "❌ *خطا در دانلود فایل رسانه‌ای تلگرام. حجم فایل صفر یا دریافت ناموفق بود.*")
            elif msg.text or (msg.media == MessageMediaType.WEB_PAGE and msg.text):
                await safe_edit_message(sender, edit, "📥 *در حال ارسال متن پیام...*")
                caption_text = msg.text.markdown if hasattr(msg.text, 'markdown') else str(msg.text)
                await safe_send_message(sender, caption_text)
                await safe_edit_message(sender, edit, "✅ *ارسال متن پیام با موفقیت پایان یافت!*")
            else:
                await safe_edit_message(sender, edit, "❌ *پیام انتخابی فاقد محتوای رسانه‌ای قابل دانلود می‌باشد.*")
        except Exception as e:
            print(f"DEBUG: Error processing public link {msg_link}: {e}")
            await safe_edit_message(sender, edit, f'❌ *خطا در دریافت پست عمومی تلگرام:* `{msg_link}`\n\n`{str(e)}`')

async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    await get_msg(userbot, client, Drone, sender, x.id, msg_link, i)
