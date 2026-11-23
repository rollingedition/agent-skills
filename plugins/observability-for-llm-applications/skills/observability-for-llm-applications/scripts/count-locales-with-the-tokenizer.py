"""Count the same 200 baseline utterances in six locales with the 4B's own tokenizer file, and price the counts at the book's
input rate. The printed hi-IN ratio is the point the prose rests on: the same request takes several times the English
tokens. Each count is the utterance's text alone, not a whole prompt."""
from decimal import Decimal

from lib.case import load_locale, load_messages
from lib.clock import VirtualClock
from lib.prices import PriceTable
from lib.report import fmt_int, fmt_usd
from lib.tokens import LocaleCounter, is_nfc

DAY = "2026-12-08"
MODEL = "Qwen3-4B-Instruct-2507"
LOCALES = ("en-US", "de-DE", "ja-JP", "hi-IN", "ar-SA", "zh-CN")
messages = load_messages(DAY)
ids = [m.message_id for m in messages]
texts = {m.message_id: m.text for m in messages}
by_id = sorted(messages, key=lambda m: int(m.message_id))   # the order load_locale returns each locale's utterances in
arrivals = [VirtualClock(DAY, start_ns=m.arrival_ns).now_ns for m in by_id]   # each message's own arrival, on the day's clock
counter, price = LocaleCounter(), PriceTable()

print("price table:", price.version)
print("utterances, the baseline day's messages joined by id:", fmt_int(len(ids)))
means = {}
for locale in LOCALES:
    utterances = load_locale(locale, ids)   # the same messages, in ascending ID order, so the locales line up
    counts = [counter.count(text) for text in utterances]
    total = sum(counts)
    means[locale] = total / len(counts)
    # The text is not cached, so every token bills at the input rate, each utterance at its message's arrival.
    per_thousand = sum((price.cost(MODEL, n, 0, 0, at) for n, at in zip(counts, arrivals)), Decimal(0)) * 1000 / len(counts)
    print(f"{locale}, tokens, total:", fmt_int(total))
    print(f"{locale}, tokens per utterance:", f"{means[locale]:.1f}")
    print(f"{locale}, input cost per 1,000 utterances, {price.version}:", fmt_usd(per_thousand))

print("hi-IN tokens per utterance, as a multiple of en-US:", f"{means['hi-IN'] / means['en-US']:.1f}")
hindi = load_locale("hi-IN", ids)
# NFC is applied by the tokenizer file, so only text that is not already NFC can count differently under another counter.
print(f"hi-IN utterances not in NFC, of {len(hindi)}:", sum(not is_nfc(text) for text in hindi))
assert [texts[i] for i in sorted(ids, key=int)] == load_locale("en-US", ids)  # the English texts are the traffic's own
assert all(is_nfc(t) for locale in LOCALES if locale != "hi-IN" for t in load_locale(locale, ids))
