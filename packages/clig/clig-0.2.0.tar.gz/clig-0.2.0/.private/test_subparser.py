from pprint import pprint
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-n", "--name")
parser.add_argument("-m", "--move")
sub_parsers = parser.add_subparsers(dest="sub")
c1 = sub_parsers.add_parser("command1")
c2 = sub_parsers.add_parser("command2")
c1.add_argument("-n", "--name")
c2.add_argument("-n", "--name")

# args = parser.parse_args(["-n", "Tibia", "command1", "-n", "diogo"])
# args = parser.parse_args(["-h"])
args1 = parser.parse_args("-n diogo  -m opa command1 -n bia".split())

args2 = c1.parse_args("-n bia".split())

print(args1)

print(args2)
