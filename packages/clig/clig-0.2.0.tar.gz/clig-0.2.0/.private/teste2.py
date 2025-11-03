import argparse

# parser = argparse.ArgumentParser(prog="git")
# parser.add_argument("x", type=int, help="the base")
# parser.add_argument("y", type=int, help="the exponent")
# parser.add_argument("-v", "--verbosity", action="count", default=0)
# args = parser.parse_args()


# parent_parser = argparse.ArgumentParser(add_help=False)
# parent_parser.add_argument("--parent", type=int)

# foo_parser = argparse.ArgumentParser(parents=[parent_parser])
# foo_parser.add_argument("foo")

# foo_parser.parse_args()


# create the top-level parser
parser = argparse.ArgumentParser(prog="PROG")
parser.add_argument("--foo", action="store_true", help="foo help")
subparsers = parser.add_subparsers(help="subcommand help")

# create the parser for the "a" command
parser_a = subparsers.add_parser("a", help="a help")
parser_a.add_argument("bar", type=int, help="bar help")

# create the parser for the "b" command
parser_b = subparsers.add_parser("b", help="b help")
parser_b.add_argument("--baz", choices=("X", "Y", "Z"), help="baz help")

# parse some argument lists
parser.parse_args(["a", "12"])
