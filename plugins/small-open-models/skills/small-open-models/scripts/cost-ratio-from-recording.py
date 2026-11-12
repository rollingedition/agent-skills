"""The throughput rates and ratios as recorded, and the machine they were measured on. Reads the recording only; no model runs."""

import json

import router_lib

folder = router_lib.HERE / "data" / "recorded" / "throughput"
ratios = json.loads((folder / "ratios.json").read_text())
rates = router_lib.recorded_rates()
manifest = json.loads((folder / "manifest.json").read_text())

print(f"machine: {manifest['machine'].split(', ')[0]}")
print(f"threads: {manifest['settings']['n_threads']}")
print(f"messages on test_200: {ratios['messages']}")
print(f"stand-in rate, one per call (messages a second): {rates['standin_one_message_per_call']}")
print(f"classifier fp32 rate, one per call (messages a second): {rates['classifier_fp32_one_message_per_call']}")
print(f"classifier fp32 rate, batches of 16 (messages a second): {rates['classifier_fp32_batches_of_16']}")
print(f"classifier int8 rate, batches of 16 (messages a second): {rates['classifier_int8_batches_of_16']}")
print(f"fp32 over stand-in, one per call, throughput ratio: {ratios['classifier_fp32_one_at_a_time_over_standin']}")
print(f"fp32 over stand-in, batches of 16, throughput ratio: {ratios['classifier_fp32_over_standin']}")
print(f"int8 over stand-in, batches of 16, throughput ratio: {ratios['classifier_int8_over_standin']}")
print(f"int8 over fp32, batches of 16, throughput ratio: {ratios['classifier_int8_over_fp32']}")
print(f"predictions agreeing, fp32 and int8: {ratios['agreement_fp32_int8']}/{ratios['messages']}")
