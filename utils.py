import os

from werkzeug.utils import safe_join

_TEMP_EXTENSIONS = {"part", "ytdl", "tmp"}


def resolve_within(base_dir, filename):
    """Return an absolute path for filename confined to base_dir, or None.

    safe_join rejects absolute paths, drive letters, and any '..'/backslash
    traversal, so a None result means the input tried to escape base_dir.
    """
    if not filename:
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
