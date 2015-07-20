# -*- coding: utf-8 -*-
# Copyright © 2015 Tuomas Räsänen

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Render ASCII boxes and arrows as images.

>>> text = '''
... +---------------------+
... |                     |
... +--------------+------+
... |              |      |
... |      +-------+      |
... |      |       |      |
... +------+--+----+------+
...    ^      |
...    |      |
...    |      |
...    +------+
... '''
>>> import asciibox
>>> asciibox.render(text, "/tmp/asciibox.png")
"""

from __future__ import absolute_import

from ._error import Error
from ._error import OutputFormatError
from ._renderer import OUTPUT_FORMATS
from ._renderer import render
from ._rst import register_rst_directive

VERSION = "0.4.0"

__all__ = [
    "Error",
    "OutputFormatError",
    "OUTPUT_FORMATS",
    "render",
    "register_rst_directive",
]
