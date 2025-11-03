# clig

A single module, pure python, **Command Line Interface Generator**

---

## Installation

```console
pip install clig
```

---

# User guide

`clig` is a single module, written in pure python, that wraps around the
_stdlib_ module `argparse` (using the _stdlib_ module `inspect`) to generate
command line interfaces through simple functions.

## Basic usage

Create or import some function and call `clig.run()` with it:

```python
# example01.py
import clig

def printperson(name, title="Mister"):
    print(locals())

clig.run(printperson)
```

In general, the function arguments that have a "default" value are turned into
optional _flagged_ (`--`) command line arguments, while the "non default" will
be positional arguments.

```
> python example01.py -h

    usage: printperson [-h] [--title TITLE] name

    positional arguments:
      name

    options:
      -h, --help     show this help message and exit
      --title TITLE

```

The script can then be used in the same way as used with `argparse`:

```
> python example01.py John

    {'name': 'John', 'title': 'Mister'}

```

```
> python example01.py Maria --title Miss

    {'name': 'Maria', 'title': 'Miss'}

```

## Helps

Arguments and command Helps are taken from the docstring when possible:

```python
# example02.py
import clig

def greetings(name, greet="Hello"):
    """Description of the command: A greeting prompt!

    Args:
        name: The name to greet
        greet: The greeting used. Defaults to "Hello".
    """
    print(f"Greetings: {greet} {name}!")

clig.run(greetings)
```

```
> python example02.py --help

    usage: greetings [-h] [--greet GREET] name

    Description of the command: A greeting prompt!

    positional arguments:
      name           The name to greet

    options:
      -h, --help     show this help message and exit
      --greet GREET  The greeting used. Defaults to "Hello".

```

There is an internal list of docstring templates from which you can choose if
the inferred docstring is not correct. It is also possible to specify your own
custom docstring template.

## Argument inference

