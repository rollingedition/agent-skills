"""Send the test_40 messages to the one POST /route through TestClient, in process, and print counts that tie the
hand-off flag to the team. The prose's point rests on the "handed off, team is None" line and the "not handed off,
team is the gold label" line; the last checks show the route's answer to a body with no message."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

from fastapi.testclient import TestClient  # noqa: E402

import router_lib  # noqa: E402

router_lib.setup_runtime()                  # seeds, deterministic algorithms and float32, so the counts repeat
client = TestClient(router_lib.make_app(router_lib.HERE / "data" / "recorded" / "lora-full"))  # checks the files, loads the model once, and reads the hand-off threshold from the adapter's manifest

test = router_lib.read_rows("test")         # each row is (message, gold label index)
sample = router_lib.read_sample("test_40")  # row numbers of the committed sample
replies = [client.post("/route", json={"message": test[i][0]}) for i in sample]
bodies = [r.json() for r in replies]
gold = [test[i][1] for i in sample]         # gold label indexes; LABELS turns one into a team name

print(f"responses: {len(replies)}")
print(f"status codes: {sorted({r.status_code for r in replies})}")
print(f"response keys: {sorted(bodies[0])}")
print(f"handed off: {sum(b['handed_off'] for b in bodies)}/{len(bodies)}")
print(f"team names outside the list: {sum(b['team'] is not None and b['team'] not in router_lib.LABELS for b in bodies)}")

sure = [k for k, b in enumerate(bodies) if not b["handed_off"]]    # kept: the route returned a team
unsure = [k for k, b in enumerate(bodies) if b["handed_off"]]      # flagged: the route returned no team
print(f"not handed off, team is the gold label: {sum(bodies[k]['team'] == router_lib.LABELS[gold[k]] for k in sure)}/{len(sure)}")
print(f"handed off, team is None: {sum(bodies[k]['team'] is None for k in unsure)}/{len(unsure)}")
print(f"adapter: {bodies[0]['adapter']}")
print(f"version: {bodies[0]['version']}")

bad = client.post("/route", json={})        # a body with no message field, which the route's body model requires
detail_is_list = isinstance(bad.json()["detail"], list)
assert detail_is_list, "a body with no message should get a 422 whose detail is a list"
print(f"status on an empty body: {bad.status_code}")
print(f"detail is a list: {'yes' if detail_is_list else 'no'}")
