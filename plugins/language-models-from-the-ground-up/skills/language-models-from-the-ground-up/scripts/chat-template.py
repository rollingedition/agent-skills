"""Prints the full prompt the tuned model read, with its chat template, and its reply with and without the template. The
prose's point rests on the last two printed lines: the same words, with and without the template.
"""
from lib import recorded

template = recorded.read("instruction-tuning", "template")
# the request is the text between the user marker and its end marker
print("request:", template["with"]["prompt"].split("<|im_start|>user\n")[1].split("<|im_end|>")[0])
print("what the tuned model reads, with its chat template:")
print(template["with"]["prompt"])
print("tuned model, with the template:", " ".join(template["with"]["text"].split()))
print("tuned model, without it:", " ".join(template["without"]["text"].split()))