Based on [type annotations](https://docs.python.org/3/library/typing.html), some
arguments can be inferred from the function signature to pass to the
`argparse.ArgumentParser.add_argument()` method:

```python
# example03.py
import clig

def recordperson(name: str, age: int, height: float):
    print(locals())

clig.run(recordperson)
```

The types in the annotation may be passed to
`argparse.ArgumentParser.add_argument()` method as `type` keyword argument:

```
> python example03.py John 37 1.70

    {'name': 'John', 'age': 37, 'height': 1.7}

```

And the type conversions are performed as usual

```
> python example03.py Mr John Doe

    usage: recordperson [-h] name age height
    recordperson: error: argument age: invalid int value: 'John'

```

### Booleans

Booleans are transformed in arguments with `action` of kind `"store_true"` or
`"store_false"` (depending on the default value).

```python
# example04.py
import clig

def recordperson(name: str, age: int, title="Mister", graduate: bool = False):
    print(locals())

clig.run(recordperson)
```

```
> python example04.py -h

    usage: recordperson [-h] [--title TITLE] [--graduate] name age

    positional arguments:
      name
      age

    options:
      -h, --help     show this help message and exit
      --title TITLE
      --graduate

```

```
> python example04.py Leo 36 --title "Doctor" --graduate

    {'name': 'Leo', 'age': 36, 'title': 'Doctor', 'graduate': True}

```

If no default is given to the boolean, a `required=True` keyword argument is
passed to `add_argument()` method in the flag boolean option and a
`BooleanOptionalAction` (already available in `argparse`) is passed as `action`
keyword argument, adding support for a boolean complement action in the form
`--no-option`:

```python
# example05.py
import clig

def recordperson(name: str, age: int, graduate: bool):
    print(locals())

clig.run(recordperson)
```

```
> python example05.py -h

    usage: recordperson [-h] --graduate | --no-graduate name age

    positional arguments:
      name
      age

    options:
      -h, --help            show this help message and exit
      --graduate, --no-graduate

```

```
> python example05.py Ana 23

    usage: recordperson [-h] --graduate | --no-graduate name age
    recordperson: error: the following arguments are required: --graduate/--no-graduate

```

### Tuples, Lists and Sequences: `nargs`

If the type is a `tuple` of specified length `N`, the argument automatically
uses `nargs=N`. If the type is a generic `Sequence`, a `list` or a `tuple` of
_any_ length (i.e., `tuple[<type>, ...]`), it uses `nargs="*"`.

```python
# example06.py
import clig


def main(name: tuple[str, str], ages: list[int]):
    print(locals())


clig.run(main)
```

```
> python example06.py -h

    usage: main [-h] name name [ages ...]

    positional arguments:
      name
      ages

    options:
      -h, --help  show this help message and exit

```

```
> python example06.py John Mary 2 78 35

    {'name': ('John', 'Mary'), 'ages': [2, 78, 35]}

```

### Literals and Enums: `choices`

If the type is a `Literal` or a `Enum` the argument automatically uses
`choices`.

```python
# example07.py
from typing import Literal
import clig

def main(name: str, move: Literal["rock", "paper", "scissors"]):
    print(locals())

clig.run(main)
```

```
> python example07.py -h

    usage: main [-h] name {rock,paper,scissors}

    positional arguments:
      name
      {rock,paper,scissors}

    options:
      -h, --help            show this help message and exit

```

As is expected in `argparse`, an error message will be displayed if the argument
was not one of the acceptable values:

```
> python example07.py John knife

    usage: main [-h] name {rock,paper,scissors}
    main: error: argument move: invalid choice: 'knife' (choose from rock, paper, scissors)

```

```
> python example07.py Mary paper

    {'name': 'Mary', 'move': 'paper'}

```

#### `Enums`

`Enums` should be passed by name

```python
# example08.py
from enum import Enum, StrEnum
import clig

class Color(Enum):
    red = 1
    blue = 2
    yellow = 3

class Statistic(StrEnum):
    minimun = "minimun"
    mean = "mean"
    maximum = "maximum"

def main(color: Color, statistic: Statistic):
    print(locals())

clig.run(main)
```

```
> python example08.py -h

    usage: main [-h] {red,blue,yellow} {minimun,mean,maximum}

    positional arguments:
      {red,blue,yellow}
      {minimun,mean,maximum}

    options:
      -h, --help            show this help message and exit

```

```
> python example08.py red mean

    {'color': <Color.red: 1>, 'statistic': <Statistic.mean: 'mean'>}

```

```
> python example08.py green

    usage: main [-h] {red,blue,yellow} {minimun,mean,maximum}
    main: error: argument color: invalid choice: 'green' (choose from red, blue, yellow)

```

#### `Literal` with `Enum`

You can even mix `Enum` and `Literal`

```python
# example09.py
from typing import Literal
from enum import Enum
import clig

class Color(Enum):
    red = 1
    blue = 2
    yellow = 3

def main(color: Literal[Color.red, "green", "black"]):
    print(locals())

clig.run(main)
```

```
> python example09.py red

    {'color': <Color.red: 1>}

```

```
> python example09.py green

    {'color': 'green'}

```

## Argument specification

TODO

## Subcommands

Instead of using the function `clig.run()`, you can create an object instance of
the type `Command`, passing your function to its constructor, and call the
`Command.run()` method.

```python
# example10.py
from clig import Command

def main(name:str, age: int, height: float):
    print(locals())

cmd = Command(main)
cmd.run()
```

```
> python example10.py "Carmem Miranda" 42 1.85

    {'name': 'Carmem Miranda', 'age': 42, 'height': 1.85}

```

This makes possible to use some methods to add subcommands. All subcommands will
also be instances of the same class `Command`. There are 4 methods available:

- `subcommand`: Creates the subcommand and returns the input function unchanged.
  This is a proper method to be used as a function decorator.
- `new_subcommand`: Creates a subcommand and returns the new created `Command`
  instance.
- `add_subcommand`: Creates the subcommand and returns the caller object. This
  is useful to add multiple subcommands in one single line.
- `end_subcommand`: Creates the subcommand and returns the parent of the caller
  object. If the caller doesn't have a parent, an error will be raised. This is
  useful when finishing to add subcommands in the object.

The functions will execute sequentially, from a `Command` to its subcommands.

```python
# example11.py
from inspect import getframeinfo, currentframe
from clig import Command

def main(verbose: bool = False):
    """The main function

    Args:
        verbose: Verbose option
    """
    print(f"{getframeinfo(currentframe()).function} {locals()}")

# The main command could also not have a function
cmd = Command(main)

@cmd.subcommand
def foo(a, b):
    """The foo command

    Args:
        a: Help for a argument
        b: Help for b argument
    """
    print(f"{getframeinfo(currentframe()).function} {locals()}")

@cmd.subcommand
def bar(c, d):
    """The bar command

    Args:
        c: Help for c argument
        d: Help for d argument
    """
    print(f"{getframeinfo(currentframe()).function} {locals()}")

cmd.run()
```

```
> python example11.py -h

    usage: main [-h] [--verbose] {foo,bar} ...

    The main function

    options:
      -h, --help  show this help message and exit
      --verbose   Verbose option

    subcommands:
      {foo,bar}
        foo
        bar

```

```
> python example11.py foo -h

    usage: main foo [-h] a b

    The foo command

    positional arguments:
      a           Help for a argument
      b           Help for b argument

    options:
      -h, --help  show this help message and exit

```

```
> python example11.py bar -h

    usage: main bar [-h] c d

    The bar command

    positional arguments:
      c           Help for c argument
      d           Help for d argument

    options:
      -h, --help  show this help message and exit

```

```
> python example11.py bar baz ham

    main {'verbose': False}
    bar {'c': 'baz', 'd': 'ham'}

```

The next example tries to reproduce some of the Git interface, using methods
after the function definitions.

```python
# example12.py
from inspect import getframeinfo, currentframe
from pathlib import Path
from clig import Command

def git(exec_path: Path = Path("git"), work_tree: Path = Path("C:/Users")):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def status(branch: str):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def commit(message: str):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def remote(verbose: bool = False):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def add(name: str, url: str):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def rename(old: str, new: str):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def remove(name: str):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def submodule(quiet: bool):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def init(path: Path = Path(".").resolve()):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def update(init: bool, path: Path = Path(".").resolve()):
    print(f"{getframeinfo(currentframe()).function} {locals()}")

######################################################################################
# The interface is all built in the code below, which could also be in another file

(
    Command(git)
    .add_subcommand(status)
    .add_subcommand(commit)
    .new_subcommand(remote)
        .add_subcommand(add)
        .add_subcommand(rename)
        .end_subcommand(remove)
    .new_subcommand(submodule)
        .add_subcommand(init)
        .end_subcommand(update)
    .run()
)
```

```
> python example12.py -h

    usage: git [-h] [--exec-path EXEC_PATH] [--work-tree WORK_TREE]
               {status,commit,remote,submodule} ...

    options:
      -h, --help            show this help message and exit
      --exec-path EXEC_PATH
      --work-tree WORK_TREE

    subcommands:
      {status,commit,remote,submodule}
        status
        commit
        remote
        submodule

```

```
> python example12.py remote -h

    usage: git remote [-h] [--verbose] {add,rename,remove} ...

    options:
      -h, --help           show this help message and exit
      --verbose

    subcommands:
      {add,rename,remove}
        add
        rename
        remove

```

```
> python example12.py remote rename oldName newName

    git {'exec_path': WindowsPath('git'), 'work_tree': WindowsPath('C:/Users')}
    remote {'verbose': False}
    rename {'old': 'oldName', 'new': 'newName'}

```
