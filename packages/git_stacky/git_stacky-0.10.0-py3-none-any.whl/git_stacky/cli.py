#!/usr/bin/env python3

import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

import click

DEBUG = False

Command = str | list[str]


class WorkflowType(Enum):
    BRANCH = "branch"
    FORK = "fork"


def complete_git_target(_: click.Context, __: click.Parameter, incomplete: str) -> list[str]:
    """Shell completion for git target argument."""
    try:
        return [t for t in get_common_targets() if is_subseq(incomplete, t)]
    except click.ClickException:
        return []


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option()
def cli():
    pass


@cli.command("hack")
@click.argument("target", required=False, shell_complete=complete_git_target)
@click.option("-c", "--carry", is_flag=True, default=False, help="Carry current changes to the new stack.")
@click.option("-x", "--fix", is_flag=True, default=False, help="You accidentally committed to main branch, so convert the changes to a stack.")
@click.option("-m", "--main", is_flag=True, default=False, help="Stay on main, don't switch back to target.")
@click.option("-n", "--no-update", is_flag=True, default=False, help="Do not update main.")
def hack_cmd(target: str, carry: bool, fix: bool, main: bool, no_update: bool) -> None:
    """
    Update main and optionally create a new stack.

    \b
    Function:
      hack        => update main, stay on starting branch
      hack TARGET => update main, create TARGET from main if it doesn't exist, and switch to it

    \b
    Examples:
      (main)    hack          => update main
      (main)    hack FEATURE  => update main, create+switch to FEATURE
      (FEATURE) hack          => update main
      (FEATURE) hack main     => update main, switch to main
    """
    workflow = workflow_type()
    main_branch = main_branch_name()

    # Validate
    dirty_changes = try_run("git status --porcelain")
    if dirty_changes:
        if carry:
            must_run("git stash push --include-untracked", loud=True)
        else:
            cexit("current branch is dirty, aborting")
    start = current_branch()
    target = target or start or (main_branch if main else None)  # default to current branch, else main if --main
    if not start and not target:
        cexit("start and target branches empty (detached head and no target), aborting")
    validate_branches()
    should_create_target = validate_target_hack_branch(target, start, main_branch, main)

    # Fix accidental commit to main
    if fix:
        if not should_create_target:
            cexit("target stack exists, aborting")
        remote_main_branch = remote_main_branch_name(main_branch)
        if branches_same_commit(main_branch, remote_main_branch):
            cexit("local and remote main branches point to the same commit, aborting")
        if not branch_is_ancestor(remote_main_branch, main_branch):
            cexit("remote main branch is not an ancestor of local main branch, aborting")
        must_run(f"git checkout {remote_main_branch}", loud=True)
        must_run(f"git branch {target}_base", loud=True)
        must_run(f"git checkout {main_branch}", loud=True)
        must_run(f"git branch {target}", loud=True)
        must_run(f"git reset --hard {remote_main_branch}", loud=True)
        should_create_target = False

    # Update main
    if not (start == main_branch or fix):
        must_run(f"git checkout {main_branch}", loud=True)
    if not no_update:
        if workflow == WorkflowType.FORK:
            must_run(f"git pull upstream {main_branch}", loud=True)
            must_run(f"git push origin {main_branch}", loud=True)
        else:
            must_run("git pull", loud=True)

    # Create/switch to stack
    if not (target == main_branch or main):
        if should_create_target:
            must_run(f"git branch {target}_base", loud=True)
            must_run(f"git checkout -b {target}", loud=True)
        else:
            must_run(f"git checkout {target}", loud=True)

    # Carry changes
    if carry:
        must_run("git stash pop", loud=True)

    if fix:
        warn(f"due to --fix, this didn't rebase your stack onto main; you may want to run 'git stack rebase'")


