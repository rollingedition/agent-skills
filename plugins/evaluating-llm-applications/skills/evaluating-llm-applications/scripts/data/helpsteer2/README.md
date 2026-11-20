# HelpSteer2 samples

Two JSONL samples from the HelpSteer2 dataset, used for judge calibration.

- **Source:** https://huggingface.co/datasets/nvidia/HelpSteer2 at commit `990b2711a36180dd19d9c94b8627844866f8982a`
  (card: https://huggingface.co/datasets/nvidia/HelpSteer2/blob/990b2711a36180dd19d9c94b8627844866f8982a/README.md)
- **Licence:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The card's front matter says `license: cc-by-4.0`
  and its text says "HelpSteer2 is an open-source Helpfulness Dataset (CC-BY-4.0)". The licence covers the whole
  dataset repository, so it covers the preference annotations in `preference/`. Read Nov 20, 2026.
- **Manifest:** `../manifest-samples.json` (file hashes, filters, drop counts, the seed).

## Files

- `ratings.jsonl`: 180 rows from the validation split, 90 `dev` and 90 `held-out`. Each row has the prompt, the response,
  and the five attribute scores (0 to 4). The judge's reference-free **correctness** verdict is PASS for scores 3 and 4,
  and FAIL for 0 to 2. Sample balance: 92 PASS and 88 FAIL. Each split has 46 PASS and 44 FAIL.
- `preferences.jsonl`: 150 non-tie pairs from the validation split (card label `val`), 75 `dev` and 75 `held-out`.
  Fields: `prompt`, `response_a`, `response_b`, `preferred` (`a` or `b`), and `strength` (1 to 3). The card's signed
  strength is stored as its magnitude, and the sign is turned into `preferred`. Pairs whose strength is 0 (the card's
  "about the same") are left out. Balance: 67 `a`, 83 `b`.

## How they were sampled

`recordings/make_samples.py` makes both files, with `numpy.random.default_rng(0)` and sources in stable order.
Before sampling, rows are dropped if:

- any prompt or response has a character outside tab, newline, carriage return and printable ASCII (`0x20`-`0x7E`);
- a prompt is over 300 words, or a response is over 400 words;
- the text holds an email, phone number, card number (Luhn-valid), IBAN (mod-97-valid) or a `NNN-NN-NNNN` number;
- the prompt has already been kept. HelpSteer2 repeats each prompt about four times, so one row per prompt is kept
  and no prompt appears twice.

Dropped rows (ratings): 289 non-ASCII, 158 over a word limit, 258 repeated prompts, 1 email.
Dropped rows (preferences): 96 ties, 114 non-ASCII, 71 over a word limit.

Scarcity of FAIL rows after these filters (88 unique prompts) means the ratings are not 90/90. All 88 FAIL rows are
used, and PASS rows fill the rest. The two files share 94 prompts, because both are drawn from the validation split.

## Attribution

HelpSteer2 by NVIDIA Corporation, licensed under CC BY 4.0. Changed: rows were selected, filtered and reformatted into
the JSONL files here. The prompts, responses, scores and preference labels are unchanged, except that the preference
strength is stored as a magnitude. The HelpSteer2-Preference paper, which the card names, is arXiv 2410.01257.
