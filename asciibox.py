#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2014 Tuomas Räsänen

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
import os
import os.path
import sys

import cairo
import pango
import pangocairo

VERSION = "0.1"
_DESCRIPTION = "Render ASCII boxes and arrows as images."
_AUTHOR = "Tuomas Räsänen"
_EMAIL = "tuomasjjrasanen@tjjr.fi"
_LONG_VERSION = """asciibox %s
Copyright (C) 2014 %s
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Written by %s <%s>.""" % (VERSION, _AUTHOR, _AUTHOR, _EMAIL)

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
>>> asciibox.render_to_filename(text, "/tmp/asciibox.png")

%s
""" % (_DESCRIPTION, _LONG_VERSION)

class _CairoCanvas(object):

    def __init__(self, surface, scale):
        scale_x, scale_y = scale
        self.__ctx = pangocairo.CairoContext(cairo.Context(surface))
        self.__ctx.set_line_width(0.25)
        self.__ctx.scale(scale_x, scale_y)
        self.__font_desc = pango.FontDescription("DejaVuSansMono 1")

    def draw_line(self, line):
        x0, y0, x1, y1 = line
        self.__ctx.move_to(x0, y0)
        self.__ctx.line_to(x1, y1)
        self.__ctx.stroke()

    def draw_text(self, pos, text):
        layout = self.__ctx.create_layout()
        layout.set_font_description(self.__font_desc)
        layout.set_text(text)
        x, y = pos
        self.__ctx.move_to(x, y)
        self.__ctx.show_layout(layout)

class _VectorCairoCanvas(_CairoCanvas):

    def __init__(self, size, scale=(8, 8)):
        scale_x, scale_y = scale
        width, height = size
        self.__imgfile = os.tmpfile()
        self.__surface = cairo.SVGSurface(self.__imgfile, width * scale_x, height * scale_y)
        _CairoCanvas.__init__(self, self.__surface, scale)

    def write(self, outfile):
        self.__surface.finish()
        self.__imgfile.seek(0)
        while True:
            data = self.__imgfile.read(1024)
            if not data:
                break
            outfile.write(data)

class _RasterCairoCanvas(_CairoCanvas):

    def __init__(self, size, scale=(8, 8)):
        scale_x, scale_y = scale
        width, height = size
        self.__surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * scale_x, height * scale_y)
        _CairoCanvas.__init__(self, self.__surface, scale)

    def write(self, outfile):
        self.__surface.write_to_png(outfile)

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

class _Figure:

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

IMAGE_FORMATS = {
    "png": _RasterCairoCanvas,
    "svg": _VectorCairoCanvas,
    }

def _parse_args(argv):
    parser = optparse.OptionParser(version=_LONG_VERSION,
                                   description=_DESCRIPTION)


    format_choices_str = ", ".join([repr(s) for s in IMAGE_FORMATS])

    parser.add_option("-i", metavar="FILE", dest="infile", default=None,
                      help="input text file, defaults to standard input")
    parser.add_option("-o", metavar="FILE", dest="outfile", default=None,
                      help="output image file, defaults to standard output")
    parser.add_option("-t", metavar="FORMAT", dest="format", type="choice",
                      choices=IMAGE_FORMATS.keys(), default=None,
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
            options.format = "png"
        options.outfile = sys.stdout
    else:
        if options.format is None:
            ext = os.path.splitext(options.outfile)[1]
            options.format = ext[len(os.path.extsep):]
        options.outfile = open(options.outfile, "wb")

    if options.format not in IMAGE_FORMATS:
        parser.error("invalid output image format: %r (choose from %s)"
                     % (options.format, format_choices_str))

    return options

def render_to_file(text, image_file, image_format):
    figure = _Figure(text)
    canvas_class = IMAGE_FORMATS[image_format]
    canvas = canvas_class(figure.size)
    figure.draw(canvas)
    canvas.write(image_file)

def render_to_filename(text, filename, image_format=None):
    with open(filename, "wb") as image_file:
        if image_format is None:
            image_format = os.path.splitext(filename)[1].lstrip(os.path.extsep)
            if not image_format:
                image_format = "png"

        render_to_file(text, image_file, image_format)

def _main():
    options = _parse_args(sys.argv)
    text = unicode(options.infile.read())
    render_to_file(text, options.outfile, options.format)

if __name__ == "__main__":
    _main()
