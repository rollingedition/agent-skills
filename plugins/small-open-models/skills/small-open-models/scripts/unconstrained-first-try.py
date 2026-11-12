"""Ask the 135M model for a team with the raw router prompt and no constraint, on the first 20 messages of test_40.
The answers stay in this example and are never returned to a caller."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()

SMALL = "HuggingFaceTB/SmolLM2-135M-Instruct"

tokenizer, model = router_lib.load_model(SMALL)
rows = router_lib.read_rows("test")
sample = router_lib.read_sample("test_40", n=20)  # the first 20, to keep the run short
teams = set(router_lib.LABELS)

answers = []
with torch.no_grad():
    for i in sample:
        inputs = tokenizer(router_lib.router_prompt(rows[i][0]), return_tensors="pt")
        out = model.generate(
            **inputs, max_new_tokens=10, do_sample=False, pad_token_id=tokenizer.eos_token_id
        )
        new_tokens = out[0, inputs["input_ids"].shape[1] :]
        answers.append(tokenizer.decode(new_tokens, skip_special_tokens=True).strip())

print(f"messages: {len(answers)}")
print(f"answers that are a team name: {sum(a in teams for a in answers)}/{len(answers)}")
