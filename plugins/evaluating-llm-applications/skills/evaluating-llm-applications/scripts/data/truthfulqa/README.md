# TruthfulQA sample

100 items from the `multiple_choice` validation split of TruthfulQA, MC1 targets only, for the benchmark chapter.

- **Source:** https://huggingface.co/datasets/truthfulqa/truthful_qa at commit `741b8276f2d1982aa3d5b832d3ee81ed3b896490`
  (card: https://huggingface.co/datasets/truthfulqa/truthful_qa/blob/741b8276f2d1982aa3d5b832d3ee81ed3b896490/README.md)
- **Licence:** Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0). The card's front matter says
  `license: apache-2.0`, and its text says "This dataset is licensed under the Apache License, Version 2.0". Read
  Nov 20, 2026.
- **Manifest:** `../manifest-samples.json`.

## Fields

`id` (`truthfulqa-val-NNNN`, the item's 0-based row in the validation split), `question`, `choices` (the MC1 choices,
in the order the source gives them), `correct_index` (0-based index of the one choice labelled 1 in the source).

## How it was sampled

`numpy.random.default_rng(0)` picks 100 of the 817 validation rows without replacement. Rows are dropped first if the
question or any choice holds an email, phone number, card number, IBAN or `NNN-NN-NNNN` number. No rows were dropped.

## Contamination

TruthfulQA is public, and it may appear in model training data. The chapter says that a score on it cannot show
whether a model saw it.

## Attribution

TruthfulQA, distributed by the `truthfulqa` organisation on the Hugging Face Hub, licensed under the Apache License,
Version 2.0. Changed: 100 items selected, and the MC1 targets reshaped into `choices` and `correct_index`. The
questions and choices are unchanged. A copy of the licence is at http://www.apache.org/licenses/LICENSE-2.0.
