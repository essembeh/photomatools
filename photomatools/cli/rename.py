import argparse
from argparse import ArgumentParser, Namespace
from pathlib import Path

from colorama import Fore, Style

from ..model import MultimediaFile
from ..tools import find_next_file_increment, label, preload
from ..utils import visit
from . import Tool


class Rename(Tool):
    """
    rename files with the creation date
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        parser.add_argument(
            "-j", "--jobs", type=int, default=4, help="number of parallel threads"
        )
        parser.add_argument(
            "-c",
            "--check",
            action="store_true",
            help="check photo already exists in output folder",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=Path.cwd(),
            help="rename files and move them to a specific folder, default is current directory",
        )
        parser.add_argument(
            "files", nargs=argparse.ONE_OR_MORE, type=Path, help="files to rename"
        )

    def run(self, args: Namespace):
        """
        process
        """
        out = 0
        folder = args.output

        # sort input files by event
        input_files = {}
        for item, event in preload(
            MultimediaFile.filter_map(
                filter(lambda f: f.parent != folder, visit(args.files, recursive=True))
            ),
            lambda x: x.get_event_label(),
            workers=args.jobs,
        ):
            if event is None:
                print(f"Cannot retrieve date in metadata: {label(item)}")
            else:
                if event not in input_files:
                    input_files[event] = []
                input_files[event].append(item)

        # process input files
        for event in sorted(input_files.keys()):
            items = input_files[event]
            # get all candidates in the target folder
            candidates = []
            if args.check:
                candidates += list(
                    MultimediaFile.filter_map(
                        filter(lambda f: f.name.startswith(event), folder.iterdir())
                    )
                )
            # process sorted photos of the event
            for item in sorted(items):
                try:
                    # check photo already exits
                    dupp = next(
                        filter(
                            lambda p: p.size == item.size and p.md5 == item.md5,
                            candidates,
                        ),
                        None,
                    )
                    if dupp is not None and dupp != item:
                        raise ValueError(f"Dupplicate of {dupp}")

                    dest = find_next_file_increment(
                        item.file, f"{event}_", item.ext, folder=folder
                    )
                    if item == dest:
                        # check source is already named
                        print(f"Skip {label(item)}: already named{Style.RESET_ALL}")
                    elif args.dryrun:
                        # check dryrun mode before renaming file
                        print(
                            f"Rename {label(item)} to {label(dest)} {Fore.CYAN}(dryrun){Style.RESET_ALL}"
                        )
                    else:
                        dest = find_next_file_increment(
                            item.file, f"{event}_", item.ext, folder=folder
                        )
                        print(f"Rename {label(item)} to {label(dest)}")
                        item.move(dest)

                    # if check mode, remember the new file
                    if args.check:
                        candidates.append(item)
                except BaseException as ex:  # pylint: disable=broad-except
                    print(
                        f"{Fore.RED}Cannot rename {item}: {Style.BRIGHT}{ex}{Style.RESET_ALL}"
                    )
                    out = 1

        return out
