from argparse import ONE_OR_MORE, ArgumentParser, Namespace
from pathlib import Path

from colorama import Fore, Style

from ..model import MultimediaFile
from ..tools import preload, label
from ..utils import filter_relevant_exif
from . import Tool


class View(Tool):
    """
    view/compare metadata
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        parser.add_argument(
            "--diff", action="store_true", help="compare two files metadata"
        )
        parser.add_argument(
            "-f", "--filter", action="append", help="filter metadata with motif"
        )
        parser.add_argument(
            "files", type=Path, nargs=ONE_OR_MORE, help="files to proceed"
        )

    def run(self, args: Namespace):
        """
        process
        """
        out = 0
        # process
        if args.diff:
            if len(args.files) != 2:
                print(
                    f"{Fore.RED}You must give only two file in --diff mode{Fore.RESET}"
                )
                out = 1
            else:
                left, right = map(MultimediaFile, args.files)
                print(
                    f"\n====================[{Fore.RED}{label(left)}{Fore.RESET}]====================",
                    f"\n====================[{Fore.GREEN}{label(right)}{Fore.RESET}]====================",
                )
                width = max(map(len, left.metadata.keys() & right.metadata.keys()))
                self.print_property(
                    "md5sum", left.md5, right.md5, verbose=args.verbose, width=width
                )
                self.print_property(
                    "event label",
                    left.get_event_label(),
                    right.get_event_label(),
                    width=width,
                )
                for k in filter(
                    filter_relevant_exif,
                    sorted(set(left.metadata.keys()) & set(right.metadata.keys())),
                ):
                    self.print_property(
                        k, left[k], right[k], verbose=args.verbose, width=width
                    )
                out = 0 if left.check_dupplicate(right) == 1 else 1
        else:
            for source, _ in preload(
                MultimediaFile.filter_map(args.files),
                lambda x: (x.metadata, x.md5),
                verbose=False,
            ):
                print(
                    f"\n====================[{Fore.GREEN}{label(source)}{Fore.RESET}]===================="
                )
                width = max(map(len, source.metadata.keys()))
                self.print_property("md5sum", source.md5, single=True, width=width)
                self.print_property(
                    "event label",
                    source.get_event_label(),
                    single=True,
                    width=width,
                )
                for k in filter(
                    filter_relevant_exif,
                    sorted(set(source.metadata.keys())),
                ):
                    if (
                        args.filter is None
                        or next(
                            filter(lambda m: m.lower() in k.lower(), args.filter), None
                        )
                        is not None
                    ):
                        self.print_property(k, source[k], single=True, width=width)
        return out

    def print_property(
        self,
        key: str,
        left: str,
        right: str = None,
        verbose: bool = True,
        width: int = 0,
        single: bool = False,
    ):
        """
        pretty print an exif metadata
        """
        if left == right == None:
            return True
        if width:
            if key.count(":") == 1:
                prefix, suffix = key.split(":")
                key = f"{Fore.BLUE}{prefix}{Fore.RESET}{suffix.rjust(width - len(prefix))}{Fore.RESET}"
            else:
                key = key.rjust(width)
        if single:
            print(f"{key}: {Fore.YELLOW}{left}{Style.RESET_ALL}")
        elif left == right:
            if verbose:
                print(f"{key}: {Style.DIM}{left}{Style.RESET_ALL}")
            return True
        else:
            print(f"{key}: {Fore.RED}{left}{Fore.RESET}")
            print(f"{' ' * width}  {Fore.GREEN}{right}{Fore.RESET}")
        return False
