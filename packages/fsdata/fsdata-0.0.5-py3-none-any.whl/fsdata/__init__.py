"""
fsdata

Collections of data files in a directory or cloud location.
Locations are represendted as local path or valid cloud urls.
Data is saved as parquet files with the extension `.parquet`

Configuration file `fsdata.ini`

Sample configuration:

[samples]
path = $HOME/samples

"""

from functools import lru_cache

from .config import read_config
from .collection import Collection


@lru_cache
def get(name: str) -> Collection:
    """get collection by name"""
    return Collection.from_config(name)


def items():
    """list available collection names from config"""
    config = read_config()
    return config.sections()


