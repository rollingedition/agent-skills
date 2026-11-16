"""Two proposals in one transcript, through one gate: the recorded T-04 run is answered yes and its inch reaches the
library; a stored T-09 run (fix the Celsius offset) is answered no and handed back. Each answer is logged with the
proposal ID and the hash of the diff it answers."""
from lib.case import CASE
from lib.permissions import Gate, library_copy, replay_task, scripted, stored_task
from lib.tasks import snapshot

with library_copy() as library:
    gate = Gate(library, scripted((True, ""), (False, "not in this change")))
    first = replay_task("T-04", gate, library)
    second = stored_task("T-09", gate, library)
    print("T-04 ended:", first.ended, "| T-09 ended:", second.ended)
    print("transcript, T-04:", first.trace.lines()[-1])
    print("transcript, T-09:", second.trace.lines()[-1])
    for line in gate.log:
        print("gate:", line)
    print("applied:", gate.counts["applied"], "refused:", gate.counts["refused"])
    assert first.ended == "finish" and second.ended == "ask_user" and gate.counts["applied"] == 1
    assert snapshot(library, "unitcraft/units.py") != snapshot(CASE, "unitcraft/units.py")
    assert snapshot(library, "unitcraft/temperature.py") == snapshot(CASE, "unitcraft/temperature.py")
    first.close()
    second.close()
