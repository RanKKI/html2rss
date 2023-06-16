import json
import logging
import os
from pathlib import Path
from typing import List, Union

from html2rss.dataclass import SiteConf

CONFIG_FOLDER = Path(os.environ.get("HTML2RSS_CONFIG_FOLDER", default="./config"))
logger = logging.getLogger(__name__)


class ConfigManager(object):
    def __init__(self) -> None:
        self.configs: List[SiteConf] = []

    def load_config(self) -> None:
        logger.info(f"Loading config from {CONFIG_FOLDER.absolute()}")
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
