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
from __future__ import print_function

import codecs
import math
import optparse
import os
import os.path
import sys

import docutils.nodes
from docutils.parsers import rst

import cairo
import pango
import pangocairo

VERSION = "0.2"
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

def _draw_line(context, line):
    x0, y0, x1, y1 = line
    context.move_to(x0, y0)
    context.line_to(x1, y1)
    context.stroke()

def _draw_text(context, text, font_description):
    pos, string = text
    layout = context.create_layout()
    layout.set_font_description(font_description)
    layout.set_text(string)
    x, y = pos
    context.move_to(x, y)
    context.show_layout(layout)

def _render_surface(figure, surface, scale_x, scale_y):
    context = pangocairo.CairoContext(cairo.Context(surface))
    context.set_line_width(0.25)
    context.set_line_cap(cairo.LINE_CAP_SQUARE)
    context.scale(scale_x, scale_y)
    font_description = pango.FontDescription("DejaVuSansMono 1")

    for line in figure.lines:
        _draw_line(context, line)

    for text in figure.texts:
        _draw_text(context, text, font_description)

def _render_svg(figure, output_file, scale_x=8, scale_y=8):
    surface = cairo.SVGSurface(output_file,
                               int(math.ceil(figure.width * scale_x)),
                               int(math.ceil(figure.height * scale_y)))
    _render_surface(figure, surface, scale_x, scale_y)

    surface.finish()

def _render_png(figure, output_file, scale_x=8, scale_y=8):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                 int(math.ceil(figure.width * scale_x)),
                                 int(math.ceil(figure.height * scale_y)))
    _render_surface(figure, surface, scale_x, scale_y)

    surface.write_to_png(output_file)

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
        self.__width = width
        self.__height = height

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    def get(self, x, y):
        if 0 <= x < self.__width and 0 <= y < self.__height:
            i = y * self.__width + x
            return self.__text[i]
        return ""

    def __iter__(self):
        for y in range(self.__height):
            for x in range(self.__width):
                char = self.get(x, y)
                yield x, y, char

class _Figure:

    def __init__(self, text):

        texts = []
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
                texts.append(((x, y), char))

        self.__width = 2 * textrect.width
        self.__height = 2 * textrect.height
        self.__lines = lines
        self.__texts = texts

    @property
    def width(self):
        return self.__width

    @property
    def height(self):
        return self.__height

    @property
    def lines(self):
        return self.__lines

    @property
    def texts(self):
        return self.__texts

_RENDER_FUNCTIONS = {
    "png": _render_png,
    "svg": _render_svg,
    }
OUTPUT_FORMATS = _RENDER_FUNCTIONS.keys()

def _parse_args(argv):
    render_options = {}
    parser = optparse.OptionParser(version=_LONG_VERSION,
                                   description=_DESCRIPTION)


    format_choices_str = ", ".join([repr(s) for s in OUTPUT_FORMATS])

    parser.add_option("-i", "--input-file", metavar="FILE",
                      help="input file, defaults to standard input")
    parser.add_option("-o", "--output-file", metavar="FILE",
                      help="output file, defaults to standard output")
    parser.add_option("-t", "--output-format", metavar="FORMAT", type="choice",
                      choices=OUTPUT_FORMATS,
                      help="output format (choose from %s)" % format_choices_str)
    parser.add_option("-s", "--scale", metavar="SCALE", type=float, default=8.0,
                      help="scale output geometry by SCALE factor, defaults to %default")

    options, args = parser.parse_args(argv)

    if len(args) > 1:
        parser.error("encountered extra arguments")

    if options.input_file is None:
        options.input_file = sys.stdin
    else:
        options.input_file = codecs.open(options.input_file,
                                         encoding=sys.stdin.encoding)

    if options.output_file is None:
        options.output_file = sys.stdout

    if options.output_format is not None:
        render_options["output_format"] = options.output_format

    if options.scale is not None:
        render_options["scale_x"] = options.scale
        render_options["scale_y"] = options.scale

    return options, render_options

def _render(text, output_file, **kwargs):
    output_format = kwargs.pop("output_format", None)
    try:
        render_function = _RENDER_FUNCTIONS[output_format]
    except KeyError:
        raise OutputFormatError(output_format)
    figure = _Figure(text)
    render_function(figure, output_file, **kwargs)

def render(text, output_file, **kwargs):
    if isinstance(output_file, (str, unicode)):
        kwargs.setdefault("output_format",
                          os.path.splitext(output_file)[1].lstrip(os.path.extsep))
        with open(output_file, "wb") as f:
            _render(text, f, **kwargs)

    _render(text, output_file, **kwargs)

def _output_format(argument):
    return rst.directives.choice(argument, OUTPUT_FORMATS)

class ASCIIBoxDirective(rst.Directive):

    required_arguments = 1
    optional_arguments = 2
    has_content = True
    option_spec = {
        'scale': rst.directives.nonnegative_int,
        'output_format': _output_format,
        }

    def run(self):
        self.assert_has_content()

        render_options = {}
        for key in ASCIIBoxDirective.option_spec:
            try:
                render_options[key] = self.options[key]
            except KeyError:
                continue

        filename = self.arguments[0]
        render("\n".join(self.content), filename, **render_options)
        uri = rst.directives.uri(filename)
        return [docutils.nodes.image(uri=uri)]

def register_directive(name='asciibox'):
    rst.directives.register_directive(name, ASCIIBoxDirective)

def _main():
    options, render_options = _parse_args(sys.argv)
    text = unicode(options.input_file.read())
    render(text, options.output_file, **render_options)

if __name__ == "__main__":
    try:
        _main()
    except Error, e:
        print("error:", e, file=sys.stderr)
        sys.exit(1)
