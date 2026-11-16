"""The same reply, run_tests three times in a row, on T-01: with no stop rules the run reaches the step cap of 16, and
with the repeat rule (three identical calls in a row) it ends at the third call. Neither run is done."""
from lib.chapter1 import call
from lib.loop import Stops
from lib.scenario import scripted_run

REPLY = call("run_tests")
plain, done_plain = scripted_run("T-01", [REPLY] * 16)
print("without the rules, ended:", plain.ended)
print("without the rules, steps:", plain.steps)
plain.close()
ruled, done_ruled = scripted_run("T-01", [REPLY] * 16, stops=Stops(repeat_limit=3))
print("with the repeat rule, ended:", ruled.ended)
print("with the repeat rule, steps:", ruled.steps)
print("done, either run:", done_plain or done_ruled)
assert plain.ended == "step_cap" and plain.steps == 16
assert ruled.ended == "repeated_call" and ruled.steps == 3 and not (done_plain or done_ruled)
ruled.close()
