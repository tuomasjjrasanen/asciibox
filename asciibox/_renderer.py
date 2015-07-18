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

from PIL import Image
from PIL import ImageColor
from PIL import ImageDraw
from PIL import ImageFont

from ._error import OutputFormatError

__all__ = [
    "OUTPUT_FORMATS",
    "render",
]

def _pillow_render_png(figure, output_file, scale_x=8, scale_y=8,
                       bg_rgb="#ffffff", fg_rgb="#000000",
                       bg_opacity=0.0, fg_opacity=1.0):
    rescale_factor = 8
    scale_x *= rescale_factor
    scale_y *= rescale_factor

    bg_opacity = min(1.0, max(0.0, bg_opacity))
    fg_opacity = min(1.0, max(0.0, fg_opacity))

    bg_alpha = int(round(bg_opacity * 255))
    fg_alpha = int(round(fg_opacity * 255))

    bg_rgba = ImageColor.getrgb(bg_rgb) + (bg_alpha,)
    fg_rgba = ImageColor.getrgb(fg_rgb) + (fg_alpha,)

    image_size = (int(math.ceil(figure.width * scale_x)),
                  int(math.ceil(figure.height * scale_y)))

    image = Image.new("RGBA", image_size, bg_rgba)
    draw = ImageDraw.Draw(image)

    font_filepath = os.path.join(os.path.dirname(__file__), "data",
                                 "DejaVuSansMono.ttf")
    font_size = int(math.ceil(2 * min(scale_x, scale_y)))
    try:
        font = ImageFont.truetype(font_filepath, font_size)
    except IOError:
        font = ImageFont.load_default()

    for line in figure.lines:
        x0, y0, x1, y1 = line
        draw.line((scale_x * x0, scale_y * y0, scale_x * x1, scale_y * y1),
                  fill=fg_rgba, width=rescale_factor)

    for text in figure.texts:
        pos, string = text
        x, y = pos
        draw.text((scale_x * x, scale_y * y), string, font=font, fill=fg_rgba)

    image_size = [v // rescale_factor for v in image_size]
    image = image.resize(image_size, Image.LANCZOS)

    image.save(output_file, "PNG")

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
            elif char == '<' and right_char == '-' and left_char == '+':
                lines.append((x - 1, y + 1, x + 1, y + 0))
                lines.append((x - 1, y + 1, x + 2, y + 1))
                lines.append((x - 1, y + 1, x + 1, y + 2))
            elif char == '<' and right_char == '-':
                lines.append((x + 0, y + 1, x + 2, y + 0))
                lines.append((x + 0, y + 1, x + 2, y + 1))
                lines.append((x + 0, y + 1, x + 2, y + 2))
            elif char == '>' and left_char == '-' and right_char == '+':
                lines.append((x + 1, y + 0, x + 3, y + 1))
                lines.append((x + 0, y + 1, x + 3, y + 1))
                lines.append((x + 1, y + 2, x + 3, y + 1))
            elif char == '>' and left_char == '-':
                lines.append((x + 0, y + 0, x + 2, y + 1))
                lines.append((x + 0, y + 1, x + 2, y + 1))
                lines.append((x + 0, y + 2, x + 2, y + 1))
            elif char == '^' and down_char == '|' and up_char == '+':
                lines.append((x + 0, y + 1, x + 1, y - 1))
                lines.append((x + 1, y + 2, x + 1, y - 1))
                lines.append((x + 2, y + 1, x + 1, y - 1))
            elif char == '^' and down_char == '|':
                lines.append((x + 0, y + 2, x + 1, y + 0))
                lines.append((x + 1, y + 2, x + 1, y + 0))
                lines.append((x + 2, y + 2, x + 1, y + 0))
            elif char == 'v' and up_char == '|' and down_char == '+':
                lines.append((x + 0, y + 1, x + 1, y + 3))
                lines.append((x + 1, y + 0, x + 1, y + 3))
                lines.append((x + 2, y + 1, x + 1, y + 3))
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
    "png": _pillow_render_png,
}
OUTPUT_FORMATS = _RENDER_FUNCTIONS.keys()

def render(text, output_file, **kwargs):
    if isinstance(output_file, (str, unicode)):
        output_file = open(output_file, "wb")

    output_ext = os.path.splitext(output_file.name.lower())[1].lstrip(os.path.extsep)

    ## The filename extension is the best guess if the user has not provided the
    ## output format explicitly.
    output_format = kwargs.pop("output_format", output_ext)
    try:
        render_function = _RENDER_FUNCTIONS[output_format]
    except KeyError:
        raise OutputFormatError(output_format)
    figure = _Figure(text)
    render_function(figure, output_file, **kwargs)
