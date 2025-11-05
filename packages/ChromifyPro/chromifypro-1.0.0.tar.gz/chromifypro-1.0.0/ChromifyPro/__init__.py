# Package metadata
NAME = "Chromify"
AUTHOR = "Plaraje"
LICENSE = "MIT"
VERSION = "1.1.9"

# Import public API directly
from .Color import Color
from .Converter import Converter
from .utils import load_from_zip, load_from_template, TEMPLATE_COLORS

# Public API
__all__ = [
    "NAME",
    "AUTHOR",
    "LICENSE",
    "VERSION",
    "Chromify",
    "Color",
    "Converter",
    "load_from_zip",
    "load_from_template",
    "TEMPLATE_COLORS",
]
