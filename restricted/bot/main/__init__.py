#Github.com/Vasusen-code

from pyrogram import Client

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

from decouple import config
import logging, time, sys

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# variables
API_ID = config("API_ID", default=None, cast=int)
API_HASH = config("API_HASH", default=None)
BOT_TOKEN = config("BOT_TOKEN", default=None)
SESSION = config("SESSION", default=None)
FORCESUB = config("FORCESUB", default=None)
AUTH = config("AUTH", default=None, cast=int)

# Create the Telethon Client instance (do not chain .start() to avoid storing the coroutine object)
bot = TelegramClient('bot', API_ID, API_HASH)

try:
    bot.start(bot_token=BOT_TOKEN)
except BaseException as e:
    print(f"Telethon Bot Start Warning: {e}")

userbot = Client("saverestricted", session_string=SESSION, api_hash=API_HASH, api_id=API_ID)

try:
    userbot.start()
except BaseException as e:
    print(f"Userbot Start Warning: {e}")

Bot = Client(
    "SaveRestricted",
    bot_token=BOT_TOKEN,
    api_id=int(API_ID),
    api_hash=API_HASH
)

try:
    Bot.start()
except Exception as e:
    print(f"Bot Start Warning: {e}")
