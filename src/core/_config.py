"""
Config informations should always be retrived from bot.config, this ensure that the config has been overwritten if
needed. Otherwise, if the config is used before the invocation of main() from main.py, config informations are not set
correcty.
A warning should be raised if we try to access config while it is not defined.
"""

import logging
import tomllib
from dataclasses import dataclass
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


@dataclass
class Config:
    SUPPORT_GUILD_ID: int = 332209340780118016
    BOT_ID: int = 500023552905314304  # this should be retrieved from bot.client.id, but anyway.
    POSTGRES_USER: str = "postgres"
    POSTGRES_DB: str = "mybot"
    POSTGRES_PASSWORD: str | None = None
    EXPORT_MODE: bool = False

    _defined: ClassVar[bool] = False

    def define(self):
        Config._defined = True

    def __getattribute__(self, name: str) -> Any:
        if name in super().__getattribute__("__dataclass_fields__").keys():
            if Config._defined == False:
                logger.warning("Config accessed but not defined.")
        return super().__getattribute__(name)


def define_config(config_path: str | None = None, **kwargs: Any):
    global config

    if config_path:
        with open(config_path) as f:
            kwargs |= tomllib.load(f.buffer)

    config.__init__(**kwargs)
    config.define()


config = Config()
