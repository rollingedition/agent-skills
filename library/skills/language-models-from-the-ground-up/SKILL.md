---
name: language-models-from-the-ground-up
description: "Use when building, training, evaluating or choosing a language model, or debugging one: next-word prediction and autocomplete, perplexity on held-out text, BPE tokenizers, n-gram baselines with Kneser-Ney smoothing, word embeddings (PPMI, SVD, skip-gram), a small neural model, attention and causal masks, transformer blocks (RMSNorm, RoPE, gated feed-forward), training with AdamW and a learning-rate schedule, decoding (greedy, beam search, temperature, top-k, top-p, repetition penalty), reading an open model's parameters, memory and attention heads, tuning a model (masked instruction loss, preference loss, LoRA) and checking its answers for made-up details, chat templates and long contexts. Small models in NumPy and PyTorch that run on a CPU."
license: CC-BY-4.0
compatibility: "The book's examples ran on Python 3.12.15 and the versions its pages name."
metadata:
  publisher: "Rolling Edition"
  book: "Language Models from the Ground Up"
  edition: "2026.11.12"
  verified: "2026-11-13"
  examples: "86 of 86 examples pass"
  edition-code: "J2AF-6HWB"
  source: "https://rollingedition.com/language-models-from-the-ground-up"
---

# Language Models from the Ground Up

This agent skill is *Language Models from the Ground Up*, Edition 2026.11.12, from Rolling Edition. Examples passed Nov 13, 2026: 86 of 86 examples pass. It's built from that edition, never written separately: the procedures below come from the book's sections, and each step links to its section on rollingedition.com, whose page has the section's text and its examples, with their code and output.

## How to use this skill

