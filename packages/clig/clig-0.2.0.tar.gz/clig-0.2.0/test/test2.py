import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../src").resolve()))

from clig import Command, Arg, data


def git(
    exec_path: Arg[Path, data("-e", metavar="<path>")] = Path("git"),
    work_tree: Arg[Path, data("-w", metavar="<path>")] = Path(".").resolve(),
):
    print(locals())


def remote(
    verbose: Arg[bool, data("-v", help="To be verbose")] = False,
):
    print(locals())


def add(name: str, url: str):
    print(locals())


def rename(old: str, new: str):
    print(locals())


def remove(name: str):
    print(locals())


def submodule(quiet: bool):
    print(locals())


def init(path: Path = Path(".").resolve()):
    print(locals())


def update(init: bool, path: Path = Path(".").resolve()):
    print(locals())


main = Command(git, subcommands_required=True)


sub1 = (
    main.new_subcommand(remote, subcommands_required=True)
    .add_subcommand(add)
    .add_subcommand(rename)
    .add_subcommand(remove)
)
sub2 = main.new_subcommand(submodule).add_subcommand(init).add_subcommand(update)


main.run()
