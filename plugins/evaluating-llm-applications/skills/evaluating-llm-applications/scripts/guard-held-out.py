"""Applies the decline guard, with its threshold frozen from dev, to the held-out items of the unfiltered recording, and
prints both rates with 95% bootstrap intervals over items. The threshold is a constant chosen by tune-guard-dev's rule
on dev; the assert checks that the rule still picks it, so a change to the dev data or the rule fails here."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.guard import denominators, errors, guarded, pick_threshold, rows
from lib.stats import bootstrap_mean, interval_pct, pct

# Picked on dev by tune-guard-dev (the rule in lib/guard.py), then frozen. Held-out is not used to change it.
FROZEN_THRESHOLD = 0.0

dev_pick = pick_threshold(rows("dev"))  # reads dev only
assert dev_pick == FROZEN_THRESHOLD, f"the dev rule now picks {dev_pick:.2f}, not the frozen {FROZEN_THRESHOLD:.2f}"

held = rows("held-out")
answerable, unanswerable = denominators(held)
refusals, answers = errors(held, FROZEN_THRESHOLD)
print(f"threshold (frozen from dev): {FROZEN_THRESHOLD:.2f}")
print(f"held-out answerable items: {answerable}")
print(f"held-out unanswerable items: {unanswerable}")
changed = [row.item_id for row in held if guarded(row, FROZEN_THRESHOLD) != row.declined]
print(f"held-out replies the guard changed to declines: {len(changed)} of {len(held)}")

# One 0/1 flag per item: the bootstrap over these flags is the bootstrap of the rate, over items.
refused_flags = [float(guarded(row, FROZEN_THRESHOLD)) for row in held if row.kind == "answerable"]
answered_flags = [float(not guarded(row, FROZEN_THRESHOLD)) for row in held if row.kind == "unanswerable"]
assert len(refused_flags) == answerable and len(answered_flags) == unanswerable

refusal_lo, refusal_hi = bootstrap_mean(refused_flags, level=0.95)  # 2,000 resamples, seeded (lib/stats.py)
answer_lo, answer_hi = bootstrap_mean(answered_flags, level=0.95)
print(f"false refusal rate: {pct(len(refusals), answerable)} interval {interval_pct(refusal_lo, refusal_hi)}")
print(f"false refusals: {', '.join(refusals) or 'none'}")
print(f"false answer rate: {pct(len(answers), unanswerable)} interval {interval_pct(answer_lo, answer_hi)}")
print(f"false answers: {', '.join(answers) or 'none'}")
