import os

from werkzeug.utils import safe_join

_TEMP_EXTENSIONS = {"part", "ytdl", "tmp"}


def resolve_within(base_dir, filename):
    """Return an absolute path for filename confined to base_dir, or None.

    Rejects empty names, backslashes and null bytes up front — a media filename
    never contains them, and '\\' is a path separator only on Windows, so
    rejecting it keeps traversal blocked identically on Linux/Docker. safe_join
    then blocks absolute paths, drive letters and '..' traversal.
    """
    if not filename or "\\" in filename or "\x00" in filename:
        return None
    return safe_join(base_dir, filename)


def unique_name(directory, filename):
    """Return filename, or filename with a numeric suffix if it already exists."""
    candidate = filename
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(directory, candidate)):
        candidate = f"{base}_{counter}{ext}"
        counter += 1
    return candidate


def list_files(directory, extensions=None):
    """List non-hidden files in directory, optionally filtered by extension set."""
    if not os.path.isdir(directory):
        return []
    result = []
    for name in sorted(os.listdir(directory)):
        if name.startswith("."):
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext in _TEMP_EXTENSIONS:
            continue
        if extensions is not None and ext not in extensions:
            continue
        result.append(name)
    return result


def list_files_detailed(directory, extensions=None):
    """Like list_files, but each entry is a dict with name, size and mtime."""
    result = []
    for name in list_files(directory, extensions):
        try:
            stat = os.stat(os.path.join(directory, name))
        except OSError:
            continue
        result.append({"name": name, "size": stat.st_size, "mtime": stat.st_mtime})
    return result
