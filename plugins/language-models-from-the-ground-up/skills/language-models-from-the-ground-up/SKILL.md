---
name: language-models-from-the-ground-up
description: "Use when building, training, evaluating or choosing a language model, or debugging one: next-word prediction and autocomplete, perplexity on held-out text, BPE tokenizers, n-gram baselines with Kneser-Ney smoothing, word embeddings (PPMI, SVD, skip-gram), a small neural model, attention and causal masks, transformer blocks (RMSNorm, RoPE, gated feed-forward), training with AdamW and a learning-rate schedule, decoding (greedy, beam search, temperature, top-k, top-p, repetition penalty), reading an open model's parameters, memory and attention heads, tuning a model (masked instruction loss, preference loss, LoRA) and checking its answers for made-up details, chat templates and long contexts. Small models in NumPy and PyTorch that run on a CPU."
license: CC-BY-4.0
compatibility: "Python 3.12.15 and the pinned packages in scripts/requirements.txt; the scripts run offline."
metadata:
  publisher: "Rolling Edition"
  book: "Language Models from the Ground Up"
  edition: "2026.11.9"
  verified: "2026-11-13"
  examples: "86 of 86 examples pass"
  edition-code: "R2B6-RC8X"
  source: "https://rollingedition.com/language-models-from-the-ground-up"
---

# Language Models from the Ground Up

This agent skill is *Language Models from the Ground Up*, Edition 2026.11.9, from Rolling Edition. Examples passed Nov 13, 2026: 86 of 86 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, `references/` holds each chapter, and `scripts/` holds the examples as the edition ran them.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section in `references/` before you act on it, and adapt it to the project in front of you.
- **Check against the book.** Each example in `scripts/` has its expected output beside it (`.out`), at the versions in `scripts/requirements.txt`. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `R2B6-RC8X` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/language-models-from-the-ground-up
- **Credit the book** when you quote it or reuse its code: Language Models from the Ground Up, Edition 2026.11.9, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

