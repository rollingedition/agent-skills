"""Every line of the examples' requirements file is a comment, a blank line, the one reviewed option, or an exact name==version pin, so a version cannot move under the book.

The point rests on the refused counts being zero. A line is judged on its exact text: a wildcard, marker, URL, extra, include, index or hash line is refused, and so is a leading or trailing space on a requirement. The file does not carry hashes; the prose explains how pip and uv would check them, and this example runs neither.
"""
import lib  # lib first: threads and seeds are fixed before anything else loads

import json
from pathlib import Path

from lib import pinning

# The runner copies JSON data, not examples/requirements.txt, so this reads the same text from a JSON copy in the data
# folder. The copy's "source" field names the original; the two must stay equal (the note's Requests say so).
LOCKFILE = Path(__file__).resolve().parent / "data" / "third-party" / "requirements.json"


def main():
    counts = pinning.lockfile_verdicts(json.loads(LOCKFILE.read_text(encoding="utf-8"))["text"])
    print(f"comment and blank lines skipped: {counts['skip']}")
    print(f"exact == pins: {counts['pinned']}")
    print(f"refused requirement lines: {counts['refused']}")
    print(f"allowed option lines: {counts['option allowed']}")
    print(f"refused option lines: {counts['option refused']}")
    print(f"hash options: {counts['hash']}")
    assert counts["refused"] == 0 and counts["option refused"] == 0, "every line must be an exact pin or the one option"


if __name__ == "__main__":
    main()
