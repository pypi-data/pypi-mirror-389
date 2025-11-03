from dataclasses import dataclass, field, fields


@dataclass
class Person:
    name: str
    age: int = field(metadata={"frozen": True})

    def __post_init__(self):
        self.__set_fields_frozen(self)

    @classmethod
    def __set_fields_frozen(cls, self):
        flds = fields(cls)
        for fld in flds:
            if fld.metadata.get("frozen"):
                field_name = fld.name
                field_value = getattr(self, fld.name)
                setattr(self, f"_{fld.name}", field_value)

                def local_getter(self):
                    return getattr(self, f"_{field_name}")

                def frozen(name):
                    def local_setter(self, value):
                        raise RuntimeError(f"Field '{name}' is frozen!")

                    return local_setter

                setattr(cls, field_name, property(local_getter, frozen(field_name)))


person = Person("John", 22)

print(person)  # prints: Person(name='John', age=36)
print(person.age)  # prints: 36
person.age = 56  # raise: RuntimeError: Field 'age' is frozen!
