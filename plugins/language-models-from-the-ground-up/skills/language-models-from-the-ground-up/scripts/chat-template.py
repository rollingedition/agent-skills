from lib import recorded

template = recorded.read("instruction-tuning", "template")
print("request:", template["with"]["prompt"].split("<|im_start|>user\n")[1].split("<|im_end|>")[0])
print("what the tuned model reads, with its chat template:")
print(template["with"]["prompt"])
print("tuned model, with the template:", " ".join(template["with"]["text"].split()))
print("tuned model, without it:", " ".join(template["without"]["text"].split()))
