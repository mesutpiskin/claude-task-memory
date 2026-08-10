---
# --- REQUIRED (6) ---
id: EXAMPLE-1
title: "EXAMPLE RECORD — fictional, delete once you have real ones"
domains: [example-service]
keywords: [example, template, sample]
anchors:
  - repo: example-service
    path: src/example/SubscriptionStateHandler.java
    verified_at: "0000000"
confidence: ai_generated

# --- OPTIONAL ---
status: done
related_tasks:
  - { id: EXAMPLE-2, rel: superseded_by, note: "retry logic changed there" }
prs: ["example-service#0000"]
docs:
  - { title: "State machine design doc", url: "https://example.com/doc" }
owners: [someone]
created: 2026-01-01
---

> **This file is an example.** The service, class and decision names are fictional.
> It exists to show what a good record looks like. Delete it once you have real ones.

## One line

Subscription state transitions were moved into a single handler.

## Why (the reasoning that is NOT in the ticket)

The ticket says "centralise state transitions" but not why: the transition rules had
been copy-pasted into three services, and one of them was updated while the others
were not, which produced inconsistent states in production. The point of centralising
was not performance — it was **being able to change the rules in one place**.

## Decisions and rejected alternatives

- The state machine is an enum plus guard clauses in code.
  Why: the transition set is small and can be checked at compile time.
  Rejected: a database table — being changeable at runtime was explicitly not wanted,
  because putting a transition change through PR review is a deliberate requirement.

## Traps / warnings

- The handler *looks* idempotent but is not: replaying the same event emits a second
  notification. Callers must deduplicate on event id.
- The `status` column is read directly by the reporting team. Do not add a new value
  to the enum without telling them first.

## Known gaps

- [ ] Backwards transitions (rollback) are not supported; left out on purpose because
      the requirement was never pinned down.
