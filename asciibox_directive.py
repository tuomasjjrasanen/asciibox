import os.path

import docutils.nodes
from docutils.parsers import rst

import asciibox

class ASCIIBoxDirective(rst.Directive):

    required_arguments = 1
    has_content = True
    option_spec = {
        'scale': rst.directives.nonnegative_int,
        }

    def run(self):
        self.assert_has_content()
        filename = self.arguments[0] + os.path.extsep + "png"
        scale = self.options.get("scale", 30)
        asciibox.render_to_filename("\n".join(self.content), filename,
                                    scale=scale)
        uri = rst.directives.uri(filename)
        return [docutils.nodes.image(uri=uri)]

rst.directives.register_directive('asciibox', ASCIIBoxDirective)
