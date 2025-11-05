"""fsdata collection"""

import time
from unicodedata import name
import pandas as pd

from upath import UPath
from pathlib import Path

from functools import cached_property

from typing import Any, Optional

from .config import read_config   
from .utils import check_path, cache_dir_path


CACHE_CHECK=60*60*24  # 1 day


class Collection:
    """collection of data files"""

    cache_dir: Optional[Path] = None

    def __init__(self, path: str, *, cache_dir: Optional[str] = None):
        path = check_path(path)
        self.path = UPath(path)
        if cache_dir:
            cache_dir = cache_dir_path(cache_dir)
            self.cache_dir = Path(cache_dir)

    def __repr__(self):
        return f"Collection({self.path!r})"

    def __iter__(self):
        return iter(self.items())

    @classmethod
    def from_config(cls, name: str):
        config = read_config()
        
        try:
            section = config[name]
        except KeyError:
            raise AttributeError(f"Configuration for '{name}' not found!") from None

        path = section.get("path")
        cache_dir = section.get("cache_dir", name)

        return Collection(path, cache_dir=cache_dir)
  

    @cached_property
    def caching_enabled(self):
        if self.cache_dir is None:
            return False
        elif self.path.protocol in ("s3", "gs", "az"):
            return True
        else:
            return False


    def items(self):
        return [p.stem for p in self.path.glob("*.parquet")]

    def item_path(self, item: str):
        return self.path.joinpath(f"{item}.parquet")

    def cached_path(self, item: str):
        path = self.item_path(item)
        cached_path = self.cache_dir.joinpath(path.name)

        if cached_path.exists():
            mtime = cached_path.stat().st_mtime

            if mtime >= time.time() - CACHE_CHECK:
                return cached_path
            
            if path.stat().st_mtime <= mtime:
                cached_path.touch()
                return cached_path
        
        data = path.read_bytes()
        cached_path.parent.mkdir(parents=True, exist_ok=True)
        cached_path.write_bytes(data)

        return cached_path

    def load(self, item: str):
        if self.caching_enabled:
            path = self.cached_path(item)
        else:
            path = self.item_path(item)
        return pd.read_parquet(path.as_uri())

    def save(self, item: str, data):
        path = self.item_path(item)
        data.to_parquet(path.as_uri())

    def remove(self, item: str):
        path = self.item_path(item)
        if path.exists():
            path.unlink()
        else:
            raise FileNotFoundError(path.as_uri())

