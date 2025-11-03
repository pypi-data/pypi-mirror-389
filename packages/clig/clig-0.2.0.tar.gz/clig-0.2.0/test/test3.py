import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../src").resolve()))

from typing import Literal
from enum import Enum, StrEnum
import clig


class Color(StrEnum):
    red = "red"
    blue = "blue"
    yellow = "yellow"


def main(a: Path | int):
    print(locals())


clig.run(main, "1".split())
