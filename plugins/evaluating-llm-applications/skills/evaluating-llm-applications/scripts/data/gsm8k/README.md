# GSM8K sample

100 items from the `main` test split of GSM8K, for the benchmark chapter.

- **Source:** https://huggingface.co/datasets/openai/gsm8k at commit `740312add88f781978c0658806c59bc2815b9866`
  (card: https://huggingface.co/datasets/openai/gsm8k/blob/740312add88f781978c0658806c59bc2815b9866/README.md)
- **Licence:** MIT (https://opensource.org/licenses/MIT). The card's front matter says `license: mit`, and its text says
  "The GSM8K dataset is licensed under the MIT License". Read Nov 20, 2026.
- **Manifest:** `../manifest-samples.json`.

## Fields

`id` (`gsm8k-test-NNNN`, the item's 0-based row in the test split), `question`, `answer` (the full worked solution as
published), `final_answer` (the text after `####`, copied from `answer`).

## How it was sampled

`numpy.random.default_rng(0)` picks 100 of the 1,319 test rows without replacement. Rows are dropped first if the
question or solution holds an email, phone number, card number, IBAN or `NNN-NN-NNNN` number. Four rows were dropped
for matching the phone pattern; the script counts them in the manifest. Shipped rows were scanned again with plain grep.

## Contamination

This sample is public, and it may appear in model training data. The chapter says that a score on it cannot show
whether a model saw it.

## Attribution

GSM8K by OpenAI, licensed under the MIT License. Changed: 100 items selected, and `final_answer` added. The question
and answer text is unchanged.

The MIT License requires the copyright notice and the permission notice to be kept with copies. The repository has no
LICENSE file at this commit, and the card does not name a copyright holder. **Unresolved:** the copyright line for
this licence is not in the sources read here, so it has not been added. It must come from the upstream licence text
before release.
