"""Compares three pairs of sablefile answers with an exact match and with difflib's ratio(), a score from 0 to 1.

Each pair is a reference and a reply written for this example, not a recorded reply: two file names, a flag with one
wrong letter, and a long answer that leaves out its folder sentence. ratio() is printed with the reference first and with
the reply first, because the documentation says the argument order can change the score. With the reference first, the
long reply is the second sequence and is 200 characters or more, so the autojunk heuristic applies to it; the long answer
is also scored with autojunk turned off."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from difflib import SequenceMatcher

FOLDERS = " Folders are created only with --apply, because a plain sync writes nothing."
PLAN = " The plan lines start with create, update or unchanged, and the lock file is written only by the apply run."
LONG_REFERENCE = (
    "With no flag, sync prints the plan and writes nothing. --apply writes the files and updates the lock file, "
    ".sablefile/lock.json." + FOLDERS + PLAN
)
LONG_REPLY = LONG_REFERENCE.replace(FOLDERS, "")  # the answer leaves out the folder sentence
PAIRS = (
    ("file names", ".sablefile/lock.json", "sablefile.lock"),
    ("flag", "--apply", "--appply"),
    ("long answer", LONG_REFERENCE, LONG_REPLY),
)

for name, reference, reply in PAIRS:
    print(f"{name}, exact match: {reply == reference}")
    print(f"{name}, ratio: {SequenceMatcher(None, reference, reply).ratio():.3f}")
    print(f"{name}, ratio with the reply first: {SequenceMatcher(None, reply, reference).ratio():.3f}")
# autojunk=False: the default treats the reply's common characters as junk once it is 200 characters or longer.
print(f"long answer, ratio with autojunk off: {SequenceMatcher(None, LONG_REFERENCE, LONG_REPLY, autojunk=False).ratio():.3f}")
