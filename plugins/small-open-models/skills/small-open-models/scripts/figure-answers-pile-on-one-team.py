"""Draw how each prompting variant's answers pile onto its most given teams, against the even share over the gold teams of test_200.
The prose reads the gold-team count and the even share. The counts are recomputed from the recording with the tie-break prompting-on-test-200 uses, and no model runs here."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import collections  # noqa: E402
import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

from lib.figures import ACCENT, INK, MUTED, new_figure, save  # noqa: E402

ANSWERS = router_lib.HERE / "data" / "recorded" / "prompting-eval" / "answers.jsonl"
STYLES = {"135m-raw": (ACCENT, "o", "135M, raw prompt"), "135m-chat": (MUTED, "s", "135M, chat template"),
          "360m-raw": (INK, "^", "360M, raw prompt")}
RANKS = 10

rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")  # the messages every variant answers
total = len(sample)
gold = collections.Counter(router_lib.LABELS[rows[i][1]] for i in sample)
even = 100 / len(gold)  # the share an even spread over the gold teams gives each one

with open(ANSWERS) as f:
    records = [json.loads(line) for line in f]

fig, ax = new_figure()
for variant, (color, marker, name) in STYLES.items():
    given = collections.Counter(r["team"] for r in records if r["variant"] == variant)
    # every variant answers all the sample's messages, so each share below uses the same total
    assert sum(given.values()) == total
    # a tie in count goes to the team name that sorts first, as in prompting-on-test-200
    ordered = sorted(given.items(), key=lambda item: (-item[1], item[0]))
    # a variant with fewer than ten teams gives no answers at the ranks past its last team
    counts = [ordered[r][1] if r < len(ordered) else 0 for r in range(RANKS)]
    print(f"{variant} most given team: {counts[0]}/{total} ({100 * counts[0] / total:.1f}%)")
    print(f"{variant} distinct teams given: {len(given)}")
    ax.plot(range(1, RANKS + 1), [100 * c / total for c in counts], color=color, marker=marker, markersize=4, label=name)

print(f"gold teams in test_200: {len(gold)}")
print(f"even share over the gold teams: {even:.1f}%")
ax.axhline(even, color=MUTED, linestyle=":", linewidth=1.4, label=f"even share over the {len(gold)} gold teams")
ax.set_xticks(range(1, RANKS + 1))
ax.set_xlabel("rank of the team, from the team given most")
ax.set_ylabel("share of the 200 answers, %")
ax.set_ylim(bottom=0)
ax.legend(frameon=False)
save(fig, "answers-pile-on-one-team")
