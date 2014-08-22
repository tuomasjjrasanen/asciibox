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
