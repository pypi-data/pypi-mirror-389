from dataclasses import dataclass, field, InitVar


@dataclass(repr=True)
class Person:
    name: InitVar[str]
    _name: str = field(init=False)
    age: int

    @property
    def name_(self) -> str:
        self._name

    def __post_init__(self, name: str) -> None:
        self._name = name


p = Person(name="digo", age=36)

print(p)
