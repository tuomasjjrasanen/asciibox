import os.path

import docutils.nodes
from docutils.parsers import rst

import asciibox

class ASCIIBoxDirective(rst.Directive):

    required_arguments = 1
    has_content = True

    def run(self):
        self.assert_has_content()
        filename = self.arguments[0] + os.path.extsep + "png"
        asciibox.render_to_filename("\n".join(self.content), filename)
        uri = rst.directives.uri(filename)
        return [docutils.nodes.image(uri=uri)]

rst.directives.register_directive('asciibox', ASCIIBoxDirective)
