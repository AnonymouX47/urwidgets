"""
urWIDgets

A collection of widgets for urwid (https://urwid.org)

Copyright (c) 2023, Toluwaleke Ogundipe <anonymoux47@gmail.com>
"""

__all__ = ("Hyperlink", "TextEmbed")
__author__ = "Toluwaleke Ogundipe"

from .hyperlink import Hyperlink
from .text_embed import TextEmbed

version_info = (1, 0, 0, "dev")

# Follows https://semver.org/spec/v2.0.0.html
__version__ = ".".join(map(str, version_info[:3]))
if version_info[3:]:
    __version__ += "-" + ".".join(map(str, version_info[3:]))
