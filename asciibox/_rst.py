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

import errno
import os
import os.path

import docutils.nodes
import docutils.parsers.rst

from ._renderer import OUTPUT_FORMATS
from ._renderer import render

__all__ = [
    "register_rst_directive",
]

def _output_format(argument):
    return docutils.parsers.rst.directives.choice(argument, OUTPUT_FORMATS)

class _ASCIIBoxDirective(docutils.parsers.rst.Directive):

    required_arguments = 1
    optional_arguments = 6
    has_content = True
    option_spec = {
        'scale': docutils.parsers.rst.directives.nonnegative_int,
        'scale_x': docutils.parsers.rst.directives.nonnegative_int,
        'scale_y': docutils.parsers.rst.directives.nonnegative_int,
        'output_format': _output_format,
        'source_file': docutils.parsers.rst.directives.path,
        'target_file': docutils.parsers.rst.directives.path,
        }

    def run(self):
        try:
            source_filepath = self.options['source_file']
        except KeyError:
            self.assert_has_content()
            source_text = "\n".join(self.content)
        else:
            with open(source_filepath) as source_file:
                source_text = source_file.read()

        render_options = {}
        for key in ('output_format', 'scale_x', 'scale_y'):
            try:
                render_options[key] = self.options[key]
            except KeyError:
                continue

        try:
            scale = self.options['scale']
        except KeyError:
            pass
        else:
            render_options['scale_x'] = scale
            render_options['scale_y'] = scale

        filename = self.options.get('target_file', self.arguments[0])
        dirname = os.path.dirname(filename)
        if dirname:
            try:
                os.makedirs(dirname)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise e
        render(source_text, filename, **render_options)
        uri = docutils.parsers.rst.directives.uri(self.arguments[0])
        return [docutils.nodes.image(uri=uri)]

def register_rst_directive(name='asciibox'):
    docutils.parsers.rst.directives.register_directive(name, _ASCIIBoxDirective)
