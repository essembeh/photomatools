import argparse
from argparse import ArgumentParser, Namespace
from pathlib import Path

from ..model import MultimediaFile
from ..tools import label, preload
from ..utils import iter_to_map, visit
from . import Tool


class Dedup(Tool):
    """
    find duplicates files
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        parser.add_argument(
            "-j", "--jobs", type=int, default=4, help="number of parallel threads"
        )
        parser.add_argument(
            "files",
            nargs=argparse.ONE_OR_MORE,
            type=Path,
            help="files/folders to check",
        )

    def run(self, args: Namespace):
        """
        process
        """
        # keep files in a dict by size
        known_files = iter_to_map(
            preload(
                MultimediaFile.filter_map(visit(args.files, recursive=True)),
                lambda x: x.size,
                workers=args.jobs,
            ),
            lambda kv: kv[1],
            value_fnc=lambda kv: kv[0],
        )
        for files in known_files.values():
            # if multiple files have the same size
            if len(files) > 1:
                # build the md5 to files dict
                md5_map = iter_to_map(set(files), lambda f: f.md5)
                for md5, duplicates in md5_map.items():
                    # check if multiple files have the same md5
                    if len(duplicates) > 1:
                        print(f"Duplicate files with md5sum {md5}:")
                        for dup in sorted(duplicates, key=lambda x: x.file):
                            print(f"  {label(dup)}")
