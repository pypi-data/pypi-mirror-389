from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument("-o")

sub = parser.add_subparsers(dest="opa")
subp = sub.add_parser("teste")
subp.add_argument("-a")


if __name__ == "__main__":
    args = parser.parse_args()
    print(args)
