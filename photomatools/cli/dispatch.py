import argparse
import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path

from colorama import Fore

from ..tools import label
from ..utils import visit
from . import Tool


class Dispatch(Tool):
    """
    auto move/link/copy files in folder named with a prefix of the file
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-d",
            "--directory",
            action="store_true",
            help="also dispach directories, by default they are ignored",
        )
        group.add_argument(
            "-r",
            "--recursive",
            action="store_true",
            help="process content of directory given in arguments",
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-l",
            "--link",
            dest="operation",
            action="store_const",
            const=self.link,
            default=self.move,
            help="do symbolic links instead of moving files",
        )
        group.add_argument(
            "-c",
            "--copy",
            dest="operation",
            action="store_const",
            const=self.copy,
            help="copy files instead of moving them",
        )
        parser.add_argument(
            "-o",
            "--output",
            metavar="FOLDER",
            default=Path.cwd(),
            type=Path,
            help="destination folder",
        )
        parser.add_argument(
            "files",
            metavar="FILE",
            nargs=argparse.ONE_OR_MORE,
            type=Path,
            help="files to move/copy/link",
        )

    def run(self, args: Namespace):
        """
        process
        """

        folder = args.output
        if not folder.is_dir():
            raise ValueError(f"Invalid destination directory: {folder}")

        subdirs = tuple(filter(Path.is_dir, folder.iterdir()))

        if len(subdirs) == 0:
            raise ValueError(f"Cannot find any folder in {folder}")

        for source in visit(
            args.files, recursive=args.recursive, yield_dir=args.directory
        ):
            try:
                candidates = [d for d in subdirs if source.name.startswith(d.name)]
                if len(candidates) == 0:
                    raise ValueError(f"No matching subfolder in {folder}")
                if len(candidates) > 1:
                    raise ValueError(
                        f"Too many matching subfolders: {', '.join(map(str, candidates))}"
                    )
                dest = candidates[0] / source.name
                if source.resolve() == dest.resolve():
                    print(f"Skip '{label(source)}': already in {label(dest.parent)}")
                elif dest.exists():
                    raise ValueError(f"'{dest}' already exists")
                else:
                    print(
                        f"{args.operation.__name__} '{label(source)}' -> '{label(dest)}' {' (dryrun)' if args.dryrun else ''}"
                    )
                    if not args.dryrun:
                        args.operation(source, dest)
            except BaseException as e:  # pylint: disable=broad-except,invalid-name
                print(f"{Fore.RED}Cannot process {source}: {e}{Fore.RESET}")

    def move(self, source, dest):
        """
        move file
        """
        shutil.move(source, dest)

    def copy(self, source, dest):
        """
        copy file
        """
        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            shutil.copy(source, dest)

    def link(self, source, dest):
        """
        link file
        """
        dest.symlink_to(source.resolve())
