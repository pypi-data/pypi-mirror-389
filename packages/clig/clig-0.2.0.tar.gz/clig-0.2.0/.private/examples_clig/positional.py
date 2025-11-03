# cSpell:disable
import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../../src").resolve()))
from clig import Command, data, Arg


def print_echo(
    echo: str,
    upper: Arg[bool, data("-u")] = True,
    value: Arg[int, data("-c", "--const", make_flag=True, action="store_const", const=123)] = 666,
):
    """Quam blanditiis qui corporis aut dolor qui officiis quo.

    Dolor totam repudiandae quam ea sit. Officiis nostrum repellendus. Ut odio omnis sed aut. Est qui fugit
    fuga et dolorem sapiente. Nostrum qui vero cumque tempore. Necessitatibus quo facilis numquam impedit quia
    ipsa minima aliquid vitae.

    Parameters
    ----------
    - `echo` (`str`):
        Repellendus id distinctio reiciendis dignissimos sit voluptatem et omnis corporis.

    - `upper` (`Arg[bool, data`, optional): Defaults to `True`.
        Amet sunt nihil consequatur ut dolorem provident aut.

    - `value` (`Arg[int, data`, optional): Defaults to `"store_const", const=123)]=666`.
        Et facilis cumque voluptatum.

    """
    print(locals())


def hello(word: str):
    pass


def hi(word: str):
    pass


cmd = Command(print_echo, description="opa")
cmd.add_command(hi)
cmd.run()
