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

from __future__ import absolute_import

__all__ = [
    "Error",
    "OutputFormatError",
]

class Error(Exception):
    pass

class OutputFormatError(Error):

    def __init__(self, output_format):
        Error.__init__(self, output_format)
        self.output_format = output_format

    def __str__(self):
        if self.output_format is None:
            return "undefined output format"
        return "invalid output format '%s'" % self.output_format
