"""Prints SmolLM2's three likeliest next tokens after five search-box prefixes, and its probability of stool after outdoor bar.
The point that its suggestions are the wrong text rests on the top token after each prefix, and on the stool line."""
from lib import open_model

for prefix, recorded in open_model.read("prefixes").items():
    shown = ", ".join(f"{token!r} {p:.2f}" for token, p in recorded["top"][:3])   # the three likeliest tokens, as recorded
    print(f"{prefix:<12} -> {shown}")
# The recorded key keeps the space before stool. Four places: at two, this probability would print as 0.00.
print("P(stool | outdoor bar), SmolLM2-360M:", f"{open_model.read('prefixes')['outdoor bar']['P( stool)']:.4f}")
