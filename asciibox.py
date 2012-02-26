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

from __future__ import division
from __future__ import absolute_import

import codecs
import optparse
import os.path
import sys
import Image
import ImageDraw
import ImageFont

VERSION = "0.1"
_DESCRIPTION = "Render ASCII boxes and arrows as images."
_AUTHOR = "Tuomas Jorma Juhani Räsänen"
_EMAIL = "tuomasjjrasanen@tjjr.fi"
_LONG_VERSION = """asciibox %s
Copyright (C) 2011 %s
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by %s.""" % (VERSION, _AUTHOR, _AUTHOR)

__doc__ = """%s

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
""" % _DESCRIPTION

class RasterCanvas:

    def __init__(self, size,
                 bgcolor="#ffffff",
                 fgcolor="#000000",
                 scale=8,
                 ttf_font_filepath="/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf"):
        self.__fgcolor = fgcolor
        self.__scale = scale
        self.__img = Image.new("RGB", [scale * v for v in size], bgcolor)
        self.__imgdraw = ImageDraw.Draw(self.__img)
        try:
            self.__font = ImageFont.truetype(ttf_font_filepath, scale * 2)
        except IOError:
            self.__font = ImageFont.load_default()

    def write(self, outfile, outformat):
        """Write image to an open file."""
        self.__img.save(outfile, outformat)

    def draw_line(self, line):
        """Draw line to the image.

        line - (x0, y0, x1, y1)
        """
        line = [self.__scale * v for v in line]
        self.__imgdraw.line(line, fill=self.__fgcolor)

    def draw_text(self, pos, text):
        """Draw character to the image.

        pos  - (x, y)
        """
        pos = [self.__scale * v for v in pos]
        self.__imgdraw.text(pos, text, font=self.__font, fill=self.__fgcolor)

class _TextRect:

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

        chars = []
        lines = []

        textrect = _TextRect(text)

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
            elif char == ' ':
                pass
            else:
                chars.append(((x, y), char))

        self.__size = [2 * v for v in textrect.size]
        self.__lines = lines
        self.__chars = chars

    @property
    def size(self):
        return self.__size

    def draw(self, canvas):
        for line in self.__lines:
            canvas.draw_line(line)
        for pos, char in self.__chars:
            canvas.draw_text(pos, char)

def _parse_args(argv):
    parser = optparse.OptionParser(version=_LONG_VERSION,
                                   description=_DESCRIPTION)

    format_choices = ["png"]
    format_choices_str = ", ".join([repr(s) for s in format_choices])

    parser.add_option("-i", metavar="FILE", dest="infile", default=None,
                      help="input text file, defaults to standard input")
    parser.add_option("-o", metavar="FILE", dest="outfile", default=None,
                      help="output image file, defaults to standard output")
    parser.add_option("-t", metavar="FORMAT", dest="format", type="choice",
                      choices=format_choices, default=None,
                      help="output image format (choose from %s)" % format_choices_str)

    options, args = parser.parse_args(argv)

    if len(args) > 1:
        parser.error("encountered extra arguments")

    if options.infile is None:
        options.infile = sys.stdin
    else:
        options.infile = codecs.open(options.infile,
                                     encoding=sys.stdin.encoding)

    if options.outfile is None:
        if options.format is None:
            options.format = format_choices[0]
        options.outfile = sys.stdout
    else:
        if options.format is None:
            ext = os.path.splitext(options.outfile)[1]
            options.format = ext[len(os.path.extsep):]
        options.outfile = open(options.outfile, "wb")

    if options.format not in format_choices:
        parser.error("invalid output image format: %r (choose from %s)"
                     % (options.format, format_choices_str))

    return options

def _main():
    options = _parse_args(sys.argv)
    text = unicode(options.infile.read())
    figure = Figure(text)
    canvas = RasterCanvas(figure.size)
    figure.draw(canvas)
    canvas.write(options.outfile, options.format)

if __name__ == "__main__":
    _main()
