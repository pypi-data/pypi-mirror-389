from code import InteractiveInterpreter
from io import StringIO, TextIOBase
import sys
import traceback
import types # For TracebackType
from contextlib import contextmanager

# --- capture_io and BlockInput remain the same ---
class BlockInput(TextIOBase):
    # ...(rest of BlockInput methods)...
    def read(self, size=-1): raise IOError("Read disabled")
    def readline(self, size=-1): raise IOError("Readline disabled")
    def readlines(self, hint=-1): raise IOError("Readlines disabled")
    def readable(self): return False
    def writable(self): return False
    def seekable(self): return False

@contextmanager
def capture_io(allow_stdin: bool = False):
    _stdout = sys.stdout
    _stderr = sys.stderr
    _stdin = sys.stdin

    captured_stdout = StringIO()
    captured_stderr = StringIO()
    sys.stdout = captured_stdout
    sys.stderr = captured_stderr # Important: Interpreter writes here
    sys.stdin = sys.stdin if allow_stdin else BlockInput()

    try:
        yield captured_stdout, captured_stderr
    finally:
        sys.stdout = _stdout
        sys.stderr = _stderr
        sys.stdin = _stdin

# --- Custom Interpreter using traceback.format_list ---
class CustomInterpreter(InteractiveInterpreter):
    """
    An InteractiveInterpreter that formats runtime tracebacks using
    standard library functions but filters out internal frames.
    """
    def showtraceback(self):
        """
        Display the exception that just occurred.
        Uses traceback.format_list on filtered frames to include code lines.
        Writes directly to sys.stderr (which should be captured).
        """
        etype, value, tb = sys.exc_info()
        if tb is None:
            print("No traceback available", file=sys.stderr)
            return

        try:
            # Extract traceback details into FrameSummary objects
            extracted_list = traceback.extract_tb(tb)

            # Skip the first frame (the call within runcode or similar interpreter internals)
            if len(extracted_list) > 0:
                # This is the crucial part: filter out the interpreter frame(s).
                # For runcode, often just skipping the first frame is enough.
                filtered_list = extracted_list[1:]
            else:
                filtered_list = []

            lines = []
            if filtered_list:
                # Add the standard header
                lines.append("Traceback (most recent call last):\n")
                # Use format_list - this SHOULD include the code lines
                lines.extend(traceback.format_list(filtered_list))

            # Add the exception type and value (formatted)
            lines.extend(traceback.format_exception_only(etype, value))

            # Write the formatted traceback to stderr
            sys.stderr.write("".join(lines))

        finally:
            # Clean up reference to traceback
            del tb

    # No showsyntaxerror needed here - handled in run method


# --- PythonTool using the CustomInterpreter ---
# Dummy decorator if archytas is not available
def tool(func):
    return func

class PythonTool:
    """
    Tool for running python code using a custom interpreter for better tracebacks.
    """
    def __init__(self, locals: dict=None):
        initial_locals = {"__name__": "__console__", '__doc__': None}
        if locals:
            initial_locals.update(locals)
        self.kernel = CustomInterpreter(locals=initial_locals)

    @tool
    def run(self, code: str) -> tuple[str, str]:
        """
        Runs python code in a persistent environment with custom traceback handling.

        Args:
            code (str): The code to run

        Returns:
            tuple[str, str]: The captured (stdout, stderr) strings.
        """
        # Don't necessarily need trailing newline for compile/exec
        # if not code.endswith('\n'):
        #     code += '\n'

        # Use the capture_io context manager
        with capture_io() as (captured_stdout, captured_stderr):
            try:
                # Attempt compilation first. This catches SyntaxErrors cleanly.
                compiled_code = self.kernel.compile(code, '<string>', 'exec')

                # The 'if compiled_code is None' check is primarily for interactive
                # mode signaling incomplete input. For 'exec' mode, true syntax
                # errors raise SyntaxError, and incomplete but valid prefixes
                # often just compile fine. So we can likely remove this check.

                if compiled_code: # Proceed if compilation succeeded
                    self.kernel.runcode(compiled_code)

            except SyntaxError:
                # Catch SyntaxErrors raised during compile()
                etype, value, tb = sys.exc_info()
                # Format *only* the exception part (includes line and caret)
                syntax_error_lines = traceback.format_exception_only(etype, value)
                # Write directly to the captured stderr stream
                captured_stderr.write("".join(syntax_error_lines))
                del tb # Clean up

            except Exception:
                # Catch other runtime exceptions during runcode()
                # Our custom showtraceback will handle formatting these
                # and write to the captured stderr stream.
                self.kernel.showtraceback()

            # Handle SystemExit separately if needed
            except SystemExit as e:
                 captured_stderr.write(f"SystemExit: {e}\n")
                 # Decide re-raise behavior based on requirements

        # Return the captured content *after* the context manager exits
        return captured_stdout.getvalue(), captured_stderr.getvalue()

# --- Example Usage ---
if __name__ == "__main__":
    kernel_tool = PythonTool()

    print("--- Run 1: Define a variable ---")
    code1 = "x = 10\ny = 5\nprint('Variables defined')"
    print(f"code1:\n{code1}")
    stdout, stderr = kernel_tool.run(code1)
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}")
    print("-" * 20)

    print("--- Run 2: Use the variable and cause an error ---")
    code2 = "import sys\nsys.stderr.write('Error about to happen...\\n')\nprint(f'x is still {x}')\nz = x / 0 # Error here"
    print(f"code2:\n{code2}")
    stdout, stderr = kernel_tool.run(code2)
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}") # Should show warning + filtered traceback WITH code line
    print("-" * 20)

    print("--- Run 3: Check state after error ---")
    code3 = "print(f'x is STILL {x}')" # x should still be 10
    print(f"code3:\n{code3}")
    stdout, stderr = kernel_tool.run(code3)
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}")
    print("-" * 20)

    print("--- Run 4: Syntax Error ---")
    code4 = "print('Hello')\ndef my_func(a,b\n    print(a+b)"
    print(f"code4:\n{code4}")
    stdout, stderr = kernel_tool.run(code4)
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}") # Should show ONLY SyntaxError with caret
    print("-" * 20)

    print("--- Run 5: Error within a function ---")
    code5 = """
def calculate(val):
    print(f"Calculating with {val}")
    return 100 / val

result = calculate(0)
print("Done calculation.")
"""
    print(f"code5:\n{code5}")
    stdout, stderr = kernel_tool.run(code5)
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}") # Should show traceback within calculate/call site WITH code lines
    print("-" * 20)

    print("--- Run 6: Incomplete input ---")
    code6 = "if True:\n  a = 1" # Should likely run without error in exec mode
    print(f"code6:\n{code6}")
    stdout, stderr = kernel_tool.run(code6)
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}")
    print("-" * 20)