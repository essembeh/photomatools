import subprocess
from dataclasses import dataclass
from datetime import datetime
from functools import total_ordering
from json import loads
from os import getenv
from pathlib import Path

from cached_property import cached_property


def borg_cmd_to_json(*cmd, multiple: bool = False):
    """
    run a borg command and parse json result
    """
    command = [getenv("BORG_BIN", "borg")] + list(map(str, cmd))
    process = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        check=True,
        capture_output=True,
    )
    return (
        [loads(line) for line in process.stdout.decode().splitlines()]
        if multiple
        else loads(process.stdout)
    )


@dataclass
class BorgRepository:
    folder: Path

    @cached_property
    def borg_info(self):
        return borg_cmd_to_json("info", self.folder, "--json")

    @cached_property
    def borg_list(self):
        return borg_cmd_to_json("list", self.folder, "--json")

    @cached_property
    def archives(self):
        return tuple(sorted(BorgArchive(self, a) for a in self.borg_list["archives"]))

    @cached_property
    def latest_archive(self):
        return self.archives[-1]

    @cached_property
    def borg_name(self):
        return f"{self.folder.resolve()}"

    def __getitem__(self, name):
        for a in self.archives:
            if a.name == name:
                return a
        raise ValueError(f"Cannot find archive {name}")


@total_ordering
@dataclass
class BorgArchive:
    repo: BorgRepository
    description: dict

    @cached_property
    def borg_list(self):
        return borg_cmd_to_json(
            "list",
            self.borg_name,
            "--json-lines",
            multiple=True,
        )

    @cached_property
    def uid(self):
        return self.description["id"]

    @cached_property
    def name(self):
        return self.description["name"]

    @cached_property
    def date(self):
        return datetime.fromisoformat(self.description["time"])

    @cached_property
    def files(self):
        return tuple(BorgFile(self, f) for f in self.borg_list)

    @cached_property
    def borg_name(self):
        return f"{self.repo.borg_name}::{self.name}"

    def __str__(self):
        return f"{self.repo.folder}::{self.name} ({self.date})"

    def __eq__(self, other):
        if not isinstance(other, BorgArchive):
            return NotImplemented
        return self.uid == other.uid

    def __lt__(self, other):
        if not isinstance(other, BorgArchive):
            return NotImplemented
        return self.date < other.date


@dataclass
class BorgFile:
    archive: BorgArchive
    description: dict

    @cached_property
    def path(self):
        return self.description["path"]

    @cached_property
    def size(self):
        return int(self.description["size"])

    def is_dir(self):
        return self.description["type"] == "d"

    def __eq__(self, other):
        if not isinstance(other, BorgFile):
            return NotImplemented
        return self.path == other.path and self.size == other.size
