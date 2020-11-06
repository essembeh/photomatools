import collections
import re
from datetime import datetime
from json import loads
from pathlib import Path
from subprocess import check_output
from typing import Iterable

from colorama import Cursor
from colorama.ansi import clear_line


DATE_PATTERN = r"^(2[0-9]{3}):([0-9]{2}):([0-9]{2}) "


def sizeof_fmt(num: float, suffix="B"):
    """
    simply display a human readable size
    """
    for unit in ("", "K", "M", "G"):
        if abs(num) < 1024:
            return f"{num:0.1f} {unit}{suffix}"
        num /= 1024.0
    raise ValueError()


def filter_relevant_exif(key: str):
    """
    filter non relevant exif keys for comparison
    """
    for prefix in ("ExifTool:",):  # depends of the tool version
        if key.startswith(prefix):
            return False
    return key not in (
        "EXIF:ThumbnailImage",  # binary content
        "EXIF:ThumbnailLength",  # depends on bin content
        "SourceFile",  # the path of the file itself
        "File:FileAccessDate",  # depends on filesystem
        "File:FileModifyDate",  # depends on filesystem
        "File:FileName",  # filename, equivalent to SourceFile
        "File:ImageHeight",  # dupplicate with Exif resolution
        "File:ImageWidth",  # idem
    )


def compute_fingerprint(file: Path, func=callable):
    """
    compute fingerprint given the algo function (sha1, md5 ...)
    """
    file = file.resolve()
    algo = func()
    with file.open("rb") as fp:
        for chunk in iter(lambda: fp.read(4096), b""):
            algo.update(chunk)
    return algo.hexdigest()


def read_metadata(file: Path):
    """
    read metada from the file using exiftool
    """
    if not file.exists():
        raise IOError(f"Cannot find {file}")
    payload = check_output(["exiftool", "-G", "-j", str(file)])
    payload = loads(payload)
    assert isinstance(payload, list)
    assert len(payload) == 1
    return payload[0]


def auto_datetime(text: str):
    """
    try to detect date format
    """
    if isinstance(text, str):
        # exiftool date are not datetime compatible
        text = re.sub(DATE_PATTERN, r"\1-\2-\3 ", text, count=1)
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            # silent error
            pass


def visit(
    item,
    recursive: bool = False,
    yield_dir: bool = False,
    filter_fnc: callable = None,
):
    """
    recursice folder visitor
    """
    if isinstance(item, collections.Iterable):
        # test if iterable
        for subfolder in item:
            yield from visit(
                subfolder,
                recursive=recursive,
                yield_dir=yield_dir,
                filter_fnc=filter_fnc,
            )
    elif isinstance(item, Path):
        if item.exists():
            # yield current item
            if (yield_dir or not item.is_dir()) and (
                filter_fnc is None or filter_fnc(item)
            ):
                yield item
        if item.is_dir():
            # yield children in case of folder
            for child in item.iterdir():
                yield from visit(
                    child,
                    recursive=recursive,
                    yield_dir=yield_dir,
                    filter_fnc=filter_fnc,
                )


def print_temp_message(msg: str):
    """
    print a message and reset the cursor to the begining of the line
    """
    print(clear_line(), msg, Cursor.BACK(len(msg)), sep="", end="", flush=True)


def iter_to_map(items: Iterable, key_fnc: callable, value_fnc: callable = None):
    """
    transform items into a dict
    """
    out = {}
    for item in items:
        key = key_fnc(item)
        if key is None:
            # skip null keys
            continue
        if key not in out:
            out[key] = []
        out[key].append(value_fnc(item) if value_fnc else item)
    return out