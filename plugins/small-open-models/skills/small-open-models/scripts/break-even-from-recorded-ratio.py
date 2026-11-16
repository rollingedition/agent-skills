"""The monthly volume at which one machine's bill equals the hosted bill for the router's prompts. The break-even line
is the point the prose rests on, and it holds only inside the capacity line, which the last line checks. The prices and
the machine's cost are example values, as in the bill; the router's rate is recorded on the machine."""

import math
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
inputs = router_lib.bill_inputs_recorded()  # example prices and cost per hour, with the router's rate from the recording
test = router_lib.read_rows("test")  # (text, label index) for every test row, in file order
messages = [test[i][0] for i in router_lib.read_sample("test_200")]  # index 0 is the text; the label is index 1

# Mean count of the whole router prompt, team list included, with SmolLM2-135M's tokenizer.
input_tokens = router_lib.router_prompt_tokens(messages)
# Prices are per million tokens, hence the division at the end.
per_message = (input_tokens * inputs["price_per_million_input_tokens"]
               + inputs["output_tokens_per_message"] * inputs["price_per_million_output_tokens"]) / 1_000_000
machine_month = inputs["machine_cost_per_hour"] * inputs["hours_per_month"]
capacity = inputs["router_messages_per_second"] * 3600 * inputs["hours_per_month"] * inputs["utilisation"]

# The machine's bill is the same each month up to its capacity, so the hosted bill
# equals it at messages = machine bill / hosted price per message.
# Rounded up: the first whole message count at which the machine is no dearer.
breakeven = math.ceil(machine_month / per_message)

print(f"input tokens per message, hosted prompt (counted with SmolLM2-135M-Instruct, a stand-in tokenizer): {input_tokens}")
print(f"example hosted price per message (example prices), USD: {per_message:.6f}")
print(f"example machine bill per month (example cost per hour), USD: {machine_month:.2f}")
print(f"machine capacity per month (recorded rate, example utilisation): {capacity:.0f}")
print(f"example break-even messages per month (example prices and cost per hour): {breakeven}")
print(f"break-even within machine capacity: {'yes' if breakeven <= capacity else 'no'}")