@cli.command("rebase")
@click.argument("target", required=False, shell_complete=complete_git_target)
@click.option("-d", "--done", is_flag=True, default=False, help="Finish rebasing a stack.")
def rebase_cmd(target: str, done: bool) -> None:
    """
    Rebase current stack onto main or the specified target.

    \b
    Examples:
      (FEATURE) rebase        => rebase FEATURE onto main
      (FEATURE) rebase TARGET => rebase FEATURE onto TARGET
      (FEATURE) rebase --done => finish rebasing FEATURE, if original rebase was interrupted
    """
    if done:
        rebase_done()
        return

    rebase_only(target)
    rebase_done()


@cli.command("stacks")
@click.option("-l", "--list", "just_list", is_flag=True, default=False, help="List the names of all stacks.")
@click.option("-g", "--graph", is_flag=True, default=False, help="Print a graph of all stacks.")
@click.option("-m", "--main", is_flag=True, default=False, help="Print the main branch name.")
@click.option("-n", "--max-count", type=int, help="Max commits to show in the graph.")
@click.option("-d", "--delete", multiple=True, help="Delete a stack.")
@click.option("-D", "--delete-force", multiple=True, help="Delete a stack forcefully.")
def stacks_cmd(just_list: bool, graph: bool, main: bool, max_count: int, delete: tuple[str], delete_force: tuple[str]) -> None:
    """
    Manage and visualize stacks.

    \b
    Examples:
      stacks                     => list all stacks
      stacks --graph             => graph all stacks
      stacks --delete FEATURE    => delete FEATURE stack
    """
    if main:
        click.echo(main_branch_name())
        return
    if graph:
        try_run(
            [
                "git",
                "log",
                "--graph",
                "--format=format:%C(auto)%h%C(reset) %C(cyan)(%cr)%C(reset)%C(auto)%d%C(reset) %s %C(dim white)- %an%C(reset)",
            ]
            + (["--max-count", str(max_count)] if max_count else [])
            + get_stacks()
            + [main_branch_name()],
            loud=True,
        )
        return
    if delete:
        delete_stacks(list(delete))
        return
    if delete_force:
        delete_stacks(list(delete_force), force=True)
        return
    print_stacks(just_list)


@cli.command("absorb")
def absorb_cmd() -> None:
    """
    Automatically absorb changes into the stack.

    Requires git-absorb to be installed.
    """
    if not try_run("git absorb -h"):
        cexit("git-absorb not installed, aborting")
    current = current_branch()
    if not current:
        cexit("current branch not found (detached head), aborting")
    if current not in get_stacks():
        cexit("current branch is not a stack, aborting")
    must_run(
        [
            "git",
            "-c",
            "sequence.editor=:",
            "-c",
            "absorb.autoStageIfNothingStaged=true",
            "absorb",
            "--and-rebase",
            "--base",
            f"{current}_base",
        ],
        loud=True,
    )


def rebase_only(target: str) -> None:
    """Rebase a stack onto the target."""
    br = must_run("git branch --show-current", "current branch not found, aborting")
    br_base = f"{br}_base"

    if try_run("git status --porcelain"):
        cexit("current branch is dirty, aborting")
    if not branch_exists(br):
        cexit(f"current branch '{br}' does not exist, aborting")
    if not branch_exists(br_base):
        cexit(f"stack may not be tracked by stacky: base branch '{br_base}' does not exist, aborting")
    if target and not branch_exists(target):
        log(f"target branch '{target}' does not exist, aborting")
    if not target:
        target = main_branch_name()
    if target == br:
        cexit("target branch is the same as current branch, aborting")
    if target == br_base:
        cexit("target branch is the same as base branch, aborting")

    save_rebase_args([target, br_base, br])

    _, stderr, errcode = run(["git", "rebase", "--onto", target, br_base, br], loud=True)
    if errcode:
        click.echo()
        click.echo(stderr)
        click.echo()
        warn("rebase failed")
        click.echo("RUN: 'git stack rebase --done' to complete rebase, after resolving conflicts")
        exit(1)


