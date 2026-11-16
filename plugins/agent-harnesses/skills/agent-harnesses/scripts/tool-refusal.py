"""The read tool refuses a path outside the case, and the refusal comes back as text the model can read. Only reads
are tried, and a refused path never reaches the disk."""
from lib.case import CASE
from lib.tools import CH1, Workspace

ABSOLUTE = "/etc/secret.txt"
ws = Workspace(CASE)
for path in ("../secret.txt", ABSOLUTE):
    result = CH1.call(ws, "read_file", {"path": path})
    # An absolute path differs on every machine, so the output shows a placeholder for it.
    print("refused:", result.text.replace(ABSOLUTE, "<absolute path>"))
