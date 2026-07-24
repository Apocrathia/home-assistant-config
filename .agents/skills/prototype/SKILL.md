---
name: prototype
description: >-
  Build a throwaway prototype under .scratch/ to answer a design question.
  Use when the user wants to sanity-check automation/state logic, explore a
  dashboard or notification shape, or says prototype or /prototype.
disable-model-invocation: true
---

# Prototype — Home Assistant Homelab

A prototype is **throwaway work that answers a question**. The question decides
the shape. Put it under [`.scratch/`](../../../.scratch/README.md) — never use
`packages/` as a throwaway playground.

Git is operator-owned
([`operator-owned-git.md`](../../rules/operator-owned-git.md)): do not commit
scratch contents. Promote validated decisions into tracked paths later.

## Pick a branch

Identify which question is being answered — from the user's prompt, nearby
config, or by asking:

| Question                                    | Shape                                                                                                    |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| "Does this logic / state model feel right?" | Tiny script, state diagram, or YAML sketch that walks hard cases (triggers, conditions, modes)           |
| "What should this look like?"               | Dashboard card mock, notification copy variants, or lovelace YAML drafts — multiple options side by side |
| "Where should this live?"                   | Package placement sketch + entity naming table (still scratch; not a live package)                       |

If the question is ambiguous and the operator isn't reachable, default to the
logic branch for automations/packages and the look branch for UI/dashboard
asks — state the assumption at the top of the prototype.

## Rules

1. **Throwaway and marked as such.** Create under `.scratch/<slug>/` with a
   short README stating the question and that it is disposable.
2. **Never throwaway under `packages/`.** Scratch is not loaded by Home
   Assistant. Promoting into `packages/`, `esphome/`, `utilities/`, or `docs/`
   is a separate, explicit step after the question is answered.
3. **One command to run** when there is runnable code (`python path`,
   `bash path`, etc.). Prefer zero-deps scripts.
4. **No persistence by default.** In-memory or a clearly named scratch file
   (`PROTOTYPE — wipe me`). Do not write `.storage/` or `.shopping_list.json`.
5. **Skip the polish.** No tests beyond what makes it runnable, no abstractions.
6. **Surface the state.** After each action or variant switch, print/show the
   full relevant state so the operator can see what changed.
7. **Capture the answer, not the junk.** When done, record the verdict (what
   was learned) in chat. If promoting, move only the validated decision into
   the right tracked path via [`implement-change`](../implement-change/SKILL.md)
   / HA domain skills — leave the scratch tree disposable.

## Workflow

```
- [ ] 1. Name the question and pick logic vs look vs placement
- [ ] 2. Create .scratch/<slug>/ with a one-paragraph README
- [ ] 3. Build the smallest artifact that answers the question
- [ ] 4. Run / walk cases with the operator
- [ ] 5. Write the verdict; recommend promote path or drop
```

## Promote vs drop

| Outcome            | Action                                                                                    |
| ------------------ | ----------------------------------------------------------------------------------------- |
| Decision validated | Hand off to implement-change / package-organize / automation path with acceptance bullets |
| Still fuzzy        | [`alignment`](../alignment/SKILL.md) or another prototype slug                            |
| Dead end           | Leave under `.scratch/`; do not commit; optional delete                                   |

## Do not

- Commit, push, or open PRs for prototypes
- Edit live `packages/` "just to try something"
- Treat scratch YAML as source of truth for Home Assistant
- Invent `docs/research/` or issue files for the prototype writeup
