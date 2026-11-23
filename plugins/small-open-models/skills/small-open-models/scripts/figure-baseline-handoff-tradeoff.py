"""Sweep the hand-off threshold over the stand-in's recorded answers on test_1001 and draw both measures; no model runs.

The printed lines at 0.5 equal baseline-measures' lines, which the assert checks. The lines at 0.9, 0.99 and 1.0 give more points on the curves, and the counts of confidences at 1.0 and in the last step explain the curves' right edge.
"""

import os

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import torch  # noqa: E402

torch.set_num_threads(2)

import json, math, router_lib  # noqa: E402

router_lib.setup_runtime()

from lib.figures import ACCENT, INK, MUTED, new_figure, save  # noqa: E402

RECORDED = router_lib.HERE / "data" / "recorded" / "standin-baseline"
answers = {row["index"]: row for row in map(json.loads, (RECORDED / "answers.jsonl").read_text().splitlines())}
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_1001")
golds = [rows[i][1] for i in sample]
preds = [answers[i]["label"] for i in sample]
confs = [math.exp(answers[i]["logprob"]) for i in sample]  # the probability the stand-in gave its answer
at = lambda threshold: router_lib.metrics(preds, golds, confs, threshold)  # noqa: E731
thresholds = [k / 100 for k in range(101)]
sweep = [at(t) for t in thresholds]
handed = [100 * m["handoff_rate"] for m in sweep]
kept = [100 * m["accuracy_not_handed_off"] if m["accuracy_not_handed_off"] is not None else math.nan for m in sweep]

assert (at(0.5)["handed_off"], at(0.5)["correct_not_handed_off"], at(0.5)["not_handed_off"]) == (30, 554, 971), "not baseline-measures"
for t in (0.5, 0.9, 0.99, 1.0):
    m = at(t)
    print(f"handed off at {t}: {m['handed_off']}/{len(sample)} ({m['handoff_rate']:.1%})")
    print(f"accuracy on messages not handed off at {t}: {m['correct_not_handed_off']}/{m['not_handed_off']} ({m['accuracy_not_handed_off']:.1%})")
print("matches baseline-measures at 0.5: yes")
exactly_one = sum(c == 1.0 for c in confs)
last_step = at(1.0)["handed_off"] - at(0.99)["handed_off"]
assert at(1.0)["handed_off"] + exactly_one == len(sample), "a confidence of 1.0 is handed off at 1.0"  # strictly below: 1.0 is kept
print(f"messages with confidence at least 0.99 and below 1.0: {last_step}")
print(f"messages with confidence exactly 1.0: {exactly_one}")

fig, ax = new_figure()
ax.plot(thresholds, handed, color=INK, linestyle="--", label="handed off, share of all messages")
ax.plot(thresholds, kept, color=ACCENT, label="accuracy on messages not handed off")
ax.axvline(0.5, color=MUTED, linestyle=":", label="placeholder threshold 0.5")
ax.set_xlabel("hand-off threshold: a confidence below it goes to a person")
ax.set_ylabel("percent")
ax.set_xlim(0, 1)
ax.set_ylim(0, 100)
ax.legend(loc="upper right")
save(fig, "baseline-handoff-tradeoff")
