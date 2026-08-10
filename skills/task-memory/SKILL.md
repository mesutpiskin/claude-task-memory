---
name: task-memory
description: Use when reading or writing team memory — when a ticket ID is mentioned (e.g. PROJ-406), when the user asks how something was built or decided in the past, what to watch out for in a service or module, or when a piece of work is finished and its context should be recorded. Triggers on "how was this done before", "what did we decide about this", "what should I watch out for here", "save this to memory", "write a memory". Reads task and domain memories from the team memory repository and writes new ones from the shared template.
---

# Task Memory

The team memory lives in a separate git repository: `$TASK_MEMORY_DIR`
(default `~/task-memory-store`).

```
tasks/<TASK-ID>/README.md   episodic  - body FROZEN once the PR is merged
domains/<name>.md           semantic  - append-only, grows over time
glossary.md                 project terms and abbreviations
config.env                  optional per-team settings
```

The two layers answer different questions. A task memory answers "what happened in
PROJ-406 and why did we do it that way". A domain memory answers "how does this part
of the system behave today". When they disagree, the domain memory is the current one.

## Reading

Search narrowly first. Never read every memory file.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_index.py" \
  --root "${TASK_MEMORY_DIR:-$HOME/task-memory-store}"
```

Then open at most one or two relevant files. Prefer the domain memory for current
behaviour and the task memory for background on a decision.

### Trust rules — do not skip these

Everything under `tasks/` is a **historical record**. It describes the system as it
was on the day it was written. Read the relevant code and verify before acting on it.

Records with `confidence: ai_generated` were never reviewed by a human. Use them as
hints, not as facts.

**If a memory and the code disagree, the code is right.** Point the contradiction out
to the user and offer to correct the memory — a wrong memory that stays in place will
mislead the next person too.

Do not read external documentation content out of a memory file; memories only store
links. Fetch the live page when the content is actually needed.

## Writing

A new task memory goes to `tasks/<TASK-ID>/README.md`. Template:
`${CLAUDE_PLUGIN_ROOT}/templates/task-README.md`.

### What to write, what to leave out

One rule decides whether this system is valuable or landfill:

> **Never write anything that can be re-derived from the code, git, the issue tracker
> or the PR.**

Do NOT write: the list of changed files, a dump of class and method names, a summary
of commit messages, a copy of the ticket description, "I added method X".

DO write: why this approach was chosen and why the alternative was rejected; business
rule nuances that are invisible in the code; surprises and traps ("this looks
idempotent but is not"); approaches that were tried and failed; implicit dependencies
("the reporting team reads this column"); gaps left on purpose and the reason.

Sanity check: if you deleted a sentence and the information would come back after
twenty minutes of reading code, do not write it. If somebody would have to *tell* you,
write it.

### Required front-matter (6 fields)

`id`, `title`, `domains`, `keywords`, `anchors` (each with `repo`, `path`,
`verified_at`), `confidence`.

`verified_at` is stored **per anchor**, because a workspace may span several
repositories and two repositories never share a commit SHA. Its value is
`git rev-parse --short HEAD` in the repository that anchor points at.

`domains` should use names that appear in file paths (service, module or package
names), so a memory can be found from a changed file.

### Domain impact — never skip this step

After writing a task memory, always ask: did this work produce knowledge that outlives
the task?

- If yes, **append a line** to the matching `domains/<name>.md` under
  `## Recurring traps` or `## Decisions`. Do not rewrite existing text. Append-only
  keeps merge conflicts at the line level when two developers touch the same domain
  file in the same week.
- Format: `- (YYYY-MM-DD / TASK-ID) <one sentence>`
- If no, say "domain impact: none" explicitly. Do not skip it silently.

### Confidentiality

Never write tokens, passwords, connection strings, internal hostnames, customer names
or personal data into a memory. When summarising logs or test data, replace them with
`<redacted>`.

### Committing

Show the file to the user and ask for approval before committing. After approval:

```bash
cd "${TASK_MEMORY_DIR:-$HOME/task-memory-store}"
git pull --ff-only && git add -A \
  && git commit -m "memory: <TASK-ID> <title>" && git push
```

Set `confidence: reviewed` only when the user actually read the content. If they
approved without reading, leave `ai_generated`. This field is the only signal that
stops a wrong AI summary from being taken as fact six months from now — inflating it
destroys the trustworthiness of the whole system.
