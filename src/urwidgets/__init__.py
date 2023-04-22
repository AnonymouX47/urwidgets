"""
urWIDgets

A collection of widgets for urwid (https://urwid.org)

Copyright (c) 2023, Toluwaleke Ogundipe <anonymoux47@gmail.com>
"""

__all__ = ()
__author__ = "Toluwaleke Ogundipe"

version_info = (0, 1, 0, "dev")

# Follows https://semver.org/spec/v2.0.0.html
__version__ = ".".join(map(str, version_info[:3]))
if version_info[3:]:
    __version__ += "-" + ".".join(map(str, version_info[3:]))
