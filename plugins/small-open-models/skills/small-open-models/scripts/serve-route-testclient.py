"""Serve banking77-lora-v1 with one POST /route and call it on test_40 through TestClient.
TestClient runs the app in-process: no server process and no socket. Nothing is trained here."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

from fastapi.testclient import TestClient  # noqa: E402

import router_lib  # noqa: E402

router_lib.setup_runtime()
client = TestClient(router_lib.make_app(router_lib.HERE / "data" / "recorded" / "lora-full"))

test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40")
replies = [client.post("/route", json={"message": test[i][0]}) for i in sample]
bodies = [r.json() for r in replies]
gold = [test[i][1] for i in sample]

print(f"responses: {len(replies)}")
print(f"status codes: {sorted({r.status_code for r in replies})}")
print(f"response keys: {sorted(bodies[0])}")
print(f"handed off: {sum(b['handed_off'] for b in bodies)}/{len(bodies)}")
print(f"team names outside the list: {sum(b['team'] is not None and b['team'] not in router_lib.LABELS for b in bodies)}")

sure = [k for k, b in enumerate(bodies) if not b["handed_off"]]
unsure = [k for k, b in enumerate(bodies) if b["handed_off"]]
print(f"not handed off, team is the gold label: {sum(bodies[k]['team'] == router_lib.LABELS[gold[k]] for k in sure)}/{len(sure)}")
print(f"handed off, team is None: {sum(bodies[k]['team'] is None for k in unsure)}/{len(unsure)}")
print(f"adapter: {bodies[0]['adapter']}")
print(f"version: {bodies[0]['version']}")

bad = client.post("/route", json={})
print(f"status on an empty body: {bad.status_code}")
print(f"detail is a list: {isinstance(bad.json()['detail'], list)}")
