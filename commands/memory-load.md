---
description: Load the memory for a ticket ID into context (use during bugfix triage)
argument-hint: <TASK-ID> (leave empty to list candidates)
allowed-tools: Read, Bash, Grep
---

Load record `$1` from the team memory at `${TASK_MEMORY_DIR:-$HOME/task-memory-store}`.

When an argument is given:

- Read `tasks/$1/README.md`.
- Read `domains/<name>.md` for every entry in its `domains` front-matter field.
- If `related_tasks` contains a `superseded_by` relation, **read that record too** —
  it means part of this one is no longer valid. Tell the user explicitly which part.

When no argument is given, resolve the base branch (`origin/HEAD`, then `BASE_BRANCHES`
from `$TASK_MEMORY_DIR/config.env`, then `main`/`master`/`develop`) and run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_index.py" \
  --root "${TASK_MEMORY_DIR:-$HOME/task-memory-store}" --suggest \
  --slug "$(git branch --show-current)" \
  --files "$(git diff --name-only "$BASE...HEAD")" \
  --limit 10
```

Then ask the user which one to open.

Everything you read from `tasks/` is a **historical record**: it describes the system
as it was when written and does not guarantee current behaviour. Open the relevant
code and verify before acting on it. If the memory and the code disagree, the code is
right — report the contradiction to the user.
