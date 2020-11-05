import argparse
import hashlib
from argparse import ArgumentParser, Namespace
from pathlib import Path

from colorama import Fore, Style

from ..model import MultimediaFile
from ..tools import preload, label
from . import Tool


class Uniq(Tool):
    """
    rename files with their fingerprint
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        parser.add_argument(
            "-j", "--jobs", type=int, default=4, help="number of parallel threads"
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--md5",
            dest="hash_fnc",
            action="store_const",
            const=hashlib.md5,
            default=hashlib.md5,
            help="use md5 for fingerprint",
        )
        group.add_argument(
            "--sha1",
            dest="hash_fnc",
            action="store_const",
            const=hashlib.sha1,
            help="use sha1 for fingerprint",
        )
        group.add_argument(
            "--sha256",
            dest="hash_fnc",
            action="store_const",
            const=hashlib.sha256,
            help="use sha256 for fingerprint",
        )
        group.add_argument(
            "--sha384",
            dest="hash_fnc",
            action="store_const",
            const=hashlib.sha384,
            help="use sha384 for fingerprint",
        )
        group.add_argument(
            "--sha512",
            dest="hash_fnc",
            action="store_const",
            const=hashlib.sha512,
            help="use sha512 for fingerprint",
        )
        parser.add_argument(
            "-l",
            "--len",
            dest="length",
            type=int,
            metavar="N",
            help="truncate fingerprint to N chars",
        )
        parser.add_argument(
            "-e", "--ext", action="store_true", help="append file extension"
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="folder",
            type=Path,
            help="rename files in specific folder",
        )
        parser.add_argument(
            "files", nargs=argparse.ONE_OR_MORE, type=Path, help="files to rename"
        )
        return parser

    def run(self, args: Namespace):
        """
        process
        """
        for source, filename in preload(
            MultimediaFile.filter_map(args.files),
            lambda x: x.fingerprint(args.hash_fnc),
            workers=args.jobs,
        ):
            if filename is None:
                print(
                    f"{Fore.RED}Cannot compute fingerprint for '{source}'{Style.RESET_ALL}"
                )
            else:
                if args.length:
                    filename = filename[: args.length]
                if args.ext:
                    filename += source.ext
                target = (args.folder or source.file.parent) / filename

                if source.file == target:
                    print(
                        f"'Skip {label(source)}': {Fore.YELLOW}already named{Style.RESET_ALL}"
                    )
                elif target.exists():
                    print(
                        f"Cannot rename '{label(source)}': '{label(target)}' {Fore.RED}already exists{Style.RESET_ALL}"
                    )
                elif args.dryrun:
                    print(
                        f"Rename '{label(source)}' to '{label(target)}' {Fore.CYAN}(dryrun){Style.RESET_ALL}"
                    )
                else:
                    print(
                        f"Rename '{label(source)}' to '{label(target)}'{Style.RESET_ALL}"
                    )
                    source.move(target)
