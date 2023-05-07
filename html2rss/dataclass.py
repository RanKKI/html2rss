from dataclasses import dataclass, fields
from typing import Union


def from_dict_to_dataclass(clz, data):
    fieldSet = {f.name for f in fields(clz) if f.init}
    filteredArgDict = {k: v for k, v in data.items() if k in fieldSet}
    return clz(**filteredArgDict)


@dataclass
class RSSConf:
    title: str
    description: Union[str, None]
    url: str

    @staticmethod
    def from_dict_to_dataclass(data):
        return from_dict_to_dataclass(RSSConf, data)


@dataclass
class SiteConf:
    url: str
    rss: RSSConf
    refresh: int = 300
    alias: Union[str, None] = None

    @staticmethod
    def from_dict_to_dataclass(data):
        ret = from_dict_to_dataclass(SiteConf, data)
        ret.rss = RSSConf.from_dict_to_dataclass(data["rss"])
        return ret

    @property
    def name(self):
        return self.alias or self.url


@dataclass
class RSSItem:
    title: str
    description: str
    url: str
    pub_date: str | None = None
