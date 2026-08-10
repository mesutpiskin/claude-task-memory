---
description: Draft a task memory from this branch, then commit it after approval
argument-hint: [TASK-ID] (defaults to the ID in the branch name)
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

Run the `memory-writer` subagent to draft a task memory from the work on this branch.
If `$1` is not given, take the ticket ID from the branch name.

When the subagent returns:

1. Show the generated `README.md` to the user **verbatim**. Do not summarise it — this
   is exactly what they are approving.
2. Highlight every line marked `[UNVERIFIED]` and ask the user to confirm or correct it.
3. Show the proposed domain lines. If the user accepts, **append** them to the right
   section of `domains/<name>.md`; never rewrite existing lines. "Domain impact: none"
   is a valid answer, but it must be a deliberate choice rather than a silent omission.
4. Set `confidence: reviewed` only if the user actually read the content. If they just
   said "ok" without reading, leave `ai_generated` — inflating this field is what makes
   the whole memory untrustworthy later.
5. After approval:

```bash
cd "${TASK_MEMORY_DIR:-$HOME/task-memory-store}"
git pull --ff-only && git add -A \
  && git commit -m "memory: <TASK-ID> <title>" && git push
```

If `git pull --ff-only` fails, do not push. Report it to the user and resolve the
divergence together.
