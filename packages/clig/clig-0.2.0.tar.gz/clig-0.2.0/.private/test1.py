import sys, os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../src"))


from clig import run
from typing import Annotated as Arg


def git(
    version: int,
    git_dir: Arg[str, 666],
    work_tree: str,
    teste: bool = False,
):
    """_summary_

    _extended_summary_

    :param version: _description_
    :type version: int
    :param git_dir: _description_
    :type git_dir: Arg[str, 666]
    :param work_tree: _description_
    :type work_tree: str
    :param teste: _description_, defaults to False
    :type teste: bool, optional
    """
    print(locals())


sys.argv += "-h".split()


if __name__ == "__main__":
    run(git)
