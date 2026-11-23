"""Rank the training file's rows per team and draw them against the test file's count per team; no model runs.

The prose's point rests on the median training count, and on how many teams have more training rows than the test file's count, which is the same for every team.
"""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402
from collections import Counter  # noqa: E402
from statistics import median  # noqa: E402

router_lib.setup_runtime()

from lib.figures import ACCENT, INK, new_figure, save  # noqa: E402

train = router_lib.read_rows("train")
test = router_lib.read_rows("test")
train_per_label = Counter(label for _, label in train)
test_per_label = Counter(label for _, label in test)
train_counts = sorted((train_per_label[i] for i in range(len(router_lib.LABELS))), reverse=True)
test_counts = [test_per_label[i] for i in range(len(router_lib.LABELS))]

assert min(train_counts) == 35 and max(train_counts) == 187, "train counts differ from count-the-splits"  # its lines
assert min(test_counts) == max(test_counts) == 40, "the test file is not even"

print(f"labels: {len(router_lib.LABELS)}")
print(f"train per label min: {min(train_counts)}")
print(f"train per label max: {max(train_counts)}")
print(f"train per label median: {median(train_counts)}")
print(f"test per label: {test_counts[0]}")
print(f"teams with more training rows than the test count: {sum(c > test_counts[0] for c in train_counts)}")
print("test file even across teams: yes")

fig, ax = new_figure()
ax.bar(range(1, len(train_counts) + 1), train_counts, color=ACCENT, label="training file: rows per team, ranked")
ax.axhline(test_counts[0], color=INK, linestyle="--", label="test file: rows per team, the same for every team")
ax.set_xlabel("team, ranked from most to fewest training rows")
ax.set_ylabel("messages per team")
ax.set_xlim(0, len(train_counts) + 1)
ax.set_ylim(0, max(train_counts) + 20)
ax.legend(loc="upper right")
save(fig, "train-rows-per-team")
