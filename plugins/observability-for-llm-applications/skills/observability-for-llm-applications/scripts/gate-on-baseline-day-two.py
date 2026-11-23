"""Gate baseline day 2 against baseline day 1, both on release r0, with the same rules and limits as the prompt release's gate. The two days share no message, so each interval resamples each day on its own. The day is a normal day with no incident, and the gate must pass it, or a gate that flags every normal day would never reach CI."""
from lib.gate import judge, measured
from lib.report import fmt_int

DAY, MODEL = "2026-12-08", "Qwen3-4B-Instruct-2507"
before = measured("baseline-day-1", DAY, MODEL)            # r0 on all 200 messages of baseline day 1
after = measured("baseline-day-2", "2026-12-10", MODEL)    # r0 again, on 80 other messages, two days later
print("messages, baseline day 1:", fmt_int(len(before)))
print("messages, baseline day 2:", fmt_int(len(after)))
print("messages shared by the two days:", fmt_int(len(set(before) & set(after))))   # no message is in both
verdict, flagged = judge("baseline day 2 against day 1", list(before.values()), list(after.values()), paired=False)
assert verdict == "pass" and flagged == []     # the same release on a normal day must pass the same gate
