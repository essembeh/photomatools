import concurrent
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Iterable

from colorama import Cursor, Fore, Style

from .model import MultimediaFile
from .utils import print_temp_message


def find_next_file_increment(
    source: Path,
    prefix: str,
    suffix: str,
    folder: Path = None,
    start: int = 1,
    digits: int = 3,
) -> Path:
    """
    find the next increment to name a file xxx<INT>yyy
    """
    if folder is None:
        folder = source.parent
    for i in range(start, pow(10, digits)):
        i = str(i).zfill(digits)
        out = folder / f"{prefix}{i}{suffix}"
        if not out.exists() or out.resolve() == source.resolve():
            return out
    raise ValueError(f"No possible increment to rename {source}")


def label(item):
    """
    colorize item given its type
    """
    if isinstance(item, MultimediaFile):
        # return f"{Fore.YELLOW}{Style.BRIGHT}{item}{Style.RESET_ALL}"
        return label(item.file)
    if isinstance(item, Path):
        if item.is_dir():
            return f"{Fore.BLUE}{Style.BRIGHT}{item}{Style.RESET_ALL}"
        return f"{Style.BRIGHT}{Fore.BLUE}{item.parent}/{Fore.MAGENTA}{item.name}{Style.RESET_ALL}"
    return str(item)


def preload(
    files: Iterable[MultimediaFile],
    func: callable,
    workers: int = 8,
    verbose: bool = True,
) -> Dict:
    """
    load metadata in parallel and yield element when done
    """

    def load(item: MultimediaFile):
        if verbose:
            print_temp_message(f"Analyze {item.file.name}")
        return func(item)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        jobs = {executor.submit(load, f): f for f in files}
        for future in concurrent.futures.as_completed(jobs):
            item, result = jobs[future], None
            if verbose:
                message = f"Analyze {item.file.name}"
                print(message, Cursor.BACK(len(message)), sep="", end="", flush=True)
            try:
                result = future.result()
            except BaseException:  # pylint: disable=broad-except
                pass
            yield item, result
