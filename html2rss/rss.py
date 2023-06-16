import logging
import time
from hashlib import md5
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

import aiohttp
import lxml.etree
import lxml.html
from jinja2 import Environment, FileSystemLoader, select_autoescape

from html2rss.dataclass import RSSChannel, RSSItem, SiteConf

NODE_RESULT = Union[lxml.etree._Element, lxml.etree._ElementUnicodeResult]
logger = logging.getLogger(__name__)


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
        if cache_file.name not in self.cache_time:
            return False
        return self.now() < self.cache_time[cache_file.name] + conf.refresh

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

    def parse_attr_normal(
        self, html: lxml.etree.ElementBase, key: str, xpath: str, required: bool = False
    ) -> List[str]:
        if required and not xpath:
            raise ValueError(f"Required key {key} not found")
        if not xpath:
            return {}
        return {key: html.xpath(xpath)}

    # do head check for enclosure url
    # return (length, type)
    async def __head_check(self, url: str) -> Tuple[str, str]:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as resp:
                headers = resp.headers
                return headers.get("Content-Length"), headers.get("Content-Type")

    # conf is a dict map, e.g. {"url": "//enclosure/@url"}
    # possible keys: url, length, type
    async def parse_attr_enclosure(
        self, html: lxml.etree.ElementBase, enclosure: dict
    ) -> List[dict]:
        url_xpath = enclosure.get("url")
        head_check = True

        urls = html.xpath(url_xpath)
        lengths, types = [], []
        if hasattr(enclosure, "length") and hasattr(enclosure, "type"):
            lengths = html.xpath(enclosure.get("length"))
            types = html.xpath(enclosure.get("type"))
            head_check = False

        if head_check:
            logger.debug("parsing enclosure and needs head-check for resources")
            for url in urls:
                length, type = await self.__head_check(url)
                lengths.append(length)
                types.append(type)

        ret = []
        for url, length, type in zip(urls, lengths, types):
            ret.append(
                {
                    "url": url,
                    "length": length if length else "",
                    "type": type if type else "",
                }
            )

        return {"enclosure": ret}

    async def xpath_rss_items(
        self, html: lxml.etree.ElementBase, conf: RSSItem
    ) -> dict:
        item = {}
        required = ["title", "description", "url"]
        optional = ["pub_date", "guid"]

        for key in required:
            logger.debug(f"parsing required {key}")
            item.update(self.parse_attr_normal(html, key, getattr(conf, key), True))

        for key in optional:
            logger.debug(f"parsing optional {key}")
            item.update(self.parse_attr_normal(html, key, getattr(conf, key), False))

        if enclosure := getattr(conf, "enclosure", None):
            logger.debug(f"parsing enclosure")
            if enclosure.get("url"):
                item.update(await self.parse_attr_enclosure(html, enclosure))

        lengths = [len(val) for val in item.values()]

        # all lengths should be the same
        if not all([length == lengths[0] for length in lengths]):
            raise ValueError("Lengths of all keys should be the same")

        return item, lengths[0]

    async def parse_html(
        self, html: lxml.etree.ElementBase, conf: RSSItem
    ) -> List[RSSItem]:
        item, length = await self.xpath_rss_items(html, conf)

        def f(val: NODE_RESULT):
            ret = val
            if isinstance(ret, lxml.etree._Element):
                ret = ret.xpath("string()")
            return ret

        keys = list(item.keys())
        i = 0
        ret = []
        while i < length:
            m = {key: f(item[key][i]) for key in keys}
            ret.append(RSSItem.from_dict_to_dataclass(m))
            i += 1

        return ret

    def extract_first_text(
        self, html: lxml.etree.ElementBase, xpath: str
    ) -> Union[str, None]:
        nodes = html.xpath(xpath)
        if not nodes:
            return None
        ret = nodes[0]
        if isinstance(ret, lxml.etree._Element):
            ret = ret.xpath("string()")
        return ret

    async def generate(self, conf: SiteConf) -> str:
        html = await self.scrape_html(conf)
        tree = lxml.etree.HTML(html)

        # Parsing
        items = await self.parse_html(tree, conf.rss)
        channel = RSSChannel(
            title=self.extract_first_text(tree, "//head/title/text()") or conf.name,
            language=self.extract_first_text(tree, "/html/@lang") or None,
            url=conf.url,
            items=items,
        )
        return self.template.render(channel=channel)


rss = RSS()
