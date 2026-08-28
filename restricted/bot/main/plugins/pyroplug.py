#Github.com-Vasusen-code

import asyncio, time, os, inspect

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
        edit = await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "📥 *در حال دریافت و تحلیل محتوای لینک عمومی تلگرام...*")

        parts = [p for p in clean_link.split("/") if p]
        chat = parts[-2] if len(parts) >= 2 else clean_link.split("t.me")[1].split("/")[1]

        from download_single import send_media_to_destinations

        try:
            print(f"DEBUG: Fetching message {msg_id} from public channel {chat} via userbot/client...")
            msg = None
            try:
                msg = await userbot.get_messages(chat, msg_id)
            except Exception as e_ub:
                print(f"DEBUG: userbot.get_messages failed for public chat {chat}: {e_ub}")
                try:
                    msg = await client.get_messages(chat, msg_id)
                except Exception as e_cl:
                    print(f"DEBUG: client.get_messages failed for public chat {chat}: {e_cl}")

            if not msg or getattr(msg, 'empty', True):
                print("DEBUG: Message was empty or unavailable.")
                await safe_edit_msg_pyroplug(client, bot, sender, edit_id, f"❌ *رئیس بزرگ، پیام یا محتوای مورد نظر در لینک عمومی دریافت نشد یا حذف شده است.*")
                raise Exception("Public message is empty or unavailable.")

            if msg.media and msg.media != MessageMediaType.WEB_PAGE:
                await safe_edit_object(edit, "⚡ *در حال استخراج و دانلود محتوای رسانه‌ای تلگرام...*")
                file = None
                try:
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
                except Exception as dl_ub_err:
                    print(f"DEBUG: userbot download_media failed: {dl_ub_err}. Trying client download_media...")
                    try:
                        file = await client.download_media(
                            msg,
                            progress=progress_for_pyrogram,
                            progress_args=(
                                client,
                                "**DOWNLOADING (RETRY):**\n",
                                edit,
                                time.time()
                            )
                        )
                    except Exception as dl_cl_err:
                        print(f"DEBUG: client download_media failed: {dl_cl_err}")

                if file and os.path.exists(file):
                    await safe_edit_object(edit, '⬆️ *فایل با موفقیت دانلود شد. در حال ارسال به شما...*')
                    caption = msg.caption if msg.caption is not None else None
                    await send_media_to_destinations(file, caption, sender)
                    try:
                        os.remove(file)
                    except Exception:
                        pass
                    await safe_delete_object(edit)
                else:
                    await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "❌ *خطا در دانلود فایل رسانه‌ای تلگرام.*")
                    raise Exception("Failed to download media file.")
            elif msg.text or (msg.media == MessageMediaType.WEB_PAGE and msg.text):
                await safe_edit_object(edit, "📥 *در حال ارسال متن پیام...*")
                caption_text = msg.text.markdown if hasattr(msg.text, 'markdown') else str(msg.text)
                try:
                    await client.send_message(sender, caption_text)
                except Exception:
                    await bot.send_message(sender, caption_text)
                await safe_delete_object(edit)
            else:
                await safe_edit_msg_pyroplug(client, bot, sender, edit_id, "❌ *پیام انتخابی فاقد محتوای قابل دانلود می‌باشد.*")
                raise Exception("Selected message has no downloadable content.")
        except Exception as e:
            print(f"DEBUG: Error processing public link {msg_link}: {e}")
            if "Public message is empty" not in str(e) and "Failed to download" not in str(e) and "no downloadable content" not in str(e):
                await safe_edit_msg_pyroplug(client, bot, sender, edit_id, f'❌ *خطا در دریافت لینک عمومی:* `{msg_link}`\n\n`{str(e)}`')
            raise e

async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    await get_msg(userbot, client, Drone, sender, x.id, msg_link, i)
