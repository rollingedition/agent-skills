"""Shows how many items of the test set exercise each behaviour B1 to B6, and which ones. The mapping in data/behaviours.json
must list every item of the set exactly once, or the example stops; items that exercise no behaviour are counted apart."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json
from pathlib import Path

from lib.testset import load_items

BEHAVIOURS = Path(__file__).resolve().parent / "data" / "behaviours.json"
ids = sorted(item.id for item in load_items())
mapping = json.loads(BEHAVIOURS.read_text(encoding="utf-8"))
assert sorted(mapping) == ids, "behaviours.json must list every item of the set, once"  # the coverage needs every item

print(f"items: {len(ids)}")
print(f"items with no behaviour: {sum(1 for labels in mapping.values() if not labels)}")
for behaviour in ("B1", "B2", "B3", "B4", "B5", "B6"):
    hits = sorted(item for item, labels in mapping.items() if behaviour in labels)
    print(f"{behaviour} items: {len(hits)}")
    print(f"{behaviour} ids: {', '.join(hits)}")
