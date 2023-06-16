from dataclasses import dataclass, fields, field
from typing import Union
from urllib.parse import urlparse


def from_dict_to_dataclass(clz, data):
    fieldSet = {f.name for f in fields(clz) if f.init}
    filteredArgDict = {k: v for k, v in data.items() if k in fieldSet}
    return clz(**filteredArgDict)


@dataclass
class RSSItemEnclosure:
    url: str
    length: Union[str, None] = None
    type: Union[str, None] = None


@dataclass
class RSSItem:
    title: str
    description: str
    url: str
    pub_date: Union[str, None] = None
    guid: Union[str, None] = None
    enclosure: Union[RSSItemEnclosure, None] = None

    @staticmethod
    def from_dict_to_dataclass(data):
        return from_dict_to_dataclass(RSSItem, data)


@dataclass
class SiteConf:
    url: str
    rss: RSSItem
    refresh: int = 300
    alias: Union[str, None] = None

    @staticmethod
    def from_dict_to_dataclass(data):
        ret = from_dict_to_dataclass(SiteConf, data)
        ret.rss = RSSItem.from_dict_to_dataclass(data["rss"])
        return ret

    @property
    def name(self):
        return self.alias or self.url


@dataclass
class RSSChannel:
    title: str
    url: str
    items: list[RSSItem] = field(default_factory=list)
    description: Union[str, None] = None
    language: Union[str, None] = None
