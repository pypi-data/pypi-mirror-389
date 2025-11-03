from functools import partial
from typing import Callable, overload


@overload
def foo[**P, T](func: Callable[P, T]) -> Callable[P, T]: ...


@overload
def foo[**P, T](**kwargs) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def foo[**P, T](func: Callable[P, T] | None = None, **kwargs) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    # foo called as decorator without arguments
    if func is not None:
        # do something using func
        return func

    # foo is called as decorator with arguments
    return partial(foo, **kwargs)

    def wrap(func: Callable[P, T]) -> Callable[P, T]:
        # do something using kwargs
        # do something using func
        return func

    # foo is called as decorator with arguments
    return wrap

    # print("setting " + str(kwargs))
    # foo is called as decorator with arguments
    return partial(foo, **kwargs)


@foo  # (b=666, c="opa")
def bar(a):
    print(a)


if __name__ == "__main__":
    bar("aba gue")
