#!/usr/bin/env python

from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from configparser import RawConfigParser
from datetime import datetime
from json import dumps
from os import path, chdir
from subprocess import Popen, PIPE

from jinja2 import Environment, BaseLoader
from requests import patch
import sys
import towncrier

GIT_COMMANDS = {
    "get_tag": ["git describe --tags --abbrev=0"],
    "commit_version_change": [
        "git add . && git commit -m 'Bumping up version from "
        "{current_version} to {new_version}'"
    ],
    "create_new_tag": [
        "git tag -a {new_version} -m 'Bumping up version from "
        "{current_version} to {new_version}'"
    ],
    "push_tag": ["git push origin {new_version}"],
    "get_change_log": [
        'git log --no-merges --pretty=format:"%h::: %cn::: %s" '
        "{current_version}.."
    ],
}


RELEASE_NOTE_TEMPLATE = """
# {{ release_name }} - {% now 'utc', '%Y-%m-%d' %}

To see the exhaustive list of pull requests included in this release see:
https://github.com/huge-success/sanic/milestone/{{milestone}}?closed=1

# Changelog
{% for row in changelogs %}
* {{ row -}}
{% endfor %}

# Credits
{% for author in authors %}
* {{ author -}}
{% endfor %}
"""

JINJA_RELEASE_NOTE_TEMPLATE = Environment(
    loader=BaseLoader, extensions=["jinja2_time.TimeExtension"]
).from_string(RELEASE_NOTE_TEMPLATE)

RELEASE_NOTE_UPDATE_URL = (
    "https://api.github.com/repos/huge-success/sanic/releases/tags/"
    "{new_version}?access_token={token}"
)


