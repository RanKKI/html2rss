import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path

import aiohttp
import redis
from rss_parser import Parser


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

CONFIG_FOLDER = Path(os.environ.get("HTML2RSS_CONFIG_FOLDER", default="./config"))
BOT_CONFIG = json.loads((CONFIG_FOLDER / "bot.json").read_text())
URLs = BOT_CONFIG["URLs"]
CALLBACK_URL = BOT_CONFIG["callback"]
r = redis.Redis(
    host=os.environ.get("REDIS_HOST", default="localhost"),
    port=os.environ.get("REDIS_PORT", default=6379),
)


async def request(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()


async def sendCallback(title, content) -> str:
    for url in CALLBACK_URL:
        full_url = url.format(title=title, content=content.replace("\n", " "))
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url) as resp:
                return await resp.text()


async def checkRSS(url: str):
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    first_run = False
    if not r.get(f"url:{url_hash}"):
        r.set(f"url:{url_hash}", 1)
        first_run = True

    resp = await request(url)
    rss = Parser.parse(resp)
    for item in rss.channel.items:
        _id = item.guid or item.url or item.title
        _id = hashlib.md5(_id.encode("utf-8")).hexdigest()
        if not first_run and not r.get(f"item:{_id}"):
            await sendCallback(item.title, item.description)
        r.set(f"item:{_id}", 1)


async def main():
    if not r.get("first_run"):
        r.set("first_run", 1)
        await sendCallback("RSS Bot", "RSS Bot is running")

    for url in URLs:
        await checkRSS(url)


if __name__ == "__main__":
    asyncio.run(main())
