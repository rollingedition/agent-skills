---
title: "Data Governance as Code"
chapter: "Finding personal data"
chapter_id: finding-personal-data
book: data-governance-as-code
edition: 2026.11.23
verified: 2026-11-12
edition_code: 4TXR-45EN
canonical: https://rollingedition.com/data-governance-as-code/finding-personal-data
license: CC BY 4.0
attribution: "“Finding personal data,” chapter 3 of Data Governance as Code, Edition 2026.11.23, examples passed Nov 12, 2026. By Rolling Edition, https://rollingedition.com/data-governance-as-code/finding-personal-data. Text CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Code MIT, copyright Rolling Edition and contributors. Written with AI. Verified by people."
---
# Finding personal data

By the end of this chapter you can find personal data on a data platform automatically. You'll propose a classification for every column from its name, its type and a reproducible sample of its values, find personal data inside free text span by span, and measure each detector against labelled data, so you know what it misses before anyone relies on it. You'll run Presidio's pattern recognizers offline with thresholds chosen by measurement, compare them with the recorded detections of a model trained to find personal data, and classify again only the columns a schema change adds.

The platform, the online learning platform this book follows, sells professional courses to adult learners, and keeps its warehouse in an Iceberg catalog of eight source tables, each under the namespace of the team that runs it. [Chapter 2](#a-catalog-you-can-test) gave every column a classification in `governance/metadata.toml`, a file people review. A reviewed file records what its reviewers believe a column holds, and on the platform three beliefs need checking. `billing.payments.card_number` is a legacy column whose description says it holds full card numbers, and nobody has checked. `crm.learners.notes` is free text that support agents type, so its name says nothing about what's in it. And learners write whatever they like in support tickets and course reviews, so a classification of the whole column can't protect that text: the platform has to find each name, email and phone number inside it before the text can be masked span by span, which [chapter 9](#replace-personal-data) does to reviews before the platform's course assistant learns from them.

This chapter builds the book's shared module for this, `lib.pii`: rules on column names, seeded samples of a column's values, a Presidio detector configured to run offline, and code that scores any detector against labelled data. Every detector in this chapter is measured against one file, which we call the truth: `data/platform/pii_spans.parquet`. The script that generated the platform's data writes it beside the tickets and reviews: every piece of personal data it placed in their text, with its exact start and end. Invoice numbers, order numbers and the date a problem happened stay unlabelled, because the platform doesn't treat them as personal data.

The platform's phone numbers, card numbers and IBANs are random in a valid format, so any one may be in service, and no example prints one whole: it masks all but the last four digits.

## Classify columns from the schema {#classify-columns-from-the-schema}

The cheapest evidence about a column is its schema: its name and its type. A rule on names reads no data, so it can run over a whole catalog in a pull request, and it catches the columns whose names say what they hold, such as `email` or `date_of_birth`. Catalog tools start the same way: OpenMetadata's auto-classification begins with a "Column Name Scanner", which validates "the column names of the table against a set of regex rules" ([OpenMetadata docs](https://docs.open-metadata.org/v2.0.x/how-to-guides/data-governance/classification/auto-classification/auto-pii-tagging)). The type decides what comes next. A text column's values can be sampled and scanned. A timestamp can't hold an email, and scanning one with a date pattern would flag every row, so numbers, dates, timestamps and booleans are classified by name alone.

The platform keeps its rules in `governance/pii.toml`, the file that holds every setting of its detector and is reviewed like the metadata. The rules are 8 regular expressions on lowercased column names, each naming the entity it suggests, and the first match wins. The same file maps each entity to a classification: a phone number to `personal`, a card number or an IBAN to `sensitive`. `lib.pii.by_name` applies the rules. Run them over every column of the catalog, and compare them with the reviewed metadata:

Example `column-name-rules` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from pyiceberg.types import StringType

from lib import metadata, pii
from lib.catalog import open_catalog

catalog = open_catalog()
described = metadata.load()
columns = [(table, f) for (namespace,) in sorted(catalog.list_namespaces())
           for _, name in sorted(catalog.list_tables(namespace))
           for table in [f"{namespace}.{name}"] for f in catalog.load_table(table).schema().fields]
print("columns in the catalog:", len(columns))
print("name rules:", len(pii.NAME_RULES))

named = [(table, f, pii.by_name(f.name)) for table, f in columns if pii.by_name(f.name)]
print("columns a name rule marks:", len(named))
for table, f, entity in named:
    print(f"  {table}.{f.name}: {entity}, so {pii.CLASSIFICATION[entity]}")
agree = sum(pii.CLASSIFICATION[entity] == described[table].columns[f.field_id].classification
            for table, f, entity in named)
print("of them, agreeing with the metadata:", agree)

text = [(table, f) for table, f in columns if isinstance(f.field_type, StringType)]
print("columns of text, whose values can be sampled:", len(text))

# Columns the metadata, reviewed by people, calls personal or sensitive, that no name rule marks.
missed = [f"{table}.{f.name}" for table, f in columns if not pii.by_name(f.name)
          and described[table].columns[f.field_id].classification in ("personal", "sensitive")]
print("personal columns no name rule marks:", ", ".join(missed))
```

Output:

```text
columns in the catalog: 64
name rules: 8
columns a name rule marks: 11
  billing.payments.card_number: CREDIT_CARD, so sensitive
  crm.instructors.full_name: PERSON, so personal
  crm.instructors.email: EMAIL_ADDRESS, so personal
  crm.instructors.payout_iban: IBAN_CODE, so sensitive
  crm.learners.full_name: PERSON, so personal
  crm.learners.email: EMAIL_ADDRESS, so personal
  crm.learners.phone: PHONE_NUMBER, so personal
  crm.learners.city: LOCATION, so personal
  crm.learners.street_address: LOCATION, so personal
  crm.learners.date_of_birth: DATE_TIME, so personal
  learning.events.ip_address: IP_ADDRESS, so personal
of them, agreeing with the metadata: 11
columns of text, whose values can be sampled: 29
personal columns no name rule marks: crm.learners.notes, learning.reviews.body, support.tickets.body
```

Of the catalog's 64 columns, the rules mark 11, and all 11 agree with the classification people gave them. The rules miss three columns the reviewers classified `personal`: `crm.learners.notes`, `learning.reviews.body` and `support.tickets.body`. All three are free text, where a name describes the container, not its contents. And the one marked column the platform worries about most, `billing.payments.card_number`, gets `sensitive` from its name without anyone learning what it holds: whole card numbers, the last four digits, or a payment provider's token would all match `card_?(number|num|no)`.

Name rules are brittle in a known way. The authors of Sherlock, a model for detecting column types, observed that "these matching-based approaches often are not robust to dirty data and only detect a limited number of types" ([Hulsebos et al., 2019](https://arxiv.org/abs/1905.10688)). So the platform reads values too, in the 29 text columns its catalog holds.

**Working rule:** Run name rules over every column first, because they're free, and let them raise a classification, never lower one. Keep the rules short, in code, and reviewed like any other rule. Treat any free-text column, whatever it's called, as one that needs its values sampled, and classify columns of other types by name alone.

## Run Presidio offline {#run-presidio-offline}

To read values, the platform uses Presidio, an open-source library for finding and masking personal data. Its analyzer runs a set of **recognizers**: regular expressions with checksums, phone-number parsing, and a named-entity model reached through an NLP engine. The engine has two jobs, as Presidio's docs put it: "NER based PII identification, and feature extraction for downstream rule based logic (such as leveraging context words for improved detection)", and its default model is spaCy's `en_core_web_lg` ([Presidio docs](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/analyzer/customizing_nlp_models.md)). At 2.2.366, `AnalyzerEngine()` with no arguments downloads that model when it isn't installed ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/nlp_engine/spacy_nlp_engine.py)), so a pipeline without network access fails on its first line, and one with access installs a model of about 400 MB as a side effect ([en_core_web_lg 3.8.0](https://github.com/explosion/spacy-models/releases/tag/en_core_web_lg-3.8.0)).

`lib.pii.detector` configures the engine explicitly instead, with `NoOpNlpEngine`, which "loads no external model" ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/nlp_engine/no_op_nlp_engine.py)). The cost is context words. Presidio raises a pattern's score when a word such as "phone" appears near the match, by comparing "each recognizer's context terms with the lemma of each token in the sentence" ([Presidio docs](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/tutorial/06_context.md)), and with no model there are no lemmas, so the engine "cannot use context words from the analyzed text". One more call reaches the network: the email recognizer checks domains with tldextract ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/predefined_recognizers/generic/email_recognizer.py)), which "fetches the latest Public Suffix List on first use" ([tldextract 5.4.0 README](https://github.com/john-kurkowski/tldextract/blob/5.4.0/README.md)). An empty `TLDEXTRACT_PUBLIC_SUFFIX_LIST_URLS` turns that off if it's set "before importing `tldextract`", as the README says, and importing Presidio imports tldextract. So `lib/__init__.py`, which Python runs before any module of the book's `lib`, sets it. When an example imported Presidio first, the same file replaces tldextract's shared extractor ([source](https://github.com/john-kurkowski/tldextract/blob/5.4.0/tldextract/tldextract.py)) with one that has no URLs. `lib.pii` refuses to load if any remain, and tldextract uses the copy it ships with, so the same text gives the same answer on every machine.

Load every predefined recognizer on that engine, and run it on one of the platform's support tickets:

Example `presidio-offline-engine` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · spacy 3.8.18 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
import spacy

from lib import pii
from lib.platform import load

# AnalyzerEngine() with no arguments loads spaCy's en_core_web_lg, and downloads it when it isn't installed.
print("en_core_web_lg installed:", spacy.util.is_package("en_core_web_lg"))
print("URLs tldextract would fetch the Public Suffix List from:", len(pii.suffix_list_urls()))

detector = pii.detector()              # every predefined recognizer, on an NLP engine that loads no model
names = sorted(r.name for r in detector.registry.recognizers)
print("recognizers loaded:", len(names))
print("recognizers:", ", ".join(names))
print("default score threshold:", detector.default_score_threshold)

# The ticket holds a phone number, which may be in service: masked() prints it with only its last four digits.
ticket = pii.texts("tickets")[1421]
found = sorted(pii.detect(detector, ticket))
print("ticket 1421:", pii.masked(ticket))
for start, end, entity, score in found:
    print(f"  {entity} on {pii.masked(ticket[start:end])}: {score:.2f}")

# Where is the phone number valid? The recognizer reads it in each of its regions.
phone = next(ticket[start:end] for start, end, entity, _ in found if entity == "PHONE_NUMBER")
[learner] = [row["learner_id"] for row in load("support.tickets").to_pylist() if row["ticket_id"] == 1421]
[country] = [row["country"] for row in load("crm.learners").to_pylist() if row["learner_id"] == learner]
print("the learner's country:", country)
print("default regions where it's valid:",
      ", ".join(r for r in pii.PhoneRecognizer.DEFAULT_SUPPORTED_REGIONS if pii.valid_phone(phone, r)))
```

Output:

```text
en_core_web_lg installed: False
URLs tldextract would fetch the Public Suffix List from: 0
recognizers loaded: 17
recognizers: CreditCardRecognizer, CryptoRecognizer, DateRecognizer, EmailRecognizer, IbanRecognizer, IpRecognizer, MacAddressRecognizer, MedicalLicenseRecognizer, NhsRecognizer, PhoneRecognizer, UrlRecognizer, UsBankRecognizer, UsItinRecognizer, UsLicenseRecognizer, UsPassportRecognizer, UsSsnRecognizer, UuidRecognizer
default score threshold: 0
ticket 1421: I can't open the videos in Introduction to Design Systems, they stop after a few seconds. It happened on 12/03 around 9pm. My colleague Jennifer Abbott (jennifer.abbott@example.net) wants to enrol as well. You can reach me on •••••••0440 after 6pm.
  DATE_TIME on 12/03: 0.10
  EMAIL_ADDRESS on jennifer.abbott@example.net: 1.00
  URL on example.net: 0.50
  PHONE_NUMBER on •••••••0440: 0.40
  US_BANK_NUMBER on •••••••0440: 0.05
  US_DRIVER_LICENSE on •••••••0440: 0.01
the learner's country: US
default regions where it's valid: BR
```

Asked whether `en_core_web_lg` is installed, spaCy answers False, so a bare `AnalyzerEngine()` would try to download it, and tldextract has 0 URLs to fetch its list from. The no-model engine loads 17 recognizers instead, and none of them looks for names: the colleague in the ticket, Jennifer Abbott, goes unnoticed. Her email is found with a score of 1.00, and its domain is found again as a URL, at 0.50. The learner's phone number, an 11-digit number typed without separators, is found three times: as a phone number at 0.40, a US bank number at 0.05 and a US driver's licence at 0.01. Even the phone number is found by chance: the learner's country is US, and of Presidio's default regions, the US among them, the digits are valid only in BR, Brazil. The date of the problem, `12/03`, which says nothing about anyone, is a date at 0.10.

Those scores aren't probabilities. Each pattern carries a constant score, low for weak patterns, as Presidio's tutorial explains: "Zip regex patterns (essentially 5 digits) are very weak, so we would want the initial confidence to be low" ([Presidio docs](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/tutorial/06_context.md)). A US bank number is any run of 8 to 17 digits ([supported entities](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/supported_entities.md)), and the FAQ admits that "A driver's license number, for example, could be any 9-digit number" ([FAQ](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/faq.md)). And the analyzer's default threshold is 0, so every weak match comes back.

**Working rule:** Configure Presidio's engine explicitly: `NoOpNlpEngine` when you run patterns only, or a pinned model you install yourself when you need its names. Never call `AnalyzerEngine()` bare in a pipeline, and pin anything a recognizer would download, such as the Public Suffix List. Read each score as a constant set for its pattern, never as a probability.

## Sample a column's values the same way every run {#sample-column-values}

Scanning every value of every text column is too slow for a warehouse of any size, so tools sample: OpenMetadata's workflow "samples rows directly from the source and validates them against an Entity Recognition engine" ([OpenMetadata docs](https://docs.open-metadata.org/v2.0.x/how-to-guides/data-governance/classification/auto-classification/auto-pii-tagging)). A sample needs three decisions. **Which rows:** a random sample, not the first rows or a block from a random start. Google's Sensitive Data Protection, for one, offers `RANDOM_START`, where "Scanning starts from a randomly selected row" ([Google Cloud docs](https://cloud.google.com/sensitive-data-protection/docs/inspecting-storage)) and reads on from there, and on a table ordered by sign-up date, that's one cohort. **The same rows every run**, so a classification can be reproduced and a change in it means the data changed. And **how many**, from how rare the data you must catch is.

DuckDB's reservoir sample takes a seed, but its docs warn that "fixing the seed only guarantees a reproducible sample when DuckDB runs single-threaded (`SET threads = 1`)" ([DuckDB 2.0.0 docs](https://duckdb.org/docs/2.0/sql/samples)). `lib.pii.sample` sets one thread, filters out NULLs and then draws a seeded reservoir sample. Draw 20 notes from `crm.learners` twice, then work out how many you'd need:

Example `seeded-column-sample` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
import math

from lib import pii
from lib.catalog import open_catalog
from lib.warehouse import connect

con = connect(open_catalog(["crm.learners"]))
first = pii.sample(con, "crm.learners", "notes", rows=20)
second = pii.sample(con, "crm.learners", "notes", rows=20)
print("second draw, same notes as the first:", "yes" if second == first else "no")
# Notes can hold a phone number, which may be in service: masked() prints it with only its last four digits.
print("first sampled notes:", " | ".join(pii.masked(note) for note in first[:3]))

# How rare is personal data in the column? Run the detector over every note, once, to know.
detector = pii.platform_detector()
[(rows, notes)] = con.sql("select count(*), count(notes) from crm.learners").fetchall()
every_note = [note for (note,) in con.sql("select notes from crm.learners where notes is not null").fetchall()]
holding = sum(bool(pii.detect(detector, note)) for note in every_note)
print("learners:", f"{rows:,}")
print("learners with notes:", notes)
print("notes holding personal data the detector finds:", holding)

# The chance that n sampled values hold at least one of them is 1 - (1 - p)^n, for a share p of the values.
for unit, p in (("rows", holding / rows), ("notes", holding / notes)):
    print(f"chance 20 sampled {unit} catch one:", f"{1 - (1 - p) ** 20:.1%}")
    print(f"sampled {unit} needed for a 99% chance:", math.ceil(math.log(0.01) / math.log(1 - p)))
print("values the platform samples per text column:", pii.ROWS)
print("rarest share that sample catches 99% of the time:", f"1 in {math.floor(1 / (1 - 0.01 ** (1 / pii.ROWS)))}")
```

Output:

```text
second draw, same notes as the first: yes
first sampled notes: VIP: bought a team licence. | Asked about invoices for their employer. | Called about a refund, call back on (•••)•••-1366x•••.
learners: 5,000
learners with notes: 527
notes holding personal data the detector finds: 138
chance 20 sampled rows catch one: 42.9%
sampled rows needed for a 99% chance: 165
chance 20 sampled notes catch one: 99.8%
sampled notes needed for a 99% chance: 16
values the platform samples per text column: 200
rarest share that sample catches 99% of the time: 1 in 43
```

Asked whether a second draw returns the same 20 notes, the example answers yes, and the third note already holds a phone number, which the output masks. Of 5,000 learners, 527 have notes, and 138 of those hold personal data that the platform's detector, [tuned later in this chapter](#tune-the-recognizers), finds. If p is the share of values holding personal data, the chance that n sampled values include at least one is

chance = 1 − (1 − p)ⁿ

and the n that gives a 99% chance is ln(0.01) / ln(1 − p). This is a rule of thumb: it treats the draws as independent, which a sample without replacement from thousands of rows nearly is. Counted over all rows, NULLs included, personal data is rare, and 20 sampled rows catch it only 42.9% of the time; a 99% chance takes 165 rows. Counted over the notes that exist, 20 catch it 99.8% of the time, and 16 are enough for 99%. The NULLs were diluting the sample.

**Working rule:** Sample non-null values, with a fixed seed, on one thread, and keep the seed with the result. Size the sample from the rarest personal data you must catch, with n = ln(0.01) / ln(1 − p) for 99%. The platform samples 200 values per text column, set in `governance/pii.toml`, which catches personal data held by 1 in 43 values or more 99% of the time. For anything rarer, scan the whole column, or classify it by rule.

## Classify columns from their values {#classify-columns-from-their-values}

[The name rules](#classify-columns-from-the-schema) and [a reproducible sample](#sample-column-values) combine into one proposal per column. `lib.pii.classify` takes the strictest classification that either supports: the entity the name suggests, and every entity found in at least one sampled value. A column with no evidence gets `internal`, because a detector that found nothing has shown nothing, and only a person decides that a column is `public`. Strictest is a choice. Presidio's own tool for tables, Presidio structured, gives each column one entity, and its default is "Most Common", which "Identifies the most frequently occurring PII entity in a data column or field" ([Presidio docs](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/structured/index.md)). That suits choosing how to mask a column. For classifying it, a column that holds one card number in 200 values still holds card numbers.

Classify all 64 columns of the catalog, sampling the 29 text columns with the platform's detector, whose recognizers [a later section](#tune-the-recognizers) chooses, and compare the proposals with the reviewed metadata:

Example `classify-sampled-columns` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from lib import metadata, pii
from lib.catalog import open_catalog
from lib.warehouse import connect

catalog = open_catalog()
findings = pii.classify(catalog, connect(catalog), pii.platform_detector())
print("columns classified:", len(findings))
print("columns sampled:", sum(f.sampled > 0 for f in findings))

holding = [f for f in findings if f.found]          # columns where sampled values hold personal data
print("columns whose sampled values hold personal data:", len(holding))
print("of them, holding something their name doesn't suggest:", sum(set(f.found) != {f.named} for f in holding))
for f in holding:
    print(f"{f.table}.{f.column}, proposed: {f.classification}")
    print(f"{f.table}.{f.column}, found: " + ", ".join(f"{e} in {n} of {f.sampled}" for e, n in f.found.most_common()))
[cards] = [f for f in findings if f.column == "card_number"]
print("sampled card numbers the card recognizer accepts:", f"{cards.found['CREDIT_CARD']} of {cards.sampled}")

named_only = [f for f in findings if pii.CLASSIFICATION.get(f.named, pii.FLOOR) != f.classification]
print("columns the values classify more strictly than the name:", ", ".join(f"{f.table}.{f.column}" for f in named_only))

# Compare with the metadata people reviewed. A column the detector found nothing in proposes only the floor, internal.
described = metadata.load()
evidenced = [f for f in findings if f.named or f.found]
print("columns with evidence:", len(evidenced))
print("of them, equal to the metadata:",
      sum(f.classification == described[f.table].columns[f.field_id].classification for f in evidenced))
for f in evidenced:
    reviewed = described[f.table].columns[f.field_id].classification
    if metadata.stricter(f.classification, reviewed) != reviewed:
        print(f"stricter than the metadata, {f.table}.{f.column}: {f.classification}, reviewed as {reviewed}")
```

Output:

```text
columns classified: 64
columns sampled: 29
columns whose sampled values hold personal data: 9
of them, holding something their name doesn't suggest: 5
billing.payments.card_number, proposed: sensitive
billing.payments.card_number, found: CREDIT_CARD in 151 of 200, PHONE_NUMBER in 3 of 200
crm.instructors.email, proposed: personal
crm.instructors.email, found: EMAIL_ADDRESS in 50 of 50
crm.instructors.payout_iban, proposed: sensitive
crm.instructors.payout_iban, found: IBAN_CODE in 50 of 50
crm.learners.email, proposed: personal
crm.learners.email, found: EMAIL_ADDRESS in 200 of 200
crm.learners.phone, proposed: personal
crm.learners.phone, found: PHONE_NUMBER in 175 of 200
crm.learners.notes, proposed: personal
crm.learners.notes, found: PHONE_NUMBER in 29 of 200, EMAIL_ADDRESS in 18 of 200
learning.events.ip_address, proposed: personal
learning.events.ip_address, found: IP_ADDRESS in 200 of 200, PHONE_NUMBER in 39 of 200
learning.reviews.body, proposed: personal
learning.reviews.body, found: EMAIL_ADDRESS in 4 of 200
support.tickets.body, proposed: sensitive
support.tickets.body, found: EMAIL_ADDRESS in 47 of 200, PHONE_NUMBER in 37 of 200, DATE_TIME in 29 of 200, IBAN_CODE in 21 of 200, CREDIT_CARD in 12 of 200
sampled card numbers the card recognizer accepts: 151 of 200
columns the values classify more strictly than the name: crm.learners.notes, learning.reviews.body, support.tickets.body
columns with evidence: 14
of them, equal to the metadata: 13
stricter than the metadata, support.tickets.body: sensitive, reviewed as personal
```

Of the 9 columns whose sampled values hold personal data, some hold only what their name says, such as `crm.learners.email`. These 5 hold something their name doesn't suggest, or have a name that suggests nothing:

| Column | Proposed | Found in the sample |
| --- | --- | --- |
| `billing.payments.card_number` | sensitive | CREDIT_CARD in 151 of 200, PHONE_NUMBER in 3 of 200 |
| `crm.learners.notes` | personal | PHONE_NUMBER in 29 of 200, EMAIL_ADDRESS in 18 of 200 |
| `support.tickets.body` | sensitive | EMAIL_ADDRESS in 47 of 200, PHONE_NUMBER in 37 of 200, DATE_TIME in 29 of 200, IBAN_CODE in 21 of 200, CREDIT_CARD in 12 of 200 |
| `learning.reviews.body` | personal | EMAIL_ADDRESS in 4 of 200 |
| `learning.events.ip_address` | personal | IP_ADDRESS in 200 of 200, PHONE_NUMBER in 39 of 200 |

The values settle what the name couldn't. Of the sampled card numbers, 151 of 200 match Presidio's card pattern and pass the Luhn checksum it checks ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/predefined_recognizers/generic/credit_card_recognizer.py)), and the rest are formats the pattern doesn't cover ([see where patterns fail](#where-patterns-fail)). The legacy column holds the full card numbers its description says it "Should not be stored at all", and the sample turns that belief into evidence that `team-billing`, the table's owner, can act on. The notes are `personal` on their values alone. The ticket text is `sensitive`, because learners paste card numbers and IBANs into tickets, which makes it the one proposal stricter than the metadata, where people reviewed it as `personal`. Of the 14 columns with any evidence, 13 match the reviewed classification.

Read the evidence, not only the verdict. Some of the IP addresses are also read as phone numbers. Here it changes nothing, because an IP address is `personal` anyway, but it shows that a detector's label says what a value looks like, not what it is.

**Working rule:** Propose the strictest classification that the name or any sampled value supports, with `internal` as the floor, and show the evidence with the proposal. A proposal stricter than the reviewed metadata is a finding for the table's owner, who raises the classification or records why not; never let a detector lower one. OpenMetadata skips a column "already tagged as `PII`"; we recommend sampling every text column on every run instead, because the reviewed tag is the thing being checked.

## Measure a detector against labelled spans {#measure-against-labelled-spans}

A column-level answer is enough to classify `support.tickets.body`, but not to mask it: masking replaces each span of personal data in each text, and a span the detector misses stays readable. To know what a detector misses, compare its spans with [the truth](#finding-personal-data), the labelled spans of every ticket and review. Two matching rules are standard, and `lib.pii` applies both. **Exact** matching, from the CoNLL-2003 shared task, counts an entity "correct only if it is an exact match of the corresponding entity in the data file" ([Tjong Kim Sang and De Meulder, 2003](https://aclanthology.org/W03-0419.pdf)): the detector found the span with the same boundaries and a label of its type. **Overlap** matching asks only for one shared character, still with a label of its type, which the SemEval-2013 task on drug interactions calls "Type matching" ([Segura-Bedmar et al., 2013](https://aclanthology.org/S13-2056.pdf)). Neither credits a span hidden under another label, so `lib.pii` adds a third measure, **coverage**: whether every character of the span is inside some detection, whatever its label. Each answers a different question. Exact asks whether the detector labelled the whole span right, overlap whether it noticed the span as what it is, and coverage whether masking its detections hides the span.

`lib.pii.score` computes exact and overlap matching as **recall**, the share of labelled spans of each type that a detector finds with a label of that type, and **precision**, the share of each label's detections that match a labelled span. `lib.pii.coverage` gives the share of each type's spans that are covered. `score` also counts the texts in which every labelled character falls inside some detection, the texts masking would leave with nothing personal. The Text Anonymization Benchmark counts a person as protected only "if all of its mentions are masked" ([Pilán et al., 2022](https://aclanthology.org/2022.cl-4.19.pdf)); the platform counts whole texts, which is stricter. And recall comes first: Presidio's evaluation guide says "recall is often more important than precision, as we'd like to avoid missing any PII" ([Presidio docs](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/evaluation/index.md)).

Run Presidio with its defaults over all 5,000 tickets and reviews, and score its 3,902 detections against the 4,292 labelled spans:

Example `measure-pattern-recognizers` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
import re

from lib import pii

labelled = pii.truth()
print("texts:", f"{sum(len(pii.texts(source)) for source in pii.SOURCES):,}")
print("labelled spans:", f"{len(labelled):,}")

detector = pii.detector()                 # Presidio's defaults: every recognizer, threshold 0
found = pii.find(detector)
scores, covered = pii.score(found, labelled), pii.coverage(found, labelled)
print("detections:", f"{len(found):,}")

for entity, (n, exact, overlap) in scores.recall.items():
    print(f"{entity}, labelled: {n:,}")
    print(f"{entity}, recall, exact: {exact / n:.2f}")
    print(f"{entity}, recall, overlap: {overlap / n:.2f}")
    print(f"{entity}, covered, any label: {covered[entity][1] / n:.2f}")

for label, (n, exact, overlap) in scores.precision.items():
    print(f"{label}, detections: {n:,}")
    print(f"{label}, precision, exact: {exact / n:.2f}")

print("precision of all detections, exact:", f"{pii.precision_overall(scores):.2f}")
print("texts holding personal data:", f"{scores.texts:,}")
print("texts with every labelled span masked:", f"{scores.masked:,}")

# The truth's limits. The generator builds every text from a few sentence templates, and writes every date of birth
# one way. Presidio's date patterns don't read every way of writing one.
print("sentence templates the texts are built from:", len(pii.templates()))
births = [pii.text_of(s) for s in labelled if s.entity == "DATE_TIME"]
print("dates of birth written like 1985-03-12:", sum(re.fullmatch(r"\d{4}-\d\d-\d\d", d) is not None for d in births))
for written in ("1985-03-12", "12 March 1985"):
    text = f"My date of birth on the account is wrong, it should be {written}."
    print(f"dates found in a date of birth written {written}:", sum(e == "DATE_TIME" for _, _, e, _ in pii.detect(detector, text)))
```

Output:

```text
texts: 5,000
labelled spans: 4,292
detections: 3,902
CREDIT_CARD, labelled: 213
CREDIT_CARD, recall, exact: 0.71
CREDIT_CARD, recall, overlap: 0.71
CREDIT_CARD, covered, any label: 0.89
DATE_TIME, labelled: 196
DATE_TIME, recall, exact: 1.00
DATE_TIME, recall, overlap: 1.00
DATE_TIME, covered, any label: 1.00
EMAIL_ADDRESS, labelled: 543
EMAIL_ADDRESS, recall, exact: 1.00
EMAIL_ADDRESS, recall, overlap: 1.00
EMAIL_ADDRESS, covered, any label: 1.00
IBAN_CODE, labelled: 236
IBAN_CODE, recall, exact: 1.00
IBAN_CODE, recall, overlap: 1.00
IBAN_CODE, covered, any label: 1.00
LOCATION, labelled: 210
LOCATION, recall, exact: 0.00
LOCATION, recall, overlap: 0.00
LOCATION, covered, any label: 0.00
PERSON, labelled: 2,455
PERSON, recall, exact: 0.00
PERSON, recall, overlap: 0.00
PERSON, covered, any label: 0.00
PHONE_NUMBER, labelled: 439
PHONE_NUMBER, recall, exact: 0.78
PHONE_NUMBER, recall, overlap: 0.79
PHONE_NUMBER, covered, any label: 0.91
CREDIT_CARD, detections: 151
CREDIT_CARD, precision, exact: 1.00
DATE_TIME, detections: 421
DATE_TIME, precision, exact: 0.47
EMAIL_ADDRESS, detections: 543
EMAIL_ADDRESS, precision, exact: 1.00
IBAN_CODE, detections: 236
IBAN_CODE, precision, exact: 1.00
MEDICAL_LICENSE, detections: 18
MEDICAL_LICENSE, precision, exact: 0.00
PHONE_NUMBER, detections: 384
PHONE_NUMBER, precision, exact: 0.89
UK_NHS, detections: 8
UK_NHS, precision, exact: 0.00
URL, detections: 751
URL, precision, exact: 0.00
US_BANK_NUMBER, detections: 689
US_BANK_NUMBER, precision, exact: 0.00
US_DRIVER_LICENSE, detections: 683
US_DRIVER_LICENSE, precision, exact: 0.00
US_ITIN, detections: 2
US_ITIN, precision, exact: 0.00
US_PASSPORT, detections: 8
US_PASSPORT, precision, exact: 0.00
US_SSN, detections: 8
US_SSN, precision, exact: 0.00
precision of all detections, exact: 0.38
texts holding personal data: 2,586
texts with every labelled span masked: 425
sentence templates the texts are built from: 30
dates of birth written like 1985-03-12: 196
dates found in a date of birth written 1985-03-12: 1
dates found in a date of birth written 12 March 1985: 0
```

| Entity type | Labelled | Recall, exact | Recall, overlap | Covered |
| --- | --- | --- | --- | --- |
| `PERSON` | 2,455 | 0.00 | 0.00 | 0.00 |
| `EMAIL_ADDRESS` | 543 | 1.00 | 1.00 | 1.00 |
| `PHONE_NUMBER` | 439 | 0.78 | 0.79 | 0.91 |
| `IBAN_CODE` | 236 | 1.00 | 1.00 | 1.00 |
| `CREDIT_CARD` | 213 | 0.71 | 0.71 | 0.89 |
| `LOCATION` | 210 | 0.00 | 0.00 | 0.00 |
| `DATE_TIME` | 196 | 1.00 | 1.00 | 1.00 |

The patterns find every email, IBAN and date of birth, most phone numbers and card numbers, and no names or street addresses at all, which is most of what the tickets hold. Precision is poor: 0.38 of all detections match a labelled span. The 689 US bank numbers, 683 driver's licences and 751 URLs are all wrong, with a precision of 0.00: phone, card and invoice numbers, all runs of digits, are read as bank numbers and licences, and pieces of emails and a few addresses as URLs. A wrong label still hides the digits, so phone and card numbers are covered more often than they're found. Of the 2,586 texts that hold personal data, 425 would come out of masking with nothing personal left.

The truth has its own limits, because the text is generated. Every ticket and review is put together from 30 sentence templates in `prep/generate.py`, so each [hard case](#where-patterns-fail) is one sentence frame, and all 196 dates of birth are written like `1985-03-12`. A recall of 1.00 for dates means that one format: in the generator's sentence, Presidio finds 1 date when the date of birth is written `1985-03-12`, and 0 when it's written `12 March 1985`. A measure on this text tells you how a detector behaves on these shapes, not how it will do on yours.

**Working rule:** Measure every detector against labelled spans before it masks anything: recall per entity type by exact and by overlap matching, both with a label of the right type, coverage whatever the label, precision per label, and the share of texts with nothing personal left. Weigh recall first. Before you trust a detector on your text, label a few hundred real records by hand and measure on those too.

## Tune the recognizers against the truth {#tune-the-recognizers}

[Presidio's defaults](#measure-against-labelled-spans) return every weak match, and the FAQ names the remedies: "1. Change the acceptance threshold", and "2. Remove unnecessary PII recognizers, if the dataset does not contain these entities", noting that "there is a trade-off between false positives (falsely detected text) and false negatives" ([FAQ](https://github.com/data-privacy-stack/presidio/blob/2.2.364/docs/faq.md)). Presidio 2.2.364 added "per-recognizer and per-entity score threshold configuration", with the analyzer's default threshold "as the fallback" ([changelog](https://github.com/data-privacy-stack/presidio/blob/2.2.364/CHANGELOG.md), [release notes](https://github.com/data-privacy-stack/presidio/releases/tag/2.2.364)). The phone recognizer has one more setting that matters on a platform whose learners live in many countries: the regions whose numbering plans it reads ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/predefined_recognizers/generic/phone_recognizer.py)).

`governance/pii.toml` keeps 6 recognizers, for the identifiers the platform's text can hold, each with its own threshold. The phone regions aren't a setting: `lib.pii.countries` reads the countries the learners live in from `crm.learners`, so the regions follow the data. Run four settings against the same truth:

Example `tune-pattern-recognizers` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from lib import pii

labelled = pii.truth()
print("recognizers kept:", len(pii.THRESHOLDS))
print("recognizers kept, with their thresholds:", ", ".join(f"{name} {t}" for name, t in pii.THRESHOLDS.items()))
print("phone regions, Presidio's default:", ", ".join(pii.PhoneRecognizer.DEFAULT_SUPPORTED_REGIONS))
print("phone regions, the learners' countries:", ", ".join(pii.countries()))

settings = {
    "Presidio's defaults": pii.detector(),
    "one threshold of 0.5": pii.detector(default_threshold=0.5),
    "kept recognizers, own thresholds": pii.detector(pii.THRESHOLDS),
    "kept recognizers, learners' phone regions": pii.platform_detector(),
}
for name, detector in settings.items():
    found = pii.find(detector)
    scores, covered = pii.score(found, labelled), pii.coverage(found, labelled)
    n, exact, _ = scores.recall["PHONE_NUMBER"]
    print(f"{name}, detections: {len(found):,}")
    print(f"{name}, precision, exact: {pii.precision_overall(scores):.2f}")
    print(f"{name}, phone recall, exact: {exact / n:.2f}")
    for entity, short in (("PHONE_NUMBER", "phones"), ("CREDIT_CARD", "cards")):
        print(f"{name}, {short} covered, any label: {covered[entity][1] / covered[entity][0]:.2f}")
    print(f"{name}, texts with every labelled span masked: {scores.masked:,}")
```

Output:

```text
recognizers kept: 6
recognizers kept, with their thresholds: EmailRecognizer 0.5, PhoneRecognizer 0.4, CreditCardRecognizer 0.5, IbanRecognizer 0.5, DateRecognizer 0.5, IpRecognizer 0.5
phone regions, Presidio's default: US, GB, DE, FR, IL, IN, CA, BR
phone regions, the learners' countries: AU, BR, CA, DE, ES, FR, GB, IN, JP, MX, PL, US
Presidio's defaults, detections: 3,902
Presidio's defaults, precision, exact: 0.38
Presidio's defaults, phone recall, exact: 0.78
Presidio's defaults, phones covered, any label: 0.91
Presidio's defaults, cards covered, any label: 0.89
Presidio's defaults, texts with every labelled span masked: 425
one threshold of 0.5, detections: 1,903
one threshold of 0.5, precision, exact: 0.59
one threshold of 0.5, phone recall, exact: 0.00
one threshold of 0.5, phones covered, any label: 0.01
one threshold of 0.5, cards covered, any label: 0.71
one threshold of 0.5, texts with every labelled span masked: 284
kept recognizers, own thresholds, detections: 1,510
kept recognizers, own thresholds, precision, exact: 0.97
kept recognizers, own thresholds, phone recall, exact: 0.78
kept recognizers, own thresholds, phones covered, any label: 0.78
kept recognizers, own thresholds, cards covered, any label: 0.72
kept recognizers, own thresholds, texts with every labelled span masked: 394
kept recognizers, learners' phone regions, detections: 1,539
kept recognizers, learners' phone regions, precision, exact: 0.97
kept recognizers, learners' phone regions, phone recall, exact: 0.84
kept recognizers, learners' phone regions, phones covered, any label: 0.84
kept recognizers, learners' phone regions, cards covered, any label: 0.72
kept recognizers, learners' phone regions, texts with every labelled span masked: 405
```

| Measure | Defaults | One threshold, 0.5 | Kept recognizers | And learners' regions |
| --- | --- | --- | --- | --- |
| Detections | 3,902 | 1,903 | 1,510 | 1,539 |
| Precision, exact | 0.38 | 0.59 | 0.97 | 0.97 |
| Phone recall, exact | 0.78 | 0.00 | 0.78 | 0.84 |
| Phones covered | 0.91 | 0.01 | 0.78 | 0.84 |
| Cards covered | 0.89 | 0.71 | 0.72 | 0.72 |
| Texts fully masked | 425 | 284 | 394 | 405 |

The obvious fix fails. One threshold of 0.5 removes the weak matches and every phone number with them, because a phone number scores 0.40 when no context word can raise it. Keeping 6 recognizers, with the phone recognizer's threshold at its own score, raises precision to 0.97 and keeps phone recall where it was. Presidio's default regions are US, GB, DE, FR, IL, IN, CA, BR; the learners live in AU, BR, CA, DE, ES, FR, GB, IN, JP, MX, PL, US, and reading their numbering plans raises phone recall to 0.84.

One number goes the wrong way: fewer texts come out fully masked than with the defaults. The recognizers the platform dropped had been masking some phone and card numbers under the wrong label, and a wrong label still hides the digits: without them, coverage falls from 0.91 to 0.78 for phone numbers and from 0.89 to 0.72 for card numbers. We think precision of 0.97 is worth that price, because detections are the evidence a reviewer reads, and with the defaults the tickets and reviews hold 689 bank numbers and 683 driver's licences, none of them real. `governance/pii.toml` maps neither entity to a classification, so they change no proposal, but each is a finding someone has to read and dismiss. Dropping the US recognizers is also a claim about the platform's text: the truth holds no US bank or licence numbers. If the platform ever asks for one, that claim, and the measurement, must change.

**Working rule:** Never run with Presidio's default threshold of 0, or with one threshold for every recognizer. Keep only the recognizers for identifiers your text can hold, set each one's threshold from its own scores, and read phone numbers in the regions your users live in, derived from your data. Put all of it in code, and measure again whenever it changes.

## See where patterns fail {#where-patterns-fail}

[The tuned recognizers](#tune-the-recognizers) score well on totals, and totals hide where they fail. A pattern detector fails in three ways: there's no pattern for the thing at all, its pattern or its validation rejects the value, or it matches something that only looks personal. The platform's tickets plant cases of each kind, as its data card says: names typed in lowercase, initials, first names that are ordinary words, phone numbers typed without separators, and invoice numbers, order numbers and dates of a problem, which [the truth](#finding-personal-data) leaves unlabelled. Count each with the platform's detector. A case counts as caught when some detection overlaps it, whatever its label:

Example `pattern-hard-cases` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from collections import Counter

from lib import pii
from lib.platform import load

labelled = pii.truth()
found = pii.find(pii.platform_detector())

cases = pii.hard_cases(labelled)               # a case is caught when some detection overlaps it, whatever its label
for case, spans in cases.items():
    print(f"{case}, labelled: {len(spans)}")
    print(f"{case}, caught: {pii.caught(spans, found)}")
print("hard cases of a name, caught:", pii.caught([s for spans in cases.values() for s in spans if s.entity == "PERSON"], found))

for kind, spans in pii.lookalikes().items():
    print(f"{kind}, in the tickets: {len(spans)}")
    print(f"{kind}, flagged as personal data: {pii.caught(spans, found)}")

# Card numbers the card pattern misses: too short or long for its 13 to 17 digits, or a first digit it doesn't accept.
missed = pii.missed([s for s in labelled if s.entity == "CREDIT_CARD"], found, {"CREDIT_CARD"})
why = lambda digits: f"{len(digits)} digits" if not 13 <= len(digits) <= 17 else f"{len(digits)} digits starting with {digits[0]}"
print("CREDIT_CARD, missed:", len(missed))
for reason, n in Counter(why(pii.text_of(s)) for s in missed).most_common():
    print(f"CREDIT_CARD, missed, {reason}: {n}")
print("IBAN_CODE, missed:", len(pii.missed([s for s in labelled if s.entity == "IBAN_CODE"], found, {"IBAN_CODE"})))

# Are the phone numbers the patterns miss valid where the ticket's learner lives? Phones appear only in tickets.
learner_of = {row["ticket_id"]: row["learner_id"] for row in load("support.tickets").to_pylist()}
country_of = {row["learner_id"]: row["country"] for row in load("crm.learners").to_pylist()}
phones = pii.missed([s for s in labelled if s.entity == "PHONE_NUMBER"], found, {"PHONE_NUMBER"})
print("phone numbers missed:", len(phones))
print("of them, invalid in the learner's country:",
      sum(not pii.valid_phone(pii.text_of(s), country_of[learner_of[s.row_id]]) for s in phones))
```

Output:

```text
names in lowercase, labelled: 211
names in lowercase, caught: 0
initial and surname, labelled: 163
initial and surname, caught: 0
first names that are words, labelled: 187
first names that are words, caught: 0
instructors named in reviews, labelled: 798
instructors named in reviews, caught: 0
phones typed as digits only, labelled: 257
phones typed as digits only, caught: 220
hard cases of a name, caught: 0
invoice numbers, in the tickets: 224
invoice numbers, flagged as personal data: 31
order numbers, in the tickets: 212
order numbers, flagged as personal data: 0
dates of a problem, in the tickets: 225
dates of a problem, flagged as personal data: 0
CREDIT_CARD, missed: 62
CREDIT_CARD, missed, 19 digits: 23
CREDIT_CARD, missed, 12 digits: 22
CREDIT_CARD, missed, 16 digits starting with 2: 10
CREDIT_CARD, missed, 15 digits starting with 2: 7
IBAN_CODE, missed: 0
phone numbers missed: 65
of them, invalid in the learner's country: 63
```

There is no pattern for a name, so every hard case of a name is missed. The tickets hold 211 names typed in lowercase, 163 initials with a surname and 187 first names such as Grace or Will, and the reviews name an instructor 798 times; the patterns catch 0 of them. Phones typed as digits only do well, 220 of 257, and the price is the look-alikes: 31 of the 224 invoice numbers are read as phone numbers. The 212 order numbers are flagged 0 times, and the 225 dates of a problem, such as `12/03`, 0 times. With [Presidio's defaults](#run-presidio-offline), `12/03` was a date at 0.10, and the date recognizer returned 421 dates where the truth labels 196; its threshold in `governance/pii.toml` keeps such weak matches out.

The card pattern's shape causes the card misses. It accepts 13 to 17 digits starting with 1, 3, 4, 50 to 55 or 6, but no 13-digit number starting with 1 ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/predefined_recognizers/generic/credit_card_recognizer.py)), and every card number in the data passes the Luhn checksum, so validation rejects none. Of the 62 card numbers it misses, 23 have 19 digits and 22 have 12, and the rest start with 2: 10 of 16 digits and 7 of 15. Validation causes the other misses. The IBAN recognizer checks each country's format and length and the IBAN's check digits ([source](https://github.com/data-privacy-stack/presidio/blob/2.2.364/presidio-analyzer/presidio_analyzer/predefined_recognizers/generic/iban_recognizer.py)). Every labelled IBAN passes, so it misses 0, but a learner who mistypes one digit of an IBAN writes a value it rejects. The phone recognizer accepts only numbers that python-phonenumbers calls valid ([source](https://github.com/daviddrysdale/python-phonenumbers/blob/v9.0.41/python/phonenumbers/phonenumbermatcher.py)), and the generator doesn't always write those: of the 65 phone numbers the platform's detector misses, 63 aren't valid in the country the ticket's learner lives in, so most of the phone misses are the generator's, not the detector's.

**Working rule:** Read a detector's misses by case, not by total, and keep a list of the cases your text holds. Use patterns for what has a checkable shape, such as emails, IBANs, card numbers, phone numbers and dates, and never for names or addresses. Keep the checksums and numbering plans, because they're what makes the patterns precise. Check the card pattern against the card numbers your payment provider issues, and the date patterns against the ways your users write dates.

## Compare a PII model {#compare-a-named-entity-model}

[The patterns](#where-patterns-fail) have nothing for names or addresses, and those are most of the personal data in the platform's text: 2,455 names and 210 addresses among the 4,292 labelled spans. Finding them takes a model that reads context, and a general named-entity model is the wrong one. The authors of the SPY dataset "define PII entities as those that can be used to identify, contact, or locate a specific individual", and found that "dedicated NER models exhibit limitations when applied to PII-specific contexts" ([Savkin et al., 2025](https://aclanthology.org/2025.naacl-srw.23.pdf)). We use a PII model, one trained for personally identifiable information: OpenAI's Privacy Filter, an Apache-2.0 model with eight fixed labels, such as `private_person`, `private_address` and `account_number` ([model card](https://huggingface.co/openai/privacy-filter/blob/7ffa9a043d54d1be65afb281eddf0ffbe629385b/README.md)). The labels are the model's: it "does not support configuring label policies dynamically at runtime" ([OpenAI, 2026](https://cdn.openai.com/pdf/c66281ed-b638-456a-8ce1-97e9f5264a90/OpenAI-Privacy-Filter-Model-Card.pdf), section 4.2). We chose it over the runner-up among open PII models, GLiNER2-PII, for those fixed labels: GLiNER2-PII "conditions on the labels you provide at inference time" and takes a threshold ([model card](https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi/blob/1cb4166094dc58fa8d836429f060d6c95f62b495/README.md)), so its recording would have to pin both. Privacy Filter has 1.5 billion parameters, 50 million of them active, and runs on a CPU.

The book's examples never run a model, so they read a recording of its output. The recording, `data/recorded/pii-entities/`, which this chapter and [chapter 9](#replace-personal-data) use, holds every span the model found in every ticket and review, with its offsets, its text and the model's label. `recordings/pii_entities.py` made it on a CPU with the model's reference decoder, `opf` ([code](https://github.com/openai/privacy-filter/tree/f7f00ca7fb869683eb732c010299d901457f19c3)), which chooses the best sequence of labels for a whole text, so most spans come back in one piece rather than token by token. It used the default operating point, all six of the decoder's transition biases at 0 ([calibration file](https://huggingface.co/openai/privacy-filter/blob/7ffa9a043d54d1be65afb281eddf0ffbe629385b/original/viterbi_calibration.json)), which can be set "for improved recall" instead (section 2.3.2). The manifest pins the model's revision and the SHA-256 of its weights, so anyone can record it again and compare, and `lib.pii.recorded` refuses spans that don't match the text at their offsets. The recording keeps the model's labels. The example maps them to the truth's entity types, `account_number` to both card numbers and IBANs, so a different mapping never needs a new recording. Score the model, the platform's patterns, and both together, masking whatever either finds:

Example `privacy-filter-spans` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from lib import pii

# Privacy Filter's eight labels, mapped to the truth's entity types. A label the truth has no type for matches nothing.
MATCHES = {"private_person": {"PERSON"}, "private_email": {"EMAIL_ADDRESS"}, "private_phone": {"PHONE_NUMBER"},
           "private_address": {"LOCATION"}, "account_number": {"CREDIT_CARD", "IBAN_CODE"},
           "private_date": {"DATE_TIME"}, "private_url": set(), "secret": set()}

model, manifest = pii.recorded("pii-entities")
print("model:", manifest["model"], "decoded with", manifest["settings"]["decode_mode"])
labelled = pii.truth()
detectors = {"patterns": pii.find(pii.platform_detector()), "model": model}
detectors["both"] = detectors["patterns"] + model          # mask whatever either one finds

for name, found in detectors.items():
    scores = pii.score(found, labelled, MATCHES)           # Presidio's labels aren't in MATCHES, so match themselves
    print(f"{name}, detections: {len(found):,}")
    for entity, (n, exact, overlap) in scores.recall.items():
        print(f"{name}, {entity}, recall, exact: {exact / n:.2f}")
        print(f"{name}, {entity}, recall, overlap: {overlap / n:.2f}")
    print(f"{name}, precision, exact: {pii.precision_overall(scores):.2f}")
    print(f"{name}, texts with every labelled span masked: {scores.masked:,} of {scores.texts:,}")

for label, (n, exact, overlap) in pii.score(model, labelled, MATCHES).precision.items():
    print(f"model, {label}, detections: {n:,}")
    print(f"model, {label}, precision, exact: {exact / n:.2f}")
    print(f"model, {label}, precision, overlap: {overlap / n:.2f}")
```

Output:

```text
model: openai/privacy-filter decoded with viterbi
patterns, detections: 1,539
patterns, CREDIT_CARD, recall, exact: 0.71
patterns, CREDIT_CARD, recall, overlap: 0.71
patterns, DATE_TIME, recall, exact: 1.00
patterns, DATE_TIME, recall, overlap: 1.00
patterns, EMAIL_ADDRESS, recall, exact: 1.00
patterns, EMAIL_ADDRESS, recall, overlap: 1.00
patterns, IBAN_CODE, recall, exact: 1.00
patterns, IBAN_CODE, recall, overlap: 1.00
patterns, LOCATION, recall, exact: 0.00
patterns, LOCATION, recall, overlap: 0.00
patterns, PERSON, recall, exact: 0.00
patterns, PERSON, recall, overlap: 0.00
patterns, PHONE_NUMBER, recall, exact: 0.84
patterns, PHONE_NUMBER, recall, overlap: 0.85
patterns, precision, exact: 0.97
patterns, texts with every labelled span masked: 405 of 2,586
model, detections: 4,424
model, CREDIT_CARD, recall, exact: 0.69
model, CREDIT_CARD, recall, overlap: 0.69
model, DATE_TIME, recall, exact: 0.97
model, DATE_TIME, recall, overlap: 0.97
model, EMAIL_ADDRESS, recall, exact: 1.00
model, EMAIL_ADDRESS, recall, overlap: 1.00
model, IBAN_CODE, recall, exact: 0.99
model, IBAN_CODE, recall, overlap: 1.00
model, LOCATION, recall, exact: 0.67
model, LOCATION, recall, overlap: 0.79
model, PERSON, recall, exact: 0.84
model, PERSON, recall, overlap: 0.84
model, PHONE_NUMBER, recall, exact: 0.94
model, PHONE_NUMBER, recall, overlap: 0.94
model, precision, exact: 0.84
model, texts with every labelled span masked: 2,095 of 2,586
both, detections: 5,963
both, CREDIT_CARD, recall, exact: 0.92
both, CREDIT_CARD, recall, overlap: 0.92
both, DATE_TIME, recall, exact: 1.00
both, DATE_TIME, recall, overlap: 1.00
both, EMAIL_ADDRESS, recall, exact: 1.00
both, EMAIL_ADDRESS, recall, overlap: 1.00
both, IBAN_CODE, recall, exact: 1.00
both, IBAN_CODE, recall, overlap: 1.00
both, LOCATION, recall, exact: 0.67
both, LOCATION, recall, overlap: 0.79
both, PERSON, recall, exact: 0.84
both, PERSON, recall, overlap: 0.84
both, PHONE_NUMBER, recall, exact: 0.99
both, PHONE_NUMBER, recall, overlap: 0.99
both, precision, exact: 0.88
both, texts with every labelled span masked: 2,120 of 2,586
model, account_number, detections: 746
model, account_number, precision, exact: 0.51
model, account_number, precision, overlap: 0.51
model, private_address, detections: 177
model, private_address, precision, exact: 0.79
model, private_address, precision, overlap: 1.00
model, private_date, detections: 384
model, private_date, precision, exact: 0.50
model, private_date, precision, overlap: 0.50
model, private_email, detections: 543
model, private_email, precision, exact: 1.00
model, private_email, precision, overlap: 1.00
model, private_person, detections: 2,110
model, private_person, precision, exact: 0.98
model, private_person, precision, overlap: 0.98
model, private_phone, detections: 464
model, private_phone, precision, exact: 0.89
model, private_phone, precision, overlap: 0.89
```

| Measure | Patterns | Model | Both |
| --- | --- | --- | --- |
| Recall, exact, `PERSON` | 0.00 | 0.84 | 0.84 |
| Recall, exact, `LOCATION` | 0.00 | 0.67 | 0.67 |
| Recall, exact, `PHONE_NUMBER` | 0.84 | 0.94 | 0.99 |
| Recall, exact, `CREDIT_CARD` | 0.71 | 0.69 | 0.92 |
| Recall, exact, `IBAN_CODE` | 1.00 | 0.99 | 1.00 |
| Precision, exact | 0.97 | 0.84 | 0.88 |
| Texts fully masked | 405 of 2,586 | 2,095 of 2,586 | 2,120 of 2,586 |

The model finds most of the names and addresses the patterns can't. Card numbers are where the two detectors complement each other: the model and the patterns find about the same share, 0.69 and 0.71, but not the same cards, so together they find 0.92; [a later section](#what-a-wrong-label-costs) shows why the model's share is low. The model pays in precision, 0.84 overall, and only 0.51 for `account_number` and 0.50 for `private_date`. That partly measures a difference in label policy: the truth leaves invoice numbers and dates of a problem unlabelled, and the card warns that "definitions of appropriate label policies and decision boundaries can differ" (section 4.2). Together, the two detectors leave 2,120 of 2,586 texts with nothing personal in them, against 405 of 2,586 for the patterns alone.

### Read the model's misses {#read-the-models-misses}

OpenAI's card for Privacy Filter lists where it fails: "under-detection of uncommon personal names, regional naming conventions, initials, honorific-heavy references, or domain-specific identifiers; over-redaction of public entities, locations, or common nouns when local context is ambiguous" ([OpenAI, 2026](https://cdn.openai.com/pdf/c66281ed-b638-456a-8ce1-97e9f5264a90/OpenAI-Privacy-Filter-Model-Card.pdf), section 4.3). Check that list against [the hard cases](#where-patterns-fail) the tickets plant:

Example `privacy-filter-hard-cases` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from collections import Counter

from lib import pii

model, _ = pii.recorded("pii-entities")
labelled = pii.truth()
cases = pii.hard_cases(labelled)

for case, spans in cases.items():
    print(f"{case}, labelled: {len(spans)}")
    print(f"{case}, caught by the model: {pii.caught(spans, model)}")
for kind, spans in pii.lookalikes().items():
    print(f"{kind}, flagged by the model: {pii.caught(spans, model)}")

# The names the model misses, by case: read them before trusting a recall figure.
missed = pii.missed([s for s in labelled if s.entity == "PERSON"], model, {"private_person"})
print("names the model misses:", len(missed))
for case in ("first names that are words", "instructors named in reviews"):
    often = Counter(pii.text_of(s) for s in pii.missed(cases[case], model, {"private_person"})).most_common(3)
    print(f"{case}, missed most often:", ", ".join(name for name, _ in often))

# A first name on its own says less than a full name: how many of the misses are one word?
print("missed names that are one word:", sum(len(pii.text_of(s).split()) == 1 for s in missed))
print("missed names of two words or more:", sum(len(pii.text_of(s).split()) > 1 for s in missed))
print("of them, typed in lowercase:", sum(len(pii.text_of(s).split()) > 1 and pii.text_of(s).islower() for s in missed))

# A lowercase name that neither the model nor the platform's patterns cover any part of, in the first ticket with one.
first = min(pii.missed(cases["names in lowercase"], model + pii.find(pii.platform_detector())), key=lambda s: s.row_id)
print("first ticket with a lowercase name both detectors miss:", first.row_id)
print("the name, as typed:", pii.text_of(first))
```

Output:

```text
names in lowercase, labelled: 211
names in lowercase, caught by the model: 167
initial and surname, labelled: 163
initial and surname, caught by the model: 162
first names that are words, labelled: 187
first names that are words, caught by the model: 128
instructors named in reviews, labelled: 798
instructors named in reviews, caught by the model: 535
phones typed as digits only, labelled: 257
phones typed as digits only, caught by the model: 256
invoice numbers, flagged by the model: 224
order numbers, flagged by the model: 125
dates of a problem, flagged by the model: 188
names the model misses: 387
first names that are words, missed most often: Summer, Will, Hope
instructors named in reviews, missed most often: Marie, Lori, Augustin
missed names that are one word: 337
missed names of two words or more: 50
of them, typed in lowercase: 43
first ticket with a lowercase name both detectors miss: 19
the name, as typed: juan fonseca
```

On the platform's text, initials aren't the problem: the model catches 162 of 163. Lowercase names are mostly caught, 167 of 211. The misses are first names that are also words, 128 of 187 caught, and an instructor's first name alone in a review, 535 of 798 caught. Most often it misses the words Summer, Will, Hope and the instructors' names Marie, Lori, Augustin. The model also flags far more look-alikes than the tuned patterns: 224 invoice numbers, 125 order numbers and 188 dates of a problem, against 31, 0 and 0.

Reading the misses also says how much they matter. Of the 387 names the model misses, 337 are a single word, a first name on its own, and 50 are longer, 43 of those typed in lowercase. The authors of the Text Anonymization Benchmark draw the same line: "failing to detect a direct identifier such as a full person name is much more harmful from a privacy perspective than failing to detect a quasi-identifier" ([Pilán et al., 2022](https://aclanthology.org/2022.cl-4.19.pdf)). A first name alone still needs masking, since a review carries its learner's ID and an instructor's first name in a review of their own course points at one person. The card's own advice is to measure: "Before production use, it's best to evaluate the model in-domain against local policy references" (section 4.5). It also lists education among the settings where "Additional caution is warranted" (section 4.4), and calls the model "a redaction and data minimization aid, not an anonymization, compliance, or a safety guarantee" (section 4.1).

**Working rule:** Mask free text with a PII model and the tuned patterns together, whatever either finds: the model for names and addresses, the patterns' checksums for card numbers and IBANs. Record the model's output with its revision, weights and operating point pinned, keep its own labels, and map them in code. Measure it on your own text, by hard case, before use and after every model change; if it misses too much, try an operating point that leans toward recall and record again. Treat masked text as reduced, never as anonymous.

## Count what a wrong label costs {#what-a-wrong-label-costs}

[The comparison with the patterns](#compare-a-named-entity-model) scored the model by exact and overlap matching, which both need a label of the span's type. Masking doesn't read the label: a card number the model labels `private_phone` is still hidden. Classification does, because `governance/pii.toml` maps each entity type to a classification, a phone number to `personal` and a card number to `sensitive`. Measure the model's coverage beside its recall, and the labels it gives the platform's card numbers, phone numbers and addresses:

Example `privacy-filter-labels` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from lib import pii

# What the model's labels cost. A span is covered when every character of it is inside some detection, whatever its
# label: that's what masking needs. Exact and overlap matching also need a label of the span's type.
model, _ = pii.recorded("pii-entities")
labelled = pii.truth()
covered = pii.coverage(model, labelled)
for entity in ("CREDIT_CARD", "PHONE_NUMBER", "LOCATION"):
    n, fully = covered[entity]
    print(f"{entity}, covered by the model, any label: {fully / n:.2f}")

spans = {entity: [s for s in labelled if s.entity == entity] for entity in ("CREDIT_CARD", "PHONE_NUMBER", "LOCATION")}
print("card numbers labelled private_phone:", pii.caught(spans["CREDIT_CARD"], model, {"private_phone"}))
print("phone numbers labelled account_number:", pii.caught(spans["PHONE_NUMBER"], model, {"account_number"}))

# For each address, the labels of the detections that overlap it, and the characters no detection covers.
on = pii.labels_on(spans["LOCATION"], model)
print("addresses with no detection at all:", sum(not labels for labels in on))
print("addresses read, at least in part, as a person:", sum("private_person" in labels for labels in on))
print("of them, with no address label:", sum({"private_person"} <= labels and "private_address" not in labels for labels in on))
left = [pii.uncovered(address, model) for address in spans["LOCATION"]]
print("addresses not fully covered:", sum(bool(chars) for chars in left))
print("of them, with only spaces and punctuation left:", sum(bool(chars) and not any(c.isalnum() for c in chars) for chars in left))
```

Output:

```text
CREDIT_CARD, covered by the model, any label: 0.87
PHONE_NUMBER, covered by the model, any label: 1.00
LOCATION, covered by the model, any label: 0.67
card numbers labelled private_phone: 40
phone numbers labelled account_number: 27
addresses with no detection at all: 24
addresses read, at least in part, as a person: 28
of them, with no address label: 20
addresses not fully covered: 70
of them, with only spaces and punctuation left: 21
```

The model covers 0.87 of card numbers, but labels 40 of the 213 as phone numbers, so its recall for cards is only 0.69. If the platform classified columns from the model's labels, a column of those card numbers would be proposed `personal`, not `sensitive`. That's what the patterns add: their Luhn check keeps card numbers labelled as cards. The mistake also runs the other way, toward the stricter side: the model labels 27 phone numbers `account_number`, which maps to card numbers and IBANs, so its phone coverage is 1.00 and its recall 0.94.

Addresses show what each measure counts. They score 0.67 by exact matching, 0.79 by overlap, and 0.67 by coverage. The model finds nothing at all in 24 addresses. It reads part of 28 as a person, since Faker builds many street names from surnames, as the platform's data card notes, and gives 20 of those no address label at all, so overlap matching misses them too. Other addresses come back in pieces with the right label, such as a street and a town split at a comma, which overlap matching credits and coverage doesn't: of the 70 addresses not fully covered, 21 have every letter and digit masked and only a comma or a space left. Coverage is the measure masking needs, and it's strict.

**Working rule:** Report coverage, whatever the label, beside recall with the right label: masking needs the first, classification the second. Read which labels a detector gives each type of span, and keep a recognizer with a checksum for every identifier whose label decides a classification, such as card numbers.

## Classify again when the schema changes {#reclassify-on-schema-change}

A classification describes a column at one moment, and [chapter 2](#catch-schema-changes) showed how schemas move under it. The question is when to run the classifier again. Not on every schema ID: in PyIceberg, editing a column's description gives the schema a new ID with no new column. What needs classifying is a [field ID](#key-column-metadata-by-field-id), the number Iceberg gives each column, that the metadata has never seen, because Iceberg gives every added column a new one, and a renamed column keeps its ID and so its reviewed classification. Values can also change while the schema stays the same, so the samples of text columns need a rerun on a schedule as well. Vendors promise this as a service: Databricks says its classification's "scanning is incremental and optimized to ensure all new data is classified without manual configuration" ([Databricks docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-classification)), a claim we don't test.

On the platform, the support team wants a number to call learners back on for tickets opened by phone, and adds a column called `callback_number` to `support.tickets`. Edit a description first, then add the column, fill it from the learners' phone numbers, and classify only the field IDs that `governance/metadata.toml` lacks:

Example `reclassify-new-columns` (Python 3.12.15 · duckdb 2.0.0 · phonenumbers 9.0.43 · presidio-analyzer 2.2.366 · pyarrow 26.0.1 · pyiceberg 0.12.0 · pyyaml 6.0.3 · tldextract 5.4.0), passing in Edition 2026.11.23:

```python
from pyiceberg.types import StringType

from lib import metadata, pii
from lib.catalog import fill_column, open_catalog
from lib.platform import load
from lib.warehouse import connect

catalog = open_catalog(["support.tickets"])
tickets = catalog.load_table("support.tickets")
reviewed = metadata.load()["support.tickets"].columns           # field ID -> the column as people reviewed it
unclassified = lambda: {f.field_id for f in tickets.schema().fields if f.field_id not in reviewed}
print("schema ID at the start:", tickets.schema().schema_id)

with tickets.update_schema() as update:                         # a doc edit: a new schema, no new column
    update.update_column("body", doc="What the learner wrote, as they wrote it.")
print("schema ID after a doc edit:", tickets.schema().schema_id)
print("fields to classify after the doc edit:", len(unclassified()))

# The support team starts storing the number to call back for tickets opened by phone: the learner's phone number.
with tickets.update_schema() as update:
    update.add_column("callback_number", StringType(), doc="Where to call the learner back.")
phone_of = {row["learner_id"]: row["phone"] for row in load("crm.learners").to_pylist()}
fill_column(tickets, "callback_number", lambda row: phone_of[row["learner_id"]] if row["channel"] == "phone" else None)
print("schema ID after adding a column:", tickets.schema().schema_id)
print("fields to classify after adding a column:", len(unclassified()))

for f in pii.classify(catalog, connect(catalog), pii.platform_detector(), only={"support.tickets": unclassified()}):
    found = ", ".join(f"{entity} in {n} of {f.sampled}" for entity, n in f.found.items())
    print(f"{f.table}.{f.column}, field ID: {f.field_id}")
    print(f"{f.table}.{f.column}, entity its name suggests: {f.named}")
    print(f"{f.table}.{f.column}, found in its sampled values: {found}")
    print(f"{f.table}.{f.column}, proposed classification: {f.classification}")
```

Output:

```text
schema ID at the start: 0
schema ID after a doc edit: 1
fields to classify after the doc edit: 0
schema ID after adding a column: 2
fields to classify after adding a column: 1
support.tickets.callback_number, field ID: 9
support.tickets.callback_number, entity its name suggests: None
support.tickets.callback_number, found in its sampled values: PHONE_NUMBER in 154 of 173
support.tickets.callback_number, proposed classification: personal
```

The doc edit moved the schema ID to 1 and left 0 fields to classify. Adding the column moved it to 2, with 1 field to classify, field 9. No name rule matches it, since `callback_number` contains none of the words the phone rule looks for, which is how a name rule misses a column nobody wrote it for. Its values settle it, PHONE_NUMBER in 154 of 173, and the proposal is personal. The pull request that adds the column is where its classification belongs, beside the metadata entry it needs: [chapter 10](#run-every-rule-as-one-job) fails that pull request until the column has one. A proposal from values, like this one, can come only once the column holds values, so it comes from the sample on a schedule.

**Working rule:** Classify every field ID the metadata doesn't have, in the pull request that adds it, and don't let it merge without a reviewed classification. Key the trigger on field IDs, never on schema IDs. Sample every text column again on a schedule too, because values change without a schema change.

## What goes wrong in production {#personal-data-in-production}

A detector fails quietly. Its output always looks like a list of findings, and what it misses never appears in it:

- **Phone numbers read as bank numbers.** With Presidio's defaults, every run of 8 to 17 digits is a US bank number, and every phone number typed without separators is one. The evidence for the ticket table lists hundreds of bank numbers that aren't there, a report of "bank numbers in tickets" sends someone to the wrong team, and mapping that entity to a classification would raise columns for the wrong reason. Keep only the recognizers your text needs, with thresholds of their own, as [the tuning section](#tune-the-recognizers) does, and notice the problem by counting detections per label: a label with hundreds of hits and no labelled spans is a false positive.
- **Names in free text missed.** Patterns find no names, and [the model](#read-the-models-misses) misses some lowercase names, first names that are also words, and first names standing alone. Ticket 19 still says "this is juan fonseca, i still can't log in" after both detectors have run, and passes every check that counts detections. You notice only by measuring recall against labelled text, per hard case, and by reading a sample of masked output.
- **Personal data in a column called `notes`.** No name rule marks it, and a reviewer who never read it classifies it `internal`. Sample every text column's values, and treat free-text columns as personal until a sample says otherwise.
- **A column more sensitive than its metadata.** Learners paste card numbers into tickets, so `support.tickets.body` holds `sensitive` data under a `personal` classification. Compare every proposal with the reviewed metadata, and route a stricter one to the table's owner.
- **A detector that reaches the network.** `AnalyzerEngine()` downloads a model, and tldextract fetches the Public Suffix List. Offline, the pipeline fails; online, the same text can be classified differently on two machines. A setting read at import holds only if it's made before anything imports the library. Configure the engine, pin what it would fetch, check that the setting held, and run the detector's tests with the network off.
- **Truth shaped by its generator.** The platform's text comes from 30 sentence templates filled by Faker, which writes every date of birth one way, phone numbers that aren't valid where the learner lives, and street names built from people's names. Read the misses before trusting a recall figure, and measure again on labelled samples of your own text.

## What this chapter decided {#personal-data-decisions}

- **Columns are classified from their name, their type and their values.** Name rules run on every column; text columns are sampled; the strictest evidence wins, with `internal` as the floor, and only a person sets `public`.
- **Samples are reproducible:** 200 non-null values per text column, by a seeded reservoir sample on one DuckDB thread.
- **Presidio runs offline,** on `NoOpNlpEngine`, with 6 recognizers, each with its own threshold, phone regions read from the learners' countries, and tldextract's own copy of the Public Suffix List, checked when `lib.pii` loads.
- **Detectors are measured against labelled spans,** by exact and overlap matching with a label of the right type and by coverage whatever the label, as recall per entity type, precision per label and texts left with nothing personal, with recall weighed first.
- **A proposal stricter than the metadata is a finding:** `support.tickets.body` goes to `team-support` as `sensitive`, and `billing.payments.card_number` to `team-billing`, with the evidence that it holds full card numbers.
- **Free text is masked with two detectors:** OpenAI's Privacy Filter, recorded at a pinned revision and operating point, for names and addresses, and the tuned patterns for card numbers, IBANs and phone numbers, whose checksums keep card numbers labelled as cards. Masking hides whatever either finds; neither is trusted to make text anonymous.
- **No example prints a whole phone number, card number or IBAN:** `lib.pii.masked` keeps the last four digits.
- **Reclassification follows field IDs:** every field the metadata lacks is classified in the pull request that adds it, and text columns are sampled again on a schedule.
