Photo Management Tools
======================

A collection of command line tools to manages photos (and videos), especially photos from mobiles phones.

Available tool:
- `pmt view` can list metadata (like *EXIF*) from photos/videos, can also compare metadata from two files
- `pmt rename` can rename photos/videos given prefixing the filename with the date
- `pmt dispatch` to move files in subfolders if a subfolder matches the begining of the filename (useful to organise photos/videos by year)
- `pmt uniq` to rename files with their fingerprint (md5, sha1 ...)
- `pmt dedup` to find duplicate files (either by comparing md5sum or exif metadata)
- `pmt borg` to extract new files from a *borg* archive, ie. all files not present in the previous *borg* archive


