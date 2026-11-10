# Rolling Edition agent skills

You learned a method from a book. Your coding agent should follow the same one. Each skill here is one of Rolling Edition's books in the Agent Skills format: the book's procedures, step by step, each step linked to the section it comes from, with the chapters as references and the examples as scripts.

Every skill is built from its book's current edition, whose examples ran at pinned versions, and it's rebuilt with every new edition. When a library changes, the book and its skill change together.

This repository is generated from the books, so changes made here are overwritten. To correct a skill, open a pull request on its book's repository: the procedures are its `skill.md`.

## The skills

| Book | Skill | Edition | Examples |
| --- | --- | --- | --- |

## Install

**Claude Code:**

```sh
/plugin marketplace add rollingedition/agent-skills
/plugin install BOOK@rolling-edition
```

A new edition updates the plugin's version. `/plugin install books@rolling-edition` adds the MCP server, to search, read and cite every book.

**Other agents** (Codex, Cursor, GitHub Copilot and more), with the [skills](https://skills.sh) CLI:

```sh
npx skills add rollingedition/agent-skills --skill BOOK
```

Or download one skill as a zip from its book's page on [rollingedition.ai](https://rollingedition.ai/).

## Licence

CC BY 4.0, as the books are. Each skill's `LICENSE.md` gives the credit to use.
