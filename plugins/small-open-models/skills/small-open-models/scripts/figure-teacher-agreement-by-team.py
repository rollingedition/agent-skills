"""Draw each team's labelled training rows as one bar, the rows the teacher gets right at the bottom and the rest hatched above, teams sorted from the highest share right to the lowest.
The printed lines give the teams where the teacher gets no row right, and the teams below one half, which the prose's point rests on."""

from lib.figures import ACCENT, MUTED, new_figure, save

import json  # noqa: E402
import os  # noqa: E402
from collections import Counter  # noqa: E402

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

train = [team for _, team in router_lib.read_rows("train")]  # gold team index of each training row
teacher_rows = [json.loads(line) for line in (router_lib.HERE / "data/recorded/teacher-labels/labels.jsonl").read_text().splitlines()]

rows, agree = Counter(), Counter()
for row in teacher_rows:
    gold = train[row["index"]]  # row["index"] is the row's position in the training file
    rows[gold] += 1
    agree[gold] += int(row["label"] == gold)

# teacher-agreement's count, from the same rows and in its own way: its line "teacher agrees with gold"
recomputed = sum(row["label"] == train[row["index"]] for row in teacher_rows)
assert sum(agree.values()) == recomputed, "per-team agreement differs from teacher-agreement's count"

order = [t for _, t in sorted(((agree[t] / rows[t], t) for t in rows), reverse=True)]
zero = [t for t in order if agree[t] == 0]
below = [t for t in order if agree[t] / rows[t] < 0.5]
assert all((rows[t] - agree[t]) * 2 > rows[t] for t in below), "a team below one half is not wrong on most of its rows"

print(f"teams with labelled rows: {len(order)}")
print(f"teams where the teacher gets no row right: {len(zero)}")
print(f"teams with agreement below one half: {len(below)}")
print(f"rows in the smallest team below one half: {min(rows[t] for t in below)}")

right = [agree[t] for t in order]
wrong = [rows[t] - agree[t] for t in order]
fig, ax = new_figure()
x = range(1, len(order) + 1)
ax.bar(x, right, color=ACCENT, label="teacher agrees with gold")
ax.bar(x, wrong, bottom=right, facecolor="none", edgecolor=MUTED, hatch="////", linewidth=0.6, label="teacher disagrees with gold")
ax.set_xlabel("team, from highest to lowest share the teacher gets right")
ax.set_ylabel("training rows labelled by the teacher")
ax.set_xlim(0, len(order) + 1)
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False)
save(fig, "teacher-agreement-by-team")
