"""Prints SmolLM2's recorded probabilities of cover and set after the same words of a description, under three versions of the name.
The point that each word follows its own name rests on the cover lines for the name as sold and without cover, and the set line for the name ending in set."""
from lib import open_model

copying = open_model.read("copying")     # keyed by the version of the name, each with the probabilities of the tokens after the same words
for label, probabilities in copying.items():
    for token, p in probabilities.items():
        print(f"SmolLM2-360M, {label}, P({token.strip()}):", f"{p:.2f}")     # the recorded tokens carry the space before them; strip removes it
