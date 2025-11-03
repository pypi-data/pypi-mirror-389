def get_argument_data(func: Callable[..., Any]) -> list[ArgumentData]:
    argument_data: list[ArgumentData] = []
    parameters = inspect.signature(func).parameters
    docstring_data = get_docstring_data(len(parameters), func.__doc__)
    helps = docstring_data.helps if docstring_data else {}
    for par in parameters:
        parameter = parameters[par]
        argument = ArgumentData(name=parameter.name)
        argument.help = helps.get(argument.name)
        if parameter.default != parameter.empty:
            argument.default = parameter.default
            argument.name = f"--{argument.name}"
        if parameter.annotation != parameter.empty:
            if callable(parameter.annotation):
                argument.kind = parameter.annotation
        argument_data.append(argument)
    return argument_data


if __name__ == "__main__":

    def foo(
        a: int, b: str, c: float, d: bool = True, e: list[str] | None = None
    ) -> tuple[str, ...]:
        """Iure qui iusto debitis sit temporibus quos saepe.

        Dolores laudantium quisquam consequuntur placeat dolor incidunt optio dolor. Ipsum et
        accusamus quibusdam et. Quo tempora aut suscipit enim velit aperiam et accusamus. Illum sunt
        voluptatum et.

        Parameters
        ----------
        a : int
            Aliquid ratione quam.
        b : str
            Id voluptatem maiores repellat qui.
        c : float
            Distinctio sit nesciunt.
        d : bool, optional
            Qui sit et sequi cupiditate deleniti eaque amet., by default True
        e : list[str] | None, optional
            Facilis quam asperiores repudiandae cupiditate sapiente., by default None

        Returns
        -------
        tuple[str, ...]
            Sequi labore ut molestias id ea suscipit.
        """
        ...

    assert foo.__doc__ is not None
    docstring_data = get_docstring_data(5, foo.__doc__)
    assert docstring_data is not None
    arg_data = get_argument_data(foo)

    parser = ArgumentParser(
        description=docstring_data.description,
        epilog=docstring_data.epilog,
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    for arg in arg_data:
        parser.add_argument(arg.name, type=arg.kind, default=arg.default, help=arg.help)
    parser.parse_args(["-h"])
