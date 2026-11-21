---
title: "Glossary"
book: "Small Open Models"
edition: "2026.11.9"
canonical: "https://rollingedition.com/small-open-models/glossary"
---

# Glossary of *Small Open Models*

The 100 terms this book defines, as Edition 2026.11.9 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/small-open-models/glossary

## accuracy

Accuracy is the messages whose team equals the gold label, divided by all the messages in the sample.

- Defined in: [Score the router on a fixed sample](route-a-message.md#score-the-router-on-a-fixed-sample)
- Address: https://rollingedition.com/concepts/model-evaluation/accuracy

## accuracy on messages not handed off

Accuracy on messages not handed off is the correct messages among those the router keeps, divided by the messages it keeps.

- Also: accuracy on kept messages
- Contrasts with: accuracy
- Defined in: [Score the router on a fixed sample](route-a-message.md#score-the-router-on-a-fixed-sample)
- Address: https://rollingedition.com/concepts/model-evaluation/accuracy-on-messages-not-handed-off

## adapter

the trained LoRA matrices are the adapter

- Also: LoRA adapter
- Part of: LoRA
- Defined in: [Adapters train a small part of the model](fine-tune-with-lora.md#adapters-train-a-small-part-of-the-model)
- Address: https://rollingedition.com/concepts/fine-tuning/adapter

## adapter version

The version the route reports is the suffix of the adapter's name.

- Defined in: [What goes wrong in production](serve-the-router-on-a-cpu.md#what-goes-wrong-in-production)
- Address: https://rollingedition.com/concepts/message-routing/adapter-version

## agreement with the teacher

Agreement with the teacher says how much of the teacher the student has learned, whether the teacher is right or wrong.

- Contrasts with: accuracy
- Defined in: [Measure agreement, not only accuracy](distill-a-larger-model.md#measure-agreement-not-only-accuracy)
- Address: https://rollingedition.com/concepts/model-evaluation/agreement-with-teacher

## answer log-probability

the log-probability of the answer, which is the sum of the answer's token log-probabilities

- Computed from: token
- Defined in: [Ask a model for one team](route-a-message.md#ask-a-model-for-one-team)
- Address: https://rollingedition.com/concepts/large-language-models/answer-log-probability

## BANKING77

The messages and their teams come from BANKING77, a public dataset of customer messages to a bank, published under CC BY 4.0.

- Defined in: [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
- Address: https://rollingedition.com/concepts/natural-language-processing/banking77

## banking77-distilled-v1

The student's adapter is banking77-distilled-v1.

- Also: student adapter
- A kind of: adapter
- Defined in: [Train the student on the teacher's labels](distill-a-larger-model.md#train-the-student-on-the-teachers-labels)
- Address: https://rollingedition.com/concepts/fine-tuning/banking77-distilled-v1

## banking77-gold-1000-v1

The control, banking77-gold-1000-v1, is the student's recipe trained on gold labels, and its rows are the rows the teacher labelled.

- Also: gold-label control
- A kind of: adapter
- Contrasts with: banking77-distilled-v1
- Defined in: [Measure agreement, not only accuracy](distill-a-larger-model.md#measure-agreement-not-only-accuracy)
- Address: https://rollingedition.com/concepts/fine-tuning/banking77-gold-1000-v1

## banking77-lora-v1

The working router uses banking77-lora-v1: the adapter from the full recorded run, version 1, written by recordings/lora_full.py.

- Also: recorded adapter, human-labelled adapter
- A kind of: adapter
- Contrasts with: banking77-distilled-v1
- Defined in: [Use the recorded adapter](fine-tune-with-lora.md#use-the-recorded-adapter)
- Address: https://rollingedition.com/concepts/fine-tuning/banking77-lora-v1

## base model

A base model is a model already pretrained on a large amount of text, which you adapt to one job.

- Defined in: [Which candidates we keep](choose-a-base-model.md#the-candidates-and-what-we-keep)
- Address: https://rollingedition.com/concepts/large-language-models/base-model

## baseline

The baseline is the stand-in's score on test_1001, the sample that the final comparison in chapter 10 uses.

- Measured from: test_1001
- Defined in: [The baseline from recorded answers](measure-the-routing-task.md#the-baseline-from-recorded-answers)
- Address: https://rollingedition.com/concepts/model-evaluation/baseline

## break-even

The break-even is the volume at which the hosted model's monthly bill and the machine's are equal.

- Formula: `break-even messages per month = machine bill per month ÷ hosted price per message`
- Computed from: machine bill
- Computed from: hosted bill
- Defined in: [Know the break-even](when-a-small-model-is-the-wrong-choice.md#know-the-break-even)
- Address: https://rollingedition.com/concepts/artificial-intelligence/break-even

## changed-prediction count

The changed-prediction count uses the same 200 messages and asks a question the three measures do not: did the two copies agree on each one?

- Contrasts with: accuracy
- Defined in: [Count the predictions that change](quantize-and-measure.md#count-the-predictions-that-change)
- Address: https://rollingedition.com/concepts/model-evaluation/changed-prediction-count

## chat form

The chat form wraps the router prompt's text in the model's chat template, which adds a default system prompt.

- True for: transformers 5.23.0
- Contrasts with: raw form
- Defined in: [The prompt, settled before any recording](prompt-and-constrain.md#the-prompt-settled-before-any-recording)
- Address: https://rollingedition.com/concepts/large-language-models/chat-form

## classification head

A classification head works differently from the stand-in: it keeps the language model's layers and adds one output layer with 77 outputs, one for each team.

- Also: score head, classifier head
- Defined in: [A head that scores the teams](fine-tune-with-lora.md#a-head-that-scores-the-teams)
- Address: https://rollingedition.com/concepts/fine-tuning/classification-head

## classifier

A classifier reads the message once and returns a score for each team.

- Contrasts with: generative model
- Defined in: [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs)
- Address: https://rollingedition.com/concepts/artificial-intelligence/classifier

## confidence

The confidence is a number from zero to one that says how sure the router is of that team.

- Formula: `confidence = exp(sum of log p(token))`
- Computed from: answer log-probability
- Contrasts with: softmax
- Defined in: [What the router returns](route-a-message.md#what-the-router-returns)
- Address: https://rollingedition.com/concepts/message-routing/confidence

## confidence

In this chapter, the confidence is the softmax probability of the chosen team.

- Computed from: softmax
- Contrasts with: confidence
- Defined in: [A head that scores the teams](fine-tune-with-lora.md#a-head-that-scores-the-teams)
- Address: https://rollingedition.com/concepts/fine-tuning/confidence

## dev baseline

The baseline is the hand-off rate on the dev split at the adapter's threshold.

- A kind of: hand-off rate
- Measured from: dev split
- Part of: hand-off watch
- Defined in: [Watch the hand-off rate](version-watch-and-fall-back.md#watch-the-hand-off-rate)
- Address: https://rollingedition.com/concepts/model-evaluation/dev-baseline

## dev split

the dev split, the training messages held back for choosing settings

- Contrasts with: test split
- Defined in: [What the router returns](route-a-message.md#what-the-router-returns)
- Address: https://rollingedition.com/concepts/model-evaluation/dev-split

## distillation

Distillation trains a small model to reproduce a large one.

- Also: knowledge distillation
- Defined in: [What distillation copies](distill-a-larger-model.md#what-distillation-copies)
- Address: https://rollingedition.com/concepts/fine-tuning/distillation

## drift

A window drifts when its hand-off rate is more than a stated number of points from the baseline, in either direction.

- Computed from: hand-off rate
- Computed from: dev baseline
- Defined in: [Watch the hand-off rate](version-watch-and-fall-back.md#watch-the-hand-off-rate)
- Address: https://rollingedition.com/concepts/model-evaluation/drift

## end-of-answer token

The end-of-answer token is the model's <|im_end|>, which is also its pad token (id 2).

- Also: <|im_end|>
- Part of: trie
- Defined in: [A token trie allows only team names](prompt-and-constrain.md#a-token-trie-allows-only-team-names)
- Address: https://rollingedition.com/concepts/large-language-models/end-of-answer-token

## error

With no threshold applied, the error is one minus accuracy

- Computed from: accuracy
- Defined in: [Where the labels collide](measure-the-routing-task.md#where-the-labels-collide)
- Address: https://rollingedition.com/concepts/model-evaluation/error

## forward pass

the forward passes, each one call of the network

- Also: forward passes
- Defined in: [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs)
- Address: https://rollingedition.com/concepts/large-language-models/forward-pass

## free decoding

the model decoded freely: greedy, taking the highest-scoring token at each step, as in this chapter, but with no mask on the tokens it could pick

- Also: unconstrained decoding
- Defined in: [Why free text fails](prompt-and-constrain.md#why-free-text-fails)
- Address: https://rollingedition.com/concepts/large-language-models/free-decoding

## full fine-tuning

Full fine-tuning changes every weight in the base model.

- Contrasts with: LoRA
- Defined in: [Adapters train a small part of the model](fine-tune-with-lora.md#adapters-train-a-small-part-of-the-model)
- Address: https://rollingedition.com/concepts/fine-tuning/full-fine-tuning

## generative model

A generative model reads the prompt once and then writes its answer one token at a time, and each token it writes is one more pass through the network.

- Contrasts with: classifier
- Defined in: [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs)
- Address: https://rollingedition.com/concepts/large-language-models/generative-model

## greedy answer

Here the teacher's greedy answer plays the part of the mode: it is the one team the teacher returns for each message.

- Contrasts with: soft targets
- Defined in: [What distillation copies](distill-a-larger-model.md#what-distillation-copies)
- Address: https://rollingedition.com/concepts/large-language-models/greedy-answer

## greedy decoding

greedy decoding, which takes the most likely token at each step

- Defined in: [Ask a model for one team](route-a-message.md#ask-a-model-for-one-team)
- Address: https://rollingedition.com/concepts/large-language-models/greedy-decoding

## hand-off

A hand-off gives the message to a person who can route it

- Defined in: [What the router returns](route-a-message.md#what-the-router-returns)
- Address: https://rollingedition.com/concepts/message-routing/hand-off

## hand-off flag

The hand-off flag is true when the confidence is too low to send the message on, and a person takes the message instead.

- Computed from: confidence
- Computed from: threshold
- Defined in: [What the router returns](route-a-message.md#what-the-router-returns)
- Address: https://rollingedition.com/concepts/message-routing/hand-off-flag

## hand-off rate

Hand-off rate is the messages whose confidence is below the threshold, divided by all the messages.

- Computed from: confidence
- Computed from: threshold
- Defined in: [Score the router on a fixed sample](route-a-message.md#score-the-router-on-a-fixed-sample)
- Address: https://rollingedition.com/concepts/model-evaluation/hand-off-rate

## hand-off rule

handoff(confidence, threshold) returns true when the confidence is below the threshold, and false when it is equal to the threshold or above it.

- Defined in: [Hand off the unsure messages](route-a-message.md#hand-off-the-unsure-messages)
- Address: https://rollingedition.com/concepts/message-routing/hand-off-rule

## hand-off watch

A watch needs three things, a window, a baseline and a rule for when a window has moved too far from the baseline.

- Measured from: hand-off rate
- Defined in: [Watch the hand-off rate](version-watch-and-fall-back.md#watch-the-hand-off-rate)
- Address: https://rollingedition.com/concepts/model-evaluation/hand-off-watch

## hosted bill

A hosted model's monthly bill is the number of messages times what one message costs, and one message costs its input tokens at the input price plus its output tokens at the output price.

- Formula: `hosted cost per month = messages × (input tokens × input price + output tokens × output price)`
- Defined in: [Count the bill and the machine](when-a-small-model-is-the-wrong-choice.md#count-the-bill-and-the-machine)
- Address: https://rollingedition.com/concepts/artificial-intelligence/hosted-bill

## inbox

Customer messages to a bank land in one support queue, which this book calls the inbox.

- Defined in: [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
- Address: https://rollingedition.com/concepts/message-routing/inbox

## int8 copy

The int8 copy, named banking77-lora-v1-int8 in the recordings, is the model the helper returns: a derived model built from the adapter, not a second adapter.

- Also: banking77-lora-v1-int8
- Computed from: merging
- Computed from: adapter
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/fine-tuning/int8-copy

## Int8WeightOnlyConfig

The scheme is torchao's Int8WeightOnlyConfig, which the torchao source at v0.18.0 describes as "int8 weight-only symmetric per-channel quantization to linear layers".

- Also: weight-only int8, int8 weight-only quantization
- True for: torchao 0.18.0
- A kind of: quantization
- Implemented by: torchao 0.18.0
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/fine-tuning/int8-weight-only-config

## intra-op threads

The set_num_threads setting covers the threads used inside one operation, the intra-op threads the documentation names.

- Also: set_num_threads
- True for: torch 2.15.0+cpu
- Defined in: [Load the model once at startup](serve-the-router-on-a-cpu.md#load-the-model-once-at-startup)
- Address: https://rollingedition.com/concepts/model-serving/intra-op-threads

## kept message

The keeps are the messages whose answers the route returned

- Defined in: [Sample handed-off messages for people](version-watch-and-fall-back.md#sample-handed-off-messages-for-people)
- Address: https://rollingedition.com/concepts/message-routing/kept-message

## kept-message sample

The check on kept messages is a second sample, drawn in the same way, and it is not a by-product of the sample of handed-off messages.

- Measured from: kept message
- Contrasts with: sample of handed-off messages
- Defined in: [Sample handed-off messages for people](version-watch-and-fall-back.md#sample-handed-off-messages-for-people)
- Address: https://rollingedition.com/concepts/model-evaluation/kept-message-sample

## label scoring

For each team, label scoring sums the log-probability of the team's tokens after the prompt, where a log-probability is the logarithm of the probability the model gives a token.

- Computed from: log-probability
- Defined in: [Why a prior is not a router](prompt-and-constrain.md#why-the-prior-wins)
- Address: https://rollingedition.com/concepts/large-language-models/label-scoring

## layer

a layer is one of the stacked blocks that a token passes through

- Defined in: [Load each model at its pinned revision](choose-a-base-model.md#load-each-model-at-its-pinned-revision)
- Address: https://rollingedition.com/concepts/large-language-models/layer

## linear layer

A linear layer is a weight matrix that maps one vector to another.

- Also: nn.Linear
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/large-language-models/linear-layer

## log-probability

a log-probability is the logarithm of the probability the model gives a token

- Comes before: label scoring
- Defined in: [Why a prior is not a router](prompt-and-constrain.md#why-the-prior-wins)
- Address: https://rollingedition.com/concepts/large-language-models/log-probability

## LoRA

The paper that introduced LoRA, Hu et al. (2021), says it freezes the pre-trained weights and injects trainable low-rank matrices into the layers of the Transformer, and the trained LoRA matrices are the adapter.

- Also: low-rank adaptation
- Contrasts with: full fine-tuning
- Implemented by: peft 0.21.3
- Defined in: [Adapters train a small part of the model](fine-tune-with-lora.md#adapters-train-a-small-part-of-the-model)
- Address: https://rollingedition.com/concepts/fine-tuning/lora

## LoRA rank

The rank, r, is the inner size of each added matrix, and it is kept small.

- Part of: LoRA
- Defined in: [Adapters train a small part of the model](fine-tune-with-lora.md#adapters-train-a-small-part-of-the-model)
- Address: https://rollingedition.com/concepts/fine-tuning/lora-rank

## lora_alpha

lora_alpha sets how strongly the update counts

- Formula: `self.scaling[adapter_name] = lora_alpha / r`
- True for: peft 0.21.3
- Part of: LoRA
- Implemented by: peft 0.21.3
- Defined in: [Adapters train a small part of the model](fine-tune-with-lora.md#adapters-train-a-small-part-of-the-model)
- Address: https://rollingedition.com/concepts/fine-tuning/lora-alpha

## machine bill

A machine's monthly bill is its hours times its hourly rate.

- Formula: `machine cost per month = hours × machine cost per hour`
- Contrasts with: hosted bill
- Defined in: [Count the bill and the machine](when-a-small-model-is-the-wrong-choice.md#count-the-bill-and-the-machine)
- Address: https://rollingedition.com/concepts/artificial-intelligence/machine-bill

## machine capacity

The number of messages a machine can route in a month is its throughput, in messages per second, times the seconds in a month, times its utilisation

- Also: machine capacity per month, capacity
- Formula: `machine capacity per month = messages per second × seconds per month × utilisation`
- Defined in: [Count the bill and the machine](when-a-small-model-is-the-wrong-choice.md#count-the-bill-and-the-machine)
- Address: https://rollingedition.com/concepts/artificial-intelligence/machine-capacity

## machine cost per message

The machine's cost per message at capacity is its fixed bill divided by its capacity

- Computed from: machine bill
- Computed from: machine capacity
- Defined in: [Know the break-even](when-a-small-model-is-the-wrong-choice.md#know-the-break-even)
- Address: https://rollingedition.com/concepts/artificial-intelligence/machine-cost-per-message

## median

The median is the lower of the two middle values, so it is a whole number of tokens.

- Defined in: [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs)
- Address: https://rollingedition.com/concepts/model-evaluation/median

## merging

Merging folds the adapter's update into the base weights, so each layer is one weight matrix, quantized once, and the layer count describes the router.

- Also: merge, merge_and_unload
- True for: peft 0.21.3
- Comes before: int8 copy
- Implemented by: peft 0.21.3
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/fine-tuning/merge

## open-weights licence

An open-weights licence such as Apache-2.0 governs the model's files

- Also: open-weights license
- Defined in: [A teacher whose terms allow it](distill-a-larger-model.md#a-teacher-whose-terms-allow-it)
- Address: https://rollingedition.com/concepts/artificial-intelligence/open-weights-licence

## parameter

A parameter is one of the numbers the model learns during training

- Defined in: [Load each model at its pinned revision](choose-a-base-model.md#load-each-model-at-its-pinned-revision)
- Address: https://rollingedition.com/concepts/large-language-models/parameter

## per-row scale

A per-row scale lets each output row use the full range of the 8-bit integers for its own weights.

- A kind of: quantization scale
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/fine-tuning/per-row-scale

## pinned revision

A revision pinned by a full commit hash names one snapshot of the files

- True for: huggingface_hub 2.4.0
- Defined in: [Load each model at its pinned revision](choose-a-base-model.md#load-each-model-at-its-pinned-revision)
- Address: https://rollingedition.com/concepts/artificial-intelligence/pinned-revision

## pins file

the pins file, examples/models.toml, records the SHA-256 of every file in that snapshot, which the runtime checks

- Also: models.toml
- Defined in: [Load each model at its pinned revision](choose-a-base-model.md#load-each-model-at-its-pinned-revision)
- Address: https://rollingedition.com/concepts/artificial-intelligence/pins-file

## placeholder threshold

A placeholder threshold has no rule behind it: it is a number that lets the rule run.

- A kind of: threshold
- Defined in: [Hand off the unsure messages](route-a-message.md#hand-off-the-unsure-messages)
- Address: https://rollingedition.com/concepts/message-routing/placeholder-threshold

## poorly calibrated

Guo et al. (2017) report that their networks are "poorly calibrated", meaning their confidence does not match how often they are right.

- Defined in: [Choose the threshold on dev](fine-tune-with-lora.md#choose-the-threshold-on-dev)
- Address: https://rollingedition.com/concepts/model-evaluation/poorly-calibrated

## prefix_allowed_tokens_fn

Transformers applies the rule through a callback, prefix_allowed_tokens_fn, which returns the allowed tokens for each position.

- True for: transformers 5.23.0
- Implemented by: transformers 5.23.0
- Defined in: [A token trie allows only team names](prompt-and-constrain.md#a-token-trie-allows-only-team-names)
- Address: https://rollingedition.com/concepts/large-language-models/prefix-allowed-tokens-fn

## prior

If the top team is the same for every message, the score is the model's prior and says little about any one message.

- Computed from: top team
- Defined in: [Why a prior is not a router](prompt-and-constrain.md#why-the-prior-wins)
- Address: https://rollingedition.com/concepts/large-language-models/prior

## quantization

Quantizing a layer stores each of its weights as an 8-bit integer, with a scale that maps the integers back to approximate float values.

- Also: quantizing
- Comes before: int8 copy
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/fine-tuning/quantization

## quantization scale

a scale that maps the integers back to approximate float values

- Part of: quantization
- Defined in: [One call to quantize the linear layers](quantize-and-measure.md#one-call-to-quantize-the-linear-layers)
- Address: https://rollingedition.com/concepts/fine-tuning/quantization-scale

## raw form

The raw form passes the router prompt's text to the model as it stands.

- Also: raw prompt
- Contrasts with: chat form
- Defined in: [The prompt, settled before any recording](prompt-and-constrain.md#the-prompt-settled-before-any-recording)
- Address: https://rollingedition.com/concepts/large-language-models/raw-form

## recording

A recording fixes the answers to one model at one revision, so a reader who runs the same example later sees the same numbers.

- Defined in: [The baseline from recorded answers](measure-the-routing-task.md#the-baseline-from-recorded-answers)
- Address: https://rollingedition.com/concepts/message-routing/recording

## recording manifest

The manifest names the script that made the recording, the model and its pinned revision, the hash of the prompt, the decoding settings and the seed, and the hash of the answers file.

- Also: manifest
- Part of: recording
- Defined in: [The baseline from recorded answers](measure-the-routing-task.md#the-baseline-from-recorded-answers)
- Address: https://rollingedition.com/concepts/message-routing/recording-manifest

## rough router

A router is rough when its threshold is a placeholder and its model is a stand-in

- A kind of: router
- Defined in: [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
- Address: https://rollingedition.com/concepts/message-routing/rough-router

## route

A route is a function that a web framework calls when a request arrives at a path with a method.

- Defined in: [One route that returns the hand-off](serve-the-router-on-a-cpu.md#one-route-that-returns-the-hand-off)
- Address: https://rollingedition.com/concepts/model-serving/route

## router

The router is the whole system: a model, a prompt, a threshold and the code that sends a message on.

- Defined in: [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
- Address: https://rollingedition.com/concepts/message-routing/router

## router prompt

The router's prompt holds the 77 team names, the message and a request for the team

- Also: routing prompt
- Part of: router
- Defined in: [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs)
- Address: https://rollingedition.com/concepts/message-routing/router-prompt

## router_lib

router_lib, the book's shared module

- Defined in: [A token trie allows only team names](prompt-and-constrain.md#a-token-trie-allows-only-team-names)
- Address: https://rollingedition.com/concepts/artificial-intelligence/router-lib

## sample of handed-off messages

A person would label a sample of the handed-off messages, drawn with a fixed seed, and the labels would say which team the person chooses for each.

- Also: handed-off sample
- Contrasts with: kept-message sample
- Defined in: [Sample handed-off messages for people](version-watch-and-fall-back.md#sample-handed-off-messages-for-people)
- Address: https://rollingedition.com/concepts/model-evaluation/handed-off-sample

## selective classification

Letting a router say when it is unsure has a name in the research literature: selective classification, or the reject option.

- Also: reject option
- Defined in: [What the router returns](route-a-message.md#what-the-router-returns)
- Address: https://rollingedition.com/concepts/model-evaluation/selective-classification

## SmolLM2

The first candidate is SmolLM2, a family of models published on Hugging Face.

- Defined in: [Which candidates we keep](choose-a-base-model.md#the-candidates-and-what-we-keep)
- Address: https://rollingedition.com/concepts/artificial-intelligence/smollm2

## SmolLM2-135M-Instruct

SmolLM2-135M-Instruct is the smallest model in the family that this book keeps, and it is the core model for the rest of the book.

- Also: core model
- Defined in: [Show what a small model does first](route-a-message.md#show-what-a-small-model-does-first)
- Address: https://rollingedition.com/concepts/artificial-intelligence/smollm2-135m-instruct

## soft targets

Hinton, Vinyals and Dean's paper, which gave distillation its name, proposed training a small model on the probabilities that a large model gives every class, as soft targets (Hinton et al., 2015, arXiv:1503.02531).

- Defined in: [What distillation copies](distill-a-larger-model.md#what-distillation-copies)
- Address: https://rollingedition.com/concepts/fine-tuning/soft-targets

## softmax

Softmax turns the scores into 77 probabilities that sum to one.

- Defined in: [A head that scores the teams](fine-tune-with-lora.md#a-head-that-scores-the-teams)
- Address: https://rollingedition.com/concepts/large-language-models/softmax

## spawned worker

A spawned worker is a new Python process.

- True for: uvicorn 0.54.0
- Defined in: [What goes wrong in production](serve-the-router-on-a-cpu.md#what-goes-wrong-in-production)
- Address: https://rollingedition.com/concepts/model-serving/spawned-worker

## stand-in

This book doesn't call a hosted model, so it uses a stand-in, a larger open model: Qwen3-4B-Instruct-2507.

- Also: Qwen3-4B-Instruct-2507
- Defined in: [Measure the routing task before you choose a model](measure-the-routing-task.md)
- Address: https://rollingedition.com/concepts/message-routing/stand-in

## suggestion

The recorded answer of the stand-in, Qwen3-4B-Instruct-2507, may travel with a handed-off message as a suggestion, labelled as the stand-in's, and the person decides whether to use it.

- Defined in: [Fall back to a person](version-watch-and-fall-back.md#fall-back-to-a-person)
- Address: https://rollingedition.com/concepts/message-routing/suggestion

## support staff

The people who read messages are the bank's support staff, and a message the router cannot send on goes to one of them.

- Defined in: [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
- Address: https://rollingedition.com/concepts/message-routing/support-staff

## teacher's agreement with gold

The teacher's agreement with gold on the training rows, measured above, is the share of the teacher's training labels that are right.

- Also: teacher agreement
- Contrasts with: agreement with the teacher
- Defined in: [When the teacher is wrong](distill-a-larger-model.md#when-the-teacher-is-wrong)
- Address: https://rollingedition.com/concepts/model-evaluation/teacher-agreement-with-gold

## teacher's recording

the teacher's recording, teacher-labels/manifest.json, which names the teacher's model and version, its settings and the rows it labelled

- Defined in: [Train the student on the teacher's labels](distill-a-larger-model.md#train-the-student-on-the-teachers-labels)
- Address: https://rollingedition.com/concepts/fine-tuning/teacher-recording

## team

A team is a label the router can return, such as card_arrival, and it is never a group of people.

- Also: intent
- Defined in: [Build a router for the bank's inbox that hands off when unsure](route-a-message.md)
- Address: https://rollingedition.com/concepts/message-routing/team

## test split

The test split is the source's own held-out file.

- Contrasts with: dev split
- Defined in: [Dev, test and fixed samples](measure-the-routing-task.md#dev-test-and-fixed-samples)
- Address: https://rollingedition.com/concepts/model-evaluation/test-split

## test_1001

test_1001, a fixed sample of 1,001 test messages

- Part of: test split
- Defined in: [Ask a model for one team](route-a-message.md#ask-a-model-for-one-team)
- Address: https://rollingedition.com/concepts/model-evaluation/test-1001

## test_200

The first 40 messages of the shuffled test sample are test_40, the first 200 are test_200, and the whole sample is test_1001.

- Part of: test_1001
- Defined in: [Dev, test and fixed samples](measure-the-routing-task.md#dev-test-and-fixed-samples)
- Address: https://rollingedition.com/concepts/model-evaluation/test-200

## test_40

test_40, a fixed sample of 40 test messages

- Part of: test_1001
- Defined in: [Score the router on a fixed sample](route-a-message.md#score-the-router-on-a-fixed-sample)
- Address: https://rollingedition.com/concepts/model-evaluation/test-40

## threshold

the threshold is the value below which a message is handed off

- Part of: router
- Defined in: [Three measures, each with its denominator](measure-the-routing-task.md#three-measures-each-with-its-denominator)
- Address: https://rollingedition.com/concepts/message-routing/threshold

## token

A token is a piece of text the model reads and writes.

- Also: tokens
- Defined in: [What the router returns](route-a-message.md#what-the-router-returns)
- Address: https://rollingedition.com/concepts/large-language-models/token

## tokenizer

The tokenizer turns the prompt's text into tokens, the units a model reads.

- Defined in: [Measure what one message costs](choose-a-base-model.md#measure-what-one-message-costs)
- Address: https://rollingedition.com/concepts/large-language-models/tokenizer

## top team

The team with the highest sum is the model's top team for the message.

- Computed from: label scoring
- Defined in: [Why a prior is not a router](prompt-and-constrain.md#why-the-prior-wins)
- Address: https://rollingedition.com/concepts/message-routing/top-team

## trie

a trie: a tree whose paths spell out each team's tokens, with the team's index at the node where its path ends

- Also: token trie
- Computed from: token
- Defined in: [A token trie allows only team names](prompt-and-constrain.md#a-token-trie-allows-only-team-names)
- Address: https://rollingedition.com/concepts/natural-language-processing/token-trie

## truncation

A message longer than 128 tokens is cut at 128 before the model reads it.

- Also: max_length
- Defined in: [Know what the route cannot score](serve-the-router-on-a-cpu.md#reject-what-the-route-cannot-score)
- Address: https://rollingedition.com/concepts/natural-language-processing/truncation

## uniform guess

A uniform guess gives each team the same probability, one in 77, so its loss is the natural log of 77.

- Defined in: [Thirty steps are not enough](fine-tune-with-lora.md#thirty-steps-are-not-enough)
- Address: https://rollingedition.com/concepts/model-evaluation/uniform-guess

## utilisation

utilisation, which is the share of the month it is busy

- Also: utilization
- Part of: machine capacity
- Defined in: [Count the bill and the machine](when-a-small-model-is-the-wrong-choice.md#count-the-bill-and-the-machine)
- Address: https://rollingedition.com/concepts/artificial-intelligence/utilisation

## version check

The version check pins the SHA-256 of each adapter's manifest.json in examples/adapter-pins.json, and make_app refuses to build on any mismatch or a moved base pin.

- Defined in: [The decisions this chapter made](version-watch-and-fall-back.md#the-decisions-this-chapter-made)
- Address: https://rollingedition.com/concepts/artificial-intelligence/version-check
