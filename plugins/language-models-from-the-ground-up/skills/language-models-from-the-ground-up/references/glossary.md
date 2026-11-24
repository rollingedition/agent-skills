---
title: "Glossary"
book: "Language Models from the Ground Up"
edition: "2026.11.19"
canonical: "https://rollingedition.com/language-models-from-the-ground-up/glossary"
---

# Glossary of *Language Models from the Ground Up*

The 134 terms this book defines, as Edition 2026.11.19 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/language-models-from-the-ground-up/glossary

## <unk>

A word the training text doesn't contain at all is counted as one more vocabulary entry, <unk>, for unknown, so the probabilities still sum to one.

- Also: unknown token
- Part of: vocabulary
- Defined in: [Give unseen pairs a little probability](predicting-the-next-word.md#smooth-unseen-pairs)
- Address: https://rollingedition.com/concepts/natural-language-processing/unk

## ablation

Leaving a part out allows a simple experiment, called an ablation: remove one part, and measure what the model loses.

- Close to: https://rollingedition.com/concepts/llm-evaluation/ablation
- Defined in: [Leave out a block to see what it does](the-transformer-block.md#leave-out-a-block)
- Address: https://rollingedition.com/concepts/artificial-intelligence/ablation

## Adam

The training script's optimizer is Adam, a refinement of gradient descent (Kingma and Ba, 2015).

- A kind of: gradient descent
- Defined in: [Train with PyTorch](a-neural-language-model.md#train-with-pytorch)
- Address: https://rollingedition.com/concepts/deep-learning/adam

## AdamW

AdamW, the Adam of chapter 5 with weight decay applied apart from the gradient

- A kind of: Adam
- Defined in: [Update with AdamW and clipped gradients](training-a-small-model.md#update-with-adamw)
- Address: https://rollingedition.com/concepts/deep-learning/adamw

## add-one smoothing

The simplest smoothing method, add-one smoothing, pretends that every possible pair occurred once more than it did.

- Formula: `P(v | w) = (count(w v) + 1) / (count(w) + V)`
- A kind of: smoothing
- Computed from: vocabulary
- Defined in: [Give unseen pairs a little probability](predicting-the-next-word.md#smooth-unseen-pairs)
- Address: https://rollingedition.com/concepts/natural-language-processing/add-one-smoothing

## analogy

In vectors, the answer to "a is to b as c is to what?" is the token nearest to b − a + c, leaving out the three tokens in the question

- Computed from: embedding
- Defined in: [Analogies, and where they fail](words-as-vectors.md#analogies-and-where-they-fail)
- Address: https://rollingedition.com/concepts/natural-language-processing/analogy

## attention

Attention lets every position look at other positions, in a language model every earlier one, and decide from their contents how much each matters.

- Contrasts with: input window
- Defined in: [Attention](attention.md)
- Address: https://rollingedition.com/concepts/deep-learning/attention

## attention score

The score of position j for position i is the dot product of i's query with j's key, divided by the square root of d, the size of each query and key, meaning how many numbers it holds.

- Computed from: query
- Computed from: key
- Part of: attention
- Defined in: [Look back with a weighted average](attention.md#look-back-with-a-weighted-average)
- Address: https://rollingedition.com/concepts/deep-learning/attention-score

## attention sink

Xiao and colleagues found that language models put large weights on the first tokens of a text whatever they are, calling them attention sinks (Xiao et al., 2024).

- Also: attention sinks
- Defined in: [Reach past the window](attention.md#reach-past-the-window)
- Address: https://rollingedition.com/concepts/large-language-models/attention-sink

## backpropagation

Backpropagation computes all the gradients at once, by applying the chain rule of calculus backwards through the forward pass

- Defined in: [Compute gradients by backpropagation](a-neural-language-model.md#compute-gradients)
- Address: https://rollingedition.com/concepts/deep-learning/backpropagation

## base model

the base model, the one trained only to predict the next token

- Defined in: [Inside an open model](inside-an-open-model.md)
- Address: https://rollingedition.com/concepts/large-language-models/base-model

## baseline

a baseline, a fixed yardstick: one model, one text, one tokenizer and one measure that every later model is compared against

- Close to: https://rollingedition.com/concepts/llm-evaluation/baseline
- Close to: https://rollingedition.com/concepts/search-and-recommendation/baseline
- Close to: https://rollingedition.com/concepts/model-evaluation/baseline
- Defined in: [The baseline every later model is measured against](counting-further-back.md#the-baseline)
- Address: https://rollingedition.com/concepts/artificial-intelligence/baseline

## batch

Each step of real training is computed on a batch of examples, a few hundred at a time here, instead of all of them, so each step is cheap and the steps vary a little.

- Part of: gradient descent
- Defined in: [Take gradient descent steps](a-neural-language-model.md#take-gradient-descent-steps)
- Address: https://rollingedition.com/concepts/deep-learning/batch

## beam search

Beam search looks further, keeping the k likeliest partial texts, the beam, scored by their total log-probability

- Contrasts with: greedy decoding
- Defined in: [Search for the likeliest text](choosing-the-next-token.md#search-for-the-likeliest-text)
- Address: https://rollingedition.com/concepts/large-language-models/beam-search

## bigram

A bigram is a pair of adjacent words, such as coffee table.

- Defined in: [Count which word follows which](predicting-the-next-word.md#count-word-pairs)
- Address: https://rollingedition.com/concepts/natural-language-processing/bigram

## byte

in UTF-8, the usual text encoding, every character in every language is stored as one to four bytes, and there are only 256 possible byte values, so a vocabulary that starts from all 256 can represent any text at all

- Defined in: [Characters cover everything](tokens.md#characters-cover-everything)
- Address: https://rollingedition.com/concepts/natural-language-processing/byte

## byte-pair encoding

Byte-pair encoding, or BPE, starts from characters and builds bigger tokens out of the pairs that occur most often.

- Also: BPE
- Implemented by: tokenizers 0.23.3
- Defined in: [Merge the most frequent pair, again and again](tokens.md#merge-frequent-pairs)
- Address: https://rollingedition.com/concepts/natural-language-processing/byte-pair-encoding

## calibrated

A model whose confidence matches how often it's right is calibrated

- Also: calibration
- Defined in: [Check whether confidence warns you](from-predicting-to-following.md#check-confidence)
- Address: https://rollingedition.com/concepts/artificial-intelligence/calibrated

## causal mask

the causal mask: before softmax, set every score for a later position to minus infinity.

- Part of: attention
- Defined in: [Hide the future with a causal mask](attention.md#hide-the-future)
- Address: https://rollingedition.com/concepts/deep-learning/causal-mask

## chat template

A tuned model's chat template is the layout it learned: special tokens that mark where a system message, instructions placed before the user's request, the request itself and the model's reply begin and end.

- Defined in: [Format the request as the model was tuned](from-predicting-to-following.md#format-the-request)
- Address: https://rollingedition.com/concepts/large-language-models/chat-template

## co-occurrence window

count, for every pair of tokens, how often one appears within a small window of the other, here two tokens either side, and never across the gap between two products' texts

- Comes before: pointwise mutual information
- Defined in: [Describe a token by the tokens around it](words-as-vectors.md#describe-by-neighbours)
- Address: https://rollingedition.com/concepts/natural-language-processing/co-occurrence-window

## confidence per token

a confidence per token can be computed for each answer, as a geometric mean

- Formula: `confidence per token = exp((log p₁ + … + log pₙ) / n)`
- Defined in: [Check whether confidence warns you](from-predicting-to-following.md#check-confidence)
- Address: https://rollingedition.com/concepts/large-language-models/confidence-per-token

## context

The tokens before the one being predicted are its context.

- Defined in: [Longer contexts fit the training text better](counting-further-back.md#longer-contexts-fit-training)
- Address: https://rollingedition.com/concepts/natural-language-processing/context

## continuation count

a token's continuation count, the number of different tokens it follows

- Comes before: Kneser-Ney smoothing
- Defined in: [Count the contexts a token follows](counting-further-back.md#count-contexts-a-token-follows)
- Address: https://rollingedition.com/concepts/natural-language-processing/continuation-count

## cosine decay

After the warm-up, the step size falls along half a cosine curve, here to a tenth of the peak by the last step

- Formula: `rate = peak × (0.1 + 0.9 × ½ (1 + cos(π × progress)))`
- Part of: schedule
- Defined in: [Warm up, then decay the step size](training-a-small-model.md#warm-up-then-decay)
- Address: https://rollingedition.com/concepts/deep-learning/cosine-decay

## cosine similarity

To measure how alike two vectors are, this book uses cosine similarity: the cosine of the angle between them, 1 when they point the same way, 0 when they're at right angles.

- The same as: https://rollingedition.com/concepts/search-and-recommendation/cosine-similarity
- Computed from: vector
- Defined in: [One-hot vectors know nothing](words-as-vectors.md#one-hot-vectors-know-nothing)
- Address: https://rollingedition.com/concepts/artificial-intelligence/cosine-similarity

## cross-entropy

The cross-entropy of a text is the average surprise over every word in it

- Formula: `cross-entropy = −(1/N) Σ log P(next word | the words before it)`
- Computed from: surprise
- Defined in: [Score a model with perplexity](predicting-the-next-word.md#score-with-perplexity)
- Address: https://rollingedition.com/concepts/natural-language-processing/cross-entropy

## declined answer

An answer is declined if it says the product's data doesn't say

- Defined in: [Measure made-up product details](from-predicting-to-following.md#measure-made-up-details)
- Address: https://rollingedition.com/concepts/large-language-models/declined-answer

## decoding

Turning a model's probabilities into text, one chosen token at a time, is called decoding

- Kinds: greedy decoding
- Kinds: beam search
- Kinds: sampling
- Defined in: [Choosing the next token](choosing-the-next-token.md)
- Address: https://rollingedition.com/concepts/large-language-models/decoding

## Direct Preference Optimization

Direct Preference Optimization, DPO, does preference tuning without a reward model, with a simple loss on the preference pairs themselves

- Also: DPO
- A kind of: preference tuning
- Defined in: [From predicting to following instructions](from-predicting-to-following.md)
- Address: https://rollingedition.com/concepts/large-language-models/direct-preference-optimization

## discount

At each order, Kneser-Ney subtracts a fixed discount d from every count it has seen, and gives the probability it took to the next order down

- Part of: Kneser-Ney smoothing
- Defined in: [Smooth with Kneser-Ney](counting-further-back.md#smooth-with-kneser-ney)
- Address: https://rollingedition.com/concepts/natural-language-processing/discount

## DPO loss

DPO's loss works on a pair of responses to one request, one preferred and one rejected.

- Also: DPO's loss
- Formula: `loss = −log σ(margin)`
- Part of: Direct Preference Optimization
- Computed from: reference model
- Defined in: [Build the two training losses by hand](from-predicting-to-following.md#build-the-losses)
- Address: https://rollingedition.com/concepts/large-language-models/dpo-loss

## early stopping

The simplest defence is early stopping: measure validation loss after every epoch, one full pass over the training text, and keep the weights from the best epoch.

- Close to: https://rollingedition.com/concepts/search-and-recommendation/early-stopping
- Defined in: [Stop when validation loss turns up](a-neural-language-model.md#stop-at-the-best-epoch)
- Address: https://rollingedition.com/concepts/deep-learning/early-stopping

## embedding

an embedding, a dense vector that stands for a token

- Also: token embedding, word embedding
- A kind of: vector
- Defined in: [Compress counts into dense vectors](words-as-vectors.md#compress-into-dense-vectors)
- Address: https://rollingedition.com/concepts/natural-language-processing/embedding

## embedding table

Each token is looked up in an embedding table, a matrix with one row of numbers per token in the vocabulary, as in chapter 4, except that this table is learned for predicting the next token rather than computed from counts.

- Part of: neural language model
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/embedding-table

## epoch

epoch, one full pass over the training text

- Comes before: early stopping
- Defined in: [Stop when validation loss turns up](a-neural-language-model.md#stop-at-the-best-epoch)
- Address: https://rollingedition.com/concepts/deep-learning/epoch

## even spread

an even spread, which puts 1 / (i + 1) on each of the i + 1 tokens position i can see

- Formula: `1 / (i + 1)`
- Defined in: [Some heads attend to the previous token](attention.md#attend-to-the-previous-token)
- Address: https://rollingedition.com/concepts/deep-learning/even-spread

## feed-forward layer

Attention moves information between positions; the feed-forward layer transforms it, at each position separately.

- Part of: transformer block
- Contrasts with: attention
- Defined in: [Transform each position with a gated feed-forward layer](the-transformer-block.md#transform-each-position)
- Address: https://rollingedition.com/concepts/deep-learning/feed-forward-layer

## fine-tuning

The way to teach a general model the store's text is fine-tuning: continue training it on that text, the same training loop as chapter 8, starting from the general model's weights instead of random ones.

- Contrasts with: instruction tuning
- Defined in: [Adapt a model to your text](from-predicting-to-following.md#adapt-a-model)
- Address: https://rollingedition.com/concepts/large-language-models/fine-tuning

## full fine-tuning

Full fine-tuning updates every weight, which for a model of hundreds of millions of parameters takes time and memory.

- A kind of: fine-tuning
- The same as: https://rollingedition.com/concepts/fine-tuning/full-fine-tuning
- Defined in: [Adapt a model to your text](from-predicting-to-following.md#adapt-a-model)
- Address: https://rollingedition.com/concepts/large-language-models/full-fine-tuning

## gated feed-forward layer

A gated feed-forward layer computes two widened vectors from the input, passes one through a function, here one called SiLU, and multiplies the two number by number, so the first decides how much of the second gets through

- Also: SwiGLU
- Formula: `FFN(x) = (SiLU(x W_gate) ⊙ (x W_up)) W_down`
- A kind of: feed-forward layer
- Defined in: [Transform each position with a gated feed-forward layer](the-transformer-block.md#transform-each-position)
- Address: https://rollingedition.com/concepts/deep-learning/gated-feed-forward-layer

## generation

To generate from this model, start at <s>, draw the next word at random in proportion to its probability, append it, and repeat from the word you drew, until the model draws </s>.

- Also: generate
- Defined in: [Generate names one word at a time](predicting-the-next-word.md#generate-one-word-at-a-time)
- Address: https://rollingedition.com/concepts/natural-language-processing/generation

## gradient

To lower the loss, each weight needs a gradient: how much the loss would change if that weight changed a little, written ∂L/∂w.

- Comes before: backpropagation
- Comes before: gradient descent
- Defined in: [Compute gradients by backpropagation](a-neural-language-model.md#compute-gradients)
- Address: https://rollingedition.com/concepts/deep-learning/gradient

## gradient clipping

The training script also clips the gradients: when their combined length, measured as if every gradient were one long vector, exceeds 1.0, it scales them all down to that length

- Also: clipping
- Defined in: [Update with AdamW and clipped gradients](training-a-small-model.md#update-with-adamw)
- Address: https://rollingedition.com/concepts/deep-learning/gradient-clipping

## gradient descent

Gradient descent moves every weight a small step against its gradient

- Formula: `w ← w − η · ∂L/∂w`
- Defined in: [Take gradient descent steps](a-neural-language-model.md#take-gradient-descent-steps)
- Address: https://rollingedition.com/concepts/deep-learning/gradient-descent

## greedy decoding

The simplest decoder is greedy: at every step, take the single likeliest token.

- Also: greedy
- Contrasts with: sampling
- The same as: https://rollingedition.com/concepts/data-engineering/greedy-decoding
- Defined in: [Choose the likeliest token](choosing-the-next-token.md#choose-the-likeliest-token)
- Address: https://rollingedition.com/concepts/large-language-models/greedy-decoding

## grouped-query attention

grouped-query attention, which shares each key and value head among several query heads

- Also: GQA
- A kind of: multi-head attention
- Defined in: [Count the parameters at scale](inside-an-open-model.md#parameters-at-scale)
- Address: https://rollingedition.com/concepts/large-language-models/grouped-query-attention

## hallucination

Making up a detail the input doesn't support is one kind of what's called hallucination

- Defined in: [Measure made-up product details](from-predicting-to-following.md#measure-made-up-details)
- Address: https://rollingedition.com/concepts/large-language-models/hallucination

## head

several attention computations, called heads, side by side, each with its own query, key and value matrices

- Also: heads, attention head
- Part of: multi-head attention
- Defined in: [Several heads look for different things](attention.md#several-heads)
- Address: https://rollingedition.com/concepts/deep-learning/head

## hidden layer

In this model, a hidden layer computes h = tanh(xW + b) from its input x: it multiplies x by a matrix of weights W, adds a vector of biases b, and passes each result through tanh

- Formula: `h = tanh(xW + b)`
- Part of: neural language model
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/hidden-layer

## induction head

an induction head: a head in an earlier layer copies each token's predecessor into its position, and the induction head uses that to find earlier positions that followed the current token, attends to them, and copies their token into the prediction

- Also: induction heads
- A kind of: head
- Defined in: [Read what trained heads attend to](attention.md#read-trained-heads)
- Address: https://rollingedition.com/concepts/large-language-models/induction-head

## input window

This chapter's model looks at a fixed window of the previous tokens, four here, the same context a 5-gram counts.

- Part of: neural language model
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/natural-language-processing/input-window

## inputs

The inputs are a text's tokens without the last

- Contrasts with: targets
- Defined in: [Turn products into batches](training-a-small-model.md#turn-products-into-batches)
- Address: https://rollingedition.com/concepts/natural-language-processing/input

## instruction tuning

Instruction tuning, or supervised fine-tuning, continues training a model on examples of requests paired with good responses, so that predicting the next token of such a pair means answering the request.

- Also: supervised fine-tuning, instruction-tuned
- Comes before: preference tuning
- Comes before: reference model
- Defined in: [From predicting to following instructions](from-predicting-to-following.md)
- Address: https://rollingedition.com/concepts/large-language-models/instruction-tuning

## interpolation

Interpolation falls back smoothly: the probability of a token is a weighted mix of what the counts of each order say (here trigram, bigram and unigram)

- Formula: `P(token | a b) = λ₃ · P₃(token | a b) + λ₂ · P₂(token | b) + λ₁ · P₁(token)`
- A kind of: smoothing
- Contrasts with: add-one smoothing
- Comes before: Kneser-Ney smoothing
- Defined in: [Mix short and long contexts](counting-further-back.md#mix-short-and-long-contexts)
- Address: https://rollingedition.com/concepts/natural-language-processing/interpolation

## key

a key, a vector for what this position offers to the positions that look at it

- Part of: attention
- Defined in: [Look back with a weighted average](attention.md#look-back-with-a-weighted-average)
- Address: https://rollingedition.com/concepts/deep-learning/key

## key and value cache

The key and value cache, every layer's keys and values for the earlier tokens, grows with the length of the text

- Also: KV cache
- Formula: `cache per token, in bytes = layers × 2 × key and value heads × head size × 2`
- Defined in: [Count what it costs to run](inside-an-open-model.md#cost-to-run)
- Address: https://rollingedition.com/concepts/large-language-models/key-and-value-cache

## Kneser-Ney smoothing

Kneser-Ney smoothing combines discounting, interpolation of orders and continuation counts.

- Also: Kneser-Ney, interpolated Kneser-Ney
- Formula: `P(w | h) = max(c(h w) − d, 0) / c(h) + d · N(h) / c(h) · P(w | shorter h)`
- A kind of: smoothing
- Defined in: [Smooth with Kneser-Ney](counting-further-back.md#smooth-with-kneser-ney)
- Address: https://rollingedition.com/concepts/natural-language-processing/kneser-ney-smoothing

## language model

A language model is a program that assigns a probability to every word that could come next, given the words so far.

- Defined in: [Predicting the next word](predicting-the-next-word.md)
- Address: https://rollingedition.com/concepts/natural-language-processing/language-model

## layer normalization

layer normalization, which subtracts each vector's mean and divides by its standard deviation, and applies a learned gain and bias

- Defined in: [Normalize before each part](the-transformer-block.md#normalize-before-each-part)
- Address: https://rollingedition.com/concepts/deep-learning/layer-normalization

## logistic function

the logistic function, σ(s) = 1 / (1 + e⁻ˢ), which turns a score into a probability

- Also: sigmoid
- Formula: `σ(s) = 1 / (1 + e⁻ˢ)`
- Defined in: [Learn vectors by predicting neighbours](words-as-vectors.md#learn-by-predicting-neighbours)
- Address: https://rollingedition.com/concepts/artificial-intelligence/logistic-function

## logits

one score per token in the vocabulary, called the logits

- Also: logit
- Comes before: softmax
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/logit

## LoRA

LoRA, low-rank adaptation, freezes the model's weights and trains a small correction beside some of them.

- Also: low-rank adaptation
- Formula: `W + BA`
- A kind of: fine-tuning
- Contrasts with: full fine-tuning
- The same as: https://rollingedition.com/concepts/fine-tuning/lora
- Defined in: [Adapt a model to your text](from-predicting-to-following.md#adapt-a-model)
- Address: https://rollingedition.com/concepts/large-language-models/lora

## loss

To measure how badly a model predicts, use a loss, here the surprise whose average is chapter 1's cross-entropy: L = −log P(next token), the negative log probability the model gave to the token that actually came next, the same surprise chapter 1 averaged into perplexity.

- Formula: `L = −log P(next token)`
- Comes before: gradient
- Defined in: [Compute gradients by backpropagation](a-neural-language-model.md#compute-gradients)
- Address: https://rollingedition.com/concepts/deep-learning/loss

## made-up answer

An answer is made up if it names a material that the product's name and description don't contain.

- A kind of: hallucination
- Defined in: [Measure made-up product details](from-predicting-to-following.md#measure-made-up-details)
- Address: https://rollingedition.com/concepts/large-language-models/made-up-answer

## maximum likelihood estimation

Estimating probabilities from the fraction of times something happened is an example of maximum likelihood estimation: of all the probability tables you could choose, it's the one that makes the training text likeliest

- Also: maximum likelihood, MLE
- Formula: `P(v | w) = count(w v) / count(w)`
- Computed from: bigram
- Defined in: [Turn counts into probabilities](predicting-the-next-word.md#counts-to-probabilities)
- Address: https://rollingedition.com/concepts/artificial-intelligence/maximum-likelihood-estimation

## minimum length

a minimum length: forbid the end marker, by setting its logit to minus infinity, until the description has some number of tokens

- Defined in: [Forbid an empty description](choosing-the-next-token.md#forbid-an-empty-description)
- Address: https://rollingedition.com/concepts/large-language-models/minimum-length

## modified Kneser-Ney

A variant, modified Kneser-Ney, uses three discounts instead of one

- A kind of: Kneser-Ney smoothing
- Defined in: [Smooth with Kneser-Ney](counting-further-back.md#smooth-with-kneser-ney)
- Address: https://rollingedition.com/concepts/natural-language-processing/modified-kneser-ney

## multi-head attention

Multi-head attention runs several attention computations, called heads, side by side, each with its own query, key and value matrices, and each in a share of the vector's numbers

- A kind of: attention
- Defined in: [Several heads look for different things](attention.md#several-heads)
- Address: https://rollingedition.com/concepts/deep-learning/multi-head-attention

## n-gram model

An n-gram model predicts each token from the n − 1 tokens before it

- Also: n-gram, n-gram language model
- A kind of: language model
- Defined in: [Longer contexts fit the training text better](counting-further-back.md#longer-contexts-fit-training)
- Address: https://rollingedition.com/concepts/natural-language-processing/n-gram-model

## neural language model

A neural language model reads the previous tokens as vectors, combines them with learned arithmetic, and produces a probability for every token in the vocabulary.

- A kind of: language model
- Defined in: [A neural language model](a-neural-language-model.md)
- Address: https://rollingedition.com/concepts/natural-language-processing/neural-language-model

## noise token

For a few random noise tokens drawn from the vocabulary, the model nudges the probability down.

- Part of: skip-gram with negative sampling
- Defined in: [Learn vectors by predicting neighbours](words-as-vectors.md#learn-by-predicting-neighbours)
- Address: https://rollingedition.com/concepts/natural-language-processing/noise-token

## normalization

Normalization rescales a vector to a standard size before a part reads it, so the part's weights work the same whether the stream is short or long.

- Part of: transformer block
- Kinds: layer normalization
- Kinds: RMSNorm
- Defined in: [Normalize before each part](the-transformer-block.md#normalize-before-each-part)
- Address: https://rollingedition.com/concepts/deep-learning/normalization

## one-hot encoding

a one-hot encoding, in which each token gets a vector as long as the vocabulary, with a 1 in its own position and 0 everywhere else

- Also: one-hot, one-hot vector
- Contrasts with: embedding
- Defined in: [One-hot vectors know nothing](words-as-vectors.md#one-hot-vectors-know-nothing)
- Address: https://rollingedition.com/concepts/natural-language-processing/one-hot-encoding

## out-of-vocabulary

any word that first appears after training is out of reach: an out-of-vocabulary word

- Also: OOV
- Defined in: [Words leave gaps](tokens.md#words-leave-gaps)
- Address: https://rollingedition.com/concepts/natural-language-processing/out-of-vocabulary

## output layer

An output layer then computes z = hU + c from the hidden layer's output h

- Formula: `z = hU + c`
- Part of: neural language model
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/output-layer

## output projection

The heads' outputs are joined side by side and mixed back together by one more learned matrix, the output projection

- Part of: multi-head attention
- Defined in: [Several heads look for different things](attention.md#several-heads)
- Address: https://rollingedition.com/concepts/deep-learning/output-projection

## overfitting

A validation perplexity that turns up while training perplexity keeps falling is the sign of overfitting: the model fits its training text, noise included, so closely that it does worse on new text.

- Measured from: perplexity
- Defined in: [Stop when validation loss turns up](a-neural-language-model.md#stop-at-the-best-epoch)
- Address: https://rollingedition.com/concepts/artificial-intelligence/overfitting

## packing

packing, several texts end to end in each row, with the attention kept from crossing between them

- Contrasts with: padding
- Defined in: [Turn products into batches](training-a-small-model.md#turn-products-into-batches)
- Address: https://rollingedition.com/concepts/deep-learning/packing

## padding

padding, which fills out short texts in a training batch

- Also: padding token
- Defined in: [Count where the parameters go](the-transformer-block.md#count-the-parameters)
- Address: https://rollingedition.com/concepts/natural-language-processing/padding

## parameter

The window model has 1,394,732 parameters, the numbers it learns.

- Also: parameters
- The same as: https://rollingedition.com/concepts/large-language-models/parameter
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/parameter

## perplexity

Perplexity is the cross-entropy turned back into a count

- Formula: `perplexity = exp(cross-entropy)`
- Computed from: cross-entropy
- Defined in: [Score a model with perplexity](predicting-the-next-word.md#score-with-perplexity)
- Address: https://rollingedition.com/concepts/natural-language-processing/perplexity

## perplexity per word

A perplexity per word divides a model's total log-probability of a text by the number of words in it, instead of by its number of tokens, before turning it back into a count.

- Also: per-word perplexity
- Formula: `perplexity per word = exp(−(log p₁ + … + log pₙ) / W)`
- A kind of: perplexity
- Computed from: total log-probability
- Defined in: [Score the store's text with a general model](inside-an-open-model.md#score-the-store-text)
- Address: https://rollingedition.com/concepts/natural-language-processing/perplexity-per-word

## pinned revision

a pinned revision, a fixed version of its repository

- Also: revision
- The same as: https://rollingedition.com/concepts/artificial-intelligence/pinned-revision
- Defined in: [Inside an open model](inside-an-open-model.md)
- Address: https://rollingedition.com/concepts/large-language-models/pinned-revision

## pointwise mutual information

Pointwise mutual information, or PMI, measures how far the real count departs from chance: the log of the ratio between how often two tokens co-occur and how often they would by chance

- Also: PMI
- Formula: `PMI(a, b) = log [ P(a, b) / (P(a) · P(b)) ]`
- Defined in: [Weigh co-occurrence by surprise](words-as-vectors.md#weigh-by-surprise)
- Address: https://rollingedition.com/concepts/natural-language-processing/pointwise-mutual-information

## positive PMI

positive PMI, or PPMI, replaces every negative value with zero.

- Also: PPMI, positive pointwise mutual information
- Computed from: pointwise mutual information
- Defined in: [Weigh co-occurrence by surprise](words-as-vectors.md#weigh-by-surprise)
- Address: https://rollingedition.com/concepts/natural-language-processing/positive-pmi

## pre-tokenizer

A pre-tokenizer splits text into pieces before any merging

- Part of: tokenizer
- Implemented by: tokenizers 0.23.3
- Defined in: [Apply SmolLM2's merges by hand](tokens.md#apply-merges-by-hand)
- Address: https://rollingedition.com/concepts/natural-language-processing/pre-tokenizer

## preference tuning

Preference tuning then trains a model to prefer the better of two responses to the same request.

- Defined in: [From predicting to following instructions](from-predicting-to-following.md)
- Address: https://rollingedition.com/concepts/large-language-models/preference-tuning

## query

a query, a vector for what this position is looking for

- Part of: attention
- Defined in: [Look back with a weighted average](attention.md#look-back-with-a-weighted-average)
- Address: https://rollingedition.com/concepts/deep-learning/query

## reference model

DPO compares how much more likely the model being tuned makes each response than the reference model it started from, the model after instruction tuning, and rewards it for raising the preferred one more.

- Defined in: [Build the two training losses by hand](from-predicting-to-following.md#build-the-losses)
- Address: https://rollingedition.com/concepts/large-language-models/reference-model

## regularization

regularization, which is anything in training that discourages memorizing

- Defined in: [Stop when validation loss turns up](a-neural-language-model.md#stop-at-the-best-epoch)
- Address: https://rollingedition.com/concepts/artificial-intelligence/regularization

## repetition

repetition: the share of four-token phrases that repeat an earlier one in the same description

- Defined in: [Measure what each setting writes](choosing-the-next-token.md#measure-each-setting)
- Address: https://rollingedition.com/concepts/large-language-models/repetition

## repetition penalty

Keskar and colleagues proposed a repetition penalty: divide the logit of every token already generated by a factor θ above 1, so that, where the logit is positive, it becomes less likely

- Defined in: [Penalize repetition](choosing-the-next-token.md#penalize-repetition)
- Address: https://rollingedition.com/concepts/large-language-models/repetition-penalty

## residual connection

Adding a part's output to its input, instead of replacing the input, is a residual connection.

- Formula: `x ← x + attention(x), then x ← x + feed-forward(x)`
- Part of: transformer block
- Comes before: residual stream
- Defined in: [Add each part's output to a residual stream](the-transformer-block.md#add-to-the-residual-stream)
- Address: https://rollingedition.com/concepts/deep-learning/residual-connection

## residual stream

Elhage and colleagues call this running sum, each position's vector with every part's output added to it, the residual stream

- Defined in: [Add each part's output to a residual stream](the-transformer-block.md#add-to-the-residual-stream)
- Address: https://rollingedition.com/concepts/deep-learning/residual-stream

## RMSNorm

RMSNorm drops the mean: it divides each vector by its root mean square, the square root of the average of its squared numbers, and multiplies each dimension by a learned gain

- Formula: `RMSNorm(x) = x / √(mean(x²) + ε) · g`
- Computed from: root mean square
- Contrasts with: layer normalization
- Defined in: [Normalize before each part](the-transformer-block.md#normalize-before-each-part)
- Address: https://rollingedition.com/concepts/deep-learning/rmsnorm

## root mean square

root mean square, the square root of the average of its squared numbers

- Computed from: vector
- Defined in: [Normalize before each part](the-transformer-block.md#normalize-before-each-part)
- Address: https://rollingedition.com/concepts/artificial-intelligence/root-mean-square

## rotary position embeddings

Before scoring, RoPE rotates each query and key by angles that grow with its position.

- Also: RoPE
- Formula: `(a, b) → (a cos pθᵢ − b sin pθᵢ, a sin pθᵢ + b cos pθᵢ)`
- Part of: transformer block
- Defined in: [Give attention positions with rotations](the-transformer-block.md#rotary-positions)
- Address: https://rollingedition.com/concepts/large-language-models/rotary-position-embedding

## sampling

Sampling, which chapter 1 used to generate names, uses all of the distribution: draw the next token at random, in proportion to its probability, so a token with probability 0.2 is chosen one time in five.

- Kinds: top-k
- Kinds: top-p
- Defined in: [Sample, with a temperature](choosing-the-next-token.md#sample-with-a-temperature)
- Address: https://rollingedition.com/concepts/large-language-models/sampling

## schedule

changes the step size after every batch, following a schedule, which sets the step size for each step of the run

- Also: learning-rate schedule
- Defined in: [Warm up, then decay the step size](training-a-small-model.md#warm-up-then-decay)
- Address: https://rollingedition.com/concepts/deep-learning/schedule

## shared module

the book's shared modules: short files in examples/lib/ that hold setup code many examples need, which you can open and read

- The same as: https://rollingedition.com/concepts/data-engineering/shared-module
- Defined in: [Load the store's text](predicting-the-next-word.md#load-the-store-text)
- Address: https://rollingedition.com/concepts/artificial-intelligence/shared-module

## SiLU

SiLU passes large positive numbers almost unchanged and turns large negative ones to nearly zero, smoothly.

- Formula: `SiLU(z) = z · σ(z)`
- Comes before: gated feed-forward layer
- Defined in: [Transform each position with a gated feed-forward layer](the-transformer-block.md#transform-each-position)
- Address: https://rollingedition.com/concepts/deep-learning/silu

## singular value decomposition

the singular value decomposition, SVD, which finds the directions that reconstruct the PPMI rows best, in order, so that the first 64 together reconstruct them best of any 64, and weights each by how much of the rows it explains

- Also: SVD
- Computed from: positive PMI
- Defined in: [Compress counts into dense vectors](words-as-vectors.md#compress-into-dense-vectors)
- Address: https://rollingedition.com/concepts/natural-language-processing/singular-value-decomposition

## skip-gram loss

The skip-gram loss for one pair is the surprise at the real neighbour plus the surprise at each noise token's not being one

- Formula: `L = −log σ(v·u) − Σₙ log σ(−v·uₙ)`
- Part of: skip-gram with negative sampling
- Computed from: logistic function
- Computed from: noise token
- Defined in: [Learn vectors by predicting neighbours](words-as-vectors.md#learn-by-predicting-neighbours)
- Address: https://rollingedition.com/concepts/natural-language-processing/skip-gram-loss

## skip-gram with negative sampling

Skip-gram with negative sampling, the method behind word2vec, gives each token two vectors, one for when it's the centre token and one for when it's a neighbour, and trains them on one task: given a token, tell its real neighbours apart from random tokens

- Also: skip-gram, SGNS
- Contrasts with: singular value decomposition
- Defined in: [Learn vectors by predicting neighbours](words-as-vectors.md#learn-by-predicting-neighbours)
- Address: https://rollingedition.com/concepts/natural-language-processing/skip-gram-with-negative-sampling

## SmolLM2-360M

SmolLM2-360M, an open model released by Hugging Face under the Apache 2.0 licence

- Defined in: [Inside an open model](inside-an-open-model.md)
- Address: https://rollingedition.com/concepts/large-language-models/smollm2-360m

## SmolLM2-360M-Instruct

SmolLM2-360M-Instruct is the base model of chapter 10 after both steps: supervised fine-tuning on public and curated datasets, then DPO on UltraFeedback

- Defined in: [From predicting to following instructions](from-predicting-to-following.md)
- Address: https://rollingedition.com/concepts/large-language-models/smollm2-360m-instruct

## smoothing

smoothing, which gives unseen pairs some probability by taking a little away from the pairs the model has seen

- Defined in: [Unseen word pairs break the model](predicting-the-next-word.md#unseen-pairs-break-the-model)
- Address: https://rollingedition.com/concepts/natural-language-processing/smoothing

## softmax

Softmax exponentiates every logit and divides by the sum, so the results are positive and sum to one, and a higher score means a higher probability

- Formula: `P(token i) = exp(zᵢ) / Σⱼ exp(zⱼ)`
- Comes before: attention
- The same as: https://rollingedition.com/concepts/large-language-models/softmax
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/softmax

## special token

Open models mark the start or end of a text, or a turn in a conversation, with special tokens written as strings such as <|endoftext|>.

- Defined in: [What goes wrong in production](tokens.md#tokens-in-production)
- Address: https://rollingedition.com/concepts/large-language-models/special-token

## step size

η, the step size, also called the learning rate, sets how far each step goes

- Also: learning rate
- Part of: gradient descent
- Defined in: [Take gradient descent steps](a-neural-language-model.md#take-gradient-descent-steps)
- Address: https://rollingedition.com/concepts/deep-learning/step-size

## supported answer

An answer is supported if it names a material and every material it names is in the product's name or description

- Contrasts with: made-up answer
- Defined in: [Measure made-up product details](from-predicting-to-following.md#measure-made-up-details)
- Address: https://rollingedition.com/concepts/large-language-models/supported-answer

## surprise

If the model gave the actual next word probability p, its surprise at that word is −log p: zero when it was certain (p = 1) and larger the less it expected the word.

- Comes before: cross-entropy
- Defined in: [Score a model with perplexity](predicting-the-next-word.md#score-with-perplexity)
- Address: https://rollingedition.com/concepts/natural-language-processing/surprise

## system message

a system message, instructions placed before the user's request

- Part of: chat template
- Close to: https://rollingedition.com/concepts/llm-evaluation/system-text
- Defined in: [Format the request as the model was tuned](from-predicting-to-following.md#format-the-request)
- Address: https://rollingedition.com/concepts/large-language-models/system-message

## tanh

tanh, a function that squashes any number into the range from −1 to 1

- Part of: hidden layer
- Defined in: [Predict from a window of embeddings](a-neural-language-model.md#predict-from-a-window)
- Address: https://rollingedition.com/concepts/deep-learning/tanh

## targets

the targets are the text's tokens without the first, so position i is trained to predict token i + 1

- Close to: https://rollingedition.com/concepts/feature-engineering/target
- Defined in: [Turn products into batches](training-a-small-model.md#turn-products-into-batches)
- Address: https://rollingedition.com/concepts/natural-language-processing/target

## temperature

Before sampling, the distribution can be made sharper or flatter with a temperature, T: divide every logit by T before the softmax.

- Formula: `P(token i) = exp(zᵢ / T) / Σⱼ exp(zⱼ / T)`
- Defined in: [Sample, with a temperature](choosing-the-next-token.md#sample-with-a-temperature)
- Address: https://rollingedition.com/concepts/large-language-models/temperature

## test split

a test split kept for final reports

- The same as: https://rollingedition.com/concepts/llm-evaluation/held-out
- Close to: https://rollingedition.com/concepts/model-evaluation/test-split
- Defined in: [Load the store's text](predicting-the-next-word.md#load-the-store-text)
- Address: https://rollingedition.com/concepts/artificial-intelligence/test-split

## token

A token is the unit a language model reads and predicts: whatever the text is cut into before the model sees it.

- Comes before: vocabulary
- The same as: https://rollingedition.com/concepts/large-language-models/token
- The same as: https://rollingedition.com/concepts/semantic-search/token
- Defined in: [Tokens](tokens.md)
- Address: https://rollingedition.com/concepts/natural-language-processing/token

## token type

The different tokens a text uses are its token types.

- Defined in: [Choose how many merges](tokens.md#choose-how-many-merges)
- Address: https://rollingedition.com/concepts/natural-language-processing/token-type

## tokenizer

A tokenizer cuts text into tokens; a BPE tokenizer is the list of merges, in the order they were learned, applied to the characters it starts from.

- Implemented by: tokenizers 0.23.3
- Close to: https://rollingedition.com/concepts/large-language-models/tokenizer
- Defined in: [Merge the most frequent pair, again and again](tokens.md#merge-frequent-pairs)
- Address: https://rollingedition.com/concepts/natural-language-processing/tokenizer

## top-k

Top-k keeps only the k likeliest tokens and renormalizes their probabilities to sum to one

- Also: top-k sampling
- Defined in: [Sample, and cut the tail](choosing-the-next-token.md#sample-and-cut-the-tail)
- Address: https://rollingedition.com/concepts/large-language-models/top-k

## top-p

Top-p, also called nucleus sampling, keeps the smallest set of likeliest tokens whose probabilities reach at least p

- Also: nucleus sampling, top-p sampling
- Contrasts with: top-k
- Defined in: [Sample, and cut the tail](choosing-the-next-token.md#sample-and-cut-the-tail)
- Address: https://rollingedition.com/concepts/large-language-models/top-p

## total log-probability

total log-probability, the sum of the logarithms of a text's token probabilities, where higher means likelier

- Comes before: beam search
- Defined in: [Search for the likeliest text](choosing-the-next-token.md#search-for-the-likeliest-text)
- Address: https://rollingedition.com/concepts/large-language-models/total-log-probability

## training split

a training split that models learn from

- Defined in: [Load the store's text](predicting-the-next-word.md#load-the-store-text)
- Address: https://rollingedition.com/concepts/artificial-intelligence/training-split

## transformer block

The transformer block adds parts around attention that transform each position, give it word order (in the form this chapter builds) and keep a deep stack from degrading

- Defined in: [The transformer block](the-transformer-block.md)
- Address: https://rollingedition.com/concepts/large-language-models/transformer-block

## validation split

a validation split for comparing models while you build them

- The same as: https://rollingedition.com/concepts/model-evaluation/dev-split
- Close to: https://rollingedition.com/concepts/llm-evaluation/dev
- Defined in: [Load the store's text](predicting-the-next-word.md#load-the-store-text)
- Address: https://rollingedition.com/concepts/artificial-intelligence/validation-split

## value

a value, a vector for what this position passes on when it's looked at

- Part of: attention
- Defined in: [Look back with a weighted average](attention.md#look-back-with-a-weighted-average)
- Address: https://rollingedition.com/concepts/deep-learning/value

## vector

a vector, a list of numbers

- Defined in: [Words as vectors](words-as-vectors.md)
- Address: https://rollingedition.com/concepts/artificial-intelligence/vector

## vector length

A vector's length here is the square root of the sum of its squared numbers

- Computed from: vector
- Defined in: [Add each part's output to a residual stream](the-transformer-block.md#add-to-the-residual-stream)
- Address: https://rollingedition.com/concepts/artificial-intelligence/vector-length

## vocabulary

A model can only predict tokens in its vocabulary, the set of tokens it learned from training text

- Comes before: out-of-vocabulary
- Defined in: [Words leave gaps](tokens.md#words-leave-gaps)
- Address: https://rollingedition.com/concepts/natural-language-processing/vocabulary

## warm-up

For the first 200 steps, the step size rises in a straight line from nearly zero to its peak, 0.003: a warm-up

- Part of: schedule
- Defined in: [Warm up, then decay the step size](training-a-small-model.md#warm-up-then-decay)
- Address: https://rollingedition.com/concepts/deep-learning/warm-up

## weight decay

Weight decay reduces each weight at every step by its value times the step size times a decay factor

- A kind of: regularization
- Comes before: AdamW
- Defined in: [Update with AdamW and clipped gradients](training-a-small-model.md#update-with-adamw)
- Address: https://rollingedition.com/concepts/deep-learning/weight-decay

## weight tying

weight tying: the output layer reuses the embedding table, turned on its side, instead of learning a matrix of its own.

- Also: tied embeddings
- Computed from: embedding table
- Defined in: [Tie the output layer to the embeddings](the-transformer-block.md#tie-the-output)
- Address: https://rollingedition.com/concepts/deep-learning/weight-tying
