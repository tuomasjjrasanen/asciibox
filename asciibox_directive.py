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

import os.path

import docutils.nodes
from docutils.parsers import rst

import asciibox

def output_format(argument):
    return rst.directives.choice(argument, asciibox.OUTPUT_FORMATS)

class ASCIIBoxDirective(rst.Directive):

    required_arguments = 1
    optional_arguments = 2
    has_content = True
    option_spec = {
        'scale': rst.directives.nonnegative_int,
        'output_format': output_format,
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
        asciibox.render("\n".join(self.content), filename, **render_options)
        uri = rst.directives.uri(filename)
        return [docutils.nodes.image(uri=uri)]

rst.directives.register_directive('asciibox', ASCIIBoxDirective)
