"""Sweeps the decline guard's threshold over dev replies of the unfiltered recording, printing both rates at each
threshold, and the threshold the dev rule picks. The line for 0.00 is the recorded replies with no guard, since no top
score is below zero; the rule's pick rests on the rate lines below it. Only dev is read here."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.guard import GRID, GUARD_RECORDING, RULE, contexts_match, denominators, errors, pick_threshold, rows
from lib.stats import pct

dev = rows("dev")
answerable, unanswerable = denominators(dev)
print(f"recording: {GUARD_RECORDING} (all versions, dev items)")
print(f"answerable dev items: {answerable}")
print(f"unanswerable dev items: {unanswerable}")

mismatches = contexts_match("dev")
print(f"dev items whose recorded sections differ from the retrieval: {mismatches}")
assert mismatches == 0, "the scores come from a retrieval that did not make the recorded replies"
highest = max(row.score for row in dev)
print(f"highest top score on dev: {highest:.3f}")
assert highest < GRID[-1], "the grid must reach above every dev score"

print(f"rule: {RULE}")
for threshold in GRID:
    refusals, answers = errors(dev, threshold)
    print(f"threshold {threshold:.2f}, false refusal rate: {pct(len(refusals), answerable)}")
    print(f"threshold {threshold:.2f}, false answer rate: {pct(len(answers), unanswerable)}")

refusals, answers = errors(dev, 0.0)
print(f"recorded false refusals (no guard): {', '.join(refusals) or 'none'}")
print(f"recorded false answers (no guard): {', '.join(answers) or 'none'}")
scores = {row.item_id: row.score for row in dev}
for item_id in answers:  # the top score of each recorded false answer, so a reader can see where it falls on the grid
    print(f"top score of recorded false answer {item_id}: {scores[item_id]:.3f}")

chosen = pick_threshold(dev)
assert chosen == 0.0, f"the dev rule now picks {chosen:.2f}, not 0.00"
refusals, answers = errors(dev, chosen)
print(f"threshold chosen by the dev rule: {chosen:.2f}")
print(f"at the chosen threshold, false refusal rate: {pct(len(refusals), answerable)}")
print(f"at the chosen threshold, false answer rate: {pct(len(answers), unanswerable)}")
