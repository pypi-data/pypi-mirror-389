from code import InteractiveInterpreter
from io import StringIO, TextIOBase
import sys
from contextlib import contextmanager
from archytas.tool_utils import tool


class BlockInput(TextIOBase):
    def read(self, size = -1):
        raise IOError("Illegal to read input in this context")
    def readline(self, size = -1):
        raise IOError("Illegal to read input in this context")
    def readlines(self, hint = -1):
        raise IOError("Illegal to read input in this context")
    def readable(self):
        return False

# context manager to capture io
@contextmanager
def capture_io(allow_stdin: bool = False):
    """
    Context manager for capturing stdout and stderr from some process
    assumes the process generates stdout/stderr from python

    Args:
        allow_stdin (bool, optional): whether to allow stdin input. If False, attempts to us standard input will raise an error. Defaults to False.
    
    Yields:

    """
    # save the original stdout/stderr/stdin
    _stdout = sys.stdout
    _stderr = sys.stderr
    _stdin = sys.stdin

    # redirect stdout/stderr/stdin to the StringIO objects
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    sys.stdin = sys.stdin if allow_stdin else BlockInput()

    # yield the StringIO objects
    try:
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout = _stdout
        sys.stderr = _stderr
        sys.stdin = _stdin
    

class PythonTool:
    """
    Tool for running python code. If the user asks you to write code, you can run it here.
    """
    def __init__(self, locals: dict=None):
        """
        Create a PythonTool instance

        Args:
            locals (dict[str,Any], optional): A dictionary of variables/classes/functions/modules/etc. to add to the python environment. Defaults to {}. # @tools will be correctly extracted from their wrappers so they can be used in the environment.
            # prelude (str, optional): Code to run before any other code. Defaults to ''. This could be used to import modules, or define functions/classes/etc. that will be used in the environment.
        """
        if locals is not None:
            locals = {"__name__": "__console__", '__doc__': None, **locals}
        self.kernel = InteractiveInterpreter(locals=locals)

    @tool
    def run(self, code: str) -> tuple[str, str]:
        """
        Runs python code in a python environment.

        The environment is persistent between runs, so any variables created will be available in subsequent runs.
        The only visible effects of this tool are from output to stdout/stderr. If you want to view a result, you MUST print it.

        Args:
            code (str): The code to run

        Returns:
            tuple[str, str]: The captured (stdout, stderr) strings from executing the code. These may be empty if there was no output.
        """
        with capture_io() as (out, err):
            pdb.set_trace() #TODO: runsource can only run 1 expression at a time...
            # self.kernel.compile(code)
            # self.kernel.runcode(code) #supposedly this is the right way to handle multiple lines!
            self.kernel.runsource(code)
        return out.getvalue(), err.getvalue()


def test():
    from easyrepl import REPL
    kernel = PythonTool()
    for query in REPL():
        if query == 'exit':
            break
        res = kernel.execute(query)
        print(f'{res=}')

    print('done!\n' + '='*20 + '\n')


if __name__ == '__main__':
    test()