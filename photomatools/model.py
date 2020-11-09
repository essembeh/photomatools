import hashlib
import shutil
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Iterable

from cached_property import cached_property

from .utils import auto_datetime, compute_fingerprint, read_metadata


def comp(a, b, func: callable = None, opposite: bool = False):
    def ret(c):
        return (c * -1) if opposite else c

    if a == b:
        return 0
    if a is None:
        return ret(-1)
    if b is None:
        return ret(1)
    if func is not None:
        a, b = func(a), func(b)
    if a < b:
        return ret(-1)
    if a > b:
        return ret(1)
    return 0


@dataclass
@total_ordering
class MultimediaFile:
    file: Path

    def __post_init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        if isinstance(self.file, str):
            self.file = Path(self.file)
        elif not isinstance(self.file, Path):
            raise ValueError(f"Invalid argument: {self.file}")
        if not self.file.is_file():
            raise ValueError(f"Invalid file {self.file}")

    @classmethod
    def filter_map(cls, iterable: Iterable[Path]):
        return map(MultimediaFile, filter(Path.is_file, iterable))

    def __hash__(self):
        return hash(self.file.resolve())

    def __str__(self):
        return f"{self.file}"

    def __getitem__(self, key: str):
        return self._get_metadata(key)

    def __contains__(self, key: str):
        return self[key] is not None

    def __eq__(self, other):
        if not isinstance(other, (MultimediaFile, Path)):
            return NotImplemented
        if isinstance(other, MultimediaFile):
            other = other.file
        return self.file.resolve() == other.resolve()

    def __lt__(self, other):
        if not isinstance(other, MultimediaFile):
            return NotImplemented
        # older first
        out = comp(
            self.create_date, other.create_date, lambda d: d.replace(tzinfo=None)
        )
        if out == 0:
            # bigger first
            out = comp(self.size, other.size, opposite=True)
            if out == 0:
                # compare files
                out = comp(self.file, other.file)
        return out == -1

    @property
    def size(self):
        return self.file.stat().st_size

    @property
    def ext(self):
        out = self["File:FileTypeExtension"]
        if out:
            return f".{out}"
        return self.file.suffix.lower()

    @property
    def dimensions(self):
        return (int(self["EXIF:ExifImageWidth"]), int(self["EXIF:ExifImageHeight"]))

    @property
    def mime(self):
        return self["File:MIMEType"]

    @cached_property
    def metadata(self):
        return read_metadata(self.file)

    def iter_key_value(self, prefix: str = None):
        for k, v in self.metadata.items():
            if prefix is None or k.lower().startswith(f"{prefix.lower()}:"):
                yield k, v

    @cached_property
    def create_date(self):
        keys = tuple()
        if self.is_photo():
            keys = (
                "Composite:SubSecDateTimeOriginal",
                "Composite:SubSecCreateDate",
                "EXIF:DateTimeOriginal",
                "EXIF:CreateDate",
            )
        elif self.is_video():
            keys = (
                "QuickTime:CreationDate",
                "QuickTime:CreateDate",
                "QuickTime:MediaCreateDate",
                "QuickTime:CreationDate",
            )

        return next(
            filter(
                None,
                map(
                    auto_datetime,
                    map(self._get_metadata, keys),
                ),
            ),
            None,
        )

    @cached_property
    def md5(self):
        return self.fingerprint(hashlib.md5)

    @cached_property
    def sha1(self):
        return self.fingerprint(hashlib.sha1)

    def fingerprint(self, func: callable = hashlib.md5):
        return compute_fingerprint(self.file, func)

    def check_dupplicate(self, other):
        if self == other:
            return 1
        if self.create_date != other.create_date:
            return 0
        if self.create_date and self.create_date.microsecond:
            return 1
        idem, diff = 0, 0
        for k, v in self.metadata.items():
            v2 = other[k]
            if v2 is not None:
                if v == v2:
                    idem += 1
                else:
                    diff += 1
        return idem / (idem + diff) if idem + diff else 0

    def __clean_cached_properties(self, keys: tuple = ("metadata",)):
        for x in keys:
            if x in self.__dict__:
                del self.__dict__[x]

    def is_photo(self):
        return self.mime.startswith("image/")

    def is_video(self):
        return self.mime.startswith("video/")

    def _get_metadata(self, key, default: str = None):
        for k, v in self.metadata.items():
            if k.lower() == key.lower():
                return v
        return default

    def get_event_label(self, fmt: str = r"%Y-%m-%d_%Hh%Mm%Ss"):
        dt = self.create_date
        return dt.strftime(fmt) if dt else None

    def move(self, dest: Path, force: bool = False):
        if dest.exists() and not force:
            raise ValueError(f"{dest} already exists")
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)
        self.file = shutil.move(self.file, dest)
        self.__clean_cached_properties()
