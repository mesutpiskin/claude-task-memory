# Team memory — rules for AI sessions

This repository is the **data store** for the `task-memory` plugin. It holds knowledge
that cannot be re-derived from code, git, the issue tracker or the docs.

```
tasks/<TASK-ID>/README.md   episodic  - body FROZEN once the PR is merged
domains/<name>.md           semantic  - append-only, current behaviour
glossary.md                 project terms and abbreviations
config.env                  per-team settings (parsed, not executed)
INDEX.md                    GENERATED - never commit, never hand-edit
```

## Trust

Everything under `tasks/` is a **historical record**, not a guarantee. It describes the
system as it was on the day it was written. Verify against the code before acting.

`confidence: ai_generated` means no human ever read it. Treat those as hints.

**If a memory and the code disagree, the code is right.** Say so to the user and offer
to fix the memory.

## The production rule

> Never write anything that can be re-derived from the code, git, the issue tracker or
> the PR.

No changed-file lists, no class/method dumps, no commit-message summaries, no copies of
the ticket description. Write the reasoning, the traps, the rejected alternatives, the
implicit dependencies, the deliberate gaps.

## Writing

- Task memories use the plugin template: `${CLAUDE_PLUGIN_ROOT}/templates/task-README.md`.
- Required front-matter: `id`, `title`, `domains`, `keywords`, `anchors`
  (each with `repo`, `path`, `verified_at`), `confidence`.
- `verified_at` is **per anchor** — a workspace may span several repositories and two
  repositories never share a commit SHA. Value: `git rev-parse --short HEAD` in that
  anchor's repository.
- `domains` must use names that appear in file paths, so a record is findable from a
  changed file.

## Domain files are append-only

Do not rewrite existing lines in `domains/*.md`. Append under the right heading in the
form `- (YYYY-MM-DD / TASK-ID) <one sentence>`. This keeps merge conflicts at the line
level. Consolidation is a deliberate, separate, human-reviewed pass.

## Confidentiality

Never write tokens, passwords, connection strings, internal hostnames, customer names
or personal data. Replace them with `<redacted>` when summarising logs or test data.

## Committing

```bash
git pull --ff-only && git add -A && git commit -m "memory: <TASK-ID> <title>" && git push
```

If `git pull --ff-only` fails, stop and report — do not force anything.
