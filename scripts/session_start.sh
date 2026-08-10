#!/usr/bin/env bash
# SessionStart hook: loads the task memory matching the ticket ID in the branch name.
# When there is no exact match it SUGGESTS candidate records instead — a bugfix
# almost always gets a NEW ticket ID, so exact matching alone would come up empty
# in exactly the situation this system exists for.
#
# Output contract: exit 0 and stdout is injected into the session context.
# Never exit non-zero: a broken hook must not break the developer's session.

set -uo pipefail

MEM="${TASK_MEMORY_DIR:-$HOME/task-memory-store}"
MAX_CHARS=8000   # safe upper bound for hook output

# --- 1. Is the memory repo present? Fail loudly, never silently. ---
if [ ! -d "$MEM/.git" ]; then
  echo "[task-memory] Memory repository not found at: $MEM"
  echo "Setup:  git clone <your-memory-repo-url> \"$MEM\""
  echo "Custom location: export TASK_MEMORY_DIR=/your/path"
  exit 0
fi

# --- 2. Optional per-team config, read from the memory repo. ---
# Parsed key by key rather than sourced: the memory repo is writable by the whole
# team, and `source`-ing it would turn any commit there into code execution on
# every developer's machine.
cfg() {
  local key="$1" default="$2" file="$MEM/config.env" val=""
  if [ -f "$file" ]; then
    val=$(grep -E "^[[:space:]]*${key}=" "$file" 2>/dev/null | tail -1 \
          | sed -E "s/^[[:space:]]*${key}=//; s/^['\"]//; s/['\"][[:space:]]*$//")
  fi
  printf '%s' "${val:-$default}"
}

TASK_ID_PATTERN=$(cfg TASK_ID_PATTERN '[A-Z][A-Z0-9]+-[0-9]+')
BASE_BRANCHES=$(cfg BASE_BRANCHES 'main master develop')

# --- 3. Freshness. Stale memory misleads silently, which is worse than no memory. ---
# Only warn when a remote actually exists; a false alarm on every startup erodes trust.
if git -C "$MEM" remote | grep -q .; then
  if ! timeout 10 git -C "$MEM" pull --ff-only -q 2>/dev/null; then
    LAST=$(git -C "$MEM" log -1 --format=%cr 2>/dev/null || echo "unknown")
    echo "[task-memory] WARNING: could not update memory (last commit: $LAST). Content may be stale."
  fi
fi

PY=$(command -v python3 || command -v python || true)
[ -z "$PY" ] && echo "[task-memory] python3 not found; index and suggestions disabled."

BRANCH=$(git branch --show-current 2>/dev/null || echo "")
TASK_ID=$(printf '%s' "$BRANCH" | grep -oE "$TASK_ID_PATTERN" | head -1)

# --- 4. Changed files. Suggestion quality depends entirely on this list, so it
# must never end up silently empty. origin/HEAD is frequently unset on fresh
# clones, so walk a cascade of candidate base branches. ---
detect_changed() {
  local base out candidates
  candidates="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)"
  for b in $BASE_BRANCHES; do candidates="$candidates origin/$b"; done
  for b in $BASE_BRANCHES; do candidates="$candidates $b"; done
  for base in $candidates; do
    [ -n "$base" ] || continue
    git rev-parse --verify --quiet "$base" >/dev/null || continue
    out=$(git diff --name-only "$base...HEAD" 2>/dev/null)
    [ -n "$out" ] && { printf '%s\n' "$out"; return; }
  done
  # No base branch resolved: fall back to the recent commits on this branch.
  git diff --name-only "HEAD~5..HEAD" 2>/dev/null \
    || git show --name-only --format= HEAD 2>/dev/null
}
CHANGED=$(detect_changed | grep -v '^$' | head -50)

echo "<task-memory>"

# --- 5a. Exact match: load the task memory. ---
if [ -n "$TASK_ID" ] && [ -f "$MEM/tasks/$TASK_ID/README.md" ]; then
  echo "## Task memory: $TASK_ID"
  echo ""
  echo "> HISTORICAL RECORD. This file describes the system as it was when written."
  echo "> It does NOT guarantee current behaviour. Treat it as a hypothesis: read the"
  echo "> relevant code and verify before acting on anything stated here."
  echo "> If the memory and the code disagree, THE CODE IS RIGHT — say so to the user."
  echo ""
  head -c "$MAX_CHARS" "$MEM/tasks/$TASK_ID/README.md"
  echo ""

# --- 5b. No match: suggest candidates. This is the bugfix path. ---
else
  if [ -n "$TASK_ID" ]; then
    echo "## No memory stored for $TASK_ID (likely a new task or a bugfix)."
  else
    echo "## No ticket ID found in the branch name."
  fi
  echo ""
  if [ -n "$PY" ]; then
    echo "Candidate records matched on branch name and changed files:"
    echo ""
    "$PY" "$(dirname "$0")/build_index.py" --root "$MEM" --suggest \
        --slug "$BRANCH" --files "$CHANGED" --limit 8 2>/dev/null \
      || echo "(could not generate suggestions)"
    echo ""
    echo "Open a relevant one with: /memory-load <TASK-ID>"
  fi
fi

# --- 6. Do not auto-load domain files (progressive disclosure); just list them. ---
if [ -d "$MEM/domains" ]; then
  echo ""
  echo "Domain memories available (read one only if relevant):"
  ls -1 "$MEM/domains" 2>/dev/null | grep -v "^_" | sed "s|^|  - domains/|"
fi

echo "</task-memory>"
exit 0
