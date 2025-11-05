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

from .ThrowPy import ThrowableExcept

__all__ = ["ThrowableExcept"]
__author__ = "Giuseppe De Martino"
__version__ = "1.0.0"
__license__ = "MIT"