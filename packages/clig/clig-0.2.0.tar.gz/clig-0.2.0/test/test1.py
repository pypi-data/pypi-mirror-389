import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../src").resolve()))

# example6.py
from typing import Literal
from enum import Enum
import clig


class Color(Enum):
    red = 1
    blue = 2
    yellow = 3


def main(color: Literal[Color.red, "azul", "preto"]):
    print(f"Passed arguments to function: {locals()}")


clig.run(main, ["red"])
