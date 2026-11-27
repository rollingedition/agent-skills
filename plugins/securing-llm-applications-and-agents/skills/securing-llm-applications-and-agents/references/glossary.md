---
title: "Glossary"
book: "Securing LLM Applications and Agents"
edition: "2026.11.4"
canonical: "https://rollingedition.com/securing-llm-applications-and-agents/glossary"
---

# Glossary of *Securing LLM Applications and Agents*

The 23 terms this book defines, as Edition 2026.11.4 has them, each in the book's own sentence. When a task this skill covers uses one, it means what it says here: read its section before you rely on it, and cite the section. Where a definition depends on a package, it says the version this edition pins and runs its examples on. On the web: https://rollingedition.com/securing-llm-applications-and-agents/glossary

## adaptive attacker

A real attacker is adaptive: it sees what happened and tries again.

- Defined in: [Red-team the assistant with an adaptive attacker](adaptive-attacker.md)
- Address: https://rollingedition.com/concepts/llm-security/adaptive-attacker

## argument policy

The argument policy adds a check on each call's arguments.

- Defined in: [Argument policies](least-privilege.md#argument-policies)
- Address: https://rollingedition.com/concepts/ai-agents/argument-policy

## asset

An asset is anything the office would lose, or anything an attacker would want: a record, a secret, or the ability to act for the office.

- Defined in: [Assets and trust](threat-model.md#assets-and-trust)
- Address: https://rollingedition.com/concepts/security/asset

## attack success

Attack success is the share of attack runs in which the attacker's goal check passes.

- Also: attack success rate
- Defined in: [The office and its assistant](attack-and-measure.md#the-office-and-its-assistant)
- Address: https://rollingedition.com/concepts/llm-security/attack-success

## datamarking

Datamarking replaces every whitespace character in the untrusted text with a marker character, and the system prompt names the marker.

- Defined in: [Datamarking](prompt-defences.md#datamarking)
- Address: https://rollingedition.com/concepts/llm-security/datamarking

## delimiters

Delimiters wrap each untrusted segment in markers, and the system prompt says what the markers mean.

- Defined in: [Delimiters](prompt-defences.md#delimiters-alone)
- Address: https://rollingedition.com/concepts/llm-security/delimiters

## dual LLM

The dual LLM splits the assistant in two, so that the tool-holding model never reads the untrusted text.

- Defined in: [The dual LLM](isolation-by-design.md#dual-llm)
- Address: https://rollingedition.com/concepts/llm-security/dual-llm

## encoding

Encoding replaces each untrusted segment with an encoded form, here the base64 encoding of its UTF-8 bytes.

- Defined in: [Encoding](prompt-defences.md#encoding)
- Address: https://rollingedition.com/concepts/llm-security/spotlight-encoding

## goal

The goal is what the injected text asks the assistant to do.

- Also: attack goal
- Defined in: [Goals, locations and styles](attack-set.md#goals-locations-styles)
- Address: https://rollingedition.com/concepts/llm-security/attack-goal

## hidden context

the hidden context in the system prompt, which holds the office's internal bank-reconciliation note and a portal key

- Defined in: [Assets and trust](threat-model.md#assets-and-trust)
- Address: https://rollingedition.com/concepts/llm-security/hidden-context

## input detector

An input detector, labelled input (detector) in this book, is a classifier that scores how likely a piece of text is to be an injection.

- Also: injection detector
- Defined in: [A classifier guard](injection-detectors.md#a-classifier-guard)
- Address: https://rollingedition.com/concepts/llm-security/input-detector

## lethal trifecta

It has three legs: access to private data, exposure to untrusted content, and a way to communicate externally.

- Defined in: [The trifecta and the rule of two](threat-model.md#the-trifecta-and-the-rule-of-two)
- Address: https://rollingedition.com/concepts/llm-security/lethal-trifecta

## location

The location is where the injected text sits.

- Defined in: [Goals, locations and styles](attack-set.md#goals-locations-styles)
- Address: https://rollingedition.com/concepts/llm-security/attack-location

## outbound allowlist

an outbound allowlist, a rule in the harness that, before each call runs, refuses a message to a recipient or a page fetch from a host it does not list

- Also: allowlist
- Defined in: [An outbound allowlist](attack-and-measure.md#an-outbound-allowlist)
- Address: https://rollingedition.com/concepts/llm-security/outbound-allowlist

## plan-then-execute

Plan-then-execute fixes the plan before any tool result is read.

- Defined in: [Plan-then-execute](isolation-by-design.md#plan-then-execute)
- Address: https://rollingedition.com/concepts/ai-agents/plan-then-execute

## privileged model

A privileged model holds the tools and never reads the untrusted text.

- Part of: dual LLM
- Defined in: [The dual LLM](isolation-by-design.md#dual-llm)
- Address: https://rollingedition.com/concepts/llm-security/privileged-model

## quarantined model

A quarantined model reads that text and holds no tools, so it has nothing to send or fetch with.

- Part of: dual LLM
- Defined in: [The dual LLM](isolation-by-design.md#dual-llm)
- Address: https://rollingedition.com/concepts/llm-security/quarantined-model

## Rule of Two

an agent session should combine no more than two of three properties: processing untrustworthy inputs, reaching sensitive systems or private data, and changing state or communicating externally

- Also: Agents Rule of Two
- Defined in: [The trifecta and the rule of two](threat-model.md#the-trifecta-and-the-rule-of-two)
- Address: https://rollingedition.com/concepts/ai-agents/rule-of-two

## spotlighting

Spotlighting is the name Hines et al. give to transforms of untrusted text that give the model a signal of where the text came from.

- Kinds: delimiters
- Kinds: datamarking
- Kinds: encoding
- Defined in: [Delimiters and spotlighting](prompt-defences.md#delimiters-and-spotlighting)
- Address: https://rollingedition.com/concepts/llm-security/spotlighting

## style

The style is how the text is written

- Defined in: [Goals, locations and styles](attack-set.md#goals-locations-styles)
- Address: https://rollingedition.com/concepts/llm-security/attack-style

## taint label

Taint labels follow a value's origin.

- Also: taint labels
- Defined in: [Taint labels](isolation-by-design.md#taint-labels)
- Address: https://rollingedition.com/concepts/ai-agents/taint-label

## utility

Utility is the share of benign task runs whose task check passes.

- Defined in: [The office and its assistant](attack-and-measure.md#the-office-and-its-assistant)
- Address: https://rollingedition.com/concepts/llm-security/utility

## utility under attack

Utility under attack is the share of attack runs in which the benign task carried by the case still passes its check.

- Defined in: [The office and its assistant](attack-and-measure.md#the-office-and-its-assistant)
- Address: https://rollingedition.com/concepts/llm-security/utility-under-attack
