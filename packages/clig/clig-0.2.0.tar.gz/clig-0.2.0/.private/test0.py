from typing import Annotated as Arg


# def foo(
#     a: Arg[str, "bia"],
#     b: Arg[int, 666],
#     c: Arg[bool, "Diogo"] = True,
# ):
#     pass


def foo(a: str, b: int, c: bool = True):

    print(a)
    print(b)
    print(c)


# def foo(a, b, c):
#     pass
