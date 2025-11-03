import sys
from pathlib import Path
from pprint import pprint
from argparse import ArgumentParser, HelpFormatter

# path = Path(__file__).parent
# sys.path.insert(0, str((path).resolve()))
# sys.path.insert(0, str((path / "../../../../src/clig").resolve()))
# import clig


# def main(lista: list[str]):
#     print(locals())


# cmd = clig.Command(main, subcommands_description="Teste de descri", formatter_class=HelpFormatter)


# @cmd.subcommand(help="opa remove1")
# def remove(name: str):
#     print(locals())


# @cmd.subcommand(help="opa add1")
# def add(name: str):
#     print(locals())


# cmd.run()
# cmd.add_parsers()
# pprint(cmd.arguments)


parser = ArgumentParser(prog="main")
parser.add_argument("lista", nargs="*")
subparsers = parser.add_subparsers(dest="subcommand_1", description="Teste de descri")
subparser1 = subparsers.add_parser("remove", help="opa remove")
subparser1.add_argument("name")
subparser2 = subparsers.add_parser("add", help="opa add")
subparser2.add_argument("name")
args = parser.parse_args()
print(args)
#
# assert parser == cmd.parser
