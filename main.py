from html2rss.config import config
from html2rss.rss import rss
import asyncio

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    config.load_config()
    conf = config.find_config("monash_events")
    if not conf:
        print("Config not found")
        return
    content = await rss.generate(conf)
    print(content)


if __name__ == "__main__":
    asyncio.run(main())
