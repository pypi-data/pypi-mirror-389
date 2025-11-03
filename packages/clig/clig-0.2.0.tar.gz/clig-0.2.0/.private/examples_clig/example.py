import clig


def hello():
    pass


app = clig.Command(hello).add_subcommand(hello)

print(app.subparsers_dest)
