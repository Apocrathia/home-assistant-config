# Session preamble

Cold-start context for a fresh agent session on Home Assistant Homelab.

## What this project is

This directory is the live Home Assistant config — modular YAML under
`packages/`, ESPHome under `esphome/`, agent steering under `.agents/`.

See [`README.md`](../../README.md) and [`.agents/context/README.md`](../context/README.md).

## How to route

Read [`AGENTS.md`](../../AGENTS.md) and follow its routing table. Pull only the
context module your task touches. See [`.agents/context/loading.md`](../context/loading.md).

## Before you edit

Edit in the **main checkout**. Do not create git worktrees
([`worktrees.md`](../rules/worktrees.md)). Do not commit or push
([`operator-owned-git.md`](../rules/operator-owned-git.md)).

## Work ledgers

- Agent gaps: [`docs/issues/`](../../docs/issues/README.md)
- How-work: [`docs/plans/`](../../docs/plans/README.md)
- Human reports: Local Todo UI (ICS read-only — see
  [`work-sources.md`](../context/work-sources.md))

## If you're looking for work

Run `find-work` (read-only). See [`development-loop.md`](../context/development-loop.md).
