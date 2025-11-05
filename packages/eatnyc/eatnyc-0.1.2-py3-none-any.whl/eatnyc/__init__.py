from importlib.metadata import version, PackageNotFoundError
from .core import load_data, filter_restaurants, top_n, sample_dish, format_card

__all__ = ["load_data", "filter_restaurants", "top_n", "sample_dish", "format_card"]

# Try to get the installed version; fallback for dev/local runs
try:
    __version__ = version("eatnyc")
except PackageNotFoundError:
    __version__ = "0.0.0"
