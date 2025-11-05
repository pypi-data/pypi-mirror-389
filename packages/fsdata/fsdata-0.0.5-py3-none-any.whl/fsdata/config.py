"""fsspec data mapper"""

import os
from pathlib import Path

from functools import lru_cache
from configparser import ConfigParser, Interpolation


class ExpandVars(Interpolation):
    """Interpolation which expands environment variables in values"""

    def before_read(self, parser, section, option, value):
        return os.path.expandvars(value)


def xdg_config_dirs():
    """list of config dirs from environment or defaults"""
    config_home = os.getenv("XDG_CONFIG_HOME", "~/.config")
    config_dirs = os.getenv("XDG_CONFIG_DIRS", "/etc/xdg").split(os.pathsep)

    config_dirs = [config_home, *config_dirs]
    config_dirs = [os.path.expanduser(p) for p in config_dirs if len(p)]

    return config_dirs


def cache_root_dir():
    """get cache folder from environment or default"""
    cache_home = os.getenv("XDG_CACHE_HOME", "~/.cache")
    cache_home = os.path.expanduser(cache_home)
    return os.path.join(cache_home, "fsdata")


@lru_cache
def read_config():
    """read configuration files"""
    config = ConfigParser(interpolation=ExpandVars())

    for folder in xdg_config_dirs():
        file = os.path.join(folder, "fsdata.ini")      
        if os.path.exists(file):
            config.read(file)

    return config

