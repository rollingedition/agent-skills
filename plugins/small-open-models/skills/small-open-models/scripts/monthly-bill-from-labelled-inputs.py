"""The monthly bill for a hosted model and for the router on one machine. Token counts are live. The prices, volume,
machine cost and utilisation are example values, not published prices; the router's rate is recorded on the machine."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
inputs = router_lib.bill_inputs_recorded()
test = router_lib.read_rows("test")
messages = [test[i][0] for i in router_lib.read_sample("test_200")]

input_tokens = router_lib.router_prompt_tokens(messages)
per_message = (input_tokens * inputs["price_per_million_input_tokens"]
               + inputs["output_tokens_per_message"] * inputs["price_per_million_output_tokens"]) / 1_000_000
hosted_month = inputs["messages_per_month"] * per_message

machine_month = inputs["machine_cost_per_hour"] * inputs["hours_per_month"]
capacity = inputs["router_messages_per_second"] * 3600 * inputs["hours_per_month"] * inputs["utilisation"]

print(f"example input, messages per month: {inputs['messages_per_month']}")
print(f"example input, price per million input tokens, USD: {inputs['price_per_million_input_tokens']}")
print(f"example input, price per million output tokens, USD: {inputs['price_per_million_output_tokens']}")
print(f"example input, output tokens per message: {inputs['output_tokens_per_message']}")
print(f"example input, machine cost per hour, USD: {inputs['machine_cost_per_hour']}")
print(f"example input, hours per month: {inputs['hours_per_month']}")
print(f"example input, utilisation: {inputs['utilisation']}")
print(f"recorded input, router messages per second, one per call: {inputs['router_messages_per_second']}")
print(f"input tokens per message, hosted prompt (counted with SmolLM2-135M-Instruct, a stand-in tokenizer): {input_tokens}")
print(f"example hosted price per message (example prices), USD: {per_message:.6f}")
print(f"example hosted bill per month (example prices), USD: {hosted_month:.2f}")
print(f"example machine bill per month (example cost per hour), USD: {machine_month:.2f}")
print(f"machine capacity per month (recorded rate, example utilisation): {capacity:.0f}")
print(f"example machine cost per message at capacity (example cost per hour), USD: {machine_month / capacity:.6f}")
print(f"example volume within machine capacity: {'yes' if inputs['messages_per_month'] <= capacity else 'no'}")
print(f"example values, cheaper route at the input volume: {'hosted' if hosted_month < machine_month else 'machine'}")
