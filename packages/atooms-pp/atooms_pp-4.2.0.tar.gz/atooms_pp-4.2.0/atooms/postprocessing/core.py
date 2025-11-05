import os
import argparse

from ._version import __version__

# Global variables
pp_output_path = '{trajectory}.pp.{symbol}.{tag}'
pp_trajectory_format = None

# Help formatter
os.environ['COLUMNS'] = "100"

class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def __init__(self, prog, *args, **kwargs):
        argparse.RawDescriptionHelpFormatter.__init__(self, prog,
                                                      indent_increment=2,
                                                      max_help_position=60,
                                                      width=None)

    def _get_help_string(self, action):
        msg = action.help
        if '%(default)' not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    msg += ' [default: %(default)s]'
        return msg

    def __add_whitespace(self, idx, iwspace, text):
        if idx == 0:
            return text
        return (" " * iwspace) + text

    def _split_lines(self, text, width):
        import re
        import textwrap as _textwrap
        textrows = text.splitlines()
        for idx, line in enumerate(textrows):
            search = re.search(r'\s*[0-9\-]{0,}\.?\s*', line)
            if line.strip() == "":
                textrows[idx] = " "
            elif search:
                lwspace = search.end()
                lines = [self.__add_whitespace(i, lwspace, x) for i, x in enumerate(_textwrap.wrap(line, width))]
                textrows[idx] = lines

        return [item for sublist in textrows for item in sublist]

# F90 modules
import os
from f2py_jit import jit

try:
    jit("""
subroutine hello()
end subroutine
""")
    _pwd = os.path.dirname(__file__)
    f90 = jit([os.path.join(_pwd, 'fourierspace.f90'),
               os.path.join(_pwd, 'realspace.f90')])
except RuntimeError:
    f90 = None
