from argparse import ArgumentParser

parser = ArgumentParser(prog="Diogo")

subparsers1 = parser.add_subparsers(dest="sub1", description="Desc do grupo")  # prog="opa")
cmd1 = subparsers1.add_parser("command1")
subparser11 = cmd1.add_subparsers(dest="sub1")
cmd11 = subparser11.add_parser("cmd11")
cmd2 = subparsers1.add_parser("command2")

cmd1.add_argument()

args = parser.parse_args("command1 -h".split())
args = parser.parse_args("command1".split())

print(args)
