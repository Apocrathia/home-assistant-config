---
alwaysApply: true
description: Write the minimum change that solves the problem; touch only what the request requires
---

# Surgical edits

Two discipline rules for config and code changes, derived from [Andrej Karpathy's
observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding
pitfalls. The other two principles (think before coding, goal-driven execution)
are covered by [`clarify-dont-guess.md`](./clarify-dont-guess.md) and
[`ground-before-asking.md`](./ground-before-asking.md).

**Tradeoff:** these bias toward caution over speed. For trivial tasks, use
judgment.

## Simplicity first

Minimum YAML/code that solves the problem. Nothing speculative.

Before writing anything, climb the ladder (stop at the first rung that holds):

1. Does this need to exist at all? Speculative need = skip it.
2. Already in this codebase? Reuse it — look in `packages/` before you write.
3. Existing package pattern covers it? Follow nomenclature and neighbors.
4. Helper / template / built-in HA feature covers it? Prefer that over custom.
5. Can it be a small addition to an existing package file? Prefer that.
6. Only then: the minimum new config that works.

Then apply these constraints to whatever you write:

- No features beyond what was asked.
- No abstractions for single-use automations.
- No flexibility or configurability that wasn't requested.
- No speculative branches for states that can't occur.
- If you write a large block and it could be a small one, rewrite your own new code.
- Push back when a simpler approach exists; say so before implementing.

The test: would a senior HA operator say this is overcomplicated? If yes,
simplify.

## Surgical changes

Touch only what you must. Clean up only your own mess.

When editing existing packages:

- Don't improve adjacent automations, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead config, mention it; don't delete it.

When your changes create orphans:

- Remove entities, helpers, or references that your changes made unused.
- Don't remove pre-existing dead config unless asked.

The test: every changed line should trace directly to the request.

## Scope

**Simplicity first** applies to config you are writing now (introduced in the
current change). **Surgical changes** applies to existing config you are touching.
You may rewrite aggressively within your own new blocks; touch surgically when
editing what was already there.

## When this applies

All config and code edits (YAML packages, ESPHome, scripts, utilities). Not
docs; see [`humanizer.md`](./humanizer.md) and
[`.agents/context/voice.md`](../context/voice.md) for doc discipline.

Protected paths still need confirmation
([`protected-paths.md`](./protected-paths.md)). No commits
([`operator-owned-git.md`](./operator-owned-git.md)).