To run an example as the book does, with [uv](https://docs.astral.sh/uv/):

```sh
uv venv --python 3.12.15
uv pip install -r scripts/requirements.txt
cd scripts && ../.venv/bin/python store-text.py
```

## Build and score a counted next-word model

**When:** a project needs a quick next-word model, such as search-box autocomplete, or a way to tell which of two language models predicts its text better.

1. Split the text once, by document, into training, validation and test parts before any model sees it; keep the test part for the final report. [Load the store's text](references/predicting-the-next-word.md#load-the-store-text)
2. Pad each text with start and end markers, count adjacent pairs in the training split only, and keep the raw counts. [Count which word follows which](references/predicting-the-next-word.md#count-word-pairs)
3. Divide each pair's count by its first word's count, and check each word's probabilities sum to one. [Turn counts into probabilities](references/predicting-the-next-word.md#counts-to-probabilities)
4. For autocomplete, offer the top few next words, dropping punctuation. [Suggest the next word as a shopper types](references/predicting-the-next-word.md#suggest-next-words)
5. Read samples generated with a fixed seed, but never choose models by them. [Generate names one word at a time](references/predicting-the-next-word.md#generate-one-word-at-a-time)
6. Score by perplexity on validation text, with natural logarithms and the end marker counted, only between models with the same tokens and text. [Score a model with perplexity](references/predicting-the-next-word.md#score-with-perplexity)
7. Check for infinite perplexity, and count the unseen pairs behind it. [Unseen word pairs break the model](references/predicting-the-next-word.md#unseen-pairs-break-the-model)
8. Smooth before shipping, and not with add-one. [Give unseen pairs a little probability](references/predicting-the-next-word.md#smooth-unseen-pairs)

**Check:** run [the example](scripts/perplexity-on-new-names.py): unsmoothed validation perplexity is inf; [the add-one example](scripts/add-one-smoothing.py) gives 1,575.1.

**Pitfalls:** [What goes wrong in production](references/predicting-the-next-word.md#next-word-in-production): counts go stale as the catalog changes; suggestions need an allowed-token filter; one word of context ignores the rest of the query.

## Choose and check a tokenizer

**When:** a project must decide how to cut its text into tokens, or relies on an open model's tokenizer.

1. Measure how many held-out words are unseen; above a percent or two, don't use word tokens. [Words leave gaps](references/tokens.md#words-leave-gaps)
2. Count characters per word: that factor multiplies every sequence length. [Characters cover everything](references/tokens.md#characters-cover-everything)
3. Learn byte-pair encoding merges from the training split only, keep their order, and break ties by a fixed rule. [Merge the most frequent pair, again and again](references/tokens.md#merge-frequent-pairs)
4. Train the tokenizer on the text the model will learn from, and use it for every model you compare. [Train the store's tokenizer](references/tokens.md#train-the-store-tokenizer)
5. Choose the merge count where tokens per held-out word stops falling much and the share of rare token types starts climbing. [Choose how many merges](references/tokens.md#choose-how-many-merges)
6. With an open model, use its tokenizer as shipped, and budget in its tokens. [Read an open model's tokenizer](references/tokens.md#read-an-open-tokenizer)
7. Apply its merges by hand on your text and compare with the library after any upgrade. [Apply SmolLM2's merges by hand](references/tokens.md#apply-merges-by-hand)

**Check:** run [the example](scripts/vocabulary-size.py): at 4,000 merges a validation word takes 1.22 tokens, and 6% of token types are rare. [The merges example](scripts/merges-by-hand.py) must match the library for every name.

**Pitfalls:** [What goes wrong in production](references/tokens.md#tokens-in-production): a mismatched tokenizer fails silently; numbers tokenize badly; special-token strings in untrusted text can become control tokens.

## Build an n-gram baseline with Kneser-Ney

**When:** a project needs a strong, simple yardstick before training a learned language model.

1. Never judge an order by perplexity on its own training text. [Longer contexts fit the training text better](references/counting-further-back.md#longer-contexts-fit-training)
2. Measure the share of held-out n-grams unseen in training at each order. [Longer contexts run out of evidence](references/counting-further-back.md#longer-contexts-run-out)
3. Combine each order with lower ones; prefer weights set from counts, such as Kneser-Ney; choose any fixed weights on held-out text. [Mix short and long contexts](references/counting-further-back.md#mix-short-and-long-contexts)
4. When backing off, weight tokens by how many contexts they follow, not how often they occur. [Count the contexts a token follows](references/counting-further-back.md#count-contexts-a-token-follows)
5. Use interpolated Kneser-Ney with a discount of 0.75, check one probability by hand, and raise the order only while validation perplexity falls noticeably. [Smooth with Kneser-Ney](references/counting-further-back.md#smooth-with-kneser-ney)
6. Test suggestions for rare prefixes apart from common ones. [Autocomplete with three tokens of context](references/counting-further-back.md#autocomplete-with-more-context)
7. Record the best counted model's validation perplexity as the baseline for every later model, same text and tokenizer. [The baseline every later model is measured against](references/counting-further-back.md#the-baseline)

**Check:** run [the example](scripts/kneser-ney-by-hand.py): 0.8621 by hand against 0.8621 from the module, summing to 1.0000. [The order example](scripts/kneser-ney-by-order.py) prints the 4-gram baseline, 23.1.

**Pitfalls:** [What goes wrong in production](references/counting-further-back.md#ngrams-in-production): tables grow, so prune and remeasure; rare contexts get generic answers; hand-written backoff often loses probability, so check sums.

## Build and check word embeddings

**When:** a project needs related tokens or short texts to sit close together as vectors.

1. Use one-hot vectors only as an index for learned ones. [One-hot vectors know nothing](references/words-as-vectors.md#one-hot-vectors-know-nothing)
2. Count co-occurrence within two to five tokens, never across documents. [Describe a token by the tokens around it](references/words-as-vectors.md#describe-by-neighbours)
3. Reweight with positive PMI, keeping only frequent tokens or requiring a minimum count. [Weigh co-occurrence by surprise](references/words-as-vectors.md#weigh-by-surprise)
4. Compress with SVD to 50 to 300 dimensions, then read some nearest neighbours. [Compress counts into dense vectors](references/words-as-vectors.md#compress-into-dense-vectors)
5. For skip-gram, draw noise tokens by frequency to the power 0.75, and check one update by hand. [Learn vectors by predicting neighbours](references/words-as-vectors.md#learn-by-predicting-neighbours)
6. Never read high similarity as synonymy without checking for opposites. [Compare learned vectors with counted ones](references/words-as-vectors.md#compare-learned-and-counted)
7. Judge embeddings by their task, not analogies. [Analogies, and where they fail](references/words-as-vectors.md#analogies-and-where-they-fail)
8. Average token vectors for a quick view of short texts; expect loose ranking. [Find similar names with vectors](references/words-as-vectors.md#find-similar-names)

**Check:** run [the example](scripts/svd-neighbours.py): 0.84, against 0.0 in [the one-hot example](scripts/one-hot-vectors.py).

**Pitfalls:** [What goes wrong in production](references/words-as-vectors.md#vectors-in-production): similar use isn't similar meaning; rare tokens get poor vectors or none; embeddings go stale.

## Train a neural language model and compare it with the baseline

**When:** a project trains a small neural language model and must show whether it helps.

1. Write the forward pass by hand once, printing every shape. [Predict from a window of embeddings](references/a-neural-language-model.md#predict-from-a-window)
2. Check hand-written gradients against nudged estimates. [Compute gradients by backpropagation](references/a-neural-language-model.md#compute-gradients)
3. Check the loss falls on a handful of examples; try a few step sizes. [Take gradient descent steps](references/a-neural-language-model.md#take-gradient-descent-steps)
4. Train with a library, keeping your own forward pass to check it. [Train with PyTorch](references/a-neural-language-model.md#train-with-pytorch)
5. Keep the best epoch's weights by validation loss, never the last. [Stop when validation loss turns up](references/a-neural-language-model.md#stop-at-the-best-epoch)
6. Compare with the counted baseline, split by seen and unseen contexts. [Compare with the baseline](references/a-neural-language-model.md#compare-with-the-baseline)
7. When close, mix the two, choosing the share on held-out text. [Mix the network with the counts](references/a-neural-language-model.md#mix-with-the-counts)
8. Add training text only if it resembles the target; measure on the target. [More text helps only if it's the same kind](references/a-neural-language-model.md#same-kind-of-text)
9. Judge predictions by measurements over many contexts, not examples. [Suggest from similar contexts](references/a-neural-language-model.md#suggest-from-similar-contexts)

**Check:** run [the example](scripts/gradients-by-hand.py) (True), then [the comparison](scripts/neural-vs-baseline.py): 36.4 against the baseline's 23.1.

**Pitfalls:** [What goes wrong in production](references/a-neural-language-model.md#neural-in-production): overfitting is silent; mismatched training text hurts; averages hide rare contexts; a mix needs both models at serving time, so rebuild the counts whenever you retrain.

## Implement and inspect attention

**When:** a project writes or debugs attention, or asks what a trained model's heads do.

1. Write attention's four lines once and print the weight matrix. [Look back with a weighted average](references/attention.md#look-back-with-a-weighted-average)
2. Mask scores before softmax; test that later positions get zero weight and that changing a later token leaves earlier outputs alone. [Hide the future with a causal mask](references/attention.md#hide-the-future)
3. Divide scores by the square root of the query's size; check what a loaded model does. [Scale the scores](references/attention.md#scale-the-scores)
4. Keep heads at least 32 numbers wide; check the weights are heads by positions by positions. [Several heads look for different things](references/attention.md#several-heads)
5. Read weights on texts you understand, as hypotheses. [Read what trained heads attend to](references/attention.md#read-trained-heads)
6. Test each hypothesis by changing the input, with a control change. [Test what the model copies](references/attention.md#test-what-the-model-copies)
7. Describe heads by averages over a few hundred texts, beside an even spread. [Some heads attend to the previous token](references/attention.md#attend-to-the-previous-token)
8. Measure how far back it attends, report marker weight apart, and keep the first tokens when cutting context. [Reach past the window](references/attention.md#reach-past-the-window)

**Check:** run [the example](scripts/causal-mask.py): weight on later tokens is 0.0, and with the mask, whether an earlier output changes with the last token reads False.

**Pitfalls:** [What goes wrong in production](references/attention.md#attention-in-production): cost grows with the square of the length; a wrong mask fails silently; attention weights aren't explanations; a fully masked row becomes NaN.

## Build a transformer, or load another model's weights

**When:** a project implements a transformer block, or runs someone else's weights in its own code.

1. Write blocks as additions to a fixed-width residual stream; measure what each part adds. [Add each part's output to a residual stream](references/the-transformer-block.md#add-to-the-residual-stream)
2. Normalize before each part and before the output layer, with RMSNorm. [Normalize before each part](references/the-transformer-block.md#normalize-before-each-part)
3. Use a gated SiLU feed-forward layer, about 8/3 the stream's width. [Transform each position with a gated feed-forward layer](references/the-transformer-block.md#transform-each-position)
4. Rotate queries and keys, never values; check pairing and base. [Give attention positions with rotations](references/the-transformer-block.md#rotary-positions)
5. Tie the output layer to the embeddings in a small model. [Tie the output layer to the embeddings](references/the-transformer-block.md#tie-the-output)
6. Check your forward pass against the library on a full text. [Check the model against PyTorch](references/the-transformer-block.md#check-against-pytorch)
7. Remove a block and measure, rather than read its weights. [Leave out a block to see what it does](references/the-transformer-block.md#leave-out-a-block)
8. Before loading weights, compare the configuration line by line: normalization and ε, RoPE pairing and base, gating, tied outputs, shared keys and values. Then score known text against reference outputs. [Measure what a mismatched detail costs](references/the-transformer-block.md#measure-mismatched-details)
9. Count parameters by part. [Count where the parameters go](references/the-transformer-block.md#count-the-parameters)

**Check:** run [the example](scripts/transformer-same-as-pytorch.py) (True), then [the mismatch example](scripts/mismatched-details.py): 24.3 as trained, 26.4 with the wrong RoPE base, and no error.

**Pitfalls:** [What goes wrong in production](references/the-transformer-block.md#transformer-in-production): mismatched details fail quietly; lengths beyond training are untested; large values overflow at reduced precision.

## Train a small transformer

**When:** a project trains a small transformer on its own text and must pick the run to keep.

1. Build inputs and shifted targets, mask padding out of the loss, shuffle with a fixed seed, and measure padding. [Turn products into batches](references/training-a-small-model.md#turn-products-into-batches)
2. Use AdamW with modest weight decay, and clip gradients by combined length. [Update with AdamW and clipped gradients](references/training-a-small-model.md#update-with-adamw)
3. Warm up for a few hundred steps, then decay; check saved step sizes against the schedule. [Warm up, then decay the step size](references/training-a-small-model.md#warm-up-then-decay)
4. Keep the best epoch by validation loss on each kind of text; never compare perplexities across kinds. [Read the training curve](references/training-a-small-model.md#read-the-training-curve)
5. Compare with the baseline on exactly the same predictions. [Compare with the baseline on names](references/training-a-small-model.md#compare-on-names)
6. Measure each kind of text served, split by seen and unseen contexts, and try a mix. [Compare on descriptions](references/training-a-small-model.md#compare-on-descriptions)
7. Prefer new text to more epochs, and change one thing per run. [What width, data and steps buy](references/training-a-small-model.md#what-width-data-and-steps-buy)
8. Test autocomplete on rare and common prefixes, with controls. [Suggest the next word in the search box](references/training-a-small-model.md#autocomplete-in-the-search-box)

**Check:** run [the example](scripts/learning-rate-schedule.py) (True), then [the comparison](scripts/transformer-on-descriptions.py): 20.1 against the 4-gram's 22.5.

**Pitfalls:** [What goes wrong in production](references/training-a-small-model.md#training-in-production): a schedule bug looks like a model problem; choices made on validation data flatter the result; repeated text gets memorized; padding wastes computation, so pack texts or group them by length.

## Choose decoding settings

**When:** a project generates text and must choose how each next token is picked.

1. Use greedy decoding for short, repeatable output; expect loops on longer text. [Choose the likeliest token](references/choosing-the-next-token.md#choose-the-likeliest-token)
2. Use beam search for short completions; rank longer text per token. [Search for the likeliest text](references/choosing-the-next-token.md#search-for-the-likeliest-text)
3. Keep temperature at or a little below 1. [Sample, with a temperature](references/choosing-the-next-token.md#sample-with-a-temperature)
4. For varied text, use top-p around 0.9 or top-k around 20, with a fixed seed. [Sample, and cut the tail](references/choosing-the-next-token.md#sample-and-cut-the-tail)
5. Compare settings on measures against real text, then read samples and check every factual claim. [Measure what each setting writes](references/choosing-the-next-token.md#measure-each-setting)
6. With greedy or low-temperature decoding, add a repetition penalty of 1.2 to 1.3 and check length. [Penalize repetition](references/choosing-the-next-token.md#penalize-repetition)
7. Set a minimum length if the training text has empty examples. [Forbid an empty description](references/choosing-the-next-token.md#forbid-an-empty-description)

**Check:** run [the example](scripts/measure-decoding.py): repeated 4-token phrases are 11% for greedy against 0% for real descriptions; [the minimum-length example](scripts/minimum-length.py) prints the empty description's probability, 0.28.

**Pitfalls:** [What goes wrong in production](references/choosing-the-next-token.md#decoding-in-production): fluent text states made-up facts; gaps in the training text become outputs; settings drift with each retrained model.

## Size up an open model before using it

**When:** a project considers an open-weights model and needs its cost, design and fit to its own text.

1. Count parameters by part from the weights, reading shapes for tying, grouped keys and values, and gating. [Count the parameters at scale](references/inside-an-open-model.md#parameters-at-scale)
2. Count from the configuration too; a mismatch means a misread detail. [Compare a family's sizes](references/inside-an-open-model.md#grow-the-same-design)
3. Budget memory as weights plus a key and value cache per text, and cap text length. [Count what it costs to run](references/inside-an-open-model.md#cost-to-run)
4. Score your own text per word or per character on the same events, never per token, against a model trained on it. [Score the store's text with a general model](references/inside-an-open-model.md#score-the-store-text)
5. Describe heads by averages beside an even spread; keep the first token. [Find the same heads at scale](references/inside-an-open-model.md#same-heads-at-scale)
6. Run the same input-change tests on every model. [Test copying at scale](references/inside-an-open-model.md#copying-at-scale)
7. Measure its suggestions on your own prefixes. [Suggest the next word at scale](references/inside-an-open-model.md#suggestions-at-scale)
8. Compare candidates side by side, and choose a model per job. [Set the two models side by side](references/inside-an-open-model.md#side-by-side)

**Check:** run [the example](scripts/open-model-on-the-store.py): per-word perplexity on names is 54,352.8 for the open model against 199.3 for the small model trained on the text.

**Pitfalls:** [What goes wrong in production](references/inside-an-open-model.md#open-models-in-production): its text and tokenizer aren't yours; its details must match the running code; its revision changes, so pin it; check its licence.

## Tune an instruction model and check its answers

**When:** a project uses a tuned model to answer or write about its own data, and must know what it gets wrong.

1. When tuning, mask the request out of the loss; for preferences, keep the reference model's log-probabilities. [Build the two training losses by hand](references/from-predicting-to-following.md#build-the-losses)
2. Use a tuned model to follow requests and a base model to continue text. [Ask the base model and the tuned model](references/from-predicting-to-following.md#ask-base-and-tuned)
3. Apply the model's own chat template through the library, check its default system message, and record the full prompt. [Format the request as the model was tuned](references/from-predicting-to-following.md#format-the-request)
4. Ask questions the input can't answer, count made-up answers, and check claims against the data. [Measure made-up product details](references/from-predicting-to-following.md#measure-made-up-details)
5. Measure how confidence relates to being right before using a threshold. [Check whether confidence warns you](references/from-predicting-to-following.md#check-confidence)
6. Put key details at the start or end of the context, and test each position. [Find what a longer context loses](references/from-predicting-to-following.md#find-what-context-loses)
7. Fine-tune on your text, with LoRA when memory is tight, and measure on held-out text. [Adapt a model to your text](references/from-predicting-to-following.md#adapt-a-model)
8. Keep one fixed yardstick, then test the job itself before serving. [Look back at the yardstick](references/from-predicting-to-following.md#look-back-at-the-yardstick)

**Check:** run [the example](scripts/made-up-materials.py): where the data names no material, the tuned model made one up 8 times and declined 0; in [the confidence example](scripts/answer-confidence.py), 3 of 11 made-up answers pass a 0.5 threshold.

**Pitfalls:** [What goes wrong in production](references/from-predicting-to-following.md#instruction-models-in-production): it answers when it should say it doesn't know; fluency hides gaps; its behaviour depends on its revision and template.
