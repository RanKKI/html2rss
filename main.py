from html2rss.config import config
from html2rss.rss import rss
import asyncio


async def main():
    print("hello")
    config.load_config()
    conf = config.find_config("monash_events")
    if not conf:
        print("Config not found")
        return
    content = await rss.generate(conf)
    print(content)


if __name__ == "__main__":
    asyncio.run(main())
