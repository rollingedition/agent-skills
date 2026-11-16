"""Train for 30 steps on the recorded recipe, then score test_200 at the placeholder threshold of 0.5.
Read the three step losses against the uniform-guess loss, then the hand-off line at that threshold. The recording runs 1,125 steps."""

import math

import torch

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
REPO = "HuggingFaceTB/SmolLM2-135M-Instruct"
STEPS, BATCH, SEED = 30, 8, 0

train, order = router_lib.training_rows(SEED)  # the seed sets the shuffled order of the training rows, the one the recording used
tok, model = router_lib.new_classifier(REPO)  # SmolLM2 with a 77-way head, LoRA rank 8, lora_alpha 16, on q_proj and v_proj
lora, head = router_lib.parameter_split(model)  # LoRA tensors have "lora_" in their names; every other trainable tensor is the head
print(f"trainable parameters: {lora + head}")
print(f"LoRA parameters: {lora}")
print(f"head parameters: {head}")

losses = router_lib.train_steps(model, tok, train, order, STEPS, BATCH)  # AdamW at learning rate 1e-3, router_lib's default
print(f"training steps: {STEPS}")
print(f"batch size: {BATCH}")
print(f"seed: {SEED}")
for step in (10, 20, 30):
    print(f"loss at step {step}: {losses[step - 1]:.2f}")  # train_steps returns one loss per step, from step 1 at index 0, so step 10 is index 9
print(f"loss of a uniform guess over 77 teams: {math.log(77):.2f}")

result = router_lib.score_test_sample(model, tok, "test_200", 0.5)  # 0.5 is chapter 1's placeholder; this run chooses no threshold
n = result["n"]
print(f"messages on test_200: {n}")
print(f"accuracy on test_200: {result['correct']}/{n} ({result['accuracy']:.1%})")
print(f"handed off at placeholder 0.50: {result['handed_off']}/{n} ({result['handoff_rate']:.1%})")
if result["accuracy_not_handed_off"] is None:  # None when no message is kept, so there is no accuracy to print
    print("accuracy on messages not handed off: not defined (0 messages not handed off)")
else:
    m = result["not_handed_off"]
    print(f"accuracy on messages not handed off: {result['correct_not_handed_off']}/{m} ({result['accuracy_not_handed_off']:.1%})")
