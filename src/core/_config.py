"""
Config informations should always be retrieved from bot.config, this ensure that the config has been overwritten if
needed. Otherwise, if the config is used before the invocation of main() from main.py, config informations are not set
correctly.
A warning should be raised if we try to access config while it is not defined.
"""

from __future__ import annotations

import logging
import tomllib
from typing import Any, ClassVar, Self

logger = logging.getLogger(__name__)


class Config:
    SUPPORT_GUILD_ID: int = 332209340780118016
    BOT_ID: int = 500023552905314304  # this should be retrieved from bot.client.id, but anyway.
    OWNERS_IDS: list[int] = [341550709193441280, 329710312880340992]
    POSTGRES_USER: str = "postgres"
    POSTGRES_DB: str = "mybot"
    POSTGRES_PASSWORD: str | None = None
    EXPORT_MODE: bool = False
    TOPGG_TOKEN: str | None = None
    TOPGG_AUTH: str | None = None
    MS_TRANSLATE_KEY: str | None = None
    MS_TRANSLATE_REGION: str | None = None
    # comma separated list of services to use for translation. Corresponding files should be in cogs/translate/adapters.
    TRANSLATOR_SERVICES: str = "libretranslate"
    LOG_WEBHOOK_URL: str | None = None

    _instance: ClassVar[Self] | None = None
    _defined: ClassVar[bool] = False

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def define(cls):
        Config._defined = True

    def __init__(self, **kwargs: Any):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattribute__(self, name: str) -> Any:
        if name in ("__init__"):
            return super().__getattribute__(name)

        if Config._defined is False:
            logger.warning("Config accessed before being defined.", extra={"ignore_discord": True})

        try:
            return super().__getattribute__(name)
        except AttributeError:
            return None


def define_config(config_path: str | None = None, **kwargs: Any):
    if config_path:
        with open(config_path, mode="r", encoding="utf-8") as f:
            kwargs |= tomllib.load(f.buffer)

    Config(**kwargs)  # it is a singleton, so it will directly affect the instance.
    Config.define()


config = Config()
