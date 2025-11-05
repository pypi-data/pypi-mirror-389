"""fsspec data mapper"""

import os
import re

from .config import cache_root_dir


def check_path(path):
    """check and normalize path"""
    if re.match(r"\w{2,}:", path):
        prefix, _, path = path.partition(":")
    else:
        prefix = "local"

    if path.startswith("~"):
        path = os.path.expanduser(path)

    if not path.startswith(("/", "\\")):
        raise ValueError(f"Path {path!r} must be absolute!")
    
    return prefix + ":" + path


def cache_dir_path(name_or_path: str) -> str:
    name_or_path = os.path.expanduser(name_or_path)
    if os.path.isabs(name_or_path):
        return name_or_path
    else:
        return os.path.join(cache_root_dir(), name_or_path)

