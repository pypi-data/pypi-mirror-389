# src/my_krml_25763727/__init__.py
try:
    from importlib.metadata import version
    __version__ = version("dataset_merge")
except Exception:
    __version__ = "0.2.0"  # fallback during development

# import main functions for easy access
from .data.sets import merge_datasets, convert_to_csv, union_datasets

# define what gets imported with `from my_krml_25763727 import *`
__all__ = [
    "merge_datasets",
    "convert_to_csv",
    "union_datasets",
]
