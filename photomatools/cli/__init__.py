"""
package cli
"""

import sys
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

from colorama import init

from .. import __version__

init()


class Tool(ABC):
    """
    abstract class for tools
    """

    @property
    def name(self):
        """
        use classname to name the tool
        """
        return self.__class__.__name__.lower()

    @property
    def description(self):
        """
        use python doc for help description
        """
        return self.__doc__

    @classmethod
    def main(cls):
        """
        standalone main
        """
        tool = cls()
        parser = default_argument_paser(tool.name, description=tool.__doc__)
        tool.configure_parser(parser)
        sys.exit(tool.run(parser.parse_args()))

    @abstractmethod
    def configure_parser(self, parser: ArgumentParser):
        """
        configure parser
        """

    @abstractmethod
    def run(self, args: Namespace):
        """
        execute
        """


def default_argument_paser(name: str, description: str = None):
    """
    create a new parser with common options
    """
    parser = ArgumentParser(name, description=description)
    parser.add_argument("--version", action="version", version=f"version {__version__}")
    parser.add_argument(
        "-n",
        "--dryrun",
        action="store_true",
        help="dryrun mode, do not change anything",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print more information",
    )
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="print less information",
    )
    parser.add_argument(
        "-j", "--jobs", type=int, default=4, help="number of parallel threads"
    )
    return parser
