# example11.py

import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../src").resolve()))

from clig import Command

cmd = Command()  # The main command may not have a function, in cases it doesn't need arguments


@cmd.subcommand
def foo(a, b):
    """The foo command

    Args:
        a: Help for a argument
        b: Help for b argument
    """
    print(locals())


@cmd.subcommand
def bar(c, d):
    """The bar command

    Args:
        c: Help for c argument
        d: Help for d argument
    """


cmd.run()
