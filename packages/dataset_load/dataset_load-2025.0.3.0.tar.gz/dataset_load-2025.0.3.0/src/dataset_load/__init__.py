from importlib.metadata import version, PackageNotFoundError

# Re-export public API from the internal implementation package
from my_krml_25763727.data.sets import (
    fetch_api_data,
    merge_datasets,
    convert_to_csv,
    union_datasets,
)

__all__ = [
    "fetch_api_data",
    "merge_datasets",
    "convert_to_csv",
    "union_datasets",
    "__version__",
]

try:
    __version__ = version("dataset-load")
except PackageNotFoundError:
    __version__ = "0.0.0"


