#!/usr/bin/env python

from argparse import ArgumentParser, Namespace
from datetime import datetime
from os import path
from configparser import RawConfigParser
from subprocess import Popen, PIPE


GIT_COMMANDS = {
    "get_tag": ["git describe --tags --abbrev=0"],
    "create_new_branch": ["git checkout -b {new_version} master"],
    "commit_version_change": ["git commit -m 'Bumping up version from {current_version} to {new_version}'"],
    "push_new_branch": ["git push origin {new_version}"],
    "create_new_tag": ["git tag -a {new_version} -m 'Bumping up version from {current_version} to {new_version}'"],
    "push_tag": ["git push origin {new_version}"],
    "get_change_log": ['git log --no-merges --pretty=format:"%h: %cn: %s" {current_version}..']
}


def _run_shell_command(command: list):
    try:
        process = Popen(command, stderr=PIPE, stdout=PIPE, stdin=PIPE,
                        shell=True)
        output, error = process.communicate()
        return_code = process.returncode
        return output, error, return_code
    except:
        return None, None, -1


def _fetch_default_calendar_release_version():
    return datetime.now().strftime("%y.%m.0")


def _fetch_current_version(config_file: str) -> str:
    if path.isfile(config_file):
        config_parser = RawConfigParser()
        with open(config_file) as cfg:
            config_parser.read_file(cfg)
            return config_parser.get("version", "current_version") or _fetch_default_calendar_release_version()
    else:
        return _fetch_default_calendar_release_version()


def _change_micro_version(current_version: str):
    version_string = current_version.split(".")
    version_string[-1] = str((int(version_string[-1]) + 1))
    return ".".join(version_string)


def _get_new_version(config_file: str = "./setup.cfg", current_version: str = None,
                     micro_release: bool = False):
    if micro_release:
        if current_version:
            return _change_micro_version(current_version)
        elif config_file:
            return _change_micro_version(_fetch_current_version(config_file))
        else:
            return _fetch_default_calendar_release_version()
    else:
        return _fetch_default_calendar_release_version()


def _get_current_tag(git_command_name="get_tag"):
    global GIT_COMMANDS
    command = GIT_COMMANDS.get(git_command_name)
    out, err, ret = _run_shell_command(command)
    if len(str(out)):
        return str(out).split("\n")[0]
    else:
        return None


def _update_release_version_for_sanic(current_version, new_version, config_file):
    old_version_line = '__version__ = "{current_version}"'.format(current_version=current_version)
    new_version_line = '__version__ = "{new_version}"'.format(new_version=new_version)

    with open("sanic/__init__.py") as init_file:
        data = init_file.read()

    new_data = data.replace(old_version_line, new_version_line)
    with open("sanic/__init__.py", "w") as init_file:
        init_file.write(new_data)

    config_parser = RawConfigParser()
    with open(config_file) as cfg:
        config_parser.read_file(cfg)
    config_parser.set("version", "current_version", new_version)

    with open(config_file, "w") as config:
        config_parser.write(config)

    command = GIT_COMMANDS.get("commit_version_change")
    command[0] = command[0].format(new_version=new_version, current_version=current_version)
    _, _, ret = _run_shell_command(command)
    if int(ret) != 0:
        print("Failed to Commit Version upgrade changes to Sanic")
        exit(1)


def _tag_release(new_version, current_version):
    global GIT_COMMANDS
    for command_name in ["push_new_branch", "create_new_tag", "push_tag"]:
        command = GIT_COMMANDS.get(command_name)
        command[0] = command[0].format(new_version=new_version, current_version=current_version)
        out, error, ret = _run_shell_command(command=command)
        if int(ret) != 0:
            print("Failed to execute the command: {}".format(command[0]))
            exit(1)


def release(args: Namespace):
    current_tag = _get_current_tag()
    current_version = _fetch_current_version(args.config)
    if current_tag and current_version not in current_tag:
        print("Tag mismatch between what's in git and what was provided by --current-version")
        exit(1)
    new_version = _get_new_version(args.config, current_version, args.micro_release)
    _update_release_version_for_sanic(current_version=current_version, new_version=new_version, config_file=args.config)
    _tag_release(current_version=current_version, new_version=new_version)


if __name__ == '__main__':
    cli = ArgumentParser(description="Sanic Release Manager")
    cli.add_argument("--release-version", "-r", help="New Version to use for Release",
                     default=_fetch_default_calendar_release_version(),
                     required=False)
    cli.add_argument("--current-version", "-cv", help="Current Version to default in case if you don't want to "
                                                      "use the version configuration files",
                     default=None, required=False)
    cli.add_argument("--config", "-c", help="Configuration file used for release", default="./setup.cfg", required=False)
    cli.add_argument("--micro-release", "-m", help="Micro Release with patches only",
                     default=False, action='store_true', required=False)
    args = cli.parse_args()
    release(args)
