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

BACKENDS = []

_last_backend_import_error = None
try:
    import cairo
    import pango
    import pangocairo
except ImportError, e:
    _last_backend_import_error = e
else:
    BACKENDS.append("pangocairo")

try:
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
except ImportError, e:
    _last_backend_import_error = e
else:
    BACKENDS.append("pillow")

if not BACKENDS:
    raise _last_backend_import_error

default_backend = BACKENDS[0]

from ._error import OutputFormatError

__all__ = [
    "BACKENDS",
    "OUTPUT_FORMATS",
    "default_backend",
    "render",
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

def _pillow_render_png(figure, output_file, scale_x=8, scale_y=8):
    image_width = int(math.ceil(figure.width * scale_x))
    image_height = int(math.ceil(figure.height * scale_y))
    image = Image.new("RGBA", (image_width, image_height), (255, 255, 255, 0))
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
        draw.line((scale_x * x0, scale_y * y0, scale_x * x1, scale_y * y1), fill=(0, 0, 0, 255))

    for text in figure.texts:
        pos, string = text
        x, y = pos
        draw.text((scale_x * x, scale_y * y), string, font=font, fill=(0, 0, 0, 255))

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
    "pangocairo": {
        "png": _pangocairo_render_png,
        "svg": _pangocairo_render_svg,
    },
    "pillow": {
        "png": _pillow_render_png,
    }
}

OUTPUT_FORMATS = _RENDER_FUNCTIONS[default_backend].keys()

def _render(text, output_file, **kwargs):
    backend = kwargs.pop("backend", default_backend)

    try:
        render_functions = _RENDER_FUNCTIONS[backend]
    except KeyError:
        raise BackendError(backend)

    output_format = kwargs.pop("output_format", None)
    try:
        render_function = render_functions[output_format]
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
