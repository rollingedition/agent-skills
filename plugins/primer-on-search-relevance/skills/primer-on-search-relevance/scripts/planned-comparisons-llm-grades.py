from lib.agreement import PLANNED, PROMPTS, chapter_one_runs, llm_qrels   # PLANNED: chapter 3's, each stage against the last
from lib.metrics import evaluate
from lib.significance import compare, verdict
from lib.store import load_products, load_queries, qrels

EXPLORATORY = [("reranked", "semantic")]                                           # chosen after seeing test means
threshold = 0.05 / len(PLANNED)                   # chapter 3's threshold, so that a verdict means the same either way
print(f"planned comparisons: {len(PLANNED)}\np-value threshold: {threshold:.4f}\ninterval level: {1 - threshold:.4f}")

runs = chapter_one_runs(load_products(), load_queries("test"))
judgment_sets = {"people": qrels("test"), **{f"{prompt} prompt": llm_qrels(prompt) for prompt in PROMPTS}}
established, disagreements = {}, {judges: 0 for judges in judgment_sets}
for judges, judgments in judgment_sets.items():
    ndcg = {ranker: evaluate(run, judgments)["ndcg@10"] for ranker, run in runs.items()}
    for after, before in PLANNED + EXPLORATORY:
        result, name = compare(ndcg[after], ndcg[before], confidence=1 - threshold), f"{after} minus {before}, {judges}"
        print(f"\n{name}: {result['mean difference']:.3f}\n{name}, permutation p: {result['permutation p']:.3f}")
        if (after, before) in PLANNED:
            print(f"{name}, t-test p: {result['t-test p']:.3f}\n{name}, interval: {result['ci low']:.3f} to {result['ci high']:.3f}")
            checks = verdict(result, threshold)
            established[(judges, after, before)] = checks["established"]
            disagree = [check for check in ["t-test", "interval"] if not checks[f"{check} agrees"]]
            disagreements[judges] += bool(disagree)
            print(f"{name}, established: {'yes' if checks['established'] else 'no'}\n"
                  f"{name}, disagrees with the permutation test: {' and '.join(disagree) or 'neither'}")

print()
for judges, count in disagreements.items():
    print(f"planned comparisons where the t-test or interval disagrees, {judges}: {count}")
for prompt in PROMPTS:
    differ = [pair for pair in PLANNED if established[(f"{prompt} prompt", *pair)] != established[("people", *pair)]]
    print(f"verdicts that differ from people's, {prompt} prompt: {'; '.join(f'{after} minus {before}' for after, before in differ) or 'none'}")
