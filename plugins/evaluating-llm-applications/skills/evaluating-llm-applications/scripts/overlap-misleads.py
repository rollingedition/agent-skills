"""Scores a wrong answer that shares most of its words with the reference above a right answer that shares few.

Each pair in data/overlap-pairs.json is a question on sablefile 2.0 with its reference, a wrong answer and a right answer.
All three pairs are hand-written for this example, not recorded replies. The scores are the textbook formulas, written
here in plain Python: ROUGE-1 F1 (unigram overlap, F1 of precision and recall) and a BLEU-style score (clipped 1- to
4-gram precision, geometric mean, brevity penalty), with no smoothing. No BLEU or ROUGE package is pinned, and none is
used. The reference facts are in examples/data/docs/2.0 (sync.md, quickstart.md, lockfile.md)."""
import lib  # first: fixes the thread counts and seeds before anything else loads

import json
import math
import re
from collections import Counter
from pathlib import Path

PAIRS = json.loads((Path(__file__).resolve().parent / "data" / "overlap-pairs.json").read_text(encoding="utf-8"))


def words(text: str) -> list[str]:
    """Lowercase runs of letters and digits: `--apply` is the word apply, and `lock.json` is two words."""
    return re.findall(r"[a-z0-9]+", text.lower())


def rouge_1_f1(candidate: str, reference: str) -> float:
    """ROUGE-1 F1: shared words, counted with repeats up to the smaller count, over both lengths."""
    cand, ref = words(candidate), words(reference)
    overlap = sum((Counter(cand) & Counter(ref)).values())
    if overlap == 0:
        return 0.0
    precision, recall = overlap / len(cand), overlap / len(ref)
    return 2 * precision * recall / (precision + recall)


def bleu_sentence(candidate: str, reference: str, max_n: int = 4) -> float:
    """Sentence BLEU-style score: clipped n-gram precision for n = 1 to 4, geometric mean, brevity penalty.

    Without smoothing, a single n-gram order with no match gives 0, as the textbook formula does.
    """
    cand, ref = words(candidate), words(reference)
    precisions = []
    for n in range(1, max_n + 1):
        cand_grams = Counter(tuple(cand[i : i + n]) for i in range(len(cand) - n + 1))
        ref_grams = Counter(tuple(ref[i : i + n]) for i in range(len(ref) - n + 1))
        clipped = sum(min(count, ref_grams[gram]) for gram, count in cand_grams.items())  # each n-gram up to the reference's count
        if clipped == 0:
            return 0.0
        precisions.append(clipped / sum(cand_grams.values()))
    # Short answers are penalised by the brevity penalty: a candidate shorter than the reference scores less.
    brevity = (1.0 if len(cand) > len(ref) else math.exp(1 - len(ref) / len(cand)))
    return brevity * math.exp(sum(math.log(p) for p in precisions) / max_n)


for number, pair in enumerate(PAIRS, start=1):
    print(f"pair {number} (hand-written), question: {pair['question']}")
    for label in ("wrong", "right"):
        print(f"pair {number}, {label} answer, ROUGE-1 F1: {rouge_1_f1(pair[label], pair['reference']):.3f}")
        print(f"pair {number}, {label} answer, BLEU: {bleu_sentence(pair[label], pair['reference']):.3f}")
# The claim the prose makes: the wrong answer overlaps the reference more than the right one, in every pair.
higher = sum(rouge_1_f1(p["wrong"], p["reference"]) > rouge_1_f1(p["right"], p["reference"]) for p in PAIRS)
print(f"pairs where the wrong answer has the higher ROUGE-1 F1: {higher} of {len(PAIRS)}")
