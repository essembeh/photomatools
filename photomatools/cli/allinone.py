import sys
from traceback import print_stack

from colorama import Fore, Style

from . import Tool, default_argument_paser
from .borg import Borg
from .dedup import Dedup
from .dispatch import Dispatch
from .rename import Rename
from .uniq import Uniq
from .view import View


def main():
    """
    all-in-one entry point
    """
    parser = default_argument_paser("pmt")
    parser.set_defaults(handler=None)

    subparsers = parser.add_subparsers(help="sub-command help")
    for tool_cls in (Rename, Uniq, View, Dispatch, Borg, Dedup):
        tool = tool_cls()
        subparser = subparsers.add_parser(tool.name, help=tool.description)
        subparser.set_defaults(handler=tool)
        tool.configure_parser(subparser)

    args = parser.parse_args()
    if not isinstance(args.handler, Tool):
        parser.print_help()
        sys.exit(2)
    try:
        ret = args.handler.run(args)
        sys.exit(ret if isinstance(ret, int) else 0)
    except SystemExit:
        raise
    except BaseException as e:  # pylint: disable=broad-except,invalid-name
        print(f"{Fore.RED}ERROR: {e}")
        if args.verbose:
            print_stack(e)
        print(Style.RESET_ALL, end="")
        sys.exit(1)
