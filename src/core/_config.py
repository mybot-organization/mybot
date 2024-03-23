"""
Config informations should always be retrieved from bot.config, this ensure that the config has been overwritten if
needed. Otherwise, if the config is used before the invocation of main() from main.py, config informations are not set
correctly.
A warning should be raised if we try to access config while it is not defined.
"""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import Any, ClassVar, Self

logger = logging.getLogger(__name__)


class Config:
    """Get any configuration information from here.

    This class is a singleton. You can get the configurations info from `bot.config`, or import the instance `config`
    from this module, or even use `Config()` as they are all the same instance.

    To ensure the config keys are accessed after being defined, the `define_config` function should be called when the
    config is ready to be used. This will set the `_defined` attribute to True, and any access to the config before this
    will raise a warning.

    The values assigned bellow are the default values, and can be overwritten by the `define_config` function.
    Everything present in the `config.toml` file will be added to the config instance (even if it is not defined here).
    But please make sure to define the config keys here, for autocompletion.

    Refer to [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) for more information.
    """

    support_guild_id: int = 332209340780118016
    owners_ids: ClassVar[list[int]] = [341550709193441280, 329710312880340992]
    translator_services: ClassVar[list[str]] = ["libretranslate"]
    extensions: ClassVar[list[str]] = []
    bot_id: int | None = None
    export_mode: bool = False
    # POSTGRES_USER: str = "postgres"
    # POSTGRES_DB: str = "mybot"
    # POSTGRES_PASSWORD: str | None = None
    # TOPGG_TOKEN: str | None = None
    # TOPGG_AUTH: str | None = None
    # MS_TRANSLATE_KEY: str | None = None
    # MS_TRANSLATE_REGION: str | None = None
    # comma separated list of services to use for translation. Corresponding files should be in cogs/translate/adapters.
    # LOG_WEBHOOK_URL: str | None = None

    _instance: ClassVar[Self] | None = None
    _defined: ClassVar[bool] = False

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def set_as_defined(cls):
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


def define_config(config_path: Path | str | None = None, **kwargs: Any):
    if config_path:
        with open(config_path, encoding="utf-8") as f:
            kwargs |= tomllib.load(f.buffer)

    Config(**kwargs)  # it is a singleton, so it will directly affect the instance.
    Config.set_as_defined()


config = Config()
