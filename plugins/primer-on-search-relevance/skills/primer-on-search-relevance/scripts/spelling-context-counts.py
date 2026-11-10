import re
from collections import Counter

from lib.queries import correct_word, edits1, word_counts
from lib.store import load_products, product_text

texts = product_text(load_products()).str.lower()
counts = word_counts(texts)                                   # the corrector's lexicon
words_per_product = [re.findall(r"[a-z]+", text) for text in texts]
pairs = Counter(pair for words in words_per_product for pair in zip(words, words[1:]))      # neighbouring words

# tye in "tye dye duvet cover", an in "refrigerator with ice an water in door": each word, the word after it
for word, after in [("tye", "dye"), ("an", "water")]:
    options = sorted(((pairs[(edit, after)], edit) for edit in edits1(word) | {word} if edit in counts), reverse=True)
    for count, edit in options[:3]:
        print(f"catalog count of {edit} {after}:", count)
    choice = correct_word(word, counts)                        # what the corrector without context picks
    print(f"the corrector's choice for {word}: {choice}")
    print(f"catalog count of {choice} {after}, the corrector's choice:", pairs[(choice, after)])
