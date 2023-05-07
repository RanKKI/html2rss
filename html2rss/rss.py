import time
from hashlib import md5
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

import aiohttp
import lxml.etree
import lxml.html
from jinja2 import Environment, FileSystemLoader, select_autoescape

from html2rss.dataclass import RSSConf, RSSItem, SiteConf

NODE_RESULT = Union[lxml.etree._Element, lxml.etree._ElementUnicodeResult]


class RSSCache(object):
    def __init__(self) -> None:
        self.cache_folder = Path("./cache")
        self.cache_folder.mkdir(exist_ok=True)
        self.cache_time: Dict[str, int] = {}
        self.now = lambda: int(time.time())

    def is_valid(self, conf: SiteConf) -> bool:
        cache_file = self.get_cache_file(conf.url)
        if not cache_file.exists():
            return False
        return True
        if cache_file.name not in self.cache_time:
            return False
        # return self.now() < self.cache_time[cache_file.name] + conf.refresh

    def get_cache_file(self, url: str) -> Path:
        url_hash = md5(url.encode("utf-8")).hexdigest()
        return self.cache_folder / url_hash

    def get_html(self, url: str) -> Union[str, None]:
        cache_file = self.get_cache_file(url)
        if cache_file.exists():
            return cache_file.read_text()
        return None

    def set_html(self, url: str, html: str) -> None:
        cache_file = self.get_cache_file(url)
        cache_file.write_text(html)


class RSS(object):
    def __init__(self) -> None:
        self.cache = RSSCache()
        jinja2Env = Environment(
            loader=FileSystemLoader(searchpath="./templates"),
            autoescape=select_autoescape(),
        )
        self.template = jinja2Env.get_template("rss.xml")

    async def _scrape_html(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.text()

    async def scrape_html(self, conf: SiteConf) -> str:
        if self.cache.is_valid(conf):
            return self.cache.get_html(conf.url)
        html = await self._scrape_html(conf.url)
        self.cache.set_html(conf.url, html)
        return html

    def __extract_text_if_needed(
        self, arr: Iterable[Tuple[NODE_RESULT, NODE_RESULT, NODE_RESULT]]
    ) -> str:
        def f(val: NODE_RESULT):
            if isinstance(val, lxml.etree._Element):
                return val.xpath("string()")
            return val

        for title, description, url in arr:
            yield f(title), f(description), f(url)

    def parse_html(self, html: lxml.etree.ElementBase, conf: RSSConf) -> List[RSSItem]:
        items = []
        titles = html.xpath(conf.title)
        descriptions = html.xpath(conf.description)
        urls = html.xpath(conf.url)
        # pub_dates = html.xpath(conf.pub_date) if conf.pub_date else []

        f = self.__extract_text_if_needed
        for title, description, url in f(zip(titles, descriptions, urls)):
            items.append(
                RSSItem(
                    title=title,
                    description=description,
                    url=url,
                )
            )
        return items

    def extract_title_from_html(self, html: lxml.etree.ElementBase) -> str:
        return html.xpath("//title/text()")[0]

    async def generate(self, conf: SiteConf) -> str:
        html = await self.scrape_html(conf)
        tree = lxml.etree.HTML(html)
        items = self.parse_html(tree, conf.rss)
        title = self.extract_title_from_html(tree) or conf.name
        return self.template.render(title=title, items=items, url=conf.url)


rss = RSS()
