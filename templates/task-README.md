---
# --- REQUIRED (6) ---
id: TASK-ID
title: One line summary
domains: [billing]                     # names that appear in file paths
keywords: [searchable, terms, here]
anchors:
  - repo: billing-service
    path: src/billing/InvoiceReconciler.java
    verified_at: abc1234               # `git rev-parse --short HEAD` in THAT repo
confidence: ai_generated               # set to `reviewed` once a human read it

# --- OPTIONAL ---
status: in_review                      # in_progress | in_review | done | abandoned
related_tasks:
  - { id: PROJ-390, rel: depends_on, note: short reason }
  - { id: PROJ-478, rel: superseded_by, note: short reason }
prs: ["billing-service#1234"]
docs:
  - { title: Design doc title, url: "https://..." }
owners: [username]
created: YYYY-MM-DD
---

## One line

<What was this work, in a single sentence.>

## Why (the reasoning that is NOT in the ticket)

<Do not copy the ticket. Only the context that exists nowhere else. Delete this
section if there is nothing to add.>

## Decisions and rejected alternatives

- <Decision>
  Why: <reason>
  Rejected: <alternative> — <why it lost>

## Traps / warnings

<Things a person reading the code would not notice. This section carries most of
the value of the whole file.>

## Known gaps

- [ ] <Gap left on purpose, and why>
