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

import math
import os.path

import cairo
import pango
import pangocairo

from ._error import OutputFormatError

__all__ = [
    "render",
    "OUTPUT_FORMATS",
]

def _pangocairo_draw_line(context, line):
    x0, y0, x1, y1 = line
    context.move_to(x0, y0)
    context.line_to(x1, y1)
    context.stroke()

def _pangocairo_draw_text(context, text, font_description):
    pos, string = text
    layout = context.create_layout()
    layout.set_font_description(font_description)
    layout.set_text(string)
    x, y = pos
    context.move_to(x, y)
    context.show_layout(layout)

def _pangocairo_render_surface(figure, surface, scale_x, scale_y):
    context = pangocairo.CairoContext(cairo.Context(surface))
    context.set_line_width(0.25)
    context.set_line_cap(cairo.LINE_CAP_SQUARE)
    context.scale(scale_x, scale_y)
    font_description = pango.FontDescription("DejaVuSansMono 1")

    for line in figure.lines:
        _pangocairo_draw_line(context, line)

    for text in figure.texts:
        _pangocairo_draw_text(context, text, font_description)

def _pangocairo_render_svg(figure, output_file, scale_x=8, scale_y=8):
    surface = cairo.SVGSurface(output_file,
                               int(math.ceil(figure.width * scale_x)),
                               int(math.ceil(figure.height * scale_y)))
    _render_surface(figure, surface, scale_x, scale_y)

    surface.finish()

def _pangocairo_render_png(figure, output_file, scale_x=8, scale_y=8):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                 int(math.ceil(figure.width * scale_x)),
                                 int(math.ceil(figure.height * scale_y)))
    _pangocairo_render_surface(figure, surface, scale_x, scale_y)

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
    "png": _pangocairo_render_png,
    "svg": _pangocairo_render_svg,
}
OUTPUT_FORMATS = _RENDER_FUNCTIONS.keys()

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
