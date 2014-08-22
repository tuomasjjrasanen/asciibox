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
>>> asciibox.render(text, "/tmp/asciibox.png")

%s
""" % (_DESCRIPTION, _LONG_VERSION)

def _cairo_draw_line(cairo_context, line):
    x0, y0, x1, y1 = line
    cairo_context.move_to(x0, y0)
    cairo_context.line_to(x1, y1)
    cairo_context.stroke()

def _cairo_draw_text(cairo_context, text, font_description):
    pos, string = text
    layout = cairo_context.create_layout()
    layout.set_font_description(font_description)
    layout.set_text(string)
    x, y = pos
    cairo_context.move_to(x, y)
    cairo_context.show_layout(layout)

def _render_surface(ascii_figure, surface, scale):
    scale_x, scale_y = scale

    cairo_context = pangocairo.CairoContext(cairo.Context(surface))
    cairo_context.set_line_width(0.25)
    cairo_context.scale(scale_x, scale_y)
    font_description = pango.FontDescription("DejaVuSansMono 1")

    for line in ascii_figure.lines:
        _cairo_draw_line(cairo_context, line)

    for text in ascii_figure.texts:
        _cairo_draw_text(cairo_context, text, font_description)

def _render_svg(ascii_figure, image_file, scale=(8, 8)):
    width, height = ascii_figure.size
    scale_x, scale_y = scale

    surface = cairo.SVGSurface(image_file, width * scale_x, height * scale_y)
    _render_surface(ascii_figure, surface, scale)

    surface.finish()

def _render_png(ascii_figure, image_file, scale=(8, 8)):
    width, height = ascii_figure.size
    scale_x, scale_y = scale

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width * scale_x, height * scale_y)
    _render_surface(ascii_figure, surface, scale)

    surface.write_to_png(image_file)

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

    @property
    def lines(self):
        return self.__lines

    @property
    def texts(self):
        return self.__chars

_RENDER_FUNCTIONS = {
    "png": _render_png,
    "svg": _render_svg,
    }
IMAGE_FORMATS = _RENDER_FUNCTIONS.keys()

def _parse_args(argv):
    parser = optparse.OptionParser(version=_LONG_VERSION,
                                   description=_DESCRIPTION)


    format_choices_str = ", ".join([repr(s) for s in IMAGE_FORMATS])

    parser.add_option("-i", metavar="FILE", dest="infile", default=None,
                      help="input text file, defaults to standard input")
    parser.add_option("-o", metavar="FILE", dest="outfile", default=None,
                      help="output image file, defaults to standard output")
    parser.add_option("-t", metavar="FORMAT", dest="format", type="choice",
                      choices=IMAGE_FORMATS, default=None,
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

def _render(ascii_text, image_file, **kwargs):
    image_format = kwargs.get("image_format", "png")
    render_function = _RENDER_FUNCTIONS[image_format]
    ascii_figure = _Figure(ascii_text)
    render_function(ascii_figure, image_file)

def render(ascii_text, image_file, **kwargs):
    if isinstance(image_file, (str, unicode)):
        kwargs.setdefault("image_format",
                          os.path.splitext(image_file)[1].lstrip(os.path.extsep))
        with open(image_file, "wb") as f:
            _render(ascii_text, f, **kwargs)

    _render(ascii_text, image_file, **kwargs)

def _main():
    options = _parse_args(sys.argv)
    text = unicode(options.infile.read())
    render(text, options.outfile, image_format=options.format)

if __name__ == "__main__":
    _main()
