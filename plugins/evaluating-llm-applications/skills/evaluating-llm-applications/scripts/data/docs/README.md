# sablefile documentation

These are the reference pages for sablefile, a command-line tool that keeps a project's generated files in step with a configuration file. The tool and these pages are invented for the book *Evaluating LLM Applications*. Example names, values and addresses are placeholders. Example addresses use reserved names such as `example.org` and the documentation range `192.0.2.0/24`.

## Licence

These pages are licensed under the Creative Commons Attribution 4.0 International licence (CC BY 4.0). The sablefile code is licensed under the MIT licence.

## Versions

Three versions are documented, in folders named `1.0`, `1.1` and `2.0`. Each folder holds the same set of files. Version 2.0 is the newest. The `CHANGELOG.md` in the `1.1` and `2.0` folders lists the sections that changed from the version before, by section ID.

## Section IDs

Every `##` heading ends with an explicit section ID, such as `{#sync-default}`. The IDs are fixed once they are published. The table lists every ID and the versions that contain it.

| Section ID | Heading | 1.0 | 1.1 | 2.0 |
| --- | --- | --- | --- | --- |
| `apply-flag` | The `--apply` flag | no | no | yes |
| `check-command` | What check reports | yes | yes | yes |
| `check-exit-status` | Exit status of check | yes | yes | yes |
| `config-file` | The configuration file | yes | yes | yes |
| `config-files-table` | The file tables | yes | yes | yes |
| `config-values` | The values table | yes | yes | yes |
| `diff-command` | What diff shows | yes | yes | yes |
| `diff-scope` | Which files diff covers | yes | yes | yes |
| `drift-meaning` | What drift means | yes | yes | yes |
| `glossary-terms` | Terms used in these docs | yes | yes | yes |
| `ignore-file` | The ignore file | yes | yes | yes |
| `ignore-recursive` | The double-star pattern | yes | yes | yes |
| `ignore-syntax` | Syntax of ignore entries | yes | yes | yes |
| `init-command` | What init creates | yes | yes | yes |
| `init-directory` | Choose the folder for init | yes | yes | yes |
| `install-archive` | Install from the archive | yes | yes | yes |
| `install-check-version` | Check the installed version | yes | yes | yes |
| `install-uninstall` | Remove sablefile | yes | yes | yes |
| `install-upgrade` | Upgrade to a newer version | yes | yes | yes |
| `lock-migration` | Migrating an older lock file | no | no | yes |
| `lock-mode` | File modes in the lock | no | yes | yes |
| `lockfile` | The lock file | yes | yes | yes |
| `no-fail-flag` | The `--no-fail` flag | no | no | yes |
| `placeholders` | Placeholders | yes | yes | yes |
| `quickstart-check` | Check for drift | yes | yes | yes |
| `quickstart-edit-template` | Add a template and a file entry | yes | yes | yes |
| `quickstart-first-sync` | Run the first sync | yes | yes | yes |
| `quickstart-init` | Create the configuration file | yes | yes | yes |
| `remote-fetch-failure` | When a remote fetch fails | yes | yes | yes |
| `remote-retries` | Retries for remote fetches | yes | yes | yes |
| `remote-templates` | Remote templates | yes | yes | yes |
| `retries-flag` | The `--retries` flag | no | no | yes |
| `sync-create-dirs` | Folders for targets | yes | yes | yes |
| `sync-default` | What sync does by default | yes | yes | yes |
| `sync-exit-status` | Exit status of sync | yes | yes | yes |
| `sync-lock-update` | Lock entries after sync | yes | yes | yes |
| `template-render` | How a template is rendered | yes | yes | yes |
| `templates-location` | Where templates live | yes | yes | yes |
| `troubleshoot-command-not-found` | The command is not found | yes | yes | yes |
| `troubleshoot-drift` | Investigate unexpected drift | yes | yes | yes |
