import argparse
from argparse import ArgumentParser, Namespace
from operator import itemgetter
from pathlib import Path
from typing import Set

from photomatools.utils import sizeof_fmt

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
            "-s",
            "--strategy",
            choices=("md5", "exif"),
            default="md5",
            help="strategy to find duplicates, default: md5",
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
        def get_data(file: MultimediaFile):
            if args.strategy == "md5":
                return file.size
            if args.strategy == "exif":
                return file.get_event_label()
            raise ValueError()

        known_files = iter_to_map(
            preload(
                MultimediaFile.filter_map(visit(args.files, recursive=True)),
                get_data,
                workers=args.jobs,
            ),
            itemgetter(1),
            value_fnc=itemgetter(0),
        )
        for files in known_files.values():
            files = set(files)
            # if multiple files have the same size
            if len(files) > 1:
                if args.strategy == "md5":
                    self._find_dupplicates_md5(set(files))
                elif args.strategy == "exif":
                    self._find_dupplicates_exif(set(files))

    def _find_dupplicates_exif(self, files: Set[MultimediaFile], min: float = 0.9):
        files = sorted(files)
        while len(files) > 0:
            file, others = files[0], files[1:]
            duplicates = list(
                filter(
                    lambda kv: kv[1] >= min,
                    [(o, file.check_dupplicate(o)) for o in others],
                )
            )
            if len(duplicates) > 0:
                print("Potential duplicate found:")
                print(f"  {label(file)} [{sizeof_fmt(file.size)}]:")
                for dup, value in duplicates:
                    print(
                        f"  {label(dup)} [{sizeof_fmt(dup.size)}] ({int(value*100)}%)"
                    )
            files.remove(file)

    def _find_dupplicates_md5(self, files: Set[MultimediaFile]):
        # build the md5 to files dict
        md5_map = iter_to_map(set(files), lambda f: f.md5)
        for md5, duplicates in md5_map.items():
            # check if multiple files have the same md5
            if len(duplicates) > 1:
                print(f"Duplicate files with md5sum {md5}:")
                for dup in sorted(duplicates, key=lambda x: x.file):
                    print(f"  {label(dup)}")
