"""The router and the stand-in on all 1,001 messages of test_1001, the committed test order. The stand-in's answers
are recorded; the router runs live on 2 threads, and its first 200 messages are the test_200 sample."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
c = router_lib.compare_router_and_standin("test_1001")
n = c["messages"]
print(f"messages on test_1001: {n}")
print(f"router banking77-lora-v1 correct: {c['router_correct']}/{n} ({c['router_correct'] / n:.1%})")
print(f"stand-in correct: {c['standin_correct']}/{n} ({c['standin_correct'] / n:.1%})")
print(f"router handed off: {c['handed_off']}/{n} ({c['handed_off'] / n:.1%})")
print(f"right for the stand-in, wrong for the router: {c['standin_right_router_wrong']}/{n}")
print(f"of those, handed off by the router: {c['of_those_handed_off']}/{c['standin_right_router_wrong']}")
print(f"wrong for the router and sent as an answer: {c['router_wrong_sent']}/{n} ({c['router_wrong_sent'] / n:.1%})")
print(f"right for the router, wrong for the stand-in: {c['router_right_standin_wrong']}/{n}")