def rebase_done() -> None:
    """Finish rebasing a stack."""
    args = load_rebase_args()
    if len(args) != 3:
        cexit("rebase arguments not found, aborting")
    target, br_base, br = args

    if not branch_exists(br):
        cexit(f"branch '{br}' does not exist, aborting")
    if not branch_exists(br_base):
        cexit(f"base branch '{br_base}' does not exist, aborting")

    must_run(f"git checkout {br_base}", loud=True)
    must_run(f"git reset --hard {target}", loud=True)
    must_run(f"git checkout {br}", loud=True)

    clear_rebase_args()


def save_rebase_args(args: list[str]) -> None:
    """Save null-separated rebase arguments to ~/.stacky/rebase_args."""
    stacky_dir = Path.home() / ".stacky"
    rebase_args_file = stacky_dir / "rebase_args"
    stacky_dir.mkdir(parents=True, exist_ok=True)
    rebase_args_file.write_text("\0".join(args))


def load_rebase_args() -> list[str]:
    """Load null-separated rebase arguments from ~/.stacky/rebase_args."""
    rebase_args_file = Path.home() / ".stacky" / "rebase_args"
    if not rebase_args_file.exists():
        return []
    return rebase_args_file.read_text().split("\0")


def clear_rebase_args() -> None:
    """Clear rebase arguments."""
    rebase_args_file = Path.home() / ".stacky" / "rebase_args"
    if rebase_args_file.exists():
        rebase_args_file.unlink()


def delete_stacks_all(force: bool = False) -> None:
    """Delete all stacks."""
    ss = get_stacks()
    ss = [s for s in ss if s if not s == current_branch()]
    delete_stacks(ss, force)


def delete_stacks(delete: list[str], force: bool = False) -> None:
    """Delete stacks."""
    delete = set(delete).intersection(get_stacks())
    delete = [s for s in delete] + [f"{s}_base" for s in delete]
    if not delete:
        log("no stacks to delete")
        return

    _, stderr, errcode = run(["git", "branch", "-D" if force else "-d"] + list(delete), loud=True)
    if errcode:
        click.echo()
        click.echo(stderr)
        click.echo()
        warn("delete failed")
        return


def print_stacks(just_list: bool = False) -> None:
    """List all tracked stacks."""
    ss = get_stacks() if just_list else [f"* {s}" if s == current_branch() else f"  {s}" for s in get_stacks()]
    if not ss:
        return
    click.echo("\n".join(ss))


def get_common_targets() -> list[str]:
    """Return a list of common Git targets."""
    return get_stacks() + [main_branch_name()]


def get_stacks() -> list[str]:
    """Return a list of tracked stacks."""
    branches = get_branches()
    ss = [b for b in branches if f"{b}_base" in branches]
    return ss


def get_branches() -> list[str]:
    """Return a list of branches."""
    return must_run("git branch --format='%(refname:short)'").split()


def main_branch_name() -> str:
    """Return the name of the main branch."""
    name = try_run("git symbolic-ref refs/remotes/origin/HEAD")
    if name:
        return name.split("/")[-1]

    name = try_run("git config --get init.defaultBranch")
    if name:
        return name

    return "master"


def remote_main_branch_name(main_branch: str) -> str:
    """Return the name of the remote main branch."""
    origin = try_run(f"git config --get branch.{main_branch}.remote")
    if not origin:
        cexit(f"unable to determine remote origin for '{main_branch}', aborting")
    remote_ref = try_run(f"git config --get branch.{main_branch}.merge")
    if not remote_ref:
        cexit(f"unable to determine remote tracking branch for '{main_branch}', aborting")
    remote_branch = remote_ref.split("/")[-1]
    return f"{origin}/{remote_branch}"


def branches_same_commit(*branches: str) -> bool:
    """Check if all branches point to the same commit."""
    if not branches:
        cexit("no branches provided to branches_same_commit, aborting")
    commits = must_run(f"git rev-parse {' '.join(branches)}")
    uniq = set(commits.split())
    return len(uniq) == 1


