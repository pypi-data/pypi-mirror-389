from argparse import ArgumentParser
from importlib.metadata import version

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


mainparser = ArgumentParser(description="Git helper utilities")
mainparser.add_argument(
    "--version",
    action="version",
    version=f"%(prog)s {version('mxrepo')}",
)
subparsers = mainparser.add_subparsers(help="command", required=True)


def listdir(path="."):
    return sorted(os.listdir(path))


def hilite(string, color, bold):
    # http://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux
    # http://stackoverflow.com/questions/2330245/python-change-text-color-in-shell
    attr = []
    if color == "green":
        attr.append("32")
    elif color == "red":
        attr.append("31")
    elif color == "blue":
        attr.append("34")
    if bold:
        attr.append("1")
    return "\x1b[{}m{}\x1b[0m".format(";".join(attr), string)


def query_repos(context):
    org_url = f"https://api.github.com/orgs/{context}/repos"
    user_url = f"https://api.github.com/users/{context}/repos"
    query = "{}?page={}&per_page=50"
    data = list()
    page = 1
    while True:
        try:
            url = query.format(org_url, page)
            res = urllib.request.urlopen(url)  # noqa: S310
        except urllib.error.URLError:
            try:
                url = query.format(user_url, page)
                res = urllib.request.urlopen(url)  # noqa: S310
            except urllib.error.URLError as e:
                print(e)
                sys.exit(0)
        page_data = json.loads(res.read())
        res.close()
        if not page_data:
            break
        data += page_data
        page += 1
    print(f"Fetched {len(data)} repositories for '{context}'")
    return data


def perform_clone(arguments):
    base_uri = "git@github.com:{}/{}.git"
    context = arguments.context[0]
    if arguments.repository:
        repos = arguments.repository
    else:
        repos = [_["name"] for _ in query_repos(arguments.context)]
    for repo in repos:
        uri = base_uri.format(context, repo)
        cmd = ["git", "clone", uri]
        subprocess.call(cmd)  # noqa: S603


sub = subparsers.add_parser("clone", help="Clone from an organisation or a user")
sub.add_argument("context", nargs=1, help="Name of organisation or user")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to clone, leave empty to clone all",
)
sub.set_defaults(func=perform_clone)


def get_branch():
    cmd = ["git", "branch"]
    p = subprocess.Popen(  # noqa: S603
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output = p.stdout.readlines()
    for line in output:
        line = line.decode("utf-8")
        if line.strip().startswith("*"):
            return line.strip().strip("*").strip()


def perform_pull(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Perform pull for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "pull", "origin", get_branch()]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser("pull", help="Pull distinct or all repositories in folder.")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to pull, leave empty to pull all",
)
sub.set_defaults(func=perform_pull)


def perform(cmd):
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
    stdout, stderr = pr.communicate()
    print(stdout.decode())
    if pr.returncode != 0:
        print("{} failed to perform: exit code {}".format(" ".join(cmd), pr.returncode))
        print(stderr.decode())


def perform_backup(arguments):
    context = arguments.context[0]
    if context not in listdir("."):
        os.mkdir(context)
    os.chdir(context)
    contents = listdir(".")
    data = query_repos(context)
    base_uri = "git@github.com:{}/{}.git"
    for repo in data:
        name = repo["name"]
        fs_name = f"{name}.git"
        if fs_name in contents:
            print(f"Fetching existing local repository '{fs_name}'")
            os.chdir(fs_name)
            perform(["git", "fetch", "origin"])
            os.chdir("..")
        else:
            print(f"Cloning new repository '{fs_name}'")
            uri = base_uri.format(context, name)
            perform(["git", "clone", "--bare", "--mirror", uri])


sub = subparsers.add_parser(
    "backup", help="Backup all repositories from an organisation or a user"
)
sub.add_argument("context", nargs=1, help="Name of organisation or user")
sub.set_defaults(func=perform_backup)


def perform_status(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Status for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "status"]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser(
    "status", help="Status of distinct or all repositories in current folder."
)
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to show, leave empty to show all",
)
sub.set_defaults(func=perform_status)


def perform_branch(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Branches for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "branch"]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser(
    "branch", help="Show branches of distinct or all repositories in current folder."
)
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to show, leave empty to show all",
)
sub.set_defaults(func=perform_branch)


def perform_diff(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Diff for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "diff"]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser(
    "diff", help="Show diff of distinct or all repositories in current folder."
)
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to show diff of, leave empty to show all",
)
sub.set_defaults(func=perform_diff)


def perform_commit(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    message = arguments.message[0]
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Commit all changes resources for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "commit", "-am", message]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser(
    "commit",
    help="Commit all changes of distinct or all repositories in current folder.",
)
sub.add_argument("message", nargs=1, help="Commit message")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to commit, leave empty to commit all",
)
sub.set_defaults(func=perform_commit)


def perform_push(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Perform push for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "push", "origin", get_branch()]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser("push", help="Push distinct or all repositories in folder.")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to push, leave empty to push all",
)
sub.set_defaults(func=perform_push)


def perform_checkout(arguments):
    if arguments.repository:
        dirnames = arguments.repository
    else:
        dirnames = listdir(".")
    for child in dirnames:
        if not os.path.isdir(child):
            continue
        if ".git" not in listdir(child):
            continue
        os.chdir(child)
        print(f"Perform checkout for '{hilite(child, 'blue', True)}'")
        cmd = ["git", "checkout", "."]
        subprocess.call(cmd)  # noqa: S603
        os.chdir("..")


sub = subparsers.add_parser("checkout", help="Discard all uncommited changes.")
sub.add_argument(
    "repository",
    nargs="*",
    help="Name of repositories to discard, leave empty to discard all",
)
sub.set_defaults(func=perform_checkout)


def main():
    arguments = mainparser.parse_args()
    arguments.func(arguments)
