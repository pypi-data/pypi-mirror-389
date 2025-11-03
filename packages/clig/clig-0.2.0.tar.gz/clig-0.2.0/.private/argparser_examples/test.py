from argparse import ArgumentParser

parser = ArgumentParser()

subparsers1 = parser.add_subparsers(dest="sub1")
subparsers2 = parser.add_subparsers(dest="sub2")  # This is not allowed


args = parser.parse_args(["-h"])
