import json
import logging
import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Union, List

# CONFIG_FOLDER = Path(os.environ.get("HTML2RSS_CONFIG_FOLDER", default="./config"))
CONFIG_FOLDER = Path(
    os.environ.get("HTML2RSS_CONFIG_FOLDER", default="./config_example")
)
logger = logging.getLogger(__name__)


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


class ConfigManager(object):
    def __init__(self) -> None:
        self.configs: List[SiteConf] = []

    def load_config(self) -> None:
        logger.info(f"Loading config... {CONFIG_FOLDER}")
        if not CONFIG_FOLDER.exists():
            logger.error("Config folder not found")
            return
        for conf_file in CONFIG_FOLDER.glob("**/*.json"):
            conf_json = json.loads(conf_file.read_text())

            if "alias" not in conf_json:
                conf_json["alias"] = conf_file.stem

            try:
                conf = SiteConf.from_dict_to_dataclass(conf_json)
            except Exception as e:
                logger.error(f"Error loading config {conf_file}: {e}")
                continue
            else:
                logger.info(f"Loaded config for {conf.name}")
                self.configs.append(conf)
        logger.info(f"Loaded {len(self.configs)} configs")

    def find_config(self, alias_or_url: str) -> Union[SiteConf, None]:
        for conf in self.configs:
            if conf.alias == alias_or_url or conf.url == alias_or_url:
                return conf
        return None


config = ConfigManager()
