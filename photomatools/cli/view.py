from argparse import ONE_OR_MORE, ArgumentParser, Namespace
from pathlib import Path

from colorama import Fore, Style

from ..model import MultimediaFile
from ..tools import preload, label
from ..utils import filter_relevant_exif
from . import Tool


class Diff(Tool):
    """
    compare metadata
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
        parser.add_argument("left", type=MultimediaFile, help="first file to compare")
        parser.add_argument("right", type=MultimediaFile, help="second file to compare")

    def run(self, args: Namespace):
        """
        process
        """
        # process
        left, right = args.left, args.right
        if args.quiet:
            print(f"{Fore.RED}--- {label(left)}{Fore.RESET}")
            print(f"{Fore.GREEN}+++ {label(right)}{Fore.RESET}")
        else:
            print(
                f"\n====================[{Fore.RED}{label(left)}{Fore.RESET}]====================",
                f"\n====================[{Fore.GREEN}{label(right)}{Fore.RESET}]====================",
            )
        width = max(map(len, left.metadata.keys() & right.metadata.keys()))
        self.print_property(
            "md5sum",
            left.md5,
            right.md5,
            quiet=args.quiet,
            verbose=args.verbose,
            width=width,
        )
        self.print_property(
            "event label",
            left.get_event_label(),
            right.get_event_label(),
            quiet=args.quiet,
            verbose=args.verbose,
            width=width,
        )
        for k in filter(
            filter_relevant_exif,
            sorted(set(left.metadata.keys()) & set(right.metadata.keys())),
        ):
            self.print_property(
                k,
                left[k],
                right[k],
                quiet=args.quiet,
                verbose=args.verbose,
                width=width,
            )

    def print_property(
        self,
        key: str,
        left: str,
        right: str,
        quiet: bool = False,
        verbose: bool = True,
        width: int = 0,
    ):
        """
        pretty print an exif metadata
        """
        if left == right == None:
            return True
        if quiet:
            if left != right:
                print(f"{Fore.RED}-{key}={left}{Fore.RESET}")
                print(f"{Fore.GREEN}+{key}={right}{Fore.RESET}")
        else:
            if width:
                if key.count(":") == 1:
                    prefix, suffix = key.split(":")
                    key = f"{Fore.BLUE}{prefix}{Fore.RESET}{suffix.rjust(width - len(prefix))}{Fore.RESET}"
                else:
                    key = key.rjust(width)
            if left == right:
                if verbose:
                    print(f"{key}: {Style.DIM}{left}{Style.RESET_ALL}")
                return True
            else:
                print(f"{key}: {Fore.RED}{left}{Fore.RESET}")
                print(f"{' ' * width}  {Fore.GREEN}{right}{Fore.RESET}")
        return False


class View(Tool):
    """
    view metadata
    """

    def configure_parser(self, parser: ArgumentParser):
        """
        configure the argument parser
        """
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
        # process
        for source, _ in preload(
            MultimediaFile.filter_map(args.files),
            lambda x: (x.metadata, x.md5),
            verbose=False,
        ):
            print(
                f"\n====================[{Fore.GREEN}{label(source)}{Fore.RESET}]===================="
            )
            width = max(map(len, source.metadata.keys()))
            self.print_property("md5sum", source.md5, width=width)
            self.print_property(
                "event label",
                source.get_event_label(),
                width=width,
            )
            for k in filter(
                filter_relevant_exif,
                sorted(set(source.metadata.keys())),
            ):
                if (
                    args.filter is None
                    or next(filter(lambda m: m.lower() in k.lower(), args.filter), None)
                    is not None
                ):
                    self.print_property(k, source[k], width=width)

    def print_property(
        self,
        key: str,
        left: str,
        width: int = 0,
    ):
        """
        pretty print an exif metadata
        """
        if width:
            if key.count(":") == 1:
                prefix, suffix = key.split(":")
                key = f"{Fore.BLUE}{prefix}{Fore.RESET}{suffix.rjust(width - len(prefix))}{Fore.RESET}"
            else:
                key = key.rjust(width)
        print(f"{key}: {Fore.YELLOW}{left}{Style.RESET_ALL}")
