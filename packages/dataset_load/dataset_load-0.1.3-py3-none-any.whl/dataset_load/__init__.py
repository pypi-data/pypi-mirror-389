# read version from installed package
from importlib.metadata import version
__version__ = version("dataset_load")

from .fetch import fetch_api_data
