ZParser2 Cli Argument Parsing Library


`zparser2` is probably the simplest most opinionated argument parsing library in python. Lot's of conventions, zero configuration!

All you have to do is add the `@z.task` notation to a function and it automatically become available to the CLI.

Perks:

  * If a function contains annotations, it's variable types will be enforced and proper help will be displayed to the user.
  * If a function contains a docstring, it will show up as the function's comment in the CLI.
  * The file in which the function is located will be the module in which the function will be available.
  * If a module contains a docstring, it will show as the module's documentation in the CLI
  * If a function is in the main python script (`__main__`), it will be directly accessible, without needing to provide the module name.
  * You can access it using the cli or a web browser

The downside is that you can only have up to two layers in your cli (either `app.py FUNCITON_NAME` or `app.py MODULE_NAME FUNCTION_NAME`). If you need somethig more complex than that, please use something like https://pypi.org/project/click/ .

Instalation
-----------
```
pip3 install zparser2
```

Example
-------

Let's say you have 3 files:


[math_functions.py](example/math_functions.py)
```python
"""here we do math"""
from zparser2 import z

@z.task
def duplicate_number(x: float):
    """returns twice the value of x"""
    return 2*x

@z.task
def triple_number(x: float):
    """returns 3 times the value of x"""
    return 3*x
```

[string_functions.py](example/string_functions.py)
```python
"""string processing"""
from zparser2 import z

@z.task
def add_square_brackets_to_string(x: str):
    """x -> [x]"""
    return f"[{x}]"

@z.task
def first_word(x: str):
    """returns the first word of a string"""
    return x.split(" ")[0]

@z.task
def last_word(x: str):
    """returns the last word of a string"""
    return x.split(" ")[-1]

@z.task
def another_task(somestring: str, some_int: int, workdir=None, root_url=None):
    """description of the task"""
    z.print(f"somestring={somestring}")
    z.print(f"some_int={some_int}")
    z.print(f"workdir={workdir}")
    z.print(f"root_url={root_url}")
```



[mycli.py](example/mycli.py)
```python
#!/usr/bin/env python3
"""description of the __main__ module"""
from zparser2 import z, zparser2_init, __version__ as zparser2_version
import math_functions
import string_functions


@z.task
def say_hello(name: str):
    """this is a function on the main file"""
    z.print(f"Hello {name}, welcome to zparser2 {zparser2_version} !")

if __name__ == "__main__":
    zparser2_init()


```

Output
------

```
(env2) mdiez@batman:~/code/zparser2/example$ ./mycli.py
./mycli.py <task>
./mycli.py <plugin_name> <task>
Plugin list:
  math_functions       - here we do math
  string_functions     - string processing
Task list:
  say_hello            - this is a function on the main file

```

```
(env2) mdiez@batman:~/code/zparser2/example$ ./mycli.py string_functions
You need to specify a task
--------------------------------------------------------------------------------
string processing
./mycli.py string_functions <task>
Plugin alias: []
Tasks:
  add_square_brackets_to_string - x -> [x]
  another_task         - description of the task
  first_word           - returns the first word of a string
  last_word            - returns the last word of a string
```

```
(env2) mdiez@batman:~/code/zparser2/example$ ./mycli.py string_functions another_task
You need to specify the required arguments [somestring, some_int]
--------------------------------------------------------------------------------
description of the task
Usage:
  ./mycli.py string_functions another_task somestring some_int [--workdir workdir] [--root_url root_url]
Positional arguments:
  somestring -  <class 'str'>
  some_int -  <class 'int'>
Optional arguments:
  --workdir (Default: None)  -
  --root_url (Default: None)  -
```

```
(env2) mdiez@batman:~/code/zparser2/example$ ./mycli.py string_functions another_task blah 42 --root_url https://blah.com
somestring=blah
some_int=42
workdir=None
root_url=https://blah.com
```

```
(env2) mdiez@batman:~/code/zparser2/example$ ./mycli.py say_hello Bob
Hello Bob, welcome to zparser 2!
```

Using the Web Browser
=====================

For very simple tools, in very specific circunstances, you may want to run your `zparser2` scripts via a web browser.
Fear not. We've got you covered!

With some small modifications to [mycli.py](example/mycli.py), we created [zparser2_web.py](example/zparser2_web.py) which makes `zparser2` a runs a [Flask](https://flask.palletsprojects.com/en/stable/) website.


To run the website in development mode, type:

* `flask --app zparser2_web run --host 0.0.0.0 --reload`

Please check the official [Flask](https://flask.palletsprojects.com/en/stable/) to run it in production.


Some technical notes on this topic:

* `zparser2` generates a [Flask](https://flask.palletsprojects.com/en/stable/) compatible output, which means although you do need [Flask](https://flask.palletsprojects.com/en/stable/) to run and host your website, [Flask](https://flask.palletsprojects.com/en/stable/) is not a dependency to `zparser2`

* For you to use this feature, you need to use `z.print()` instead of `print()` in your functions, else the output will go to `stdout` instead of to the zparser2 flask website. If you are just using `zparser2` for the cli, it does not matter.

* Lines are sent from the server to the browser one at a time (streamed), instead of all at once, just like in the cli.


WebSite Output
--------------

Main Website

![Main Website](screenshots/zparser2_web1.png "Main Website")

-----------

Function `say_hello`, with input forms

![Function say_hello](screenshots/zparser2_web2.png "Function say_hello")

-----------

Function output

![Function output](screenshots/zparser2_web3.png "Function output")



How to build & publish
======================

* `python3 -m build`
* `python3 -m twine upload --repository testpypi dist/*`
* `python3 -m twine upload --repository pypi dist/*`

Link
----
* https://pypi.org/project/zparser2/
* https://github.com/marcosdiez/zparser2/