"""
JSON Anatomy - A Python package for exploring and navigating JSON structures.

MIGRATION NOTICE
----------------
This package was previously named 'json-scout' with import name 'jsonscout'.
If you're upgrading from json-scout:
  1. Uninstall: pip uninstall json-scout
  2. Install: pip install json-anatomy
  3. Update imports: import jsonscout → import jsonanatomy

See https://github.com/deamonpog/json-anatomy/blob/main/MIGRATION.md

This package provides tools for introspecting, summarizing, and safely accessing
nested JSON data structures. It includes utilities for file handling, safe data
access patterns, and unified exploration interfaces.

Classes
-------
Explore : class
    Lightweight structural explorer for JSON objects.
Maybe : class
    Monadic-style wrapper for safe optional traversal.
Xplore : class
    Unified convenience facade combining all exploration tools.
SimpleXML : class
    Utility for converting XML to nested dictionary structures.

Functions
---------
get_json_file_paths : function
    Find JSON files in a directory using glob patterns.
read_json_file : function
    Read and parse JSON files with error handling.

Examples
--------
>>> import jsonanatomy as ja
>>> data = {'users': [{'name': 'Alice', 'age': 30}]}
>>> explorer = ja.Xplore(data)
>>> name = explorer['users'][0]['name'].value()
>>> print(name)  # 'Alice'
"""

from .file_reader import get_json_file_paths, read_json_file
from .Explore import Explore
from .Maybe import Maybe
from .Xplore import Xplore
from .SimpleXML import SimpleXML
from ._version import __version__, __author__, __email__

__all__ = [
    "get_json_file_paths",
    "read_json_file",
    "Explore",
    "Maybe",
    "Xplore",
    "SimpleXML",
]