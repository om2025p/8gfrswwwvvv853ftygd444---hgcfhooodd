#Github.com/Vasusen-code

from pyrogram import Client

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from decouple import config
import logging, time, sys
import asyncio

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# Check if we are running in an active async event loop context
is_async_context = False
try:
    loop = asyncio.get_running_loop()
    if loop and loop.is_running():
        is_async_context = True
except RuntimeError:
    pass

# variables
def safe_int_config(key):
    val = config(key, default=None)
    if not val:
        return None
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None

API_ID = safe_int_config("API_ID")
API_HASH = config("API_HASH", default=None)
BOT_TOKEN = config("BOT_TOKEN", default=None)
SESSION = config("SESSION", default=None)
FORCESUB = config("FORCESUB", default=None)
AUTH = safe_int_config("AUTH")

# Create the Telethon Client instance
bot = TelegramClient('bot', API_ID, API_HASH)

if not is_async_context:
    try:
        bot.start(bot_token=BOT_TOKEN)
    except BaseException as e:
        print(f"Telethon Bot Start Warning: {e}")

userbot = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID)

if not is_async_context:
    try:
        userbot.start()
    except BaseException as e:
        print(f"Userbot Start Warning: {e}")

Bot = Client(
    "SaveRestricted",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

if not is_async_context:
    try:
        Bot.start()
    except Exception as e:
        print(f"Bot Start Warning: {e}")
