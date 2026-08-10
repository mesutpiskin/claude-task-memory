# Contributing

Thanks for looking. This is a small plugin with a strong opinion; the opinion is more
likely to be wrong than the code, so design feedback is as welcome as patches.

## The most useful contribution

Tell us **where retrieval fails on your codebase**. The suggestion ranking in
`scripts/build_index.py` is a heuristic tuned against a handful of repositories. If it
surfaces the wrong record, an issue containing the branch name, the changed file list
and what you expected to see is worth more than a feature PR.

## Ground rules

**Everything is English.** Skills, agents, commands, templates, code comments, docs.

**No hard dependencies.** git, bash and python3 only. PyYAML is optional and there is a
fallback parser; keep it that way.

**The hook must never break a session.** `scripts/session_start.sh` exits 0 under every
condition. Failures print a visible warning instead — a hook that fails silently is the
worst outcome, because the developer keeps trusting a system that stopped working.

**Do not execute anything from the memory repo.** It is writable by a whole team.
`config.env` is parsed key by key, deliberately, and must stay that way.

**Keep hook output small.** It is injected into every session. `MAX_CHARS` is 8000 and
domain files are listed, never loaded — progressive disclosure is a design constraint,
not an optimisation.

## Versioning

The version lives in **two** files. Bump both or `/plugin update` misbehaves:

- `.claude-plugin/plugin.json` → `version`
- `.claude-plugin/marketplace.json` → `metadata.version` and `plugins[0].version`

## Testing

There is no test framework yet; run these three scenarios by hand. The second one is
the important one — it is the reason the project exists.

```bash
export TASK_MEMORY_DIR=~/task-memory-store

# 1. Syntax
bash -n scripts/session_start.sh
python3 -m py_compile scripts/build_index.py
python3 -c "import json;[json.load(open(f)) for f in ['.claude-plugin/plugin.json','.claude-plugin/marketplace.json','hooks/hooks.json']]"

# 2. Exact match: on a branch whose ticket ID has a stored record
git checkout feature/PROJ-406-state-machine
bash /path/to/claude-task-memory/scripts/session_start.sh

# 3. Suggestion: on a NEW ticket ID, it must still surface the old record
git checkout -b fix/PROJ-478-retry-duplicate
bash /path/to/claude-task-memory/scripts/session_start.sh
```

Also run scenario 2 with PyYAML uninstalled; the fallback parser must produce the same
output.

## Scope

In scope: retrieval quality, staleness detection, making the write step cheaper.

Out of scope for now: a web UI, a database backend, automatic memory generation without
human review. The last one is tempting and is exactly how this turns into landfill —
`confidence: reviewed` has to mean a human read it.
