---
title: "Data Governance as Code"
chapter: "Governing data for AI"
chapter_id: governing-data-for-ai
book: data-governance-as-code
edition: 2026.11.27
verified: 2026-11-14
edition_code: 2QX0-VKZT
canonical: https://rollingedition.com/data-governance-as-code/governing-data-for-ai
license: CC BY 4.0
attribution: "“Governing data for AI,” chapter 9 of Data Governance as Code, Edition 2026.11.27, examples passed Nov 14, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/governing-data-for-ai. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Governing data for AI

By the end of this chapter you can build the data an AI assistant learns from under the same rules as every other read of your platform. You'll admit only records whose authors agreed to that use, replace their personal data with pseudonyms and measure what the detector missed, remove duplicates found with MinHash, keep the source of every record with it, and have the pipeline write and check a dataset card on every run. You'll also be able to quote what the EU AI Act says about training data.

The platform, the online learning platform this book follows, wants a course assistant that answers from what learners write in their reviews. It plans to ground the assistant on that text first, and later to fine-tune it on the same text. `review_corpus`, one of the four SQL pipelines that [chapter 4](#lineage-from-pipelines) captures lineage from, copies every row of `learning.reviews` into `ai.review_corpus`, with each review's course and rating. [Chapter 2](#a-catalog-you-can-test) found that `ai.review_corpus` has no owner and no classification, and the copy has four more problems. It holds every review, whether or not its author agreed to their text training an AI. Its text holds names and emails, which [chapter 3](#finding-personal-data) found in reviews. Most of its reviews repeat each other. And nothing in it says where a record came from, so nobody can show that a review was allowed in, or find it again when its author changes their mind.

This chapter rebuilds the job with the book's shared module for AI data, `lib.ai_data`, and the assistant learns only from that governed build: `pipelines/review_corpus.sql` stays as [chapter 4](#lineage-from-pipelines)'s ungoverned copy, so [CI](#run-every-rule-as-one-job) keeps checking its lineage. The module runs the pipeline's own SQL through the enforcement layer that [chapter 6](#enforcing-policies-on-queries) built, replaces the personal data left in the text, removes duplicates, and writes the corpus, its lineage and its dataset card. Its settings are in `governance/ai_data.toml`, reviewed like a policy, and so are the answers the code needs to legal questions, each a placeholder that the platform's legal team replaces with its answer and reason.

## Admit only reviews whose authors consented {#admit-consented-reviews}

On the platform, consent to one use doesn't cover another, because the question a learner answers names the use. Article 5(1)(b) of the EU's General Data Protection Regulation (GDPR) says that personal data shall be "collected for specified, explicit and legitimate purposes and not further processed in a manner that is incompatible with those purposes" ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). The code reads the recorded answer to whether training an AI is covered from `[legal.consent]` in `governance/ai_data.toml`, and decides consent per record when the corpus is built, not from the account's sign-up and not once for the whole table.

`crm.learners.ai_training_consent` records whether a learner agreed to their text training the platform's AI. [Chapter 5](#narrow-by-attribute) made it an attribute the access policy reads, so a read of `learning.reviews` for the purpose `ai-training` keeps only the reviews whose author's answer is true, with contact details removed. `lib.ai_data.read` runs the `SELECT` of `pipelines/review_corpus.sql` through [the enforcement layer](#enforcing-policies-on-queries) as `analyst-1`, the data-science principal, stating the purpose. `lib.ai_data.build` refuses to run unless the layer filters on the column the consent answer names. Compare three builds: the plain pipeline, `pipelines/review_corpus.sql` run as written; the governed read; and a consent filter written by hand.

Example `corpus-consent-filter` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Counts the reviews that three builds of the corpus would hold, and the personal data the plain copy would keep. The prose's point rests on the "share by learners never asked" line."""
from collections import Counter

from lib import ai_data, pii
from lib.catalog import open_catalog
from lib.enforce import Enforcer

platform = Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.reviews"]))
layer = platform.connection           # the enforcement layer's own access, for counting what each build would hold

# The plain pipeline copies every review, with its text as written.
plain = layer.sql("select count(*) from learning.reviews").fetchall()[0][0]
print("reviews the plain pipeline copies:", f"{plain:,}")

# The governed build: the same SQL, through the enforcement layer, as the job's principal, for its purpose.
# the job's own read: its principal and purpose come from the build settings
governed = ai_data.read(platform)
print(f"reviews the governed build reads, as {ai_data.BUILD['principal']} for {ai_data.BUILD['purpose']}:", f"{len(governed):,}")
# no purpose stated: the layer returns every review, with its text left out
without = ai_data.read(platform, purpose=None)
print("reviews read without the purpose:", f"{len(without):,}")
print("of them, with their text:", sum(r["body"] is not None for r in without))

# The filter that looks right: leave out the learners who said no.
# every review except those whose learner said no; a null answer passes, since only "= false" is excluded
opt_out = layer.sql("""
    select count(*), count(*) filter (where l.ai_training_consent is null)
    from learning.reviews r join crm.learners l using (learner_id)
    where r.learner_id not in (select learner_id from crm.learners where ai_training_consent = false)""").fetchall()[0]
print("reviews a filter on refusals keeps:", f"{opt_out[0]:,}")
print("of them, by learners never asked:", f"{opt_out[1]:,}")
print("share by learners never asked:", f"{opt_out[1] / opt_out[0]:.0%}")
# the signup dates of the learners whose consent is still unknown
never = layer.sql("""select min(signup_at)::date, max(signup_at)::date from crm.learners
                     where ai_training_consent is null""").fetchall()[0]
print("learners never asked signed up:", " to ".join(f"{day:%b} {day.day}, {day.year}" for day in never))

# Personal data the plain pipeline's corpus would hold, from the labelled truth, and how often each email is written.
raw = dict(layer.sql("select review_id, body from learning.reviews").fetchall())
for entity, (placed, _) in ai_data.left(raw).items():
    print(f"plain pipeline, labelled {entity} values:", f"{placed:,}")
# each labelled email's text, counted by how many spans write it
emails = Counter(pii.text_of(s) for s in pii.truth() if s.source == "reviews" and s.entity == "EMAIL_ADDRESS")
print("plain pipeline, distinct labelled EMAIL_ADDRESS values:", len(emails))
print("of them, written once:", sum(n == 1 for n in emails.values()))
```

Output:

```text
reviews the plain pipeline copies: 3,000
reviews the governed build reads, as analyst-1 for ai-training: 436
reviews read without the purpose: 3,000
of them, with their text: 0
reviews a filter on refusals keeps: 2,045
of them, by learners never asked: 1,609
share by learners never asked: 79%
learners never asked signed up: Jan 1, 2024 to May 31, 2025
plain pipeline, labelled EMAIL_ADDRESS values: 120
plain pipeline, labelled PERSON values: 798
plain pipeline, distinct labelled EMAIL_ADDRESS values: 113
of them, written once: 106
```

Copied as written, the plain pipeline would put 120 labelled emails and 798 labelled names into the corpus, from 3,000 reviews.

The governed read keeps 436 reviews, the ones whose authors said yes. Without a purpose, the same principal gets 3,000 reviews, 0 of them with their text, so a job that forgets to state its purpose gets nothing it could train on.

Notice that the filter written by hand looks like respect for consent, which is why it's the one to recognize: it leaves out the learners who said no. It keeps 2,045 reviews, and 1,609 of them, 79%, are by learners who were never asked. The README of the platform's generated data says consent is unknown for sign-ups before Jun 1, 2025, and every learner with no answer signed up from Jan 1, 2024 to May 31, 2025. An unknown answer isn't a yes. A corpus built with that filter would be mostly text that no consent covers, and nothing about it would look wrong: no error, a plausible row count, and a condition on the consent column that a reviewer would read as correct. The enforcement layer's filter tests `IS TRUE`, so an unknown answer counts as no, which [chapter 6](#build-row-filters-from-data) built for exactly this case.

On the platform, every review was written under one set of terms, so the card states one licence, read from `[legal.licence]`. A corpus that mixes sources, such as reviews and forum posts, needs a licence per record too, which is one reason [every record keeps its source table](#carry-provenance).

**Working rule:** Decide consent per record, when the corpus is built, from the answer your legal team says covers the use, and admit only records whose answer is yes: never filter out the refusals and keep the rest. Build the corpus through the enforcement layer with its purpose stated, and have the build check that the layer filters on that answer. Keep the legal team's answers, with their reasons, in a reviewed file the code reads, and carry licences per record when a source mixes them.

## Replace personal data in the text, then measure what's left {#replace-personal-data}

Consent decides whose text may enter the corpus. It doesn't make the text free of personal data: a review names its instructor, or gives its author's email for questions. Before such text trains or grounds a model, the corpus job detects the personal data in it, replaces each value, and measures what's left, because a detector's output lists what it found and never what it missed. [The truth](#measure-against-labelled-spans), chapter 3's labelled spans, marks every piece of personal data the generator placed in the reviews. `lib.ai_data.left` counts how many labelled values are still in the text after a step, matching by value, since every replacement moves the offsets after it.

The reviews arrive from the enforcement layer with its `redact_contacts` mask applied, which replaces emails and phone numbers with `[email]` and `[phone]` ([chapter 6](#write-masks-as-sql)). [Chapter 3](#tune-the-recognizers)'s detector, `lib.pii.platform_detector`, runs Presidio's pattern recognizers with no language model, and no pattern finds a name. So `lib.ai_data.detector` adds a Presidio deny list of the names the platform knows: every word of every instructor's name, which Presidio escapes and matches as a whole word, ignoring case unless told otherwise ([Presidio's pattern recognizer](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/pattern_recognizer.py)). The list comes from `crm.instructors`, which `analyst-1` may not read. So the platform team's own job, named in `[names]` in `governance/ai_data.toml`, builds it with the platform's own access, as the enforcement layer reads `crm.learners` for consent, and hands the corpus job the list, never the table. The card records which job built it and how many words it holds. `lib.ai_data.known_names` stands for that job. Each value found becomes a keyed pseudonym, which [the next section](#consistent-pseudonyms) builds. Measure each step on the reviews the corpus reads, then try a longer list, with every learner's name in it too:

Example `corpus-personal-data-left` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Counts the labelled names and emails still in the reviews after each step of the corpus job, and the false positives of the instructors' list and of a longer one. The prose's point rests on the "then the instructors' names, PERSON left" line and the false-positive lines."""
from lib import ai_data, pii
from lib.catalog import open_catalog
from lib.enforce import Enforcer

# The reviews the corpus job reads: consenting authors only, with emails and phone numbers already masked.
rows = ai_data.read(Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.reviews"])))
texts = {row["review_id"]: row["body"] for row in rows}    # keyed by review ID, to match the labelled values row by row

# What's left of the labelled personal data after each step, matched by value against the generator's truth.
detectors = {"then the pattern recognizers": pii.platform_detector(), "then the instructors' names": ai_data.detector()}
# the texts as the enforcement layer leaves them, before any detector runs
stages = {"masked by the enforcement layer": texts}
# each detector runs alone on the masked texts; pseudonymize returns the text first
stages |= {name: {i: ai_data.pseudonymize(engine, text)[0] for i, text in texts.items()} for name, engine in detectors.items()}
for stage, done in stages.items():
    for entity, (placed, still) in ai_data.left(done).items():
        print(f"{stage}, {entity} left: {still} of {placed}")

# the instructors' words, from the governance team's list
names = ai_data.known_names()
print("words in the list of instructors' names:", len(names))
# short words are the ones ordinary text could contain
print("words in the list of 3 characters or fewer:", ", ".join(word for word in names if len(word) <= 3))
false_positives = sum(ai_data.unlabelled(ai_data.detector(), texts).values())
assert false_positives == 0
print("false positives, instructors' names:", false_positives)

# Every name the platform holds, learners' too, on the same reviews: in any case, then only as written.
# the union of the instructors' words and every learner's, which the table holds
longer = sorted(set(names) | set(ai_data.known_names("crm.learners")))
# matched in any case, as the platform's detector matches by default
everyone = ai_data.detector(longer)
wrong = ai_data.unlabelled(everyone, texts)
print("words in the list, with learners' names:", f"{len(longer):,}")
print("false positives, with learners' names:", sum(wrong.values()))
print("most common false positives:", ", ".join(f"{word} ({n})" for word, n in wrong.most_common(2)))
# review 24, which the longer list changes
print("a review after:", ai_data.pseudonymize(everyone, texts[24])[0])
# a word matches only as written, so a lowercase word no longer matches a capitalized name
cased = ai_data.detector(longer, match_case=True)
cased_wrong = sum(ai_data.unlabelled(cased, texts).values())
assert cased_wrong == 0
print("false positives, with learners' names, matching case:", cased_wrong)
# pseudonymize with the cased detector, then count what is left by value
left = ai_data.left({i: ai_data.pseudonymize(cased, text)[0] for i, text in texts.items()})
assert left["PERSON"][1] == 0
print("names left, with learners' names, matching case:", f"{left['PERSON'][1]} of {left['PERSON'][0]}")
```

Output:

```text
masked by the enforcement layer, EMAIL_ADDRESS left: 0 of 19
masked by the enforcement layer, PERSON left: 120 of 120
then the pattern recognizers, EMAIL_ADDRESS left: 0 of 19
then the pattern recognizers, PERSON left: 120 of 120
then the instructors' names, EMAIL_ADDRESS left: 0 of 19
then the instructors' names, PERSON left: 0 of 120
words in the list of instructors' names: 106
words in the list of 3 characters or fewer: Ray, Roy, Ulf, Uss, de, la
false positives, instructors' names: 0
words in the list, with learners' names: 4,316
false positives, with learners' names: 147
most common false positives: best (80), date (67)
a review after: Some videos are out of <PERSON_8e2b63a6>.
false positives, with learners' names, matching case: 0
names left, with learners' names, matching case: 0 of 120
```

The enforcement layer's mask leaves 0 of 19 emails and 120 of 120 names, and the pattern recognizers leave 120 of 120 names, since no pattern finds a name.

Only the instructors' list removes names. With its names added, the detector leaves 0 of 120 names and makes no false positives, although its list holds short words that ordinary text could contain: `Ray, Roy, Ulf, Uss, de, la`.

The longer list, with every learner's name in it too, makes 147 false positives. The most common, `best (80), date (67)`, are surnames that are also English words, and the list turns `Some videos are out of date.` into `Some videos are out of <PERSON_8e2b63a6>.` in the corpus.

Matching case avoids both. Matched only as written, the longer list makes no false positives and leaves no names, because every name in these reviews is capitalized. On real text it would miss the names typed in lowercase that [chapter 3 found in tickets](#where-patterns-fail). The platform keeps the instructors' list, matched in any case: instructors are the people reviews talk about, and the corpus job then holds their names instead of every learner's.

The list's result holds for this data only. The labelled spans are generated, and the generated reviews name only instructors, so they can't contain the case a list of instructors misses, such as a classmate's name. For names nobody listed, the detector to try is a named-entity model. [Chapter 3](#compare-a-named-entity-model) compared one, OpenAI's Privacy Filter, from a recording of its detections, scored against the labelled spans with `lib.pii.score`. Score it the same way, on the reviews the corpus reads:

Example `privacy-filter-on-the-corpus` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Scores OpenAI's Privacy Filter, from its recorded detections, against the labelled spans in the reviews the corpus reads. The prose's point rests on the "names the model finds, exactly" and "names the model misses" lines."""
from collections import Counter

from lib import ai_data, pii
from lib.catalog import open_catalog
from lib.enforce import Enforcer

# Privacy Filter's eight labels, mapped to the labelled spans' entity types. A label with no type matches nothing.
MATCHES = {"private_person": {"PERSON"}, "private_email": {"EMAIL_ADDRESS"}, "private_phone": {"PHONE_NUMBER"},
           "private_address": {"LOCATION"}, "account_number": {"CREDIT_CARD", "IBAN_CODE"},
           "private_date": {"DATE_TIME"}, "private_url": set(), "secret": set()}

# The reviews the corpus job reads, with the model's recorded detections and the labelled spans in them. The model read
# each review as written, before the enforcement layer's mask, which changes no name.
corpus = {row["review_id"] for row in ai_data.read(Enforcer(open_catalog(["crm.learners", "learning.courses",
                                                                          "learning.reviews"])))}
# the model's detections as recorded, not a live call to the model
model, manifest = pii.recorded("pii-entities")
found = [span for span in model if span.source == "reviews" and span.row_id in corpus]
labelled = [span for span in pii.truth() if span.source == "reviews" and span.row_id in corpus]
print("model:", manifest["model"])
print("reviews measured:", len(corpus))

# per entity type: [labelled, found exactly, found overlapping], then per detector label: [found, exact, overlapping]
scores = pii.score(found, labelled, MATCHES)
# the overlap count is unused here: the prose counts exact matches only
placed, exact, _ = scores.recall["PERSON"]
print("labelled names:", placed)
print("names the model finds, exactly:", exact)
# private_person is the model's label for a name, so only that label counts as a match
missed = pii.missed([span for span in labelled if span.entity == "PERSON"], found, {"private_person"})
print("names the model misses:", len(missed))
often = Counter(map(pii.text_of, missed)).most_common(3)
print("names it misses most often:", ", ".join(f"{name} ({n})" for name, n in often))

# What the model finds where no labelled span of the type its label maps to is: text it would replace for nothing.
wrong = sum(n - overlap for n, _, overlap in scores.precision.values())
print("the model's detections:", len(found))
print("of them, overlapping no labelled span of their type:", wrong)
```

Output:

```text
model: openai/privacy-filter
reviews measured: 436
labelled names: 120
names the model finds, exactly: 83
names the model misses: 37
names it misses most often: Marie (4), Liwia (4), Luigi (4)
the model's detections: 102
of them, overlapping no labelled span of their type: 0
```

On these reviews the model can't replace the list, and this data can't show what it adds, since every name in it is on the list. It finds 83 of the 120 labelled names exactly and misses 37, most often `Marie (4), Liwia (4), Luigi (4)`, where the list misses none.

Of its 102 detections, 0 overlap no labelled span of their type. Where text names people no list holds, run both, measured this way first.

The text that comes out can still identify people. A detector misses spans, the text can identify someone without a name, and each record keeps a review ID that leads back to its author through `learning.reviews`. The GDPR's Recital 26 says: "Personal data which have undergone pseudonymisation, which could be attributed to a natural person by the use of additional information should be considered to be information on an identifiable natural person" ([GDPR, Recital 26](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). So we call the corpus pseudonymized, never anonymized.

**Working rule:** Detect personal data in corpus text after the enforcement layer's masks, add the identifiers your platform holds about the people the text is about, and measure what's left against labelled data, by value, after every change to the detector. Prefer a short list of the names your text is about to every name you hold, since a long list matches ordinary words. Have a job that may read the names build the list, and record which list each corpus used. Measure a named-entity model the same way before you rely on it for names no list holds. Keep the list out of the corpus, and call the result pseudonymized.

## Keep pseudonyms consistent with a keyed hash {#consistent-pseudonyms}

A detected name can be replaced by a placeholder, `<PERSON>`, or by a pseudonym: a token for one name, the same wherever that name appears. The platform's reviews name an instructor by first name only, and no two instructors share a first name, so here a token stands for one person. A pseudonym keeps who is who, so two reviews that praise the same instructor still say so.

Presidio's anonymizer has a `hash` operator, and since version 2.2.361 it salts each hash at random by default, for security ([Presidio anonymizer](https://presidio.dataprivacystack.org/anonymizer/)). A random salt makes each hash unlinkable to the next, and so useless as a pseudonym. To get the same hash for the same value, the docs say you "**must** explicitly provide a `salt` parameter", at least 128 bits (16 bytes) long.

The corpus job uses its own keyed hash instead, through Presidio's `custom` operator, which takes a lambda that must return a string. `lib.ai_data.pseudonym` computes an HMAC with SHA-256 of the entity type and the case-folded value, under a key only the corpus job holds, and keeps eight hexadecimal digits. HMAC is the construction RFC 2104 describes for keying a hash, and one of its stated goals is "To have a well understood cryptographic analysis of the strength of the authentication mechanism based on reasonable assumptions on the underlying hash function" ([RFC 2104](https://www.rfc-editor.org/rfc/rfc2104)). Python's standard library has it, as `hmac`, so the job has no reason to key a hash any other way.

Two of the corpus's reviews name the same instructor, and replacing that name both ways shows which way keeps the two linked:

Example `keyed-pseudonyms` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Replaces the same instructor's name in two reviews by Presidio's hash, by the corpus's keyed hash and by the enforcement layer's mask. The prose's point rests on the Presidio hash lines and the keyed pseudonym line."""
from collections import Counter

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import InvalidParamError, OperatorConfig
from sqlglot import exp

from lib import ai_data, enforce
from lib.catalog import open_catalog
from lib.enforce import Enforcer
from lib.platform import load

# Two of the corpus's reviews that name the same instructor, with what the detector found in each.
layer = Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.reviews"]))
engine = ai_data.detector()
found = [(row["body"], engine.analyze(row["body"], language="en")) for row in ai_data.read(layer)]
# the first two reviews whose only detected name is Patrick
named = [(text, spans) for text, spans in found if [text[s.start:s.end] for s in spans] == ["Patrick"]][:2]
print("reviews naming Patrick:", len(named))

def replaced(operator: OperatorConfig) -> list[str]:
    """The value that replaced the name in each of the two reviews."""
    results = [AnonymizerEngine().anonymize(text, spans, {"PERSON": operator}) for text, spans in named]
    return [result.text[item.start:item.end] for result in results for item in result.items]

# Presidio's hash salts each value at random, so the same name gets a different hash in each review
hashed = replaced(OperatorConfig("hash"))
assert hashed[0] != hashed[1]
print("Presidio's hash, the same name in two reviews gets one value:", hashed[0] == hashed[1])
# and hashing the same review again gives it a different hash too
rehashed = replaced(OperatorConfig("hash"))[0]
assert rehashed != hashed[0]
print("Presidio's hash, one review hashed twice gets one value:", rehashed == hashed[0])
# a fixed salt must be at least 16 bytes; this one is 10, so Presidio refuses it
try:
    replaced(OperatorConfig("hash", {"salt": "ten bytes!"}))
except InvalidParamError as error:
    print("a fixed salt of 10 bytes:", error)

# the custom operator's lambda returns the keyed pseudonym as the replacement
keyed = replaced(OperatorConfig("custom", {"lambda": lambda value: ai_data.pseudonym("PERSON", value)}))
print("keyed pseudonyms:", ", ".join(keyed))
print("the name typed in lowercase:", ai_data.pseudonym("PERSON", "patrick"))
# the first word of each instructor's full name
first_names = Counter(name.split()[0] for name in load("crm.instructors").column("full_name").to_pylist())
shared = sum(n for n in first_names.values() if n > 1)
assert shared == 0
print("instructors who share a first name with another:", shared)

# What the enforcement layer's pseudonymize mask makes of the same name, run by the layer under its own key.
mask = enforce.masked("pseudonymize", exp.Literal.string("Patrick"), "VARCHAR").sql(enforce.DIALECT)
print("the enforcement layer's pseudonymize mask, on the same name:", layer.run(f"select {mask}").fetchall()[0][0])
# functions whose name mentions HMAC: the prose says DuckDB has none
hmac = layer.connection.sql("select count(*) from duckdb_functions() where function_name ilike '%hmac%'").fetchall()[0][0]
assert hmac == 0
print("HMAC functions in DuckDB:", hmac)
```

Output:

```text
reviews naming Patrick: 2
Presidio's hash, the same name in two reviews gets one value: False
Presidio's hash, one review hashed twice gets one value: False
a fixed salt of 10 bytes: Salt must be at least 16 bytes (128 bits). Provided salt is 10 bytes.
keyed pseudonyms: <PERSON_d14171be>, <PERSON_d14171be>
the name typed in lowercase: <PERSON_d14171be>
instructors who share a first name with another: 0
the enforcement layer's pseudonymize mask, on the same name: 23b3d8671d01840655296f752121aecc4f7991694260e5e1431d2b57c5e3d53f
HMAC functions in DuckDB: 0
```

Presidio's `hash` gives the same name a different value in each of the two reviews, and gives one review a different value each time it's hashed. Presidio also refuses a fixed salt that's too short, here 10 bytes, with `Salt must be at least 16 bytes (128 bits). Provided salt is 10 bytes.`, as the docs say. The keyed hash gives both reviews `<PERSON_d14171be>, <PERSON_d14171be>`, and the name typed in lowercase gets `<PERSON_d14171be>` too.

The enforcement layer's `pseudonymize` mask, run by the layer on the same name, gives `23b3d8671d01840655296f752121aecc4f7991694260e5e1431d2b57c5e3d53f`. It's SHA-256 over the layer's key followed by the value, as [chapter 6](#write-masks-as-sql) writes it, not an HMAC, because the layer's masks are SQL and DuckDB 2.0.0 has no HMAC function. The two are different constructions under different keys, so the corpus's pseudonyms can't be joined with the ones the layer shows analysts.

Consistency has two costs. Whoever holds the key and a list of names can compute every pseudonym, as chapter 6 showed for emails, so the key lives in a secret manager, never in the corpus, the repository or a log. Keyed pseudonyms also keep apart reviews that placeholders would merge: 96 distinct texts against 21, which [the next section](#near-duplicates-with-minhash) measures. We recommend keyed pseudonyms where the text's meaning depends on telling people apart, as in a ticket that names an agent and a learner, and placeholders where nothing downstream needs to.

**Working rule:** Make pseudonyms with HMAC under a key only the job holds, and give each corpus or audience whose pseudonyms must not join a key of its own. Never use Presidio's `hash` operator without a salt for pseudonyms, since at its pinned version each hash is random. Pseudonymize a person's ID rather than a word of their name when two people can share one, and use a plain placeholder when nothing downstream needs to tell people apart.

## Find near-duplicates with MinHash {#near-duplicates-with-minhash}

Once its names are [pseudonymized](#consistent-pseudonyms), the corpus's next problem is repetition: templates, copies, a review pasted twice, the same sentence from many people. Repetition is a privacy problem as well as a quality one. Kandpal, Wallace and Raffel found that "a sequence that is present 10 times in the training data is on average generated ~1000 times more often than a sequence that is present only once" ([Kandpal et al., 2022](https://arxiv.org/abs/2202.06539)).

Near-copies need a measure of similarity. Broder defined the resemblance of two documents as the Jaccard similarity of their sets of shingles, the overlapping runs of characters or words in each. He showed that sampling the smallest shingles under a random permutation gives an unbiased estimate of that resemblance ([Broder, 1997](https://doi.org/10.1109/SEQUEN.1997.666900)). Taking the smallest shingle under each of many permutations gives a MinHash signature, which estimates the similarity of two texts without comparing their sets ([Mining of Massive Datasets, section 3.3](http://infolab.stanford.edu/~ullman/mmds/ch3n.pdf)).

`lib.ai_data.deduplicate` removes exact copies first, by SHA-256 of the case-folded text with runs of white space made one. It compares what's left as sets of 5-character shingles with datasketch's `MinHash` and `MinHashLSH`, which returns candidate pairs, and confirms each candidate by its exact Jaccard similarity. A confirmed pair at 0.8 or more is a near-duplicate, unless it differs only in a name, and of each group of duplicates the record with the lowest review ID stays. The duplicate step runs on the pseudonymized reviews, and each stage reports what it removed:

Example `corpus-duplicates` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Runs the corpus's duplicate step on the pseudonymized reviews: exact copies, then near-duplicates by MinHash LSH, each confirmed exactly, and the records kept. The prose's point rests on the "of them, differing only in a name" and "near-duplicates removed" lines."""
from collections import Counter

from lib import ai_data
from lib.catalog import open_catalog
from lib.enforce import Enforcer

# The reviews the corpus job reads, pseudonymized, then deduplicated: exact copies, then near-duplicates.
# the reviews read, each text pseudonymized; the second value counts the replacements
rows, _ = ai_data.read_pseudonymized(Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.reviews"])))
# groups of reviews that stand for one record, and how many each step removed
groups, removed = ai_data.duplicate_groups(rows)
print("reviews read:", len(rows))
# one review per distinct normalized text: the one with the lowest review ID
print("distinct texts:", len(ai_data.exact_distinct(rows)))
for step, count in removed.items():
    print(f"{step}:", count)
print("records kept:", len(groups))
print("share of the reviews read that duplicate another:", f"{1 - len(groups) / len(rows):.0%}")

# identical texts only, before normalization
text, copies = Counter(row["body"] for row in rows).most_common(1)[0]
print("the most repeated text:", text)
print("its copies:", copies)

# A pair MinHash finds and the exact comparison confirms, and whether it differs only in a name.
distinct = [row["body"] for row in ai_data.exact_distinct(rows)]
# the first confirmed pair, by position among the distinct texts
i, j = sorted(ai_data.near_duplicates(distinct).confirmed)[0]
print("a near-duplicate pair:", distinct[i], "|", distinct[j])
print("its Jaccard similarity:", f"{ai_data.jaccard(distinct[i], distinct[j]):.2f}")
# equal once each pseudonym is a placeholder: the pair differs only in which names it holds
print("it differs only in a name:", ai_data.placeholders(distinct[i]) == ai_data.placeholders(distinct[j]))

# Each record kept stands for its group's reviews, under the review ID and course of the first.
# a group whose reviews come from more than one course
several = sum(len({row["course_id"] for row in group}) > 1 for group in groups)
print("records that stand for reviews of several courses:", several)
```

Output:

```text
reviews read: 436
distinct texts: 96
exact duplicates removed: 340
near-duplicate pairs from LSH: 381
near-duplicate pairs confirmed: 8
of them, differing only in a name: 8
near-duplicates removed: 0
records kept: 96
share of the reviews read that duplicate another: 78%
the most repeated text: Clear explanations and good exercises.
its copies: 56
a near-duplicate pair: Some videos are out of date. <PERSON_85783bac> explains things well. Happy to talk about it, write to me at [email]. | Some videos are out of date. <PERSON_967f9ae8> explains things well. Happy to talk about it, write to me at [email].
its Jaccard similarity: 0.81
it differs only in a name: True
records that stand for reviews of several courses: 23
```

Most of the corpus repeats itself. Of the 436 reviews read, 78% repeat another: 340 are exact copies, and only 96 texts are distinct. That's mostly the generator's doing, since it builds reviews from a handful of fixed sentences, so measure the share on your own text before training on it.

The most repeated text, "Clear explanations and good exercises.", alone appears 56 times.

MinHash then confirms 8 pairs at 0.8 or more, such as two reviews at a similarity of 0.81 that differ only in their instructor's pseudonym. Of those pairs, 8 differ only in a name, which the platform keeps apart, so near-duplicates remove 0.

Why pairs that differ only in a name stay apart comes down to what one threshold means at different lengths. Compare the corpus's reviews with the names as written, with keyed pseudonyms and with plain placeholders, then split every pair of distinct texts by whether it differs only in a name:

Example `names-and-near-duplicates` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Counts near-duplicate pairs of the corpus's reviews with names as written, with keyed pseudonyms and with placeholders, then splits the pairs that differ only in a name by length. The prose's point rests on the pair counts and the length ranges."""
from itertools import combinations

from lib import ai_data
from lib.catalog import open_catalog
from lib.enforce import Enforcer

# The reviews the corpus job reads, three ways: names as written, keyed pseudonyms, and plain placeholders.
layer = Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.reviews"]))
keyed, _ = ai_data.read_pseudonymized(layer)
# the same reviews with each pseudonym replaced by a plain placeholder, as the third way
ways = {"names as written": ai_data.read(layer), "keyed pseudonyms": keyed,
        "placeholders": [row | {"body": ai_data.placeholders(row["body"])} for row in keyed]}
# the similarity at which a pair is a near-duplicate
threshold = ai_data.DUPLICATES["threshold"]
for way, rows in ways.items():
    texts = [row["body"] for row in ai_data.exact_distinct(rows)]
    print(f"{way}, distinct texts:", len(texts))
    print(f"{way}, pairs at {threshold} or more:", len(ai_data.near_duplicates(texts).confirmed))

# Every pair of distinct pseudonymized texts, split by whether the pair differs only in a name.
# distinct texts only, so each text appears once in the pairs
texts = [row["body"] for row in ai_data.exact_distinct(keyed)]
name_only, other = [], []
for a, b in combinations(texts, 2):
    # similarity comes first, so min and max over these tuples order the pairs by it
    pair = (ai_data.jaccard(a, b), len(a), a, b)
    (name_only if ai_data.placeholders(a) == ai_data.placeholders(b) else other).append(pair)
print("pairs that differ only in a name:", len(name_only))
# the lowest and highest similarity among the name-only pairs
print("their Jaccard similarity:", f"{min(name_only)[0]:.2f} to {max(name_only)[0]:.2f}")
for label, lengths in [(f"below {threshold}", [n for s, n, _, _ in name_only if s < threshold]),
                       (f"at {threshold} or more", [n for s, n, _, _ in name_only if s >= threshold])]:
    print(f"their length in characters, {label}:", f"{min(lengths)} to {max(lengths)}")
# the most similar pair among those that differ in more than a name
similarity, _, a, b = max(other)
print("the most similar pair that differs in more than a name:", f"{similarity:.2f}")
print("that pair:", a, "|", b)
```

Output:

```text
names as written, distinct texts: 96
names as written, pairs at 0.8 or more: 10
keyed pseudonyms, distinct texts: 96
keyed pseudonyms, pairs at 0.8 or more: 8
placeholders, distinct texts: 21
placeholders, pairs at 0.8 or more: 0
pairs that differ only in a name: 459
their Jaccard similarity: 0.68 to 0.83
their length in characters, below 0.8: 66 to 78
their length in characters, at 0.8 or more: 116 to 119
the most similar pair that differs in more than a name: 0.66
that pair: Clear explanations and good exercises. Happy to talk about it, write to me at [email]. | Clear explanations and good exercises. <PERSON_3026fb67> explains things well. Happy to talk about it, write to me at [email].
```

Which pairs reach 0.8 depends on what stands in for each name. With the names as written, 10 pairs reach 0.8, and with keyed pseudonyms 8, since a pseudonym is longer than most first names and so a larger share of a short review. With plain placeholders, the 21 distinct texts hold 0.

Among the pseudonymized texts, 459 pairs differ only in which pseudonym they hold, at similarities from 0.68 to 0.83, and the threshold splits them by length alone: those below 0.8 are 66 to 78 characters long, and those at 0.8 or more are 116 to 119 characters long.

So the task, not the threshold, decides whether such reviews are duplicates: for a model that learns how learners describe courses, they are, and for one that learns what learners say about each instructor, they aren't. The platform's assistant answers about each course and its instructor, so `name_only_pairs_are_duplicates = false` in `governance/ai_data.toml`, and `deduplicate` never merges two texts that are the same once their pseudonyms are placeholders. The threshold decides the other pairs. The most similar of those, at 0.66, is a review with and without its sentence about the instructor: two different reviews. The platform keeps 0.8, above that pair with a margin.

Deduplicating on text folds reviews of different courses into one record, under the review ID and course of its first review, so the corpus keeps 96 records, and 23 of them stand for reviews of several courses. For training that's the point, since the model learns from the text. For grounding an answer about one course it costs recall, which [the provenance section](#carry-provenance) takes up.

**Working rule:** Deduplicate training text in two steps, exact copies by a hash of the normalized text and then near-duplicates by MinHash, each confirmed by its exact similarity, and report how much each step removed. Pseudonymize first, so that no name reaches the comparison or the sketches and the comparison can tell which pairs differ only in a name. Keep those pairs apart when the text's meaning depends on whom it names, and compare on placeholders when it doesn't. Choose the threshold by reading the pairs close above and below it in your own text.

## Tune LSH for recall, then confirm every pair {#tune-lsh-then-confirm}

[MinHash signatures](#near-duplicates-with-minhash) make each comparison cheap; locality-sensitive hashing (LSH) avoids most comparisons. It cuts each signature into b bands of r rows, and two texts become a candidate pair when all the rows of any one band match. Leskovec, Rajaraman and Ullman derive the chance of that for a pair with Jaccard similarity s ([Mining of Massive Datasets, chapter 3](http://infolab.stanford.edu/~ullman/mmds/ch3n.pdf)):

P(candidate) = 1 − (1 − sʳ)ᵇ

It's an S-shaped curve: a pair well below the threshold is rarely a candidate, a pair well above it nearly always, and near the threshold it's close to a coin toss. Its approximate threshold is (1/b)^(1/r). datasketch's documentation warns of both kinds of error: "There will be false positives - sets that do not satisfy your threshold but returned, and false negatives - qualifying sets that are not returned" ([datasketch, MinHash LSH](https://ekzhu.github.io/datasketch/lsh.html)).

With 96 distinct texts, the platform can afford to compare every pair exactly, 4,560 pairs, and that gives the exact pairs to measure LSH against. LSH sees only similarity, so it must return every pair at 0.8, whatever the name rule then decides. Score LSH against the exact comparison, tuned for 0.8 and tuned lower, each under datasketch's default hashing and under the hashing it used before its 2.0.0 release:

Example `lsh-misses-near-duplicates` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Measures the pairs LSH misses against every pair compared exactly, under two tunings and two hashing schemes, and shows what datasketch does with sketches of two schemes. The prose's point rests on the "missed" lines."""
from itertools import combinations

from datasketch import MinHashLSH

from lib import ai_data
from lib.catalog import open_catalog
from lib.enforce import Enforcer

rows, _ = ai_data.read_pseudonymized(Enforcer(open_catalog(["crm.learners", "learning.courses", "learning.reviews"])))
texts = [row["body"] for row in ai_data.exact_distinct(rows)]
# the similarity at which a pair is a near-duplicate
threshold = ai_data.DUPLICATES["threshold"]

# Every pair compared exactly: possible at this size, and the truth LSH is measured against.
pairs = {(i, j) for i, j in combinations(range(len(texts)), 2) if ai_data.jaccard(texts[i], texts[j]) >= threshold}
print("pairs compared exactly:", f"{len(texts) * (len(texts) - 1) // 2:,}")
print(f"pairs at a Jaccard similarity of {threshold} or more:", len(pairs))

found = {}
for scheme in ["affine32", "legacy"]:
    # LSH tuned for the threshold, and for the lower candidate threshold
    for tuned_for in [threshold, ai_data.DUPLICATES["candidate_threshold"]]:
        # the bands and rows LSH chose, its candidates, and the candidates the exact check confirms
        found[scheme, tuned_for] = result = ai_data.near_duplicates(texts, threshold, tuned_for, scheme)
        setting = f"{scheme}, LSH tuned for {tuned_for}"
        print(f"{setting}, bands:", result.bands)
        print(f"{setting}, rows per band:", result.rows)
        print(f"{setting}, candidate pairs:", len(result.candidates))
        print(f"{setting}, confirmed:", len(result.confirmed))
        # pairs the exact comparison found that LSH never proposed as candidates
        missed = len(pairs - result.candidates)
        print(f"{setting}, missed:", missed)
        if tuned_for != threshold:
            assert missed == 0  # tuned lower, LSH finds every pair under either scheme

# The chance that a pair of similarity s becomes a candidate, with b bands of r rows: 1 - (1 - s^r)^b.
# the bands and rows LSH chose for the threshold, as the formula uses them
b, r = found["affine32", threshold].bands, found["affine32", threshold].rows
for s in [0.8, 0.9]:
    print(f"chance of a candidate at similarity {s}, LSH tuned for {threshold}:", f"{1 - (1 - s ** r) ** b:.2f}")
# the S-curve's approximate threshold, which the prose compares with the threshold asked for
print("the approximate threshold, (1/b)^(1/r):", f"{(1 / b) ** (1 / r):.2f}")

# What datasketch does with a sketch made under the other scheme.
# an index takes sketches of one scheme, so the legacy sketch below is refused
index = MinHashLSH(threshold=threshold, num_perm=ai_data.DUPLICATES["num_perm"])
index.insert(0, ai_data.minhash(texts[0], "affine32"))
try:
    index.insert(1, ai_data.minhash(texts[1], "legacy"))
except ValueError as error:
    print("a legacy sketch in an index of affine32 sketches:", error)
```

Output:

```text
pairs compared exactly: 4,560
pairs at a Jaccard similarity of 0.8 or more: 8
affine32, LSH tuned for 0.8, bands: 9
affine32, LSH tuned for 0.8, rows per band: 13
affine32, LSH tuned for 0.8, candidate pairs: 36
affine32, LSH tuned for 0.8, confirmed: 1
affine32, LSH tuned for 0.8, missed: 7
affine32, LSH tuned for 0.6, bands: 18
affine32, LSH tuned for 0.6, rows per band: 7
affine32, LSH tuned for 0.6, candidate pairs: 381
affine32, LSH tuned for 0.6, confirmed: 8
affine32, LSH tuned for 0.6, missed: 0
legacy, LSH tuned for 0.8, bands: 9
legacy, LSH tuned for 0.8, rows per band: 13
legacy, LSH tuned for 0.8, candidate pairs: 52
legacy, LSH tuned for 0.8, confirmed: 6
legacy, LSH tuned for 0.8, missed: 2
legacy, LSH tuned for 0.6, bands: 18
legacy, LSH tuned for 0.6, rows per band: 7
legacy, LSH tuned for 0.6, candidate pairs: 406
legacy, LSH tuned for 0.6, confirmed: 8
legacy, LSH tuned for 0.6, missed: 0
chance of a candidate at similarity 0.8, LSH tuned for 0.8: 0.40
chance of a candidate at similarity 0.9, LSH tuned for 0.8: 0.93
the approximate threshold, (1/b)^(1/r): 0.84
a legacy sketch in an index of affine32 sketches: MinHash scheme 'legacy' does not match scheme 'affine32' of the MinHash previously given to this index
```

Tuned for 0.8, datasketch's default LSH returns 36 candidate pairs, misses 7 of the 8 pairs that reach 0.8, and so confirms only 1 of them.

The formula says why. With the 9 bands of 13 rows datasketch chose, a pair at similarity 0.8 becomes a candidate with a probability of 0.40, one at 0.9 with 0.93, and the approximate threshold is 0.84, above the threshold asked for.

Under the default scheme, tuned for 0.6, LSH finds every pair and returns 381 candidates. Each candidate costs one exact comparison, against 4,560 for comparing every pair, and the exact comparison discards every pair below 0.8. So the platform tunes LSH for 0.6 and confirms at 0.8, both settings in `governance/ai_data.toml`.

datasketch's 2.0.0 release made `affine32` the default permutation scheme of MinHash, and [its release notes](https://github.com/ekzhu/datasketch/releases/tag/v2.0.0) say that hash values differ from earlier versions, so they advise rebuilding persisted sketches and LSH indexes, or passing `MinHash(..., scheme="legacy")`. With the legacy scheme, LSH tuned for 0.8 returns 52 candidates and confirms 6, so a count recorded under one scheme isn't reproduced under the other.

Tuned for 0.6, both schemes find all 8 pairs. With high recall and an exact check, the result depends on the similarity, not on the hash functions.

datasketch refuses to mix schemes in one index, with `MinHash scheme 'legacy' does not match scheme 'affine32' of the MinHash previously given to this index`, but it won't stop you comparing old counts with new ones. The book's examples pin datasketch at 2.0.0 and write `scheme = "affine32"` into the settings, so an upgrade can't change a recorded count without a reviewed change.

**Working rule:** Tune LSH below your similarity threshold, so that it misses few pairs, and confirm every candidate by its exact similarity. Measure LSH's misses against an exhaustive comparison on a sample of your corpus whenever its settings, its library or the text change. Pin the MinHash library, write its hashing scheme into your settings, and never compare counts or stored sketches made under different schemes.

## Carry provenance on every record {#carry-provenance}

A record that can't be traced to its source can't be checked, corrected or removed. Provenance at the level of the record answers three questions: which table it came from, which row, and which run of which job put it in the corpus. [Chapter 4](#send-run-events) gives the platform the last part: every run of a job sends OpenLineage events, with a run ID derived from the run's time and the job's name, and column lineage parsed from the job's SQL.

`lib.ai_data.build` writes every record with its provenance beside the review's own columns: `source_table`, `review_id`, `job` and `run_id`. It sends the job's run events with `lib.lineage.record`. One choice there matters: the lineage is parsed from the query as the enforcement layer ran it, with the consent filter and the mask in it, not from the SQL in `pipelines/review_corpus.sql`. Build the corpus, then follow one record back to its run:

Example `corpus-provenance` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Builds the corpus and follows one record back to its source row, its job and the run that wrote it, then checks that run's lineage against the query as written. The prose's point rests on the "rows filtered by" and "body" lines."""
from lib import ai_data, lineage, pipelines
from lib.catalog import open_catalog

catalog = open_catalog(["crm.learners", "learning.courses", "learning.reviews"])
built = ai_data.build(catalog)
# the second record, whose text holds a pseudonym
record = built.records.to_pylist()[1]
print("a record's text:", record["body"])
for column in ["source_table", "review_id", "job"]:
    print(f"its {column}:", record[column])

# The run that wrote it, from the lineage events: the query as the enforcement layer ran it.
# the job's COMPLETE event, which carries the run's lineage
complete = [e for e in lineage.read_events(built.folder / "events.jsonl") if e["eventType"] == "COMPLETE"][0]
same_run = record["run_id"] == complete["run"]["runId"]
assert same_run
print("its run_id is the COMPLETE event's run:", same_run)
print("the run's inputs:", ", ".join(dataset["name"] for dataset in complete["inputs"]))
# column lineage: the inputs that filter the rows, and how each field is transformed
facet = complete["outputs"][0]["facets"]["columnLineage"]
# a FILTER transformation marks an input whose values decide which rows the output holds
filters = [f"{i['name']}.{i['field']}" for i in facet["dataset"] if any(t["subtype"] == "FILTER" for t in i["transformations"])]
print("rows filtered by, as run:", ", ".join(filters))
# the lineage of the review text, from the reviews table
text = [i for i in facet["fields"]["body"]["inputFields"] if (i["name"], i["field"]) == ("learning.reviews", "body")]
# IDENTITY means copied unchanged; TRANSFORMATION means the value was changed on its way
print("body, as run:", text[0]["transformations"][0]["subtype"])
# the same lineage parsed from the SQL as written, with no enforcement rewrite
fields, rows = lineage.column_lineage(pipelines.sql(ai_data.BUILD["job"]), lineage.schema(catalog))
print("rows filtered by, as written:", ", ".join(i.source for i in rows if i.subtype == "FILTER") or "nothing")
print("body, as written:", fields["body"][0].subtype)

# Back from every record to its review's author, with the platform's own access, against today's answers.
# each record's review ID, checked against the author's consent today, not at build time
ids = built.records.column("review_id").to_pylist()
print("records whose author consented:", f"{ai_data.consenting(catalog, ids)} of {len(ids)}")
```

Output:

```text
a record's text: Too fast in the second half. <PERSON_85783bac> explains things well.
its source_table: learning.reviews
its review_id: 18
its job: platform/review_corpus
its run_id is the COMPLETE event's run: True
the run's inputs: crm.learners, learning.courses, learning.reviews
rows filtered by, as run: crm.learners.ai_training_consent, learning.reviews.learner_id
body, as run: TRANSFORMATION
rows filtered by, as written: nothing
body, as written: IDENTITY
records whose author consented: 96 of 96
```

Following a record back shows what the lineage has to record. The record "Too fast in the second half. <PERSON_85783bac> explains things well." came from `learning.reviews`, review 18, written by the job `platform/review_corpus`, and its `run_id` is the run of the job's `COMPLETE` event.

That run read `crm.learners, learning.courses, learning.reviews`, and its lineage says the rows were filtered by `crm.learners.ai_training_consent, learning.reviews.learner_id`, the [`INDIRECT` inputs](#add-indirect-inputs) that decide which rows exist, and that `body` is a `TRANSFORMATION` of the review's text.

Parsed from the pipeline's SQL as written, the same job's rows are filtered by nothing, and `body` is an `IDENTITY` copy. That would say personal text was copied unchanged, with no consent column involved. The query as run is what happened, so it's what the lineage records.

Provenance makes the corpus checkable after the fact. Joining every record back through `learning.reviews` to its author finds 96 of 96 records whose author consented, a check the platform can run on any old build against today's answers.

Provenance also lets retrieval respect each reader's permissions. OWASP asks applications built on language models to "Implement fine-grained access controls and permission-aware vector and embedding stores" ([OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)). The platform answers one person from an index built from this corpus, which keeps each record's `review_id` with its vectors. Before a retrieved record reaches the model, the retrieval layer asks the enforcement layer, as the person being answered, which of those reviews they may read, the way [chapter 6](#query-on-someones-behalf) runs an assistant's queries, and drops the rest. An instructor then gets only records from their own courses. A record that stands for reviews of several courses carries the first review's ID, so the check fails closed: for each of the 23 such records, it may hide a text the person could have read, and never shows one they couldn't.

**Working rule:** Give every record its source table, its row's ID, and the job and run that wrote it, and record the job's lineage from the query as it ran, filters and masks included. Check old builds against today's consent through that provenance. Filter every retrieval by the reader's own decision on each record's source row before a model sees it.

## Generate the dataset card from the run {#generate-the-dataset-card}

A dataset card tells whoever trains or audits a model what's in its data, where it came from and what was done to it. Croissant is MLCommons' metadata format for machine-learning datasets ([Akhtar et al., 2024](https://arxiv.org/abs/2403.19546)). Its 1.1 specification makes a card checkable: "Croissant datasets must declare that they conform to the versioned schema, e.g. http://mlcommons.org/croissant/1.1", and every dataset must give a description, licence, name, URL, creator and publication date. For provenance, the specification recommends the W3C PROV Ontology (PROV-O) ([Croissant 1.1](https://docs.mlcommons.org/croissant/docs/croissant-spec-1.1.html)). Its responsible-AI vocabulary adds properties such as `rai:dataCollection` and `rai:personalSensitiveInformation` ([Croissant RAI 1.0](https://docs.mlcommons.org/croissant/docs/croissant-rai-spec.html)). A card written by hand describes the data someone meant to build; a card generated by the run describes the data it built.

`lib.ai_data.card` generates the platform's card with mlcroissant 1.1.1, MLCommons' Python library for Croissant. The run supplies the counts, the corpus file's SHA-256, a field for every column, and three PROV-O properties: the tables the pipeline's own SQL reads, which the values come from, as `prov:wasDerivedFrom`; the table the enforcement layer's rewrite adds, which only decides which rows exist, as `prov:wasInfluencedBy`; and the run, as `prov:wasGeneratedBy`. mlcroissant writes them through its `extra_properties` argument but adds no `prov` prefix to the card's context, so the module adds it. The creator is the owner of `ai.review_corpus` in `governance/metadata.toml`. The licence, the name, URL, description and use cases come from `governance/ai_data.toml`, and `lib.ai_data.card_problems` is the platform's own check of the result. Generate the card, first with mlcroissant's default `conformsTo`:

Example `corpus-dataset-card` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Generates the corpus's Croissant card twice, first with mlcroissant's default conformsTo and then as the platform writes it, and runs the platform's own check on it. The prose's point rests on the "conformsTo" lines and the "problems" line."""
from lib import ai_data
from lib.catalog import open_catalog

built = ai_data.build(open_catalog(["crm.learners", "learning.courses", "learning.reviews"]))

# mlcroissant's default, then the card the pipeline writes, with Croissant 1.1 written out.
# an empty list leaves conformsTo to mlcroissant, which writes its own default
default, _ = ai_data.card(built, conforms_to=[])
print("conformsTo, mlcroissant's default:", default["conformsTo"])
# the card as the platform writes it: Croissant 1.1 and the RAI vocabulary, written out
card, warnings = ai_data.card(built)
ai_data.write_card(card, built.folder)
print("conformsTo, written out:", ", ".join(card["conformsTo"]))
print("datePublished, the run's:", card["datePublished"])
# the build's date as the major number: a nightly build may remove records
print("version, the run's:", card["version"])
print("the sources the card names:", ", ".join(source["@id"] for source in card["prov:wasDerivedFrom"]))
print("the tables that decided which rows, as the card names them:",
      ", ".join(table["@id"] for table in card["prov:wasInfluencedBy"]))
print("the activity the card names:", card["prov:wasGeneratedBy"]["prov:label"])
# the card names every column of the corpus as a field
print("fields in the record set:", ", ".join(f["name"] for f in card["recordSet"][0]["field"]))
for line in card["rai:dataPreprocessingProtocol"] + card["rai:personalSensitiveInformation"]:
    print("-", line)

# What mlcroissant reports, and what the platform's own check of the card reports.
# the message after mlcroissant's severity tag
print("mlcroissant's warnings:", len(warnings))
for warning in warnings:
    print("- mlcroissant:", warning.split("] ", 1)[1])
# the platform's own check: the library's validator doesn't report every requirement
problems = ai_data.card_problems(card, built.folder)
print("problems the book's check finds:", len(problems))
for problem in problems:
    print("-", problem)
```

Output:

```text
conformsTo, mlcroissant's default: http://mlcommons.org/croissant/1.0
conformsTo, written out: http://mlcommons.org/croissant/1.1, http://mlcommons.org/croissant/RAI/1.0
datePublished, the run's: 2026-10-01T02:00:00Z
version, the run's: 20261001.0.0
the sources the card names: iceberg://platform/learning.courses, iceberg://platform/learning.reviews
the tables that decided which rows, as the card names them: iceberg://platform/crm.learners
the activity the card names: platform/review_corpus
fields in the record set: review_id, course_id, course_title, rating, body, source_table, job, run_id
- Read 436 of 3,000 reviews, filtered on crm.learners.ai_training_consent, learning.reviews.learner_id.
- Replaced personal data with keyed pseudonyms (PERSON 120).
- Removed 340 exact duplicates and 0 near-duplicates (MinHash LSH, Jaccard similarity of 0.8 or more, confirmed exactly; 8 pairs that differ only in a name kept apart).
- Kept 96 records, each with its source table, review ID, job and run.
- Values replaced by keyed pseudonyms: PERSON 120.
- Emails and phone numbers replaced by [email] and [phone] by the enforcement layer's redact_contacts mask.
- Names found with a list of 106 words from crm.instructors, built by the governance team's job governance/instructor_names; the list isn't part of the corpus.
- Measured against labelled spans: 0 of 139 labelled values left in the text.
mlcroissant's warnings: 1
- mlcroissant: Property "http://mlcommons.org/croissant/citeAs" is recommended, but does not exist.
problems the book's check finds: 1
- creator: missing
```

Left to its default, mlcroissant writes `http://mlcommons.org/croissant/1.0`, although its own `LATEST_VERSION` is 1.1 ([mlcroissant source](https://github.com/mlcommons/croissant/blob/v1.1.1/python/mlcroissant/mlcroissant/_src/core/context.py)), so a card would declare a version it wasn't written for. The platform writes `http://mlcommons.org/croissant/1.1, http://mlcommons.org/croissant/RAI/1.0`.

The card's `datePublished`, `2026-10-01T02:00:00Z`, is the build's time, because the platform publishes a card only with the build it describes. Its `version`, `20261001.0.0`, takes the build's date as its major number. Croissant recommends MAJOR.MINOR.PATCH, where a new major version means "the existing data has been changed (edited, removed or shuffled records across splits)", and any nightly build may remove records.

The card names the sources `iceberg://platform/learning.courses, iceberg://platform/learning.reviews`, the influence `iceberg://platform/crm.learners` and the activity `platform/review_corpus`, and lists preprocessing steps with the run's counts.

The warnings mlcroissant reports, 1 in all, are about recommended properties, here `citeAs`, not about the problem the platform's check finds: `creator` is missing. `ai.review_corpus` has no owner in the metadata file, the gap [chapter 2](#test-the-catalog-against-the-metadata) found, so the card stays unpublished until the table has an owner. [Chapter 10](#run-every-rule-as-one-job) reports the same gap on every run, as a finding already on main.

mlcroissant can also read a card back, with `mlc.Dataset`, but at 1.1.1, with rdflib 7.6.0 and pandas 3.1.1, reading emits a `DeprecationWarning` from rdflib and a `Pandas4Warning`, and returns text fields as bytes. So the book's examples only write cards, and check them with the platform's own code.

**Working rule:** Generate the card in the run that builds the data, with every count, hash, source and version taken from that run, and write the format's version out. Check the card with your own code for every property the specification requires, since the library's validator doesn't report them all, and don't publish or train on a corpus whose card fails.

## Quote what the EU AI Act says about training data {#what-the-ai-act-says}

The EU's Artificial Intelligence Act, Regulation (EU) 2024/1689, addresses training data in several places. This section quotes two of them, Article 10 and Article 53(1)(d), and we interpret neither.

For high-risk AI systems, Article 10(2) says that training, validation and testing data sets "shall be subject to data governance and management practices", and lists what those practices concern. They include data collection processes and the origin of data, with the original purpose of collecting personal data, and data preparation such as annotation, labelling, cleaning, updating, enrichment and aggregation ([AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)).

Article 10(3) asks for data sets that are "relevant, sufficiently representative, and to the best extent possible, free of errors and complete in view of the intended purpose" ([AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)).

Regulation (EU) 2026/1744, the Digital Omnibus on AI, published Jul 24, 2026, leaves these passages as quoted. It replaces paragraphs 1 and 6 of Article 10, deletes paragraph 5, and inserts an Article 4a, "Processing of special categories of personal data for bias detection and correction". It also sets when Chapter III, Sections 1 to 3, which include Article 10, apply: from 2 December 2027 to high-risk AI systems classified under Article 6(2) and Annex III, and from 2 August 2028 to those classified under Article 6(1) and Annex I ([Regulation (EU) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj)).

For providers of general-purpose AI models, Article 53(1)(d) requires them to "draw up and make publicly available a sufficiently detailed summary about the content used for training of the general-purpose AI model, according to a template provided by the AI Office." The European Commission published that template as C(2025) 8311 ([Commission template](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models), [PDF](https://ec.europa.eu/newsroom/dae/redirection/document/118480)).

Its [explanatory notice](https://digital-strategy.ec.europa.eu/en/library/explanatory-notice-and-template-public-summary-training-content-general-purpose-ai-models) says that a downstream entity that modifies a model already placed on the Union market can become the provider of the resulting model, under the Commission guidelines on general-purpose AI models that the notice names. In that case the modifying entity reports only the training content used for the modification.
The Act's Annex III is titled "High-risk AI systems referred to in Article 6(2)", and its point 3, "Education and vocational training", includes "(b) AI systems intended to be used to evaluate learning outcomes, including when those outcomes are used to steer the learning process of natural persons in educational and vocational training institutions at all levels" ([AI Act](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)). We quote it because the platform is an education platform, and stop there. Whether any system of the platform's is high-risk under Article 6 is another question, and none of this chapter's code depends on the answer.

**Working rule:** Quote the Act as amended, from the Official Journal, with a link and the date you read it, because the Omnibus moved both text and dates. Keep the law out of your pipeline's logic: generate the card's facts from the run, and let the people who answer legal questions decide which passages apply.

## What goes wrong in production {#ai-data-in-production}

A corpus gives no warning. The model trains, the card is published, and the problems surface later, in what the model says or in a request nobody can answer.

### A learner withdraws after the build {#withdrawn-after-the-build}

Like marketing's list in [chapter 7](#consent-at-query-time), a corpus records who had consented on the day it was built. Take the corpus that `lib.ai_data.build` writes in the nightly run of Oct 1, the Oct 1 build, and withdraw the consent of the author of one of its records. Then rebuild the corpus in the same folder the next night, without generating its card again, and check each build against today's consent, as a training run does before it starts:

Example `consent-withdrawn-after-build` (Python 3.12.15 · datasketch 2.0.0 · duckdb 2.0.0 · mlcroissant 1.1.1 · openlineage-python 1.55.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · presidio-anonymizer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · regopy 1.5.2 · sqlglot 30.31.0 · tldextract 5.4.0), passing in Edition 2026.11.27:

```python
"""Withdraws one author's consent after a build, rebuilds the corpus in the same folder, and checks both builds against today's consent and the card against the file. The prose's point rests on the "records whose author consents today" and "problems" lines."""
from datetime import timedelta

import pyarrow.compute as pc
import pyarrow.parquet as pq

from lib import ai_data, lineage
from lib.catalog import open_catalog
from lib.platform import load

catalog = open_catalog(["crm.learners", "learning.courses", "learning.reviews"])
first = ai_data.build(catalog)                        # the nightly run of Oct 1, and its card
card, _ = ai_data.card(first)
ai_data.write_card(card, first.folder)

# The next day, the author of one of the corpus's records withdraws their consent to AI training.
# review ID to the learner who wrote it, from the reviews table
authors = dict(zip(*load("learning.reviews").select(["review_id", "learner_id"]).to_pydict().values()))
# the author of the Oct 1 build's second record
learner = authors[first.records.column("review_id")[1].as_py()]
learners = catalog.load_table("crm.learners")
rows = learners.scan().to_arrow()
# that learner's answer becomes False; every other row keeps its answer
consent = pc.if_else(pc.equal(rows["learner_id"], learner), False, rows["ai_training_consent"])
learners.overwrite(rows.set_column(rows.schema.get_field_index("ai_training_consent"), "ai_training_consent", consent))

# The next nightly run rebuilds the corpus in the same folder, and nobody generates the card again. A training run
# checks its build against today's consent before it starts.
# the same folder: the corpus file is replaced, so the first card no longer matches it
second = ai_data.build(catalog, first.folder, lineage.NIGHTLY + timedelta(days=1))
for name, built in [("Oct 1 build", first), ("Oct 2 build", second)]:
    ids = built.records.column("review_id").to_pylist()
    # records in each build whose author is the learner who withdrew
    print(f"{name}, records from the learner who withdrew:", sum(authors[i] == learner for i in ids))
    print(f"{name}, records whose author consents today:", f"{ai_data.consenting(catalog, ids)} of {len(ids)}")
different_runs = first.run_id != second.run_id
assert different_runs
print("the two builds are different runs:", different_runs)
# the legal team's placeholder answer, from governance/ai_data.toml
print("a model made from the Oct 1 build, the legal team's answer:", ai_data.LEGAL["withdrawal"]["models_made_before"])

# the card's last preprocessing step, which states the Oct 1 counts
print("the Oct 1 card says:", card["rai:dataPreprocessingProtocol"][-1])
print("records in the corpus file now:", pq.read_metadata(first.folder / ai_data.CORPUS_FILE).num_rows)
# the platform's check of the Oct 1 card against the corpus file as it is now
problems = ai_data.card_problems(card, first.folder)
print("problems with the Oct 1 card, checked against the corpus now:", len(problems))
for problem in problems:
    print("-", problem)
```

Output:

```text
Oct 1 build, records from the learner who withdrew: 1
Oct 1 build, records whose author consents today: 95 of 96
Oct 2 build, records from the learner who withdrew: 0
Oct 2 build, records whose author consents today: 95 of 95
the two builds are different runs: True
a model made from the Oct 1 build, the legal team's answer: undecided
the Oct 1 card says: Kept 96 records, each with its source table, review ID, job and run.
records in the corpus file now: 95
problems with the Oct 1 card, checked against the corpus now: 2
- creator: missing
- review_corpus.parquet: its SHA-256 isn't the one the card states
```

The Oct 1 build holds 1 record by that learner, and the Oct 2 build holds 0, so the next corpus leaves the learner out. The two builds are different runs, with their own run IDs. The next training run has to leave the learner out too, and so does the next index.

Checked through provenance against today's answers, the Oct 1 build has 95 of 96 records whose author consents, so a training run that makes the check refuses it. The Oct 2 build passes with 95 of 95.

What was made from the Oct 1 build before the withdrawal keeps the review: a copy of its file, an index built from it, a model fine-tuned on it. The European Data Protection Board considers that "AI models trained with personal data cannot, in all cases, be considered anonymous" ([EDPB Opinion 28/2024](https://www.edpb.europa.eu/our-work-tools/our-documents/opinion-board-art-64/opinion-282024-certain-data-protection-aspects_en)).

Article 7(3) of the GDPR gives the right to withdraw consent at any time. It says that withdrawing doesn't affect the lawfulness of processing based on consent before the withdrawal, that the person must be told of this right before giving consent, and that withdrawing must be no harder than giving it ([GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). [Chapter 7](#consent-at-query-time) quotes the first sentences of the same article and says what a withdrawal changes in the platform's code.

The code's part is to find, through provenance, every build that holds the record, and, by run ID, every model and index made from those builds. It then reads what happens to them from `[legal.withdrawal]` in `governance/ai_data.toml`. The legal team's answer for a model made from the Oct 1 build is `undecided`, a placeholder under which the job lists such models for the legal team and changes nothing. If the answer is that a model must not keep the review, the one way to remove it that we can vouch for is to train the model again on a build without it.

The card failed too, without a sound. Its last preprocessing step still reads "Kept 96 records, each with its source table, review ID, job and run." The file holds 95 records, and the platform's check finds 2 problems: the missing creator, and a file whose SHA-256 isn't the one the card states. A card that isn't generated again with its data describes another dataset.

**Working rule:** Record which build, by run ID, every model and index was made from. Before every training run, check the build's records against today's consent and the file's hash against its card, and refuse a build that fails either. When a learner withdraws, find the builds that hold their records and the models made from them, and let your legal team's answer in config decide what happens to those.

### Other failures {#other-ai-data-failures}

- **A filter on refusals that keeps the unknowns.** Built with it, the corpus held 2,045 reviews instead of 436, mostly by learners never asked. Notice it by counting the corpus's records per consent answer, through their provenance: any answer but yes is a defect.
- **Personal data a model memorizes from its text.** Carlini and colleagues extracted training text from a language model, including public personal information such as names, phone numbers and email addresses, even though each such sequence appeared in a single document ([Carlini et al., 2021](https://arxiv.org/abs/2012.07805)). The plain pipeline's corpus holds 120 labelled emails, 113 of them distinct and 106 written only once, and duplicates repeat whatever a detector misses in every copy. Measure what's left against labelled samples of your own text, and deduplicate before training.
- **A pseudonym key that leaks.** With the corpus's key and a list of instructors' names, anyone can compute every pseudonym in the corpus. When the key may have leaked, rotate it, rebuild every corpus made with it, and find by run ID the copies and models made from builds under the old key, as for a withdrawal.

## What this chapter decided {#ai-data-decisions}

- **The corpus is built through the enforcement layer,** as `analyst-1` for `ai-training`: only reviews whose author's `ai_training_consent` is true, contacts masked, an unknown consent counted as no.
- **Every legal answer the code needs is a placeholder for the legal team** in `[legal]` in `governance/ai_data.toml`: the consent that admits a record, the card's licence, and what happens to models made before a withdrawal.
- **Personal data is detected after the enforcement layer's masks,** with the pattern recognizers and the platform team's list of instructors' names, and replaced by keyed pseudonyms. Privacy Filter is measured, not added. The corpus is pseudonymized, never anonymized.
- **Pseudonyms are HMAC-SHA256 under the corpus job's own key,** not the enforcement layer's SHA-256 over key and value, and never Presidio's randomly salted `hash`.
- **Duplicates are removed in two steps,** exact copies by SHA-256, then near-duplicates from MinHash LSH tuned for 0.6 and confirmed at a Jaccard similarity of 0.8, never merging texts that differ only in a name. datasketch and its scheme, `affine32`, are pinned.
- **Every record keeps its provenance,** `source_table`, `review_id`, `job` and `run_id`, and a training run checks its build against today's consent first.
- **The dataset card is Croissant 1.1 with RAI 1.0,** generated by the run, checked by the platform's own code, and unpublished until `ai.review_corpus` has an owner.
- **Answers for one person come from an index of the corpus,** filtered by that person's decision on each record's source review.
- **The EU AI Act is quoted as amended and linked, never interpreted.** A corpus is only as clean as what was admitted into it. Each record is decided when the corpus is built, each record keeps its source, so a decision can be traced back to the review it came from, and the card says what was done with the rest.
