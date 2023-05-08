import time
from hashlib import md5
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union
import logging
import aiohttp
import lxml.etree
import lxml.html
from jinja2 import Environment, FileSystemLoader, select_autoescape

from html2rss.dataclass import RSSItem, SiteConf, RSSChannel

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

    def parse_html(self, html: lxml.etree.ElementBase, conf: RSSItem) -> List[RSSItem]:
        ret = []
        item = {
            "title": html.xpath(conf.title),
            "description": html.xpath(conf.description),
            "url": html.xpath(conf.url),
        }

        if conf.pub_date:
            item["pub_date"] = html.xpath(conf.pub_date)

        if conf.guid:
            item["guid"] = html.xpath(conf.guid)

        lengths = [len(val) for val in item.values()]

        # all lengths should be the same
        if not all([length == lengths[0] for length in lengths]):
            logger.error("Lengths of elements are not the same")
            return []

        def f(val: NODE_RESULT):
            ret = val
            if isinstance(ret, lxml.etree._Element):
                ret = ret.xpath("string()")
            return ret

        keys = list(item.keys())
        i = 0
        while i < lengths[0]:
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
        channel = RSSChannel(
            title=self.extract_first_text(tree, "//head/title/text()") or conf.name,
            language=self.extract_first_text(tree, "/html/@lang") or None,
            url=conf.url,
            items=self.parse_html(tree, conf.rss),
        )
        return self.template.render(channel=channel)


rss = RSS()
