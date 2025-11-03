import sys
from pathlib import Path

path = Path(__file__).parent
sys.path.insert(0, str((path).resolve()))
sys.path.insert(0, str((path / "../../src").resolve()))
from clig import Command, data, Arg


def git(
    exec_path: str = "git",
    bare: bool = False,
    git_dir: str = ".git",
    work_tree: str = ".",
):
    """The Git version control system

    'git help -a' and 'git help -g' list available subcommands and some concept guides. See 'git help
    <command>' or 'git help <concept>' to read about a specific subcommand or concept. See 'git help git' for
    an overview of the system.

    Parameters
    ----------
    - `exec_path` (`str`, optional): Defaults to `"git"`.
        The path to the executable.

    - `bare` (`bool`, optional): Defaults to `False`.
        Whether the repository is bare or not

    - `git_dir` (`str`, optional): Defaults to `".git"`.
        The path to the repository data base.

    - `work_tree` (`str`, optional): Defaults to `"."`.
        The path to the worktree.
    """
    print(locals())
    return "Exec git"


def add(pathspec: list[str], interactive: Arg[bool, data("-i")] = False, edit: Arg[bool, data("-e")] = False):
    """Add file contents to the index

    Used to add file contents to the index

    Parameters
    ----------
    - `pathspec` (`list[str]`):
        The paths to add

    - `interactive` (`Arg[bool, data`, optional): Defaults to `False`.
        interactive picking

    - `edit` (`Arg[bool, data`, optional): Defaults to `False`.
        edit current diff and apply

    """
    print(locals())
    return "Exec add"


def commit(message: Arg[str, data("-m")], amend: bool = False):
    """Record changes to the repository

    Use this to commit changes

    Parameters
    ----------
    - `message` (`Arg[str, data`):
        commit message

    - `amend` (`bool`, optional): Defaults to `False`.
        amend previous commit
    """
    print(locals())
    return "Exec commit"


def remote(verbose: bool = False):
    """Manage remote repositories

    Use this subcommand to manage fetched remote repos.

    Parameters
    ----------
    - `verbose` (`bool`, optional): Defaults to `False`.
        Whether the subcommand is verbose

    """
    print(locals())
    return "Exec remote"


def rename(old: str, new: str):
    """Renames the remote

    Use to rename the remote repo

    Parameters
    ----------
    - `old` (`str`):
        Old name of the repo

    - `new` (`str`):
        New name of the remote
    """
    print(locals())
    return "Exec rename"


def remove(name: str):
    """Removes a remote

    Use to remove a remote reference

    Parameters
    ----------
    - `name` (`str`):
        Name of the remote
    """
    print(locals())
    return "Exec remove"


def prune(name: str, dry_run: bool = False):
    """Prune the remote repo

    Use to prune the remote repo

    Parameters
    ----------
    - `name` (`str`):
        Name of the remote

    - `dry_run` (`bool`, optional): Defaults to `False`.
        Whether to dry run
    """
    print(locals())
    return "Exec prune"


app = (
    Command(git, subcommands_description="These are common Git commands used in various situations:")
    .add_subcommand(add)
    .add_subcommand(commit)
)
remote_cmd = (
    app.new_subcommand(remote, subcommands_description="Comands used with git remote")
    .add_subcommand(rename)
    .add_subcommand(remove)
    .add_subcommand(prune)
)
print(app.run())
