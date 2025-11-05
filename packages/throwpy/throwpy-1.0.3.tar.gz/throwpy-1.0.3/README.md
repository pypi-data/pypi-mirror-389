# 🧰 ThrowPy

**ThrowPy** is a lightweight Python library that provides a simple and elegant way to make any function or class method *"throwable"*, similar to Java-style exception handling.

It offers an easy-to-use decorator — `@ThrowableExcept` — that automatically catches exceptions, prints meaningful error messages, and optionally logs them to a file.

---

## Features

- 🔹 Simple decorator-based usage  
- 🔹 Automatic exception catching with file and line context  
- 🔹 Optional file logging (`logErr=True`)  
- 🔹 Works with both functions and class methods  
- 🔹 Minimal dependencies (pure Python)  
- 🔹 Python 3.8+ compatible  

---

## 1. Installation

You can install **ThrowPy** directly from [PyPI](https://pypi.org/project/throwpy/):

```bash
pip install throwpy

```

## 2. Import and Basic Usage

The decorator can be applied to functions or methods.

```python
from throwpy import ThrowableExcept

```
When a decorated function raises an exception, the decorator intercepts it, generates a structured error message, and:
prints it to the console (stdout)
if logErr=True, writes it to a specified log file
The decorator returns None when an exception occurs (i.e., it does not re-raise the error).

## 3. Decorator Parameters

```python
logErr (bool)

```
Purpose: Enables or disables writing the error message to a file.
Default: True (if not specified, logging to file is enabled).

If logErr=False, the decorator will not attempt to write to a file, but the error message will still be printed to the console.

```python
logfile (string)

```

Purpose: Specifies the path/name of the log file where error messages are appended.
Default: "logErr.log" (typically created in the current working directory).

If logErr=True but the logfile cannot be written to (e.g., due to missing permissions), an error will be caught and a message such as
[LOGGING ERROR] Unable to write log: …
will be printed to the console.


## 4. Usage Examples

## 4.1 Simple Function with Default File Logging

```python
from throwpy import ThrowableExcept

@ThrowableExcept()  # equivalent to logErr=True, logfile="logErr.log"
def divide(a, b):
    return a / b

divide(10, 0)

```

Behavior:
The ZeroDivisionError is intercepted.
A message similar to the following is generated:

```css
[2025-11-04 18:00:00.123456][ERROR] script.py:12 <no class>.divide() -> division by zero

```

The message is printed to the console and appended to the file logErr.log (created if it doesn’t exist).


## 4.2 Disabling File Logging

```python
@ThrowableExcept(logErr=False)
def get_item(lst, idx):
    return lst[idx]

get_item([], 5)

```

Behavior:
The IndexError is intercepted.
The message is printed to the console, but not written to any file.


## 4.3 Using a Custom Log File

```python
@ThrowableExcept(logErr=True, logfile="errors/my_errors.log")
def risky_operation(x):
    return 10 / x

risky_operation(0)

```

Behavior:
If the errors/ directory exists and my_errors.log is writable, the log will be written there.
If writing fails (e.g., directory doesn’t exist or permissions are missing), a message like:

```css
[LOGGING ERROR] Unable to write log: <internal error>

```

will be printed.



## 4.4 Usage in Classes (Methods)

```python
class Example:
    @ThrowableExcept()
    def risky(self, x):
        return 100 / x

ex = Example()
ex.risky(0)

```

Behavior:
The generated message will include the class name:

```css
[2025-11-04 18:05:34.567890][ERROR] myfile.py:45 Example.risky() -> division by zero

```