class Directory:
    def __init__(self):
        self._old_path = path.dirname(path.abspath(__file__))
        self._new_path = path.dirname(self._old_path)

    def __enter__(self):
        chdir(self._new_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        chdir(self._old_path)


def _run_shell_command(command: list):
    try:
        process = Popen(
            command, stderr=PIPE, stdout=PIPE, stdin=PIPE, shell=True
        )
        output, error = process.communicate()
        return_code = process.returncode
        return output.decode("utf-8"), error, return_code
    except:
        return None, None, -1


def _fetch_default_calendar_release_version():
    return datetime.now().strftime("%y.%m.0")


def _fetch_current_version(config_file: str) -> str:
    if path.isfile(config_file):
        config_parser = RawConfigParser()
        with open(config_file) as cfg:
            config_parser.read_file(cfg)
            return (
                config_parser.get("version", "current_version")
                or _fetch_default_calendar_release_version()
            )
    else:
        return _fetch_default_calendar_release_version()


def _change_micro_version(current_version: str):
    version_string = current_version.split(".")
    version_string[-1] = str((int(version_string[-1]) + 1))
    return ".".join(version_string)


def _get_new_version(
    config_file: str = "./setup.cfg",
    current_version: str = None,
    micro_release: bool = False,
):
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
    if str(out):
        return str(out).split("\n")[0]
    else:
        return None


def _update_release_version_for_sanic(
    current_version, new_version, config_file, generate_changelog
):
    config_parser = RawConfigParser()
    with open(config_file) as cfg:
        config_parser.read_file(cfg)
    config_parser.set("version", "current_version", new_version)

    version_files = config_parser.get("version", "files")
    current_version_line = config_parser.get(
        "version", "current_version_pattern"
    ).format(current_version=current_version)
    new_version_line = config_parser.get(
        "version", "new_version_pattern"
    ).format(new_version=new_version)

    for version_file in version_files.split(","):
        with open(version_file) as init_file:
            data = init_file.read()

        new_data = data.replace(current_version_line, new_version_line)
        with open(version_file, "w") as init_file:
            init_file.write(new_data)

    with open(config_file, "w") as config:
        config_parser.write(config)

    if generate_changelog:
        towncrier.__main(
            draft=False,
            directory=path.dirname(path.abspath(__file__)),
            project_name=None,
            project_version=new_version,
            project_date=None,
            answer_yes=True,
        )

    command = GIT_COMMANDS.get("commit_version_change")
    command[0] = command[0].format(
        new_version=new_version, current_version=current_version
    )
    _, err, ret = _run_shell_command(command)
    if int(ret) != 0:
        print(
            "Failed to Commit Version upgrade changes to Sanic: {}".format(
                err.decode("utf-8")
            )
        )
        sys.exit(1)


def _generate_change_log(current_version: str = None):
    global GIT_COMMANDS
    command = GIT_COMMANDS.get("get_change_log")
    command[0] = command[0].format(current_version=current_version)
    output, error, ret = _run_shell_command(command=command)
    if not str(output):
        print("Unable to Fetch Change log details to update the Release Note")
        sys.exit(1)

    commit_details = OrderedDict()
    commit_details["authors"] = {}
    commit_details["commits"] = []

    for line in str(output).split("\n"):
        commit, author, description = line.split(":::")
        if "GitHub" not in author:
            commit_details["authors"][author] = 1
        commit_details["commits"].append(" - ".join([commit, description]))

    return commit_details


def _generate_markdown_document(
    milestone, release_name, current_version, release_version
):
    global JINJA_RELEASE_NOTE_TEMPLATE
    release_name = release_name or release_version
    change_log = _generate_change_log(current_version=current_version)
    return JINJA_RELEASE_NOTE_TEMPLATE.render(
        release_name=release_name,
        milestone=milestone,
        changelogs=change_log["commits"],
        authors=change_log["authors"].keys(),
    )


def _tag_release(new_version, current_version, milestone, release_name, token):
    global GIT_COMMANDS
    global RELEASE_NOTE_UPDATE_URL
    for command_name in ["create_new_tag", "push_tag"]:
        command = GIT_COMMANDS.get(command_name)
        command[0] = command[0].format(
            new_version=new_version, current_version=current_version
        )
        out, error, ret = _run_shell_command(command=command)
        if int(ret) != 0:
            print("Failed to execute the command: {}".format(command[0]))
            sys.exit(1)

    change_log = _generate_markdown_document(
        milestone, release_name, current_version, new_version
    )

    body = {"name": release_name or new_version, "body": change_log}

    headers = {"content-type": "application/json"}

    response = patch(
        RELEASE_NOTE_UPDATE_URL.format(new_version=new_version, token=token),
        data=dumps(body),
        headers=headers,
    )
    response.raise_for_status()


def release(args: Namespace):
    current_tag = _get_current_tag()
    current_version = _fetch_current_version(args.config)
    if current_tag and current_version not in current_tag:
        print(
            "Tag mismatch between what's in git and what was provided by "
            "--current-version. Existing: {}, Give: {}".format(
                current_tag, current_version
            )
        )
        sys.exit(1)
    new_version = args.release_version or _get_new_version(
        args.config, current_version, args.micro_release
    )
    _update_release_version_for_sanic(
        current_version=current_version,
        new_version=new_version,
        config_file=args.config,
        generate_changelog=args.generate_changelog,
    )
    if args.tag_release:
        _tag_release(
            current_version=current_version,
            new_version=new_version,
            milestone=args.milestone,
            release_name=args.release_name,
            token=args.token,
        )


if __name__ == "__main__":
    cli = ArgumentParser(description="Sanic Release Manager")
    cli.add_argument(
        "--release-version",
        "-r",
        help="New Version to use for Release",
        default=_fetch_default_calendar_release_version(),
        required=False,
    )
    cli.add_argument(
        "--current-version",
        "-cv",
        help="Current Version to default in case if you don't want to "
        "use the version configuration files",
        default=None,
        required=False,
    )
    cli.add_argument(
        "--config",
        "-c",
        help="Configuration file used for release",
        default="./setup.cfg",
        required=False,
    )
    cli.add_argument(
        "--token",
        "-t",
        help="Git access token with necessary access to Huge Sanic Org",
        required=False,
    )
    cli.add_argument(
        "--milestone",
        "-ms",
        help="Git Release milestone information to include in relase note",
        required=False,
    )
    cli.add_argument(
        "--release-name",
        "-n",
        help="Release Name to use if any",
        required=False,
    )
    cli.add_argument(
        "--micro-release",
        "-m",
        help="Micro Release with patches only",
        default=False,
        action="store_true",
        required=False,
    )
    cli.add_argument(
        "--tag-release",
        help="Tag a new release for Sanic",
        default=False,
        action="store_true",
        required=False,
    )
    cli.add_argument(
        "--generate-changelog",
        help="Generate changelog for Sanic as part of release",
        default=False,
        action="store_true",
        required=False,
    )
    args = cli.parse_args()
    if args.tag_release:
        for key, value in {
            "--token/-t": args.token,
            "--milestone/-m": args.milestone,
        }.items():
            if not value:
                print(f"{key} is mandatory while using --tag-release")
                sys.exit(1)
    with Directory():
        release(args)
