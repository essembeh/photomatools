import re
import subprocess
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from os import getenv
from pathlib import Path

from ..borg import BorgArchive, BorgFile, BorgRepository
from ..utils import sizeof_fmt
from . import Tool


class Borg(Tool):
    """
    find new files in a borg archive
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        parser.add_argument(
            "--version", action="version", version="version {0}".format("0.1.0")
        )
        parser.add_argument(
            "-a",
            "--archive",
            metavar="NAME",
            help="use this archive instead of the latest",
        )
        parser.add_argument(
            "-t",
            "--test",
            action="store_true",
            help="try an interactive borg info first",
        )
        parser.add_argument(
            "-i",
            "--include",
            metavar="PATTERN",
            dest="include_patterns",
            type=re.compile,
            action="append",
            help="regex pattern",
        )
        parser.add_argument(
            "-I",
            "--Include",
            metavar="PATTERN",
            dest="include_patterns",
            type=lambda x: re.compile(x, re.IGNORECASE),
            action="append",
            help="like -i but ignore case",
        )
        parser.add_argument(
            "-o",
            "--output-dir",
            metavar="FOLDER",
            type=Path,
            help="extract new files to this folder",
        )
        parser.add_argument("repo", type=Path)

    def run(self, args: Namespace):
        """
        process
        """
        if args.test:
            subprocess.run(["borg", "info", str(args.repo)], check=True)

        repo = BorgRepository(args.repo)
        archive = repo.latest_archive if args.archive is None else repo[args.archive]

        previous_archive = next(
            iter(sorted(filter(archive.__gt__, repo.archives), reverse=True)), None
        )
        print("Searching new files")
        print(f"     in {archive}")
        print(f"  since {previous_archive}")

        filefilter = FileFilter(previous_archive, args.include_patterns)
        newfiles = tuple(filter(filefilter.accept, archive.files))
        if len(newfiles) == 0:
            print(f"No new file in {archive}")
        else:
            total_size = 0
            for f in newfiles:
                print(f"    {f.path}  [{sizeof_fmt(f.size)}]")
                total_size += f.size
            print(
                f"Found {len(newfiles)} new file{'s' if len(newfiles)>1 else ''}, {sizeof_fmt(total_size)}"
            )

            if args.output_dir:
                if not args.output_dir.exists():
                    args.output_dir.mkdir(parents=True)
                if not args.output_dir.is_dir():
                    raise ValueError(f"Invalid folder {args.output_dir}")

                print(
                    f"Extract {len(newfiles)} new file{'s' if len(newfiles)>1 else ''} to {args.output_dir}"
                )

                subprocess.run(
                    [getenv("BORG_BIN", "borg"), "extract", "--list", archive.borg_name]
                    + [f.path for f in newfiles],
                    cwd=args.output_dir,
                    check=True,
                )


@dataclass
class FileFilter:
    other_archive: BorgArchive
    patterns: list

    def __match_pattern(self, filepath: str):
        return (
            self.patterns is None
            or len(self.patterns) == 0
            or next(filter(lambda p: p.match(filepath), self.patterns), None)
            is not None
        )

    def accept(self, bfile: BorgFile):
        return (
            not bfile.is_dir()
            and self.__match_pattern(bfile.path)
            and (self.other_archive is None or bfile not in self.other_archive.files)
        )
