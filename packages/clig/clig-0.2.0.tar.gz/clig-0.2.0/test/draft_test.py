# cspell:disable
import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../src").resolve()))

import clig


@clig.Command
def main(a: str = "diogo", b: int = 666, c: float = 32.0):
    """Optio est dolorem illo esse ipsa dolor provident.

    Commodi accusamus sunt aut aut illum repudiandae.

    Parameters
    ----------
    - `a` (`str`):
        Earum iure expedita ut repellat fugit vero ducimus ut non.

    - `b` (`int`):
        Eos omnis est provident vel.

    - `c` (`float`, optional): Defaults to `32.0`.
        Quia vitae aut sunt.

    """
    print(locals())


@main.subcommand
def suba(d: int, e: str = "TiBia"):
    """Autem quisquam tempora illo reprehenderit inventore eum voluptates.

    Quis blanditiis ad praesentium minus numquam sit rerum recusandae.

    Parameters
    ----------
    - `d` (`int`):
        Alias occaecati et sed iste voluptate aut.

    - `e` (`str`, optional): Defaults to `"TiBia"`.
        Voluptate blanditiis totam harum.

    """
    pass


@main.subcommand
def subb(d: int, e: str = "TiBia"):
    """Autem quisquam tempora illo reprehenderit inventore eum voluptates.

    Quis blanditiis ad praesentium minus numquam sit rerum recusandae.

    Parameters
    ----------
    - `d` (`int`):
        Alias occaecati et sed iste voluptate aut.

    - `e` (`str`, optional): Defaults to `"TiBia"`.
        Voluptate blanditiis totam harum.

    """
    pass


main.run("suba -h".split())
