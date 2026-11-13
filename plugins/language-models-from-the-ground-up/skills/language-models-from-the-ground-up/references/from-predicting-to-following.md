---
title: "Language Models from the Ground Up"
chapter: "From predicting to following instructions"
chapter_id: from-predicting-to-following
book: language-models-from-the-ground-up
edition: 2026.11.10
verified: 2026-11-13
edition_code: ZD73-7XB0
canonical: https://rollingedition.com/language-models-from-the-ground-up/from-predicting-to-following
license: CC BY 4.0
attribution: "“From predicting to following instructions,” chapter 11 of Language Models from the Ground Up, Edition 2026.11.10, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up/from-predicting-to-following. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# From predicting to following instructions

By the end of this chapter you can explain how a model that predicts the next token becomes one that follows requests, build the two training losses that do it, and measure what that change does and doesn't fix. You'll compare a base model with its instruction-tuned version on the same requests, measure how often each makes up a product detail, check whether its confidence warns you when it does, and find where in a longer context a model stops finding what it was given.

This book follows one case throughout: an online furniture and home-goods store, which it calls the store, and the text of its product names and descriptions. Every model in the book so far has done one thing: predict the next token of text like its training text. [Chapter 10](#inside-an-open-model) read **SmolLM2-360M**, an open model trained that way on general text, and found it scored the store's names far worse, per word, than the store's own small model, and its descriptions worse. People don't want a continuation of their text; they want an answer to their request. Models are taught that in two further steps of training.

**Instruction tuning**, or supervised fine-tuning, continues training the model on examples of requests paired with good responses, so that predicting the next token of such a pair means answering the request. Wei and colleagues found that tuning on many tasks phrased as instructions made a model better at tasks it had never seen ([Wei et al., 2022](https://arxiv.org/abs/2109.01652)). **Preference tuning** then trains the model to prefer the better of two responses to the same request. Ouyang and colleagues had people rank the responses, and trained with reinforcement learning from a reward model learned from those rankings ([Ouyang et al., 2022](https://arxiv.org/abs/2203.02155)); **Direct Preference Optimization**, DPO, gets the same effect with a simple loss on the preference pairs themselves ([Rafailov et al., 2023](https://arxiv.org/abs/2305.18290)).

**SmolLM2-360M-Instruct** is the base model of [chapter 10](#inside-an-open-model) after both steps: supervised fine-tuning on public and curated datasets, then DPO on UltraFeedback ([model card](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct/blob/a10cc1512eabd3dde888204e902eca88bddb4951/README.md)). UltraFeedback's preference pairs were scored by a large language model, not by people ([Cui et al., 2023](https://arxiv.org/abs/2310.01377)). This chapter calls SmolLM2-360M the base model and SmolLM2-360M-Instruct the tuned model. The script `recordings/instruction_tuning.py` ran both once, at pinned revisions, decoding greedily, so each answer is the model's likeliest and the run can be repeated exactly, and saved what they wrote and how likely they found each token it wrote. The examples measure everything from those files.

## Build the two training losses by hand {#build-the-losses}

Both steps of tuning are training, with the loop of [chapter 8](#update-with-adamw); what changes is the loss. Instruction tuning uses the ordinary next-token loss with one difference: only the response's tokens count. The request is read, as context, but the model isn't trained to predict it, since the point is to answer requests, not to write them.

For the store, lay a product out as a request and a response, its name as the request and its description as the response, as the store's model already reads it. Compute the store's model's loss over every token, and over the response's tokens only:

Example `instruction-loss-by-hand` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
import numpy as np

from lib import transformer
from lib.store import load_products

_, vocabulary, manifest = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
product = load_products("validation").query("name == 'double chaise patio furniture cover'").iloc[0]
ids = transformer.product_ids(product["name"], product["description"], index, manifest["settings"]["longest"])
sep = ids.index(index[transformer.SEP])           # the name plays the request; the description, the response

probabilities = transformer.softmax(transformer.forward(ids)[:-1])
loss = -np.log(probabilities[np.arange(len(ids) - 1), ids[1:]])     # each token's loss, given the tokens before it
response = np.arange(1, len(ids)) > sep                             # the description's tokens and its end
print("tokens predicted in the text:", len(loss))
print("tokens the instruction loss counts, the response's:", int(response.sum()))
print("average loss over every token:", f"{loss.mean():.3f}")
print("average loss over the response only:", f"{loss[response].mean():.3f}")
```

Output:

```text
tokens predicted in the text: 96
tokens the instruction loss counts, the response's: 90
average loss over every token: 2.267
average loss over the response only: 2.132
```

Of the 96 tokens the model predicts, the instruction loss counts 90: the description's tokens and its end. The average loss over every token is 2.267, and over the response only 2.132. Training on the second number, over many requests and responses, teaches a model to produce responses.

DPO's loss works on a pair of responses to one request, one preferred and one rejected. It compares how much more likely the model being tuned makes each response than the **reference model** it started from, the model after instruction tuning, and rewards it for raising the preferred one more. With log-probabilities log π of each response under the tuned model and log π_ref under the reference, and a factor β that sets how far the model may move:

margin = β × [(log π(preferred) − log π_ref(preferred)) − (log π(rejected) − log π_ref(rejected))]

loss = −log σ(margin)

with σ the logistic function from [chapter 4](#learn-by-predicting-neighbours) ([Rafailov et al., 2023](https://arxiv.org/abs/2305.18290), equation 7). For the store, follow the arithmetic on made-up log-probabilities, with β = 0.1:

Example `dpo-loss-by-hand` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.10:

```python
import numpy as np

beta = 0.1                                       # how far the tuned model may move from the reference
print("beta:", beta)
# Total log-probabilities of a preferred and a rejected answer to one request, under the model being tuned and under
# the reference model it started from. Made-up numbers, to follow the arithmetic.
cases = {"tuned model favours the preferred answer more than the reference does": (-12.0, -20.0, -14.0, -18.0),
         "tuned model favours it less": (-15.0, -15.0, -14.0, -18.0)}
for label, (preferred, rejected, preferred_reference, rejected_reference) in cases.items():
    margin = beta * ((preferred - preferred_reference) - (rejected - rejected_reference))
    loss = np.log1p(np.exp(-margin))             # -log σ(margin), written so it can't overflow
    print(f"{label}, margin:", f"{margin:.2f}")
    print(f"{label}, loss:", f"{loss:.3f}")
```

Output:

```text
beta: 0.1
tuned model favours the preferred answer more than the reference does, margin: 0.40
tuned model favours the preferred answer more than the reference does, loss: 0.513
tuned model favours it less, margin: -0.40
tuned model favours it less, loss: 0.913
```

When the tuned model favours the preferred response more than the reference does, the margin is 0.40 and the loss 0.513; when it favours it less, the margin is -0.40 and the loss rises to 0.913. Lowering the loss pushes the preferred response's probability up and the rejected one's down, measured against where the model started.

**Working rule:** Mask the request out of the loss when you tune a model on requests and responses, and keep the reference model's log-probabilities beside the tuned model's when you train on preferences. Both are small changes to a loop you already have.

## Ask the base model and the tuned model {#ask-base-and-tuned}

The store needs descriptions for products that have none, the job [chapter 9](#choosing-the-next-token) gave its own small model. The base model, SmolLM2-360M, can't be asked, only continued, so it gets the start of a product listing: `Product:`, the name, and `Description:`. The tuned model, SmolLM2-360M-Instruct, gets a request: `Write a short product description for:` and the name.

For the store, read what each model wrote for [chapter 9](#choosing-the-next-token)'s product, `front porch welcome sign wall décor`, and measure all 8 products the recording described, each without a description to draw on:

Example `base-and-tuned` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from collections import Counter

from lib import claims, recorded

described = recorded.read("instruction-tuning", "descriptions")
product = next(row for row in described if row["name"] == "front porch welcome sign wall décor")
print("product:", product["name"])
print("base model:", " ".join(product["base"]["text"].split()))
print("tuned model:", " ".join(product["tuned"]["text"].split()))


def repeats(text):
    """The share of four-word phrases that repeat an earlier one in the text."""
    words = text.lower().split()
    phrases = [tuple(words[i:i + 4]) for i in range(len(words) - 3)]
    return sum(count - 1 for count in Counter(phrases).values()) / max(len(phrases), 1)


print("products described, none of which has a description to draw on:", len(described))
for role in ["base", "tuned"]:
    texts = [row[role]["text"] for row in described]
    invented = sum(bool(claims.materials(row[role]["text"]) - claims.materials(row["name"])) for row in described)
    print(f"{role} model, descriptions that name a material the name doesn't:", f"{invented} of {len(described)}")
    print(f"{role} model, repeated four-word phrases:", f"{sum(map(repeats, texts)) / len(texts):.0%}")
```

Output:

```text
product: front porch welcome sign wall décor
base model: Front porch welcome sign wall décor The front porch is a common feature of many homes. It is a place where people can relax and enjoy the outdoors. It is also a place where people can socialize and meet new friends. The front porch is a great place to hang out with your family
tuned model: "Welcome to our front porch welcome sign wall décor, a space that brings warmth and comfort to your home. This wall is a statement piece that showcases your personality and style. With a mix of rustic and modern elements, you can create a unique and inviting atmosphere that reflects your individuality.
products described, none of which has a description to draw on: 8
base model, descriptions that name a material the name doesn't: 2 of 8
base model, repeated four-word phrases: 14%
tuned model, descriptions that name a material the name doesn't: 1 of 8
tuned model, repeated four-word phrases: 0%
```

For the welcome sign, the base model writes about front porches: `The front porch is a common feature of many homes`, then about relaxing and meeting friends. It continues the text in a plausible direction, which isn't the one the store needs. The tuned model writes something shaped like a product description, `a statement piece that showcases your personality and style`, but calls the sign `a space` and `This wall`: fluent about a product it doesn't understand. Across the products, the base model's texts repeat 14% of their four-word phrases, and the tuned model's 0%. The recording can't say which step of tuning stopped the loops.

Neither model knows anything about the products beyond their names. The base model named a material the name doesn't give in 2 of 8 descriptions, and the tuned model in 1 of 8, and each of those came from the model, not from the store's data, as [chapter 9](#choosing-the-next-token)'s did.

**Working rule:** Use a tuned model when you need a request followed, and a base model when you need text continued in the style of what came before. Don't read fluency as knowledge: a tuned model writes a better-shaped description from the same lack of facts.

## Format the request as the model was tuned {#format-the-request}

The tuned model answered in the [previous section](#ask-base-and-tuned) because its request came in the layout it was tuned on, its **chat template**: special tokens that mark where a **system message**, instructions placed before the user's request, the request itself and the model's reply begin and end. The model learned to answer requests only in that layout, so a request in any other form is only text to continue. Libraries that load the model apply the template from the model's tokenizer files ([tokenizer configuration](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct/blob/a10cc1512eabd3dde888204e902eca88bddb4951/tokenizer_config.json)).

For the store, read exactly what the tuned model was given with its template, and compare its reply with the reply to the same request given as plain text:

Example `chat-template` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from lib import recorded

template = recorded.read("instruction-tuning", "template")
print("request:", template["with"]["prompt"].split("<|im_start|>user\n")[1].split("<|im_end|>")[0])
print("what the tuned model reads, with its chat template:")
print(template["with"]["prompt"])
print("tuned model, with the template:", " ".join(template["with"]["text"].split()))
print("tuned model, without it:", " ".join(template["without"]["text"].split()))
```

Output:

```text
request: Write a short product description for: front porch welcome sign wall décor
what the tuned model reads, with its chat template:
<|im_start|>system
You are a helpful AI assistant named SmolLM, trained by Hugging Face<|im_end|>
<|im_start|>user
Write a short product description for: front porch welcome sign wall décor<|im_end|>
<|im_start|>assistant

tuned model, with the template: "Welcome to our front porch welcome sign wall décor, a space that brings warmth and comfort to your home. This wall is a statement piece that showcases your personality and style. With a mix of rustic and modern elements, you can create a unique and inviting atmosphere that reflects your individuality.
tuned model, without it: .
```

With the template, the request sits between `<|im_start|>user` and `<|im_end|>`, after a system message the template adds by default, `You are a helpful AI assistant named SmolLM, trained by Hugging Face`, and before `<|im_start|>assistant`, where the model's reply begins. The model replies with the description of the previous section. Without the template, given the same words as plain text, the tuned model writes `.` and stops. Tuning didn't teach the model to follow requests in general; it taught it to follow requests in that layout.

The system message matters too: it's part of every request the model reads, so a different one, such as a description of the store and its tone, can change any reply. That makes it a setting to choose and record, like a decoding setting in [chapter 9](#choosing-the-next-token).

**Working rule:** Always format requests to a tuned model with its own chat template, applied by the library from the model's tokenizer files, never assembled by hand. Check the template's default system message, since the model reads it on every request, and record the full formatted prompt with every answer you keep.

## Measure made-up product details {#measure-made-up-details}

A model that writes about a product with no facts has to make them up. The fairer test gives it the facts. Both SmolLM2 models are shown a product's name and real description, and asked: `What material is this product made of? Answer in a few words, using only the description.` The tuned model gets it as a request in its template; the base model gets it as a listing to continue, ending `Question:`, the question, and `Answer:`. If the product's data names a material, a good answer names it; if not, a good answer says the description doesn't say.

Checking the answers takes a list of material words, from `wood` and `metal` to `polyester` and `leather`, in the book's shared module `lib.claims`. An answer is **supported** if every material it names is in the product's name or description, **made up** if it names one that isn't, **declined** if it says the data doesn't say, and **none** if it names no material and doesn't decline. The check has limits, and makes judgement calls: it counts engineered wood such as `mdf` and `rubberwood` as wood, it counts `brushed nickel finish` as naming nickel, and it misses a material the list doesn't include. Every answer it classes is recorded for anyone to read. Making up a detail the input doesn't support is one kind of what's called **hallucination** ([Ji et al., 2023](https://arxiv.org/abs/2202.03629)), and this test measures exactly that kind.

For the store, class each model's answers for 40 products drawn at random, split by whether the product's data names a material. Before you run it, predict whether the tuned model makes up fewer materials than the base model where the data names none:

Example `made-up-materials` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from collections import Counter

from lib import claims, recorded

asked = recorded.read("instruction-tuning", "answers")
print("products asked, each with its description given:", len(asked))
given = [bool(claims.materials(row["description"]) | claims.materials(row["name"])) for row in asked]
print("products whose name or description names a material:", sum(given))
print("products whose name and description name none:", len(given) - sum(given))
for role in ["base", "tuned"]:
    for label, keep in [("data names a material", True), ("data names none", False)]:
        rows = [row for row, named in zip(asked, given) if named == keep]
        counts = Counter(claims.classify(row[role]["text"], row["description"], row["name"]) for row in rows)
        for kind in ["supported", "made up", "none", "declined"]:
            print(f"{role} model, {label}, {kind}:", counts[kind])
```

Output:

```text
products asked, each with its description given: 40
products whose name or description names a material: 28
products whose name and description name none: 12
base model, data names a material, supported: 24
base model, data names a material, made up: 2
base model, data names a material, none: 2
base model, data names a material, declined: 0
base model, data names none, supported: 0
base model, data names none, made up: 7
base model, data names none, none: 5
base model, data names none, declined: 0
tuned model, data names a material, supported: 23
tuned model, data names a material, made up: 3
tuned model, data names a material, none: 2
tuned model, data names a material, declined: 0
tuned model, data names none, supported: 0
tuned model, data names none, made up: 8
tuned model, data names none, none: 4
tuned model, data names none, declined: 0
```

| Answer | Base, data names a material | Tuned, data names a material | Base, data names none | Tuned, data names none |
| --- | --- | --- | --- | --- |
| Supported | 24 | 23 | 0 | 0 |
| Made up | 2 | 3 | 7 | 8 |
| None | 2 | 2 | 5 | 4 |
| Declined | 0 | 0 | 0 | 0 |

Of the products, 28 have data that names a material, and on those both models mostly answer from it. On the 12 that don't, the right answer is that the description doesn't say, and neither model gave it once. Both mostly made a material up instead, and the rest of their answers named none without saying why.

Instruction tuning didn't fix this, and on these products the base model, given a listing to continue, did no worse. The request said to use only the description; when the description had no answer, the models answered anyway, with a material that products like this one often have. Following the form of an instruction isn't the same as knowing when you don't know.

**Working rule:** Test a model on questions its input can't answer, not only on ones it can, and count made-up answers separately. Check every factual claim a model makes about a product against the product's data, automatically where you can, as `lib.claims` does for materials.

## Check whether confidence warns you {#check-confidence}

The [previous section](#measure-made-up-details) classed the tuned model's answers to the material question as supported or made up. If its made-up answers came with low confidence, low confidence could flag them. A model whose confidence matches how often it's right is **calibrated**, and Guo and colleagues found that the deep neural networks they studied often aren't: they were more confident than their accuracy warranted ([Guo et al., 2017](https://arxiv.org/abs/1706.04599)). The recording saved the probability the tuned model gave each token it wrote, its end token included, so a confidence per token can be computed for each answer, as a geometric mean:

confidence per token = exp((log p₁ + … + log pₙ) / n)

the exponential of the average log-probability, the same average that perplexity inverts, so a short answer and a long one are measured on the same scale.

For the store, compare the tuned model's confidence in its supported and made-up answers, and count how many of each a threshold of 0.5 per token would keep:

Example `answer-confidence` (Python 3.12.15 · numpy 2.5.4), passing in Edition 2026.11.10:

```python
import numpy as np

from lib import claims, recorded

asked = recorded.read("instruction-tuning", "answers")
by_kind = {"supported": [], "made up": []}
for row in asked:
    kind = claims.classify(row["tuned"]["text"], row["description"], row["name"])
    if kind in by_kind:
        by_kind[kind].append(np.exp(np.mean(np.log(row["tuned"]["token_probabilities"]))))   # per token, on average
for kind, confidence in by_kind.items():
    print(f"tuned model, {kind} answers:", len(confidence))
    print(f"tuned model, {kind} answers, average probability per token:", f"{np.mean(confidence):.2f}")
threshold = 0.5
for kind, confidence in by_kind.items():
    print(f"tuned model, {kind} answers above {threshold} per token:", f"{sum(c > threshold for c in confidence)} of {len(confidence)}")
```

Output:

```text
tuned model, supported answers: 23
tuned model, supported answers, average probability per token: 0.65
tuned model, made up answers: 11
tuned model, made up answers, average probability per token: 0.45
tuned model, supported answers above 0.5 per token: 21 of 23
tuned model, made up answers above 0.5 per token: 3 of 11
```

The made-up answers are less confident on average, 0.45 per token against 0.65 for supported ones. But a threshold of 0.5 per token would keep 21 of 23 supported answers and still let through 3 of 11 made-up ones. Confidence is a signal, not a filter: it shifts the odds, and it lets confident errors through. With so few answers, these are directions, not rates to rely on.

**Working rule:** Don't use a model's confidence alone to decide whether to trust an answer. Measure how its confidence relates to being right on your own questions, as here, and if you use a threshold, choose it from those measurements and count what it lets through.

## Find what a longer context loses {#find-what-context-loses}

The [material question](#measure-made-up-details) gave the model one product at a time. A store's assistant often has several products' data in front of it at once, such as search results, a category page or a comparison, and has to find the right product's details among the others. Liu and colleagues found that models use information at the start and the end of a long context better than information in the middle ([Liu et al., 2024](https://arxiv.org/abs/2307.03172)).

For the store, give the tuned model, SmolLM2-360M-Instruct, 10 product listings, the asked product among them, first, in the middle or last, and ask what that product is made of. Count the answers that name only its own materials, as `lib.claims` checks them, for the 14 products whose data names one:

Example `answer-position` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from collections import defaultdict

from lib import claims, recorded

context = recorded.read("instruction-tuning", "context")
others = recorded.read("instruction-tuning", "manifest")["settings"]["context_others"]
print("product listings in each context:", others + 1)
results = defaultdict(list)
for row in context:
    if claims.materials(row["description"]) | claims.materials(row["name"]):   # only products whose data names one
        results[row["place"]].append(claims.classify(row["tuned"]["text"], row["description"], row["name"]) == "supported")
print("products asked about at each place:", len(results["first"]))
for place in ["first", "middle", "last"]:
    print(f"product placed {place}, answers that name only its own materials:", f"{sum(results[place])} of {len(results[place])}")
```

Output:

```text
product listings in each context: 10
products asked about at each place: 14
product placed first, answers that name only its own materials: 12 of 14
product placed middle, answers that name only its own materials: 6 of 14
product placed last, answers that name only its own materials: 12 of 14
```

With the product first, 12 of 14 answers name only its materials; last, 12 of 14; in the middle, 6 of 14. A product in the middle is found least often, the pattern Liu and colleagues found in much larger models. The counts are small, but the gap is wide. The context here is short, a few thousand characters, well within the model's limit: the middle loses details long before a context is full.

**Working rule:** Put the details a model most needs at the start or the end of its context, not in the middle, and give it as little unrelated text as the task allows. Test retrieval from a longer context at each position, as here, before trusting a model to find details among many.

## Adapt a model to your text {#adapt-a-model}

[Chapter 10](#inside-an-open-model) found the general model far worse than the store's small model on the store's names, per word. Instruction tuning changes how a model answers, not what it knows about one store. The way to teach it the store's text is **fine-tuning**: continue training it on that text, the same training loop as [chapter 8](#update-with-adamw), starting from the general model's weights instead of random ones.

Full fine-tuning updates every weight, which for a model of hundreds of millions of parameters takes time and memory. **LoRA**, low-rank adaptation, freezes the model's weights and trains a small correction beside some of them. For a weight matrix that maps k numbers to d numbers, it trains a matrix B of d by r and a matrix A of r by k, and adds their product to the weights: W + BA ([Hu et al., 2022](https://arxiv.org/abs/2106.09685)). With a small rank r, there's far less to train and store, and Hu and colleagues found it matched full fine-tuning on the tasks they tested.

For the store, count what LoRA would train on SmolLM2-360M, adapting the query and value weights of every layer, at two ranks, against full fine-tuning. The query weights map 960 numbers to 960; the value weights, because keys and values are grouped, map 960 to 320:

Example `lora-parameters` (Python 3.12.15), passing in Edition 2026.11.10:

```python
from lib import open_model

config = open_model.config("SmolLM2-360M")
width, layers = config["hidden_size"], config["num_hidden_layers"]
key_value_width = config["num_key_value_heads"] * width // config["num_attention_heads"]
total = open_model.parameters(config)["total"]
for rank in [8, 64]:
    # LoRA adds two small matrices beside each adapted weight: width x rank, then rank x output width.
    added = layers * (rank * (width + width) + rank * (width + key_value_width))       # on the query and value weights
    print(f"rank {rank}, parameters trained:", f"{added:,}")
    print(f"rank {rank}, share of the model's parameters:", f"{added / total:.2%}")
print("parameters trained by full fine-tuning:", f"{total:,}")
```

Output:

```text
rank 8, parameters trained: 819,200
rank 8, share of the model's parameters: 0.23%
rank 64, parameters trained: 6,553,600
rank 64, share of the model's parameters: 1.81%
parameters trained by full fine-tuning: 361,821,120
```

At rank 8, LoRA trains 819,200 parameters, 0.23% of the model; at rank 64, 6,553,600, or 1.81%. Full fine-tuning trains all 361,821,120. A rank-8 correction is smaller than the store's own small model, and it can be stored and swapped per task while the base weights stay shared.

This book doesn't run the fine-tuning: our judgement is that even LoRA, over the store's text, would take far longer on a laptop's processor than any recording here. It's the next step for a store that wants a general model to write in its own voice: fine-tune on the catalog, then measure the result against the store's own model, per word, as [chapter 10](#inside-an-open-model) did. Fine-tuning has risks of its own. A model trained on the catalog learns its gaps along with its text, as the store's small model learned to leave a bulb's description empty in [chapter 9](#forbid-an-empty-description). And training on one narrow text can weaken what the model knew before; Biderman and colleagues found LoRA forgets less of it than full fine-tuning ([Biderman et al., 2024](https://arxiv.org/abs/2405.09673)). Both are measured the same way as everything else in this book: on held-out text, before and after.

**Working rule:** To teach a general model your text, fine-tune it on that text, with LoRA when memory or storage is tight, and measure the result on held-out text of the same kind. Don't expect instruction tuning or a cleverer prompt to supply knowledge the model never learned.

## Look back at the yardstick {#look-back-at-the-yardstick}

This book has scored every model the same way on names, from [chapter 3](#counting-further-back) on: perplexity per token of the store's tokenizer, on the store's validation names. The test names were kept aside for one final comparison, so that choices made by looking at the validation names, such as the kept epochs and the mixing shares, couldn't flatter the results. Now they're used. For the store, score the five models that were chosen between on the 4,281 test names, with the mixing shares chosen on validation:

Example `test-names` (Python 3.12.15 · numpy 2.5.4 · pandas 3.1.1), passing in Edition 2026.11.10:

```python
import numpy as np

from lib import neural, transformer
from lib.names import name_tokens
from lib.ngrams import KneserNey, ngrams, padded

# The test names, untouched until now: every model scores each name's tokens and its end. The mixing shares are the
# ones chosen on the validation names, in chapters 5 and 8.
test = name_tokens("test")
counted = KneserNey(name_tokens("train"), 4)
from_counts = np.array([counted.probability(c, t) for text in test for c, t in ngrams(padded(text, 4), 4)])
from_window = neural.token_probabilities(test)
_, vocabulary, _ = transformer.load()
index = {token: i for i, token in enumerate(vocabulary)}
from_transformer = []
for name in test:
    ids = [index[transformer.START]] + [index[t] for t in name] + [index[transformer.SEP]]
    probabilities = transformer.softmax(transformer.forward(ids)[:-1])
    from_transformer += list(probabilities[np.arange(len(ids) - 1), ids[1:]])
from_transformer = np.array(from_transformer)

perplexity = lambda p: f"{np.exp(-np.log(p).mean()):.1f}"
print("test names:", f"{len(test):,}")
print("test perplexity, the 4-gram baseline:", perplexity(from_counts))
print("test perplexity, the window model:", perplexity(from_window))
print("test perplexity, the window model mixed with the counts, share 0.2:", perplexity(0.2 * from_window + 0.8 * from_counts))
print("test perplexity, the store's transformer:", perplexity(from_transformer))
print("test perplexity, the store's transformer mixed with the counts, share 0.5:", perplexity((from_transformer + from_counts) / 2))
```

Output:

```text
test names: 4,281
test perplexity, the 4-gram baseline: 22.9
test perplexity, the window model: 35.4
test perplexity, the window model mixed with the counts, share 0.2: 21.6
test perplexity, the store's transformer: 23.7
test perplexity, the store's transformer mixed with the counts, share 0.5: 18.3
```

Set side by side, the scores tell the book's story in one table, and the test column agrees with the validation one to within a few tenths: the choices made on validation flattered the results very little.

| Model | Chapter | Validation names | Test names |
| --- | --- | --- | --- |
| Counts of single tokens, a 1-gram | [3](#smooth-with-kneser-ney) | 687.2 | |
| Counts of pairs, a 2-gram | [3](#smooth-with-kneser-ney) | 46.9 | |
| Counts of four tokens, the 4-gram baseline | [3](#the-baseline) | 23.1 | 22.9 |
| The window model, a small neural network | [5](#compare-with-the-baseline) | 36.4 | 35.4 |
| The window model mixed with the counts | [5](#mix-with-the-counts) | 21.9 | 21.6 |
| The store's transformer | [8](#compare-on-names) | 24.0 | 23.7 |
| The store's transformer mixed with the counts | [8](#compare-on-names) | 18.4 | 18.3 |

Three lessons run through it. Counting goes a long way on short, formulaic text: no learned model in this book beat the 4-gram baseline on names alone, and both mixes beat it. A learned model earns its place by being wrong in different places from the counts, which is why every mix beat both its parts. And on longer text, where distant context matters, the transformer pulled ahead on its own, as [chapter 8](#compare-on-descriptions) measured on descriptions. Size alone didn't decide anything: [chapter 10's](#score-the-store-text) general model, hundreds of times larger, scored 54,352.8 per word on the store's names, against the store's transformer's 199.3.

None of these numbers says whether a model is useful. Perplexity measures how well a model predicts text like its training text, which is what autocomplete needs. It doesn't measure whether a description is true, whether an answer follows a request, or whether a shopper finds what they came for. This chapter's tests, made-up materials, confidence and the place of a fact in a context, are a first step past perplexity, toward measuring the job itself.

**Working rule:** Keep one fixed yardstick for comparing models, the same text, tokenizer and measure every time, as this book did. Then measure the job itself, with tests built for it, before choosing a model to serve it: a lower perplexity is a reason to test a model, not a reason to ship it.

## What goes wrong in production {#instruction-models-in-production}

A tuned model is the kind people can use without help, and its failures sound as fluent as its successes:

- **It answers when it should say it doesn't know.** The base and the tuned SmolLM2 models made up a material for most products whose data named none, and neither ever said the data didn't say. Check every factual claim against the product's data before it reaches a shopper.
- **Its confidence lets errors through.** Made-up answers were less confident on average, but a threshold that kept most good answers still let 3 of 11 made-up ones through.
- **Its format is part of its training.** Without its chat template, the tuned model wrote a full stop. Apply the template from the model's files, and record the full prompt with every answer.
- **The middle of a context gets lost.** Put the details that matter at the start or the end, and test retrieval at each position.
- **It doesn't know your text.** Instruction tuning teaches the form of answers, not a store's catalog. Fine-tune on the catalog, and measure.
- **Fluency hides gaps.** The tuned model's descriptions read better than the base model's and contain no more facts. Judge generated text by checks on its claims, not by how it reads.
- **Its behaviour depends on its revision and its template's default messages.** Pin the model's revision, as the recording does, and rerun these measurements after any update.

## What this chapter decided {#instruction-decisions}

- **The book compares base and tuned models on the same requests,** recorded once at pinned revisions and decoded greedily, and measures their answers with checks anyone can rerun, such as `lib.claims` for materials.
- **Made-up details are measured on questions the input can't answer** as well as ones it can. On the store's products, both SmolLM2 models made up a material for most products whose data named none, and neither declined once, so generated product facts are always checked against the product's data.
- **A model's confidence is a signal, not a filter.** It's used only with a threshold measured on the store's own questions, and the errors it lets through are counted.
- **The details a model needs go at the start or the end of its context,** never buried among other products.
- **Perplexity stays the book's yardstick for comparing models,** on the same text, tokenizer and events every time, and the job each model is chosen for is measured with tests built for that job.
- **Teaching a general model the store's text means fine-tuning,** measured per word against the store's own model; instruction tuning changes how a model answers, not what it knows. Measuring a model inside an application, beyond the next-token tests of this book, is a subject of its own.