def branch_is_ancestor(ancestor: str, descendant: str) -> bool:
    """Check if the ancestor branch is an ancestor of the descendant branch."""
    if not ancestor or not descendant:
        cexit("ancestor or descendant branch is empty, aborting")
    _, _, errcode = run(f"git merge-base --is-ancestor {ancestor} {descendant}")
    return errcode == 0


def workflow_type() -> WorkflowType:
    """Return the type of Git workflow."""
    if try_run("git remote get-url upstream"):
        return WorkflowType.FORK
    return WorkflowType.BRANCH


def branch_exists(target: str) -> bool:
    """Check if a branch exists."""
    return bool(try_run(f"git show-ref refs/heads/{target}"))


def current_branch() -> str:
    """Return the name of the current branch, or an empty string if detached."""
    return try_run("git branch --show-current")


def validate_branches() -> None:
    """Validate branch names."""
    bs = get_branches()
    ss = get_stacks()
    for b in bs:
        if b.endswith("_base_base"):
            warn(f"potentially colliding base branch '{b}' detected")
        if b.endswith("_base") and strip_suffix(b, "_base") not in ss:
            warn(f"potentially orphaned base branch '{b}' detected")


def validate_target_hack_branch(target: str, start: str, main_branch: str, main: bool) -> bool:
    """Validate the target branch for the hack command. Returns True iff the target needs to be created."""
    if target == main_branch or (target == start and main):
        return False

    target_exists = branch_exists(target)
    target_base_exists = branch_exists(f"{target}_base")

    if not target_exists and not target_base_exists:
        return True
    if target_exists and not target_base_exists:
        cexit(f"target branch '{target}' exists, but base branch '{target}_base' does not, aborting")
    if not target_exists and target_base_exists:
        cexit(f"base branch '{target}_base' exists, but target branch '{target}' does not, aborting")
    return False


def strip_suffix(s: str, suffix: str) -> str:
    """Strip a suffix from a string."""
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


def is_subseq(small: str, big: str):
    """Check if small is a subsequence of big."""
    it = iter(big)
    return all(c in it for c in small)


def run(command: Command, loud: bool = False) -> tuple[str, str, int]:
    """Run a shell command and return the (stdout, stderr, returncode)."""
    if DEBUG:
        click.echo(f"DEBUG: {command}")
    shell = isinstance(command, str)
    if loud:
        res = subprocess.run(command, shell=shell)
        return "", "", res.returncode
    else:
        res = subprocess.run(command, shell=shell, text=True, capture_output=True)
        return res.stdout.strip(), res.stderr.strip(), res.returncode


def must_run(command: Command, fail_msg: Optional[str] = None, loud: bool = False) -> str:
    """Run a shell command and return the output, or exit on error."""
    stdout, stderr, errcode = run(command, loud=loud)
    if errcode:
        msg = fail_msg or f"failed to run command '{command}'"
        if loud:
            msg = fail_msg or f"failed to run command '{command}'\n\n{stdout}\n\n{stderr}"
        cexit(msg)
    return stdout


def try_run(command: Command, loud: bool = False) -> str:
    """Run a shell command and return the output, or return None on error."""
    stdout, _, errcode = run(command, loud)
    if errcode:
        return ""
    return stdout


class Colors:
    YELLOW = "\033[33m"
    RED = "\033[31m"
    RESET = "\033[0m"


def cexit(msg: str) -> None:
    """Print an error message and exit."""
    err(msg)
    sys.exit(1)


def log(msg: str) -> None:
    """Print a message."""
    click.echo(fmt_log(msg))


def warn(msg: str) -> None:
    """Print a warning message."""
    click.echo(f"{Colors.YELLOW}WARN: {msg}{Colors.RESET}")


def err(msg: str) -> None:
    """Print an error message."""
    click.echo(f"{Colors.RED}ERROR: {msg}{Colors.RESET}")


def fmt_log(msg: str) -> str:
    """Capitalize the first letter of a log message."""
    if not msg:
        return msg
    return msg[0].upper() + msg[1:]


if __name__ == "__main__":
    cli()