- **Pick the procedure that fits the task,** and follow its steps in order. Each step links the section it comes from: read that section before you act on it, with the Rolling Edition MCP server's `get_section` (book `language-models-from-the-ground-up` and the section's ID, the link's last part) or on its page, and adapt it to the project in front of you.
- **Check against the book.** An example's section shows its code, the versions it ran on and its output. If the project uses other versions, say so before relying on a step.
- **Is this copy current?** Call `check_code` with `J2AF-6HWB` on the Rolling Edition MCP server (https://rollingedition.ai/mcp), or compare the edition with the book's page: https://rollingedition.com/language-models-from-the-ground-up
- **Credit the book** when you quote it or reuse its code: Language Models from the Ground Up, Edition 2026.11.12, examples passed Nov 13, 2026. By Rolling Edition, https://rollingedition.com/language-models-from-the-ground-up. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people.

The full skill, with the chapters beside it and every example as a script to run at the book's pinned versions, is the `language-models-from-the-ground-up` plugin and the zip on the book's page at rollingedition.ai.

## Build and score a counted next-word model

**When:** a project needs a quick next-word model, such as search-box autocomplete, or a way to tell which of two language models predicts its text better.

1. Split the text once, by document, into training, validation and test parts before any model sees it; keep the test part for the final report. [Load the store's text](https://rollingedition.com/language-models-from-the-ground-up/s/load-the-store-text)
2. Pad each text with start and end markers, count adjacent pairs in the training split only, and keep the raw counts. [Count which word follows which](https://rollingedition.com/language-models-from-the-ground-up/s/count-word-pairs)
3. Divide each pair's count by its first word's count, and check each word's probabilities sum to one. [Turn counts into probabilities](https://rollingedition.com/language-models-from-the-ground-up/s/counts-to-probabilities)
4. For autocomplete, offer the top few next words, dropping punctuation. [Suggest the next word as a shopper types](https://rollingedition.com/language-models-from-the-ground-up/s/suggest-next-words)
5. Read samples generated with a fixed seed, but never choose models by them. [Generate names one word at a time](https://rollingedition.com/language-models-from-the-ground-up/s/generate-one-word-at-a-time)
6. Score by perplexity on validation text, with natural logarithms and the end marker counted, only between models with the same tokens and text. [Score a model with perplexity](https://rollingedition.com/language-models-from-the-ground-up/s/score-with-perplexity)
7. Check for infinite perplexity, and count the unseen pairs behind it. [Unseen word pairs break the model](https://rollingedition.com/language-models-from-the-ground-up/s/unseen-pairs-break-the-model)
8. Smooth before shipping, and not with add-one. [Give unseen pairs a little probability](https://rollingedition.com/language-models-from-the-ground-up/s/smooth-unseen-pairs)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/unseen-pairs-break-the-model): unsmoothed validation perplexity is inf; [the add-one example](https://rollingedition.com/language-models-from-the-ground-up/s/smooth-unseen-pairs) gives 1,575.1.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/next-word-in-production): counts go stale as the catalog changes; suggestions need an allowed-token filter; one word of context ignores the rest of the query.

## Choose and check a tokenizer

**When:** a project must decide how to cut its text into tokens, or relies on an open model's tokenizer.

1. Measure how many held-out words are unseen; above a percent or two, don't use word tokens. [Words leave gaps](https://rollingedition.com/language-models-from-the-ground-up/s/words-leave-gaps)
2. Count characters per word: that factor multiplies every sequence length. [Characters cover everything](https://rollingedition.com/language-models-from-the-ground-up/s/characters-cover-everything)
3. Learn byte-pair encoding merges from the training split only, keep their order, and break ties by a fixed rule. [Merge the most frequent pair, again and again](https://rollingedition.com/language-models-from-the-ground-up/s/merge-frequent-pairs)
4. Train the tokenizer on the text the model will learn from, and use it for every model you compare. [Train the store's tokenizer](https://rollingedition.com/language-models-from-the-ground-up/s/train-the-store-tokenizer)
5. Choose the merge count where tokens per held-out word stops falling much and the share of rare token types starts climbing. [Choose how many merges](https://rollingedition.com/language-models-from-the-ground-up/s/choose-how-many-merges)
6. With an open model, use its tokenizer as shipped, and budget in its tokens. [Read an open model's tokenizer](https://rollingedition.com/language-models-from-the-ground-up/s/read-an-open-tokenizer)
7. Apply its merges by hand on your text and compare with the library after any upgrade. [Apply SmolLM2's merges by hand](https://rollingedition.com/language-models-from-the-ground-up/s/apply-merges-by-hand)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/choose-how-many-merges): at 4,000 merges a validation word takes 1.22 tokens, and 6% of token types are rare. [The merges example](https://rollingedition.com/language-models-from-the-ground-up/s/apply-merges-by-hand) must match the library for every name.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/tokens-in-production): a mismatched tokenizer fails silently; numbers tokenize badly; special-token strings in untrusted text can become control tokens.

## Build an n-gram baseline with Kneser-Ney

**When:** a project needs a strong, simple yardstick before training a learned language model.

1. Never judge an order by perplexity on its own training text. [Longer contexts fit the training text better](https://rollingedition.com/language-models-from-the-ground-up/s/longer-contexts-fit-training)
2. Measure the share of held-out n-grams unseen in training at each order. [Longer contexts run out of evidence](https://rollingedition.com/language-models-from-the-ground-up/s/longer-contexts-run-out)
3. Combine each order with lower ones; prefer weights set from counts, such as Kneser-Ney; choose any fixed weights on held-out text. [Mix short and long contexts](https://rollingedition.com/language-models-from-the-ground-up/s/mix-short-and-long-contexts)
4. When backing off, weight tokens by how many contexts they follow, not how often they occur. [Count the contexts a token follows](https://rollingedition.com/language-models-from-the-ground-up/s/count-contexts-a-token-follows)
5. Use interpolated Kneser-Ney with a discount of 0.75, check one probability by hand, and raise the order only while validation perplexity falls noticeably. [Smooth with Kneser-Ney](https://rollingedition.com/language-models-from-the-ground-up/s/smooth-with-kneser-ney)
6. Test suggestions for rare prefixes apart from common ones. [Autocomplete with three tokens of context](https://rollingedition.com/language-models-from-the-ground-up/s/autocomplete-with-more-context)
7. Record the best counted model's validation perplexity as the baseline for every later model, same text and tokenizer. [The baseline every later model is measured against](https://rollingedition.com/language-models-from-the-ground-up/s/the-baseline)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/smooth-with-kneser-ney): 0.8621 by hand against 0.8621 from the module, summing to 1.0000. [The order example](https://rollingedition.com/language-models-from-the-ground-up/s/smooth-with-kneser-ney) prints the 4-gram baseline, 23.1.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/ngrams-in-production): tables grow, so prune and remeasure; rare contexts get generic answers; hand-written backoff often loses probability, so check sums.

## Build and check word embeddings

**When:** a project needs related tokens or short texts to sit close together as vectors.

1. Use one-hot vectors only as an index for learned ones. [One-hot vectors know nothing](https://rollingedition.com/language-models-from-the-ground-up/s/one-hot-vectors-know-nothing)
2. Count co-occurrence within two to five tokens, never across documents. [Describe a token by the tokens around it](https://rollingedition.com/language-models-from-the-ground-up/s/describe-by-neighbours)
3. Reweight with positive PMI, keeping only frequent tokens or requiring a minimum count. [Weigh co-occurrence by surprise](https://rollingedition.com/language-models-from-the-ground-up/s/weigh-by-surprise)
4. Compress with SVD to 50 to 300 dimensions, then read some nearest neighbours. [Compress counts into dense vectors](https://rollingedition.com/language-models-from-the-ground-up/s/compress-into-dense-vectors)
5. For skip-gram, draw noise tokens by frequency to the power 0.75, and check one update by hand. [Learn vectors by predicting neighbours](https://rollingedition.com/language-models-from-the-ground-up/s/learn-by-predicting-neighbours)
6. Never read high similarity as synonymy without checking for opposites. [Compare learned vectors with counted ones](https://rollingedition.com/language-models-from-the-ground-up/s/compare-learned-and-counted)
7. Judge embeddings by their task, not analogies. [Analogies, and where they fail](https://rollingedition.com/language-models-from-the-ground-up/s/analogies-and-where-they-fail)
8. Average token vectors for a quick view of short texts; expect loose ranking. [Find similar names with vectors](https://rollingedition.com/language-models-from-the-ground-up/s/find-similar-names)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/compress-into-dense-vectors): 0.84, against 0.0 in [the one-hot example](https://rollingedition.com/language-models-from-the-ground-up/s/one-hot-vectors-know-nothing).

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/vectors-in-production): similar use isn't similar meaning; rare tokens get poor vectors or none; embeddings go stale.

## Train a neural language model and compare it with the baseline

**When:** a project trains a small neural language model and must show whether it helps.

1. Write the forward pass by hand once, printing every shape. [Predict from a window of embeddings](https://rollingedition.com/language-models-from-the-ground-up/s/predict-from-a-window)
2. Check hand-written gradients against nudged estimates. [Compute gradients by backpropagation](https://rollingedition.com/language-models-from-the-ground-up/s/compute-gradients)
3. Check the loss falls on a handful of examples; try a few step sizes. [Take gradient descent steps](https://rollingedition.com/language-models-from-the-ground-up/s/take-gradient-descent-steps)
4. Train with a library, keeping your own forward pass to check it. [Train with PyTorch](https://rollingedition.com/language-models-from-the-ground-up/s/train-with-pytorch)
5. Keep the best epoch's weights by validation loss, never the last. [Stop when validation loss turns up](https://rollingedition.com/language-models-from-the-ground-up/s/stop-at-the-best-epoch)
6. Compare with the counted baseline, split by seen and unseen contexts. [Compare with the baseline](https://rollingedition.com/language-models-from-the-ground-up/s/compare-with-the-baseline)
7. When close, mix the two, choosing the share on held-out text. [Mix the network with the counts](https://rollingedition.com/language-models-from-the-ground-up/s/mix-with-the-counts)
8. Add training text only if it resembles the target; measure on the target. [More text helps only if it's the same kind](https://rollingedition.com/language-models-from-the-ground-up/s/same-kind-of-text)
9. Judge predictions by measurements over many contexts, not examples. [Suggest from similar contexts](https://rollingedition.com/language-models-from-the-ground-up/s/suggest-from-similar-contexts)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/compute-gradients) (yes), then [the comparison](https://rollingedition.com/language-models-from-the-ground-up/s/compare-with-the-baseline): 36.4 against the baseline's 23.1.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/neural-in-production): overfitting is silent; mismatched training text hurts; averages hide rare contexts; a mix needs both models at serving time, so rebuild the counts whenever you retrain.

## Implement and inspect attention

**When:** a project writes or debugs attention, or asks what a trained model's heads do.

1. Write attention's four lines once and print the weight matrix. [Look back with a weighted average](https://rollingedition.com/language-models-from-the-ground-up/s/look-back-with-a-weighted-average)
2. Mask scores before softmax; test that later positions get zero weight and that changing a later token leaves earlier outputs alone. [Hide the future with a causal mask](https://rollingedition.com/language-models-from-the-ground-up/s/hide-the-future)
3. Divide scores by the square root of the query's size; check what a loaded model does. [Scale the scores](https://rollingedition.com/language-models-from-the-ground-up/s/scale-the-scores)
4. Keep heads at least 32 numbers wide; check the weights are heads by positions by positions. [Several heads look for different things](https://rollingedition.com/language-models-from-the-ground-up/s/several-heads)
5. Read weights on texts you understand, as hypotheses. [Read what trained heads attend to](https://rollingedition.com/language-models-from-the-ground-up/s/read-trained-heads)
6. Test each hypothesis by changing the input, with a control change. [Test what the model copies](https://rollingedition.com/language-models-from-the-ground-up/s/test-what-the-model-copies)
7. Describe heads by averages over a few hundred texts, beside an even spread. [Some heads attend to the previous token](https://rollingedition.com/language-models-from-the-ground-up/s/attend-to-the-previous-token)
8. Measure how far back it attends, report marker weight apart, and keep the first tokens when cutting context. [Reach past the window](https://rollingedition.com/language-models-from-the-ground-up/s/reach-past-the-window)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/hide-the-future): weight on later tokens is 0.0, and with the mask, changing the last token moves the output at an earlier position by 0.00.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/attention-in-production): cost grows with the square of the length; a wrong mask fails silently; attention weights aren't explanations; a fully masked row becomes NaN.

## Build a transformer, or load another model's weights

**When:** a project implements a transformer block, or runs someone else's weights in its own code.

1. Write blocks as additions to a fixed-width residual stream; measure what each part adds. [Add each part's output to a residual stream](https://rollingedition.com/language-models-from-the-ground-up/s/add-to-the-residual-stream)
2. Normalize before each part and before the output layer, with RMSNorm. [Normalize before each part](https://rollingedition.com/language-models-from-the-ground-up/s/normalize-before-each-part)
3. Use a gated SiLU feed-forward layer, about 8/3 the stream's width. [Transform each position with a gated feed-forward layer](https://rollingedition.com/language-models-from-the-ground-up/s/transform-each-position)
4. Rotate queries and keys, never values; check pairing and base. [Give attention positions with rotations](https://rollingedition.com/language-models-from-the-ground-up/s/rotary-positions)
5. Tie the output layer to the embeddings in a small model. [Tie the output layer to the embeddings](https://rollingedition.com/language-models-from-the-ground-up/s/tie-the-output)
6. Check your forward pass against the library on a full text. [Check the model against PyTorch](https://rollingedition.com/language-models-from-the-ground-up/s/check-against-pytorch)
7. Remove a block and measure, rather than read its weights. [Leave out a block to see what it does](https://rollingedition.com/language-models-from-the-ground-up/s/leave-out-a-block)
8. Before loading weights, compare the configuration line by line: normalization and ε, RoPE pairing and base, gating, tied outputs, shared keys and values. Then score known text against reference outputs. [Measure what a mismatched detail costs](https://rollingedition.com/language-models-from-the-ground-up/s/measure-mismatched-details)
9. Count parameters by part. [Count where the parameters go](https://rollingedition.com/language-models-from-the-ground-up/s/count-the-parameters)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/check-against-pytorch) (yes), then [the mismatch example](https://rollingedition.com/language-models-from-the-ground-up/s/measure-mismatched-details): 24.3 as trained, 26.4 with the wrong RoPE base, and no error.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/transformer-in-production): mismatched details fail quietly; lengths beyond training are untested; large values overflow at reduced precision.

## Train a small transformer

**When:** a project trains a small transformer on its own text and must pick the run to keep.

1. Build inputs and shifted targets, mask padding out of the loss, shuffle with a fixed seed, and measure padding. [Turn products into batches](https://rollingedition.com/language-models-from-the-ground-up/s/turn-products-into-batches)
2. Use AdamW with modest weight decay, and clip gradients by combined length. [Update with AdamW and clipped gradients](https://rollingedition.com/language-models-from-the-ground-up/s/update-with-adamw)
3. Warm up for a few hundred steps, then decay; check saved step sizes against the schedule. [Warm up, then decay the step size](https://rollingedition.com/language-models-from-the-ground-up/s/warm-up-then-decay)
4. Keep the best epoch by validation loss on each kind of text; never compare perplexities across kinds. [Read the training curve](https://rollingedition.com/language-models-from-the-ground-up/s/read-the-training-curve)
5. Compare with the baseline on exactly the same predictions. [Compare with the baseline on names](https://rollingedition.com/language-models-from-the-ground-up/s/compare-on-names)
6. Measure each kind of text served, split by seen and unseen contexts, and try a mix. [Compare on descriptions](https://rollingedition.com/language-models-from-the-ground-up/s/compare-on-descriptions)
7. Prefer new text to more epochs, and change one thing per run. [What width, data and steps buy](https://rollingedition.com/language-models-from-the-ground-up/s/what-width-data-and-steps-buy)
8. Test autocomplete on rare and common prefixes, with controls. [Suggest the next word in the search box](https://rollingedition.com/language-models-from-the-ground-up/s/autocomplete-in-the-search-box)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/warm-up-then-decay) (yes), then [the comparison](https://rollingedition.com/language-models-from-the-ground-up/s/compare-on-descriptions): 20.1 against the 4-gram's 22.5.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/training-in-production): a schedule bug looks like a model problem; choices made on validation data flatter the result; repeated text gets memorized; padding wastes computation, so pack texts or group them by length.

## Choose decoding settings

**When:** a project generates text and must choose how each next token is picked.

1. Use greedy decoding for short, repeatable output; expect loops on longer text. [Choose the likeliest token](https://rollingedition.com/language-models-from-the-ground-up/s/choose-the-likeliest-token)
2. Use beam search for short completions; rank longer text per token. [Search for the likeliest text](https://rollingedition.com/language-models-from-the-ground-up/s/search-for-the-likeliest-text)
3. Keep temperature at or a little below 1. [Sample, with a temperature](https://rollingedition.com/language-models-from-the-ground-up/s/sample-with-a-temperature)
4. For varied text, use top-p around 0.9 or top-k around 20, with a fixed seed. [Sample, and cut the tail](https://rollingedition.com/language-models-from-the-ground-up/s/sample-and-cut-the-tail)
5. Compare settings on measures against real text, then read samples and check every factual claim. [Measure what each setting writes](https://rollingedition.com/language-models-from-the-ground-up/s/measure-each-setting)
6. With greedy or low-temperature decoding, add a repetition penalty of 1.2 to 1.3 and check length. [Penalize repetition](https://rollingedition.com/language-models-from-the-ground-up/s/penalize-repetition)
7. Set a minimum length if the training text has empty examples. [Forbid an empty description](https://rollingedition.com/language-models-from-the-ground-up/s/forbid-an-empty-description)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/measure-each-setting): repeated 4-token phrases are 11% for greedy against 0% for real descriptions; [the minimum-length example](https://rollingedition.com/language-models-from-the-ground-up/s/forbid-an-empty-description) prints the empty description's probability, 0.28.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/decoding-in-production): fluent text states made-up facts; gaps in the training text become outputs; settings drift with each retrained model.

## Size up an open model before using it

**When:** a project considers an open-weights model and needs its cost, design and fit to its own text.

1. Count parameters by part from the weights, reading shapes for tying, grouped keys and values, and gating. [Count the parameters at scale](https://rollingedition.com/language-models-from-the-ground-up/s/parameters-at-scale)
2. Count from the configuration too; a mismatch means a misread detail. [Compare a family's sizes](https://rollingedition.com/language-models-from-the-ground-up/s/grow-the-same-design)
3. Budget memory as weights plus a key and value cache per text, and cap text length. [Count what it costs to run](https://rollingedition.com/language-models-from-the-ground-up/s/cost-to-run)
4. Score your own text per word or per character on the same events, never per token, against a model trained on it. [Score the store's text with a general model](https://rollingedition.com/language-models-from-the-ground-up/s/score-the-store-text)
5. Describe heads by averages beside an even spread; keep the first token. [Find the same heads at scale](https://rollingedition.com/language-models-from-the-ground-up/s/same-heads-at-scale)
6. Run the same input-change tests on every model. [Test copying at scale](https://rollingedition.com/language-models-from-the-ground-up/s/copying-at-scale)
7. Measure its suggestions on your own prefixes. [Suggest the next word at scale](https://rollingedition.com/language-models-from-the-ground-up/s/suggestions-at-scale)
8. Compare candidates side by side, and choose a model per job. [Set the two models side by side](https://rollingedition.com/language-models-from-the-ground-up/s/side-by-side)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/score-the-store-text): per-word perplexity on names is 54,352.8 for the open model against 199.3 for the small model trained on the text.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/open-models-in-production): its text and tokenizer aren't yours; its details must match the running code; its revision changes, so pin it; check its licence.

## Tune an instruction model and check its answers

**When:** a project uses a tuned model to answer or write about its own data, and must know what it gets wrong.

1. When tuning, mask the request out of the loss; for preferences, keep the reference model's log-probabilities. [Build the two training losses by hand](https://rollingedition.com/language-models-from-the-ground-up/s/build-the-losses)
2. Use a tuned model to follow requests and a base model to continue text. [Ask the base model and the tuned model](https://rollingedition.com/language-models-from-the-ground-up/s/ask-base-and-tuned)
3. Apply the model's own chat template through the library, check its default system message, and record the full prompt. [Format the request as the model was tuned](https://rollingedition.com/language-models-from-the-ground-up/s/format-the-request)
4. Ask questions the input can't answer, count made-up answers, and check claims against the data. [Measure made-up product details](https://rollingedition.com/language-models-from-the-ground-up/s/measure-made-up-details)
5. Measure how confidence relates to being right before using a threshold. [Check whether confidence warns you](https://rollingedition.com/language-models-from-the-ground-up/s/check-confidence)
6. Put key details at the start or end of the context, and test each position. [Find what a longer context loses](https://rollingedition.com/language-models-from-the-ground-up/s/find-what-context-loses)
7. Fine-tune on your text, with LoRA when memory is tight, and measure on held-out text. [Adapt a model to your text](https://rollingedition.com/language-models-from-the-ground-up/s/adapt-a-model)
8. Keep one fixed yardstick, then test the job itself before serving. [Look back at the yardstick](https://rollingedition.com/language-models-from-the-ground-up/s/look-back-at-the-yardstick)

**Check:** run [the example](https://rollingedition.com/language-models-from-the-ground-up/s/measure-made-up-details): where the data names no material, the tuned model made one up 8 times and declined 0; in [the confidence example](https://rollingedition.com/language-models-from-the-ground-up/s/check-confidence), 3 of 11 made-up answers pass a 0.5 threshold.

**Pitfalls:** [What goes wrong in production](https://rollingedition.com/language-models-from-the-ground-up/s/instruction-models-in-production): it answers when it should say it doesn't know; fluency hides gaps; its behaviour depends on its revision and template.
