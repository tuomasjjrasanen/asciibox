#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2011 Tuomas Jorma Juhani Räsänen

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
>>> figure = asciibox.Figure(text)
>>> canvas = asciibox.RasterCanvas(figure.size)
>>> figure.draw(canvas)
>>> canvas.write(open("/tmp/asciibox.png", "wb"), "png")
"""

from __future__ import division
from __future__ import absolute_import

import sys
import Image
import ImageDraw

VERSION = "0.1"

class RasterCanvas:

    def __init__(self, size,
                 bgcolor="#ffffff",
                 fgcolor="#000000",
                 scale=5):
        self.__fgcolor = fgcolor
        self.__scale = scale
        self.__img = Image.new("RGB", [scale * v for v in size], bgcolor)
        self.__imgdraw = ImageDraw.Draw(self.__img)

    def write(self, outfile, outformat="png"):
        """Write image to an open file."""
        self.__img.save(outfile, outformat)

    def draw_line(self, line):
        """Draw line to the image.

        line - (x0, y0, x1, y1)
        """
        line = [self.__scale * v for v in line]
        self.__imgdraw.line(line, fill=self.__fgcolor)

class TextRect:

    def __init__(self, text):
        lines = []
        width = 0
        height = 0
        for line in text.splitlines():
            line = line.rstrip()
            lines.append(line)
            width = max(len(line), width)
            height += 1
        self.__text = "".join([l.ljust(width) for l in lines])
        self.__size = (width, height)

    @property
    def size(self):
        return self.__size

    def get(self, x, y):
        width, height = self.__size
        if 0 <= x < width and 0 <= y < height:
            i = y * width + x
            return self.__text[i]
        return ""

    def __iter__(self):
        width, height = self.__size
        for y in range(height):
            for x in range(width):
                char = self.get(x, y)
                yield x, y, char

class Figure:

    def __init__(self, text):

        lines = []

        textrect = TextRect(text)

        for i, j, char in textrect:
            right_char = textrect.get(i + 1, j)
            left_char = textrect.get(i - 1, j)
            down_char = textrect.get(i, j + 1)
            up_char = textrect.get(i, j - 1)
            x, y = i * 2, j * 2 # Text indices to figure coordinates.
            if char == '-':
                lines.append((x + 0, y + 1, x + 2, y + 1))
            elif char == '|':
                lines.append((x + 1, y + 0, x + 1, y + 2))
            elif char == '<' and right_char == '-':
                lines.append((x + 0, y + 1, x + 2, y + 0))
                lines.append((x + 0, y + 1, x + 2, y + 1))
                lines.append((x + 0, y + 1, x + 2, y + 2))
            elif char == '>' and left_char == '-':
                lines.append((x + 0, y + 0, x + 2, y + 1))
                lines.append((x + 0, y + 1, x + 2, y + 1))
                lines.append((x + 0, y + 2, x + 2, y + 1))
            elif char == '^' and down_char == '|':
                lines.append((x + 0, y + 2, x + 1, y + 0))
                lines.append((x + 1, y + 2, x + 1, y + 0))
                lines.append((x + 2, y + 2, x + 1, y + 0))
            elif char == 'v' and up_char == '|':
                lines.append((x + 0, y + 0, x + 1, y + 2))
                lines.append((x + 1, y + 0, x + 1, y + 2))
                lines.append((x + 2, y + 0, x + 1, y + 2))
            elif char == '+':
                if right_char == '-':
                    lines.append((x + 1, y + 1, x + 2, y + 1))
                if left_char == '-':
                    lines.append((x + 1, y + 1, x + 0, y + 1))
                if down_char == '|':
                    lines.append((x + 1, y + 1, x + 1, y + 2))
                if up_char == '|':
                    lines.append((x + 1, y + 1, x + 1, y + 0))

        self.__size = [2 * v for v in textrect.size]
        self.__lines = lines

    @property
    def size(self):
        return self.__size

    def draw(self, canvas):
        for line in self.__lines:
            canvas.draw_line(line)

def _main():
    text = sys.stdin.read()
    figure = Figure(text)
    canvas = RasterCanvas(figure.size)
    figure.draw(canvas)
    canvas.write(sys.stdout)

if __name__ == "__main__":
    _main()
