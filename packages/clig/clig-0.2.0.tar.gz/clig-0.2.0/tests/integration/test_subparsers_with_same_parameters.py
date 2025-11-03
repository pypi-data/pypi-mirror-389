import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../../src").resolve()))

from clig import Command, Arg, data


def test_subparsers_with_same_parameters_all_kw():
    def maincmd(foo: str | None = None):
        assert foo == "yoco"

    def subcmd(foo: str | None = None):
        assert foo == "rocky"

    def subsubcmd(foo: str | None = None):
        assert foo == "sand"

    (
        Command(maincmd)
        .new_subcommand(subcmd)
        .end_subcommand(subsubcmd)
        .run("--foo yoco subcmd --foo rocky subsubcmd --foo sand".split())
    )
