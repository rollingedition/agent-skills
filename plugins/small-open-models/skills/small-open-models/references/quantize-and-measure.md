---
title: "Small Open Models"
chapter: "Quantize the router and measure what changes"
chapter_id: quantize-and-measure
book: small-open-models
edition: 2026.11.1
verified: 2026-11-12
edition_code: 8J4E-MZEZ
canonical: https://rollingedition.com/small-open-models/quantize-and-measure
license: CC BY 4.0
attribution: "“Quantize the router and measure what changes,” chapter 7 of Small Open Models, Edition 2026.11.1, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/small-open-models/quantize-and-measure. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Quantize the router and measure what changes

By the end of this chapter, you can store the fine-tuned router's backbone weights as 8-bit integers in one call, count the predictions that change on a fixed sample, and say what that count does and does not show. It also says how speed is measured, and what that measurement found on one machine.

[Chapter 5](fine-tune-with-lora) left the router as one adapter, `banking77-lora-v1`, whose weights are float32. Its hand-off threshold is 0.63, chosen on the dev split by the rule in [chapter 5](fine-tune-with-lora#choose-the-threshold-on-dev). Quantizing stores the weights in fewer bits. A quantized model takes less space for its weights, and it may return different answers. This chapter measures the second part on the fixed sample of 200 test messages that chapter 5 scored, `test_200`. It does not claim that quantizing is free. Speed comes from a separate recording, described below.

The inbox needs three answers before it runs a smaller copy in place of the float32 adapter. How many bytes do the copy's weights take, compared with the adapter's? Does the copy answer the same messages the same way? And is it faster on the machine that serves the inbox? The first two can be measured here, from the model's shapes and from a fixed sample. The third comes from a recording on a named machine, and the section on speed says what that recording found and what it does not cover. Each answer is a count with its denominator, or a ratio with its inputs named. None of them is a promise about a reader's own router, which has its own adapter, sample and machine.

## One call to quantize the linear layers {#one-call-to-quantize-the-linear-layers}

A linear layer is a weight matrix that maps one vector to another. The router's backbone is made of them. Quantizing a layer stores each of its weights as an 8-bit integer, with a scale that maps the integers back to approximate float values. Fewer bits per weight means fewer bytes for the layer, and the answers can move, because the values the layer computes are no longer the exact ones.

The scale is what makes the scheme work for a whole matrix. A single scale for an entire matrix has to cover its largest weight, so the rows whose weights are small get a coarse grid. Jacob et al. (2018) report that a shared resolution causes "weights in channels with smaller ranges to have much higher relative error" ([arXiv:1712.05877](https://arxiv.org/abs/1712.05877)). That is a CNN result, so here it is a reason to test per-row scales, not a measurement. A per-row scale lets each output row use the full range of the 8-bit integers for its own weights. That is why the byte count adds one float32 scale for each output row. The scales are few, but they are not free, so the example counts them.

The helper in this book, `int8_classifier`, names its scheme in its docstring: per-row int8 weights, with float32 activations. The scheme is torchao's `Int8WeightOnlyConfig`, which the [torchao source at v0.18.0](https://raw.githubusercontent.com/pytorch/ao/v0.18.0/torchao/quantization/quant_api.py) describes as "int8 weight-only symmetric per-channel quantization to linear layers". The helper applies it in three steps. It merges the adapter's weights into the base model with PEFT's `merge_and_unload`. It calls `quantize_` from `torchao.quantization` with `Int8WeightOnlyConfig`, and passes a filter that selects every `nn.Linear` layer except the one named `score`. Then it returns the model in evaluation mode. The result is the int8 copy, named `banking77-lora-v1-int8` in the recordings. It is a derived model built from the adapter, not a second adapter. The output layer, `score`, is the head that chapter 5 trained, and the section on it explains why the helper leaves it out.

The merge comes first for a reason. [Chapter 5](fine-tune-with-lora#adapters-train-a-small-part-of-the-model) described the adapter as a small set of matrices beside the base model's layers. Merging folds the adapter's update into the base weights, so each layer is one weight matrix, quantized once, and the layer count describes the router. Without the merge, the same call would also quantize the adapter's own matrices as separate int8 layers.

Older PyTorch code uses `torch.ao.quantization.quantize_dynamic`, which also stores Linear weights as int8 and quantizes activations as it runs, a different scheme. PyTorch 2.15 marks it deprecated, with the warning "1. Eager mode quantization (torch.ao.quantization.quantize, torch.ao.quantization.quantize_dynamic), please migrate to use torchao eager mode quantize_ API instead" ([PyTorch v2.15.0, `torch/ao/quantization/utils.py`](https://raw.githubusercontent.com/pytorch/pytorch/v2.15.0/torch/ao/quantization/utils.py)). The migration target is `quantize_`, as the [torchao README at v0.18.0](https://raw.githubusercontent.com/pytorch/ao/v0.18.0/README.md) shows. The examples in this book call no deprecated API themselves.

Example `int8-layers-and-bytes` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Count the backbone Linear layers the int8 copy quantizes, and the weight bytes they store.
Bytes come from shapes: float32 is 4 bytes a weight; int8 is 1 byte a weight plus one float32 scale (4 bytes) per output row.
Prints counts and one rate: no file sizes, no timings."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"

_, model = router_lib.int8_classifier(RECORDED / "adapter")
layers = router_lib.backbone_linears(model)
quantized = [layer for _, layer in layers if router_lib.is_int8(layer)]
weights = sum(layer.weight.numel() for _, layer in layers)
rows = sum(layer.weight.shape[0] for _, layer in layers)

print(f"backbone Linear layers: {len(layers)}")
print(f"backbone Linear layers quantized to int8: {len(quantized)}")
print(f"score head quantized: {router_lib.is_int8(model.score)}")
print(f"score head weight dtype: {model.score.weight.dtype}")
print(f"weights in backbone Linear layers: {weights}")
print(f"output rows in backbone Linear layers: {rows}")
float_bytes = 4 * weights
int8_bytes = 1 * weights + 4 * rows
print(f"weight bytes, int8 as a share of float32: {int8_bytes / float_bytes:.1%}")
```

Output:

```text
backbone Linear layers: 210
backbone Linear layers quantized to int8: 210
score head quantized: False
score head weight dtype: torch.float32
weights in backbone Linear layers: 106168320
output rows in backbone Linear layers: 155520
weight bytes, int8 as a share of float32: 25.1%
```

The example builds the int8 copy and counts its layers and their weights. The output reads: the backbone has 210 linear layers, and the int8 copy quantizes 210 of them. Those layers hold 106168320 weights, in 155520 output rows.

The last line is arithmetic on shapes, and it is not a measurement of a file or a process. A float32 weight takes 4 bytes. An int8 weight takes 1 byte, and the example adds one float32 scale, 4 bytes, for each output row, because that is the convention the helper's scheme names. Over the weights in those layers, the int8 copy takes 25.1% of the float32 bytes. A quarter of that is the weights themselves, and the rest is the scales. The figure covers only the weights of these layers. It leaves out every other tensor the model holds, so it says nothing about the size of a file on disk, and nothing about the memory a running router uses.

For the inbox, the bytes matter only if the weights are part of what the serving machine has to hold. Whether they are depends on that machine and on the rest of the process, and this chapter does not measure either. The ratio tells a reader how much of the weight budget the copy frees, and nothing more.

Importing torchao prints warnings to standard error, and an example's first run may print a load report from transformers. They come from the libraries' own import code, not from a call the examples make, and the examples neither suppress nor act on them. Some lines say torchao could not load its GPU-only kernel libraries, which the CPU path does not use. A `SyntaxWarning` from torchao's own source shows only on the first import, before Python caches the bytecode. Notices that `register_constant()` is deprecated come from torch and are triggered by torchao's import. The load report lists `score.weight` as MISSING: the base checkpoint has no classification head, so transformers starts a new one, and the adapter's saved head replaces it. None of these changes an output line. The book pins torchao at 0.18.0 in its requirements file, and every example uses that pin.

**Working rule:** Quantize only the layers you can name, leave the output layer in float32, and count the bytes from the shapes before you claim any saving. Report the saving as a ratio of weight bytes, with the count of layers beside it, and never as a file size or as a speed.

## Count the predictions that change {#count-the-predictions-that-change}

Quantizing changes the numbers a layer computes, so the answers can change too. The test of a quantized copy is whether it answers the same messages the same way. The example scores `test_200` with the float32 adapter and with its int8 copy, at the threshold in chapter 5's manifest. For each copy it counts the correct answers, the hand-offs and the accuracy on the messages not handed off. It then counts the messages whose team differs between the two copies, and the hand-off decisions that differ. It also scores a third copy, with the head quantized too, for the section on the score head.

The two copies are not treated the same way on purpose. The float32 side is the adapter as chapter 5 loaded it, unmerged. The int8 side is merged first, because the helper merges before it quantizes. So the count below holds the merge and the quantization together. The example never scores a merged float32 copy on its own, and the chapter does not claim that the merge alone changes nothing.

Example `int8-changed-predictions` (Python 3.12.15 · peft 0.21.2 · torch 2.15.0+cpu · torchao 0.18.0+cpu · transformers 5.22.2), passing in Edition 2026.11.1:

```python
"""Score test_200 with the float32 adapter, its int8 copy and the copy with the head in int8, at the recorded threshold.
Prints counts and rates only: accuracy, hand-offs, and how many predictions and hand-off decisions change."""

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import json  # noqa: E402

import torch  # noqa: E402

torch.set_num_threads(2)

import router_lib  # noqa: E402

router_lib.setup_runtime()
RECORDED = router_lib.HERE / "data" / "recorded" / "lora-full"
threshold = json.loads((RECORDED / "manifest.json").read_text())["handoff_threshold"]
test = router_lib.read_rows("test")
sample = router_lib.read_sample("test_200")
golds = [test[i][1] for i in sample]
texts = [test[i][0] for i in sample]

tokenizer, float_model = router_lib.load_classifier(RECORDED / "adapter")
float_preds, float_confs = router_lib.classify_by_length(float_model, tokenizer, texts)
_, int8_model = router_lib.int8_classifier(RECORDED / "adapter")
int8_preds, int8_confs = router_lib.classify_by_length(int8_model, tokenizer, texts)
_, head_model = router_lib.int8_classifier_all_linears(RECORDED / "adapter")
head_preds, head_confs = router_lib.classify_by_length(head_model, tokenizer, texts)

print(f"handoff threshold from manifest: {threshold:.2f}")
print(f"messages on test_200: {len(texts)}")
router_lib.print_copy_report("float32", float_preds, float_confs, golds, threshold)
router_lib.print_copy_report("int8", int8_preds, int8_confs, golds, threshold)
changed, handoffs = router_lib.count_changes(float_preds, float_confs, int8_preds, int8_confs, threshold)
print(f"predictions changed by int8: {changed}/{len(texts)} ({changed / len(texts):.1%})")
print(f"hand-off decisions changed by int8: {handoffs}/{len(texts)}")
changed_head, _ = router_lib.count_changes(float_preds, float_confs, head_preds, head_confs, threshold)
print(f"predictions changed with the head in int8 too: {changed_head}/{len(texts)}")
```

Output:

```text
handoff threshold from manifest: 0.63
messages on test_200: 200
float32 accuracy on test_200: 172/200 (86.0%)
float32 handed off: 33/200 (16.5%)
float32 accuracy on messages not handed off: 156/167 (93.4%)
int8 accuracy on test_200: 172/200 (86.0%)
int8 handed off: 33/200 (16.5%)
int8 accuracy on messages not handed off: 156/167 (93.4%)
predictions changed by int8: 0/200 (0.0%)
hand-off decisions changed by int8: 0/200
predictions changed with the head in int8 too: 1/200
```

The output reads as a comparison of the two copies, line by line. The threshold is 0.63, and the sample has 200 messages. The float32 adapter gets 172/200 (86.0%) right, and the int8 copy gets 172/200 (86.0%). At the threshold, the float32 adapter hands off 33/200 (16.5%) messages, and the int8 copy hands off 33/200 (16.5%). On the messages not handed off, the float32 adapter is correct on 156/167 (93.4%), and the int8 copy on 156/167 (93.4%). Three counts of change follow. Predictions changed by int8: 0/200 (0.0%). Hand-off decisions changed by int8: 0/200. Predictions changed when the head is quantized too: 1/200.

The three measures are the ones [chapter 2](measure-the-routing-task#three-measures-each-with-its-denominator) defined, and each has its denominator. Accuracy divides the correct messages by all 200, so a handed-off message counts as wrong if its team is wrong. The hand-off rate divides the messages below the threshold by all 200. Accuracy on the messages not handed off divides the correct ones among the kept messages, and it is not defined when none are kept. The changed-prediction count uses the same 200 messages and asks a different question: did the two copies agree on each one? Agreement is not correctness, which is why the example prints the accuracy as well.

A changed prediction is not automatically a loss. It can turn a wrong team into a right one, or a right team into a wrong one, and the count alone does not say which. To read the direction, compare each copy's team with the gold label on every message the copies disagree on. Accuracy can hide this. Two copies can have the same accuracy while different messages are right on each, so the same total says nothing about which messages moved. The changed count above is the number to read first. When it is zero, there are no flips to read in either direction. A reader who gets a non-zero count should read the flips before reading the totals.

In the inbox, a flip has a concrete cost. Suppose the float32 adapter sends a message to `card_arrival` and the int8 copy sends the same message to `card_delivery_estimate`. Both are teams, and only one of them can be the message's gold label, so the change either fixes an answer or breaks one, unless both teams are wrong. The inbox sends the message to one team either way. The change would reach the support staff who work that team's queue, and nobody would see it in a total. The count is what makes that change visible before the copy serves any message.

On this sample, the count of changed predictions is 0/200 (0.0%). That is a result on 200 messages, from one adapter, at one threshold. It is not a guarantee. A different sample, a different adapter or a different threshold could show a change, and a sample of 200 can miss a change that is rare in a full stream of messages.

The count is about predictions and nothing else. It does not measure speed or memory in use. The copy also keeps its activations in float32, as the helper's docstring says, so this count tells you nothing about a copy that quantizes activations as well. This chapter does not measure that copy, and it does not claim anything about it.

**Working rule:** Count the changed predictions on the same messages, at the same threshold, for both copies, and print each count with its denominator beside the accuracy and the hand-off count. When the count is zero, report it as zero on that sample, and name the sample and the adapter it was taken from.

## Keep the score head in float32 {#keep-the-score-head-in-float32}

The score head is the layer with 77 outputs, one for each team. Its softmax gives the confidence that chapter 5 compares with the threshold, and its largest probability is the team the router returns. The helper leaves the head out of the call, so the head stays in float32. This section says why the book makes that choice, and what the count shows for it.

The example also quantizes the head and counts the result, on the same sample and at the same threshold. Its last line reads 1/200, which is the number of predictions that change when the head is quantized too. The copy this chapter serves keeps its head in float32, and that choice is backed by this count on one sample. It is not an argument about which layer is the most sensitive, and the chapter does not claim that the head is or is not the layer where any change comes from.

In the inbox, the messages at risk are the ones whose confidence sits a little above the threshold. A change in the head can carry such a message below it, and the message then goes to a person rather than to a team. The hand-off decisions count in the previous section is the way to see whether a copy moves any. On this sample the int8 copy moves 0/200 of them. The sample is 200 messages, and that is too few to say how often a rare change would show.

The example's output also shows what the helper did with the head. Its line for the head reads False, which means the head is not quantized, and its weight type reads torch.float32. Those two lines and the layer counts above come from the same run, so the reader can compare them directly.

The example measures the whole int8 copy and the copy with the head quantized as well. It does not split either copy layer by layer, so it cannot say which layer a change comes from. A reader who wants that should quantize one layer at a time and count again on the dev split.

**Working rule:** Keep the score head in float32 unless a count on the dev split, at the chosen threshold, shows that a quantized head changes no team and no hand-off that you rely on. Say which threshold you counted at.

## Measure speed in a recording {#measure-speed-in-a-recording}

Fewer bytes for the weights does not by itself make a model faster, and this chapter does not claim that it does. Whether the int8 copy computes faster on a given CPU depends on the arithmetic routines that run on that CPU, so the book measures it on one named machine.

The examples print no timings. A timing changes with the machine and with the load on it, so an example that printed one would give a different output on every run, and the book's examples have to give the same output every time. A speed ratio belongs in a recording instead. The recording for this comparison is `throughput`. It measures this chapter's int8 copy, `banking77-lora-v1-int8`, built by the same helper the examples use, against the float32 adapter and against the stand-in, on the machine named in its manifest. Weight-only int8 saves weight bytes. Whether the copy computes faster on a CPU is what that recording measures, and the copy may not be faster. On the machine that manifest names, with four threads, the int8 copy ran at 0.9 times the float32 classifier's messages a second, in batches of 16. So weight-only int8 saved weight bytes, and on that machine it gave no speed reason to serve int8. [Chapter 10](when-a-small-model-is-the-wrong-choice#count-the-bill-and-the-machine) reports the rates with the machine they were measured on. The recording did not time the 360M model, and this chapter claims no speed for any machine but that one.

A recording of that kind pins its model and its inputs, runs them once on the named machine, and saves the outputs with a manifest that names the script. Examples that use a recording read its saved outputs and do not run the model themselves. For the speed comparison, the recording runs the same messages through both copies, with the same number of threads for each, and saves the timing of each copy as its own output. The ratio is worked out from those saved outputs, and the reader can see the machine and the thread count beside it. A reader who wants the ratio for their own machine should run the same recording there, and report the machine with the result.

**Working rule:** Read a speed ratio only from a recording that names the machine it ran on, and never infer one from the weight bytes. The ratio above describes its own machine only, so run the recording on the machine you would serve from before you read it as your speed.

## Decide with the hand-off in view {#decide-with-the-hand-off-in-view}

The decision is which copy the router serves. Chapter 8 serves the float32 adapter by default, and the measurements in this chapter do not change that default. On this sample the int8 copy's count of changed predictions is 0/200 (0.0%), and its count of changed hand-off decisions is 0/200. A zero count on one sample keeps the copy a candidate, and it does nothing more than that. The saving it offers is a ratio of weight bytes in some layers. The recording found no speed gain for the int8 copy on its machine, and the book has no measured memory need that favours it, so a copy with no changed answers on this sample and no measured gain has nothing to recommend it yet.

Keeping float32 is a choice with a cost. The adapter takes more bytes than its int8 copy would, and on a small machine that can matter. What the book has shown is narrower. On this sample, the count of changed predictions is 0/200 (0.0%), and only a zero count removes prediction change as the reason to refuse the copy. The remaining reasons are the ones this chapter has not measured, and they decide the default. If a recording on the inbox's own machine shows a speed gain that matters, and a memory need is measured, the case for int8 becomes an engineering case with a counted risk. Until then the float32 adapter is the one with the fewest open questions.

The hand-off is the part to watch. Chapter 5 chose its threshold so that accuracy on the messages not handed off reaches its target on the dev split. A copy whose confidences move even a little can hand off a different set of messages, and then the threshold no longer does what it was chosen to do. That is why the changed-prediction count is taken at the chosen threshold, and why the hand-off count sits beside it. The same measures apply to any adapter that is quantized, such as a retrained `v2`.

What goes wrong in production is a change nobody counted. A library upgrade can change the arithmetic, and a shift in the mix of messages can move some of them across the threshold. Count again on the dev split whenever the libraries or the messages change, and before a quantized copy serves its first message.

The same steps apply to a quantized copy of a reader's own router, and they need nothing in this book beyond the samples and the threshold. Take the threshold from the adapter's manifest, and check that the manifest says it was chosen on the dev split. Quantize the backbone and leave the head in float32, as the helper does. Score the fixed sample with both copies, and count the accuracy, the hand-offs, the accuracy on the messages not handed off and the changed predictions, each with its denominator. Read the flips in each direction before reading the totals. Then count again on the dev split at the chosen threshold, because the threshold was chosen there. A copy that passes these steps still has its speed and its memory measured in a recording before it replaces the float32 adapter.

**Working rule:** Serve the float32 adapter by default. Consider the int8 copy only when a recording on the serving machine names a speed gain, a measured memory need favours it, and then count its changed predictions on the dev split at the chosen threshold before it serves a message.
