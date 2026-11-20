# Test set: sablefile documentation assistant

This folder holds `testset.jsonl`, the 120 test questions for the running case of *Evaluating LLM Applications*. Each question is a thing a user might ask a documentation assistant about sablefile, a command-line tool invented for the book. Each item has a reference answer and the documentation sections that support it, for one version of the docs (1.0, 1.1 or 2.0).

## What the labels are

The reference answers and supporting sections are **written labels**. The book's agents wrote them from the docs, a second pass checked each one against the cited sections, and a script checked the schema, the section IDs and the counts. They are not human labels: no person judged these answers, and they should be read as the book's own reference, not as a ground truth from outside.

## Fields

One JSON object per line:

- `id`: `q-` and four digits. Frozen once written.
- `question`: 1 to 400 ASCII characters.
- `version`: `"1.0"`, `"1.1"` or `"2.0"`.
- `kind`: `answerable`, `unanswerable`, `version-dependent` or `ambiguous`.
- `reference_answer`: a string, or `null` exactly when `kind` is `unanswerable`. An `ambiguous` reference has one line per reading, each starting `Reading 1:`, `Reading 2:`.
- `supporting_sections`: a list of `{version, section_id}`. Empty for `unanswerable` items. Otherwise each `version` equals the item's version. An `unanswerable` item may name the other version's section that makes the difference, such as a section that shows a flag exists only in 2.0.
- `split`: `dev` or `held-out`. Only `dev` may be used for tuning.
- `planted` and `planted_why`: see below. `planted_why` is `null` exactly when `planted` is false.
- `twin_of`: the id of the item that asks the same question for another version, or `null`. Twins are symmetric.

## Counts

| Kind | Dev | Held-out | Total |
| --- | --- | --- | --- |
| answerable | 40 | 20 | 60 |
| unanswerable | 13 | 7 | 20 |
| version-dependent | 17 | 8 | 25 |
| ambiguous | 10 | 5 | 15 |
| **Total** | **80** | **40** | **120** |

The 25 version-dependent items are 12 twin pairs and one singleton (`q-0033`).

The chapter 1 set is `q-0001` to `q-0020` (dev): 10 answerable, 4 unanswerable, 4 version-dependent, 2 ambiguous, and 4 planted.

Every behaviour in the docs (sync default, check exit status, ignore syntax, lock file, placeholders, remote retries) has at least two answerable or version-dependent items.

## Planted items

24 items (16 dev, 8 held-out) break an assistant in a known way. Each has one reason:

| Reason | Count | What it tests |
| --- | --- | --- |
| `false-premise` | 6 | asks about a flag or behaviour that the asked version does not have |
| `near-miss-term` | 5 | uses a term that one version renames, such as `sablefile.lock` or `{{name}}` |
| `version-swap` | 5 | asks for one version using the wording of another |
| `stale-answer` | 4 | the answer sits under a section ID that only the asked version has, so an answer built from the older version is stale |
| `ambiguous-target` | 4 | the referent of "it" or "the file" is unclear without the sections |

## Licence

The test set is licensed under the Creative Commons Attribution 4.0 International licence (CC BY 4.0), the same as the sablefile docs it is written from.
