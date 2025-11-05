"""
===============================================================================


 ███████████ █████                                         ███████████            
░█░░░███░░░█░░███                                         ░░███░░░░░███           
░   ░███  ░  ░███████   ████████   ██████  █████ ███ █████ ░███    ░███ █████ ████
    ░███     ░███░░███ ░░███░░███ ███░░███░░███ ░███░░███  ░██████████ ░░███ ░███ 
    ░███     ░███ ░███  ░███ ░░░ ░███ ░███ ░███ ░███ ░███  ░███░░░░░░   ░███ ░███ 
    ░███     ░███ ░███  ░███     ░███ ░███ ░░███████████   ░███         ░███ ░███ 
    █████    ████ █████ █████    ░░██████   ░░████░████    █████        ░░███████ 
   ░░░░░    ░░░░ ░░░░░ ░░░░░      ░░░░░░     ░░░░ ░░░░    ░░░░░          ░░░░░███ 
                                                                         ███ ░███ 
                                                                        ░░██████  
                                                                         ░░░░░░   

 ThrowPy - Throwable Exception Decorator
===============================================================================

Author: Giuseppe De Martino, PhD
Created: 2025-11-04
Version: 1.0.0
License: MIT
Description:
    A lightweight Python utility that provides a decorator (`ThrowableExcept`)
    for automatic exception handling and logging. Inspired by Java's "throwable"
    behavior, it allows developers to make any Python function or class method
    automatically catch and log exceptions with contextual details such as file,
    line number, class name, and method name.

    The decorator can optionally write errors to a log file, providing an easy
    and consistent way to trace and debug runtime issues in both small scripts
    and large applications.

Usage Example:
    from ThrowPy import ThrowableExcept

    @ThrowableExcept(logErr=True, logfile="error.log")
    def divide(a, b):
        return a / b

    divide(10, 0)
    # Output:
    # [2025-11-04 16:35:20.123456][ERROR] example.py:10 <no class>.divide() -> division by zero
    # (and the same line appended to "error.log")

-------------------------------------------------------------------------------
"""

from functools import wraps
from datetime import datetime
import traceback, sys

class ThrowableExcept(object):
    """
        A decorator class designed to automatically catch and handle exceptions
        raised within the decorated function or method. When an exception occurs,
        the error message is printed to the console and optionally logged to a file.

        This decorator provides a simplified "throwable" behavior similar to
        exception handling in Java, allowing developers to make any Python
        function or method automatically log its exceptions with contextual
        information such as file, line number, class, and method name.

        Attributes
        ----------
        logErr : bool, optional
            Enables or disables error logging to a file (default is True).
        logfile : str, optional
            Path to the log file where errors will be recorded if `logErr` is True
            (default is "logErr.log").

        Notes
        -----
        - If `logErr` is set to True, each error is appended to the end of the
        specified log file.
        - If logging to file fails, the decorator prints a secondary warning
        indicating that log writing was unsuccessful.

        Example
        -------
        Example usage for standalone functions:

            >>> from ThrowPy import ThrowableExcept

            @ThrowableExcept(logErr=True, logfile="error_log.txt")
            def divide(a, b):
                return a / b

            divide(10, 0)
            # Output:
            # [2025-11-04 16:15:20.123456][ERROR] example.py:10 <no class>.divide() -> division by zero
            # (and the same line appended to "error_log.txt")

        Example usage for class methods:

        >>> class Example:
        ...     @ThrowableExcept(logErr=False)
        ...     def risky_method(self, value):
        ...         return 10 / value

        >>> ex = Example()
        >>> ex.risky_method(0)
        # Output:
        # [2025-11-04 16:15:20.123789][ERROR] example.py:16 Example.risky_method() -> division by zero
        # (no log file written because logErr=False)
    """
    def __init__(self, logErr=True, logfile="logErr.log"):
        self.logErr     = logErr
        self.logfile    = logfile
        self.__ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def __call__(self, function):
        @wraps(function)
        def wrappedFunction(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                eType, eObject, eTraceback = sys.exc_info()
                tb = traceback.extract_tb(eTraceback)[-1]
                method_name = function.__name__
                class_name = args[0].__class__.__name__ if args and hasattr(args[0], "__class__") else "<no class>"
                msg = (
                    f"[{self.__ts}][ERROR] "
                    f"{tb.filename}:{tb.lineno} "
                    f"{class_name}.{method_name}() -> {e}"
                )
                if self.logErr:
                    try:
                        with open(self.logfile, "a", encoding="utf-8") as f:
                            f.write(msg + "\n")
                    except Exception as log_err:
                        print(f"[LOGGING ERROR] Unable to write log: {log_err}")

                print(msg)
                return None

        return wrappedFunction