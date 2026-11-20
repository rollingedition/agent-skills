"""Reads the reference-guided judge's verdict on the baseline reply to q-0005, a planted near-miss item, from its recording.

The judge sees the question, the written reference and the reply; the first line of its reply is the verdict."""
import lib  # first: fixes the thread counts and seeds before anything else loads

from lib.answers import Assistant, chapter_items
from lib.contract import parse_verdict
from lib.prompts import P1_SHA256, P1_SYSTEM, REF_SHA256
from lib.replay import ReplayModel

assistant = Assistant("assistant-baseline", P1_SYSTEM, P1_SHA256)
item = next(item for item in chapter_items() if item.id == "q-0005")
print(f"question {item.id} (version {item.version}, {item.kind}, planted: {item.planted_why}): {item.question}")
print(f"reference answer: {item.reference_answer}")
reply = assistant.reply(item)
print(f"assistant reply: {reply.text}")

judge = ReplayModel("judge-answers-baseline", REF_SHA256)  # the prompt hash must match the judge's manifest
raw = judge.reply(item.id, 0)
verdict = parse_verdict(raw)
assert verdict is not None, "the judge's first line must be a verdict"
print(f"judge verdict: {verdict}")
reason = [line.strip() for line in raw.splitlines() if line.strip()][1:]  # the line after the verdict
print(f"judge reason: {reason[0] if reason else 'none'}")
