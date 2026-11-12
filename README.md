# Rolling Edition agent skills

You learned a method from a book. Your coding agent should follow the same one. Each skill here is one of Rolling Edition's books in the Agent Skills format: the book's procedures, step by step, each step linked to the section it comes from, with the chapters as references and the examples as scripts.

Every skill is built from its book's current edition, whose examples ran at pinned versions, and it's rebuilt with every new edition. When a library changes, the book and its skill change together.

This repository is generated from the books, so changes made here are overwritten. To correct a skill, open a pull request on its book's repository: the procedures are its `skill.md`.

## The skills

| Book | Skill | Edition | Examples |
| --- | --- | --- | --- |
| [Business Intelligence with Agents](https://rollingedition.com/business-intelligence-with-agents) | `business-intelligence-with-agents` | 2026.11.7 | 78 of 78 examples pass |
| [Data Governance as Code](https://rollingedition.com/data-governance-as-code) | `data-governance-as-code` | 2026.11.22 | 108 of 108 examples pass |
| [Model Context Protocol in Practice](https://rollingedition.com/model-context-protocol-in-practice) | `model-context-protocol-in-practice` | 2026.11.10 | 70 of 70 examples pass |
| [Open Table Formats](https://rollingedition.com/open-table-formats) | `open-table-formats` | 2026.11.5 | 39 of 39 examples pass |
| [A Primer on Search Relevance](https://rollingedition.com/primer-on-search-relevance) | `primer-on-search-relevance` | 2026.11.6 | 132 of 132 examples pass |
| [Time Series Forecasting](https://rollingedition.com/time-series-forecasting) | `time-series-forecasting` | 2026.11.3 | 41 of 41 examples pass |

## Install

**Claude Code:** add the catalog once, then one book, or every book with the MCP server:

```sh
/plugin marketplace add rollingedition/agent-skills
/plugin install business-intelligence-with-agents@rolling-edition
/plugin install rolling-edition@rolling-edition
```

A new edition is a new version of its plugin. `claude plugin update business-intelligence-with-agents@rolling-edition` fetches it, or turn on auto-update for this catalog in `/plugin`.

**Claude (chat and Cowork):** in Customize, Plugins, add this repository as a marketplace, and install `rolling-edition`.

**Other agents** (Codex, Cursor, GitHub Copilot and more), with the [skills](https://skills.sh) CLI:

```sh
npx skills add rollingedition/agent-skills --skill business-intelligence-with-agents
```

Or from rollingedition.ai, which lists every skill for the same command:

```sh
npx skills add https://rollingedition.ai
```

Each book's page on [rollingedition.ai](https://rollingedition.ai/) also has its skill as a zip.

## Licence

CC BY 4.0, as the books are. Each skill's `LICENSE.md` gives the credit to use.
